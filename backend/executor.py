import ast
import asyncio
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

FORBIDDEN_MODULES = {"os", "sys", "subprocess", "socket", "multiprocessing", "threading", "ctypes", "importlib"}

_thread_pool = ThreadPoolExecutor(max_workers=8)


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
    """同步執行子程序，在 ThreadPoolExecutor 裡呼叫。跨平台相容。"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", runner_script],
            capture_output=True,
            timeout=timeout,
        )
        return (
            result.stdout.decode().strip(),
            result.stderr.decode().strip(),
            result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ("", "執行超時（超過時間限制）", -1)


async def run_code(code: str, input_val: str, timeout: float = 5.0) -> dict:
    """
    在 ThreadPoolExecutor 執行學生程式碼，跨平台相容（Linux / Windows）。

    Returns:
        dict: { actual: str|None, error_type: str|None, stderr: str }
        error_type 可能值: "syntax_error" | "runtime_error" | "no_return" | None
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

    runner_script = f"""{code}

_sol = Solution()
_result = _sol.lengthOfLongestSubstring({repr(input_val)})
print(_result)
"""

    loop = asyncio.get_event_loop()
    stdout_str, stderr_str, returncode = await loop.run_in_executor(
        _thread_pool, _run_subprocess, runner_script, timeout
    )

    if returncode == -1:
        return {"actual": None, "error_type": "runtime_error", "stderr": stderr_str}

    if returncode != 0:
        if "SyntaxError" in stderr_str:
            return {"actual": None, "error_type": "syntax_error", "stderr": stderr_str}
        return {"actual": None, "error_type": "runtime_error", "stderr": stderr_str}

    if stdout_str in ("None", ""):
        return {"actual": None, "error_type": "no_return", "stderr": ""}

    return {"actual": stdout_str, "error_type": None, "stderr": ""}
