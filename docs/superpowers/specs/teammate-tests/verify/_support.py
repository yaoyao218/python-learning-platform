# -*- coding: utf-8 -*-
"""驗收測試共用工具（負責人用；組員不要修改這個資料夾，scope_check 會標出）。

設計原則（因為實作者可能是 AI，會傾向「讓測試過關」而不是「把事情做對」）：
  * 以「即時計算的真值（live oracle）」比對，而不是比對寫死的雜湊或答案；
  * 輸入由驗收者當下的 VERIFY_SEED 產生，每次不同；
  * 所有會執行受測實作的呼叫都放在獨立子程序，並有硬性逾時，實作卡死也不會拖垮驗收；
  * 另有靜態檢查（不得在主程序 exec、不得寫死基準雜湊）。
"""
import importlib.util
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]                    # docs/superpowers/specs/teammate-tests/verify -> repo root
BACKEND = REPO / "backend"
BASELINE_JSON = HERE.parents[1] / "baseline_assess.json"
sys.path.insert(0, str(BACKEND))

IMPL_FILE = Path(os.environ.get("SAFE_BATCH_FILE", BACKEND / "testgen" / "safe_batch.py"))
EXECUTOR_FILE = Path(os.environ.get("EXECUTOR_FILE", BACKEND / "executor.py"))
SEED = int(os.environ.get("VERIFY_SEED", str(int(time.time()) % 1_000_000)))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 殘留程序偵測（不需要 psutil）
def descendants(pid: int) -> list[int]:
    """回傳 pid 的所有子孫程序 id（Windows 用 PowerShell，其餘用 ps）。列舉用的工具程序本身會被排除。
    找不到工具時丟出 RuntimeError。"""
    if os.name == "nt":
        cmd = ["powershell", "-NoProfile", "-Command",
               "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId),$($_.ParentProcessId)\" }"]
    else:
        cmd = ["ps", "-eo", "pid=,ppid="]
    try:
        lister = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        out, _ = lister.communicate(timeout=60)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"無法列出程序：{e}")
    pairs = []
    for ln in out.splitlines():
        parts = ln.replace(",", " ").split()
        if len(parts) == 2 and all(x.isdigit() for x in parts):
            pairs.append((int(parts[0]), int(parts[1])))
    kids: dict[int, list[int]] = {}
    for p_, pp in pairs:
        kids.setdefault(pp, []).append(p_)
    ignore = {lister.pid}
    found, stack = [], [pid]
    while stack:
        cur = stack.pop()
        for k in kids.get(cur, []):
            if k not in found and k not in ignore:
                found.append(k)
                stack.append(k)
    return found


RUNNER = r'''
import json, os, subprocess, sys, time, importlib.util
cfg = json.loads(sys.stdin.read())
sys.path.insert(0, cfg["backend"])
spec = importlib.util.spec_from_file_location("sb_under_test", cfg["impl"])
sb = importlib.util.module_from_spec(spec); spec.loader.exec_module(sb)
inputs = [tuple(a) for a in cfg["inputs"]]
t0 = time.time()
res = sb.evaluate_solution(cfg["code"], cfg["method"], inputs, **cfg["kwargs"])
wall = time.time() - t0
ERR = getattr(sb, "ERR", object())
def conv(o):
    return "__ERR__" if o is ERR else o
out = {"wall": wall, "status": getattr(res, "status", None),
       "outputs": [conv(o) for o in getattr(res, "outputs", [])],
       "timed_out_at": getattr(res, "timed_out_at", None),
       "elapsed_attr": getattr(res, "elapsed", None),
       "fields": {f: hasattr(res, f) for f in ("outputs", "status", "timed_out_at", "elapsed")}}
if cfg.get("check_descendants"):
    time.sleep(cfg.get("settle", 1.5))
    sys.path.insert(0, cfg["support_dir"])
    import _support
    out["descendants"] = _support.descendants(os.getpid())
sys.stdout.write("\n@@RESULT@@" + json.dumps(out, default=repr))
'''


def call_impl(code: str, method: str, inputs, hard_timeout: float = 120.0, check_descendants: bool = False, **kwargs) -> dict:
    """在獨立子程序呼叫受測的 evaluate_solution。實作若卡死，hard_timeout 到了就判定失敗。"""
    cfg = {"backend": str(BACKEND), "impl": str(IMPL_FILE), "code": code, "method": method,
           "inputs": [list(a) for a in inputs], "kwargs": kwargs, "check_descendants": check_descendants,
           "support_dir": str(HERE)}
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        r = subprocess.run([sys.executable, "-c", RUNNER], input=json.dumps(cfg, default=repr), capture_output=True,
                           text=True, encoding="utf-8", timeout=hard_timeout, env=env)
    except subprocess.TimeoutExpired:
        raise AssertionError(f"實作在 {hard_timeout} 秒內沒有返回（可能在主程序執行了 AI 程式，或逾時機制失效）")
    if "@@RESULT@@" not in r.stdout:
        raise AssertionError("實作呼叫失敗（沒有回傳結果）。stderr 末段：\n" + r.stderr[-1500:])
    return json.loads(r.stdout.rsplit("@@RESULT@@", 1)[1])


# ---------------------------------------------------------------- 題庫與真值
def pools(pid: str):
    """回傳 {(kind, name): code} —— 人工寫的池（可信），含 S+、S-、驗收。"""
    from testgen import registry
    out = {}
    for kind in ("correct", "wrong", "heldout"):
        d = registry.pool_dir(pid, kind)
        if d.exists():
            for p in sorted(d.glob("*.py")):
                out[(kind, p.stem)] = p.read_text(encoding="utf-8")
    return out


def make_inputs(pid: str, n_random: int = 300, n_small: int = 500, seed: int = SEED):
    from testgen import registry
    spec = registry.load_spec(pid)
    rng = random.Random(seed)
    rnd = [spec.random_args(rng) for _ in range(n_random)]
    small = list(spec.small_args())
    rng.shuffle(small)
    return rnd + small[:n_small]


def oracle_outputs(pid: str, code: str, inputs):
    """即時真值：在主程序以 assess_problem 的方式執行（只用於可信的人工池）。"""
    from testgen import assess_problem as ap
    from problem import PROBLEMS
    method = PROBLEMS[pid]["method"]
    ns: dict = {}
    exec(code, ns)
    call = getattr(ns["Solution"](), method)
    return ["__ERR__" if (o := ap.run(call, a)) is ap._ERR else o for a in inputs]


def same(a, b) -> bool:
    if a == "__ERR__" or b == "__ERR__":
        return a == b
    from testgen import assess_problem as ap
    return ap.same(a, b)
