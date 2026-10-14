import ast
import asyncio
import re
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

FORBIDDEN_MODULES = {"os", "sys", "subprocess", "socket", "multiprocessing", "threading", "ctypes", "importlib"}

_thread_pool = ThreadPoolExecutor(max_workers=8)

# 回傳值前面加的標記：學生自己 print 的內容都在標記之前，判題只看標記之後
_RESULT_MARKER = "\x00__RESULT__\x00"

# 子程序只帶最少的環境變數，不繼承後端的 GROQ_API_KEY / GEMINI_API_KEY。
# Windows 少了 SYSTEMROOT 會讓 Python 啟動失敗，所以有的話保留。
_CHILD_ENV = {k: os.environ[k] for k in ("SYSTEMROOT",) if k in os.environ}

# 子程序裡的執行包裝。學生程式碼用 exec(compile(..., "<student>")) 執行，
# 錯誤訊息的行號才會對應學生自己的程式碼。
#
# 安全性：AST 檢查（check_forbidden）擋得住 `import os`，但擋不住
# `__import__("os")`。這裡再用 audit hook 擋掉「讀密鑰」與「開子程序／網路」
# 這類動作，hook 一旦裝上，同一個程序內的程式碼就移除不了。
# 這不是完整的沙箱（沒有限制記憶體、沒有隔離檔案系統），只是補上最危險的洞。
_RUNNER_TEMPLATE = """\
import io as _io
import sys as _sys

_BLOCKED_PREFIXES = ("subprocess.", "os.system", "os.exec", "os.posix_spawn",
                     "os.spawn", "os.fork", "os.forkpty", "socket.", "ctypes.")

def _guard(event, args):
    if event == "open":
        path = args[0]
        if isinstance(path, bytes):
            path = path.decode(errors="replace")
        if isinstance(path, str):
            name = path.replace("\\\\", "/").rsplit("/", 1)[-1]
            if path.startswith("/proc") or name.startswith(".env"):
                raise PermissionError("不允許讀取這個檔案")
    elif event.startswith(_BLOCKED_PREFIXES):
        raise PermissionError(f"不允許的操作：{{event}}")

_sys.addaudithook(_guard)

_out = _sys.stdout
_ns = {{"__name__": "__main__"}}
exec(compile({code!r}, "<student>", "exec"), _ns)
if "Solution" not in _ns:
    raise NameError("name 'Solution' is not defined")
_result = _ns["Solution"]().{method}(*{args!r})
_out.write("\\n" + {marker!r} + repr(_result))
"""


def check_forbidden(code: str) -> str | None:
    """Check for forbidden module imports using AST parsing.

    Known limitation (classroom MVP): dynamic imports such as
    __import__("os") or importlib.import_module("os") are NOT caught here.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # SyntaxError is caught later in the subprocess
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    return f"不允許使用 {root} 模組"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_MODULES:
                return f"不允許使用 {root} 模組"
    return None


def _run_subprocess(runner_script: str, timeout: float) -> tuple[str, str, int]:
    """同步執行子程序，在 ThreadPoolExecutor 裡呼叫。跨平台相容。

    程式從 stdin 傳入（`python -`），不放在命令列：命令列有長度上限
    （Windows 32767 字元、Linux 單一參數約 128KB），大型測資放不進去。
    stdin 讀完程式後就是 EOF，學生程式呼叫 input() 會立刻得到 EOFError，不會卡到超時。
    """
    try:
        # -I：隔離模式，不讀 PYTHON* 環境變數、不把工作目錄加進 sys.path
        # -X utf8：Windows 上也用 UTF-8 輸出，學生 print 中文不會解碼失敗
        # cwd 設在暫存目錄，學生用相對路徑讀不到 backend/ 底下的檔案
        result = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-"],
            input=runner_script.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            env=_CHILD_ENV,
            cwd=tempfile.gettempdir(),
        )
        return (
            result.stdout.decode(errors="replace").strip(),
            result.stderr.decode(errors="replace").strip(),
            result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ("", "執行超時（超過時間限制）", -1)


_RUNNER_FRAME = re.compile(r'^\s*File "<stdin>", line \d+, in .*\n?', re.MULTILINE)


def _hide_runner_frames(stderr: str) -> str:
    """去掉 traceback 裡平台包裝腳本（從 stdin 執行）的那幾層，只留學生程式（<student>）的行號。
    否則學生和 AI 會看到「line 26」這種學生程式裡根本不存在的行號。"""
    return _RUNNER_FRAME.sub("", stderr)


async def run_code(code: str, method: str, args: tuple, timeout: float = 5.0) -> dict:
    """
    在 ThreadPoolExecutor 執行學生程式碼，跨平台相容（Linux / Windows）。

    Args:
        method: Solution 類別要呼叫的方法名
        args: 呼叫該方法的位置參數（tuple）

    Returns:
        dict: { actual: str|None, error_type: str|None, stderr: str }
        error_type 可能值: "syntax_error" | "runtime_error" | "timeout" | "no_return" | None
        actual 是 repr() 過的字串，可用 ast.literal_eval 還原成實際型別。
    """
    forbidden_error = check_forbidden(code)
    if forbidden_error:
        return {"actual": None, "error_type": "runtime_error", "stderr": forbidden_error}

    try:
        compile(code, "<student>", "exec")
    except SyntaxError as e:
        lines = [f"SyntaxError: {e.msg} (line {e.lineno})"]
        if e.text:
            lines.append(f"  {e.text.rstrip()}")
            if e.offset:
                lines.append("  " + " " * (e.offset - 1) + "^")
        return {"actual": None, "error_type": "syntax_error", "stderr": "\n".join(lines)}

    runner_script = _RUNNER_TEMPLATE.format(
        code=code, method=method, args=args, marker=_RESULT_MARKER
    )

    loop = asyncio.get_running_loop()
    stdout_str, stderr_str, returncode = await loop.run_in_executor(
        _thread_pool, _run_subprocess, runner_script, timeout
    )

    if returncode == -1:
        return {"actual": None, "error_type": "timeout", "stderr": stderr_str}

    if returncode != 0:
        stderr_str = _hide_runner_frames(stderr_str)
        if "SyntaxError" in stderr_str:
            return {"actual": None, "error_type": "syntax_error", "stderr": stderr_str}
        return {"actual": None, "error_type": "runtime_error", "stderr": stderr_str}

    if _RESULT_MARKER not in stdout_str:
        # 程式正常結束卻沒走到回傳那步（例如學生自己呼叫了 exit()）
        return {"actual": None, "error_type": "runtime_error", "stderr": "程式提前結束，沒有回傳結果"}

    actual = stdout_str.rsplit(_RESULT_MARKER, 1)[1].strip()
    if actual == "None":
        return {"actual": None, "error_type": "no_return", "stderr": ""}

    return {"actual": actual, "error_type": None, "stderr": ""}
