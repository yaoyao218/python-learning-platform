"""registry.py — testgen 支援的題目清單，以及每題的 S+/S- 池位置、參考解、TNR 上限。

每題的資料放在 testgen/problems/<problem_id>/ 底下：

    problems/<problem_id>/
    ├── solutions_correct/   S+ 池
    ├── solutions_wrong/     S- 訓練池
    ├── solutions_heldout/   S- 驗收池（迭代期間不使用）
    └── feedback_<label>.json

例外：LC3（longest-substring）的 S+ / S- 訓練池與 feedback 是 AI 輔助實驗之前就有的
歷史紀錄，留在 testgen/ 根目錄不搬動；它的驗收池仍放在 problems/longest-substring/。

新增題目時：在 problem.PROBLEMS 加題目、建好上面的資料夾、在 TESTGEN_PROBLEMS 登記。
"""
from __future__ import annotations
from pathlib import Path

HERE = Path(__file__).resolve().parent

# problem_id → {reference: S* 檔名, ceiling: TNR 上限（第四節第三關估算）}
TESTGEN_PROBLEMS: dict[str, dict] = {
    "longest-substring": {"reference": "sliding_window.py", "ceiling": 1.0},
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
    return TESTGEN_PROBLEMS[problem_id]["ceiling"]
