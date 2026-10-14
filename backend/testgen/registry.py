"""registry.py — testgen 支援的題目清單，以及每題的 S+/S- 池位置、參考解、TNR 上限。

每題的資料放在 testgen/problems/<problem_id>/ 底下：

    problems/<problem_id>/
    ├── solutions_correct/   S+ 池
    ├── solutions_wrong/     S- 訓練池
    ├── solutions_heldout/   S- 驗收池（迭代期間不使用）
    ├── spec.py              輸入規格：validate / random_args / small_args
    └── feedback_<label>.json

例外：LC3（longest-substring）的 S+ / S- 訓練池與 feedback 是 AI 輔助實驗之前就有的
歷史紀錄，留在 testgen/ 根目錄不搬動；它的驗收池仍放在 problems/longest-substring/。

新增題目時：在 problem.PROBLEMS 加題目、建好上面的資料夾、在 TESTGEN_PROBLEMS 登記。
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent

# problem_id → {
#   reference: S* 檔名（在 solutions_correct/ 裡）
#   ceiling:   TNR 上限，由 `python -m testgen.assess_problem` 估算後填入
#   converged: 測資是否已收斂；False 時品質守門員 skip（第 0 輪只有官方範例，一定不達標）
# }
TESTGEN_PROBLEMS: dict[str, dict] = {
    "longest-substring": {"reference": "sliding_window.py", "ceiling": 1.0, "converged": True},
    # 上限 5/6：no_clamp_zero 只在答案為 0 時答錯，這種輸入抓不到其他大多數 S-（assessment.json）
    "best-time-stock": {"reference": "one_pass.py", "ceiling": 5 / 6, "converged": False},
    "longest-valid-parentheses": {"reference": "stack_index.py", "ceiling": 1.0, "converged": False},
    # 上限 1/2：單筆輸入最多抓到 3 個 S-（assessment.json）
    "valid-parentheses": {"reference": "stack_match.py", "ceiling": 0.5, "converged": False},
    "median-two-sorted-arrays": {"reference": "merge_two_pointer.py", "ceiling": 1.0, "converged": False},
}

# 歷史紀錄留在 testgen/ 根目錄的題目
_LEGACY = {"longest-substring"}


def _check(problem_id: str) -> None:
    if problem_id not in TESTGEN_PROBLEMS:
        raise KeyError(f"testgen 尚未登記題目 {problem_id!r}；已登記：{list(TESTGEN_PROBLEMS)}")


def problem_dir(problem_id: str) -> Path:
    """該題的 testgen/problems/<problem_id>/ 目錄。"""
    _check(problem_id)
    return HERE / "problems" / problem_id


def feedback_dir(problem_id: str) -> Path:
    """run_eval 寫 feedback_<label>.json 的位置。"""
    _check(problem_id)
    return HERE if problem_id in _LEGACY else problem_dir(problem_id)


def pool_dir(problem_id: str, kind: str) -> Path:
    """kind: 'correct'（S+）、'wrong'（S- 訓練池）、'heldout'（S- 驗收池）"""
    _check(problem_id)
    if problem_id in _LEGACY and kind in ("correct", "wrong"):
        return HERE / f"solutions_{kind}"
    return problem_dir(problem_id) / f"solutions_{kind}"


def reference_path(problem_id: str) -> Path:
    return pool_dir(problem_id, "correct") / TESTGEN_PROBLEMS[problem_id]["reference"]


def ceiling(problem_id: str) -> float:
    value = TESTGEN_PROBLEMS[problem_id]["ceiling"]
    if value is None:
        raise ValueError(f"{problem_id} 還沒估算 TNR 上限，先跑 python -m testgen.assess_problem --problem {problem_id}")
    return value


def converged(problem_id: str) -> bool:
    return TESTGEN_PROBLEMS[problem_id]["converged"]


def load_spec(problem_id: str):
    """載入該題的 spec.py（資料夾名稱含連字號，不能直接 import）。"""
    path = problem_dir(problem_id) / "spec.py"
    spec = importlib.util.spec_from_file_location(f"testgen_spec_{problem_id.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
