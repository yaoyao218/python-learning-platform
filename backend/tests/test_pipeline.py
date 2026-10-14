"""test_pipeline.py — testgen/pipeline.py 的停止條件與彙整（只讀真實的 rounds 紀錄，不呼叫 API、不寫檔）。"""
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from testgen import pipeline, rounds   # noqa: E402


def test_is_converged_requires_all_three_conditions():
    ok = {"TPR": 1.0, "uncaught": [], "achievement": 0.9}
    assert pipeline.is_converged(ok, 0.85)
    assert not pipeline.is_converged(dict(ok, TPR=0.98), 0.85)
    assert not pipeline.is_converged(dict(ok, uncaught=["x"]), 0.85)
    assert not pipeline.is_converged(dict(ok, achievement=0.84), 0.85)


def test_stop_reasons_match_recorded_runs():
    # LC121：第 3 輪沒有保留任何新測資 → 停滯
    assert pipeline.stop_reason("best-time-stock", 3, 4, 0.85) == "stalled"
    # LC32：已跑到第 5 輪，超過上限 4
    assert pipeline.stop_reason("longest-valid-parentheses", 5, 4, 0.85) == "max_rounds"
    # LC3：只有第 0 輪、未收斂、還沒到上限 → 要繼續（K16：全自動輪次已刪除）
    assert pipeline.stop_reason("longest-substring", 0, 4, 0.85) is None


def test_round_rows_follow_tests_files():
    rows = pipeline.round_rows("longest-valid-parentheses", 5)
    assert [r["round"] for r in rows] == [0, 1, 2, 3, 4, 5]
    for r in rows:
        stored = json.loads(rounds.round_path("longest-valid-parentheses", r["round"], "tests").read_text(encoding="utf-8"))
        assert r["n_cases"] == len(stored["cases"])
        assert r["TNR"] == stored["evaluation"]["TNR"]


def test_heldout_recorded_once_per_problem():
    for pid in ("best-time-stock", "longest-valid-parentheses"):
        held = json.loads((rounds.rounds_dir(pid) / "heldout_final.json").read_text(encoding="utf-8"))
        assert held["round"] == pipeline.last_round(pid)
        assert held["TPR"] == 1.0


def test_unparsable_reply_is_not_recorded_as_a_round(tmp_path, monkeypatch):
    """AI 回覆整份讀不出 JSON 時，propose 要失敗退出、不寫 rN_candidates.json，pipeline 才不會誤判停滯。"""
    import shutil
    import pytest
    from testgen import propose
    pid = "valid-parentheses"
    shutil.copy(rounds.round_path(pid, 0, "tests"), tmp_path / "r0_tests.json")
    monkeypatch.setattr(rounds, "rounds_dir", lambda problem_id: tmp_path)
    monkeypatch.setattr(propose, "BACKEND", tmp_path)          # 只影響印出的相對路徑
    monkeypatch.setattr(propose, "call_model", lambda *a, **kw: ('[{"candidates": []}]', None))
    monkeypatch.setattr(sys, "argv", ["propose", "--problem", pid, "--round", "1"])
    with pytest.raises(SystemExit):
        propose.main()
    assert not rounds.round_path(pid, 1, "candidates").exists()
    assert len(list(tmp_path.glob("r1_candidates.unparsed.*.json"))) == 1
