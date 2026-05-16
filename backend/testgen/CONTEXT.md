# testgen/ — 一頁快速 onboarding

> 完整背景見 [`/CLAUDE.md`](../../CLAUDE.md) 跟 [`PROGRESS.md`](PROGRESS.md)。
> 這份是給「打開 testgen/ 後想立刻動手」的最精簡入門。

## 它在幹嘛

論文方法的本地實作。離線收斂高品質測資集 → 替換 `backend/problem.py`。
線上服務（main.py / judge.py 等）完全沒動。

**已上線狀態**：TPR=1.0 / **TNR=0.88**（原 0.49）。17 筆測資，每個 bug 都被至少一筆抓到。

## 一頁圖

```
   gen.py（10 mode）           solutions_correct/  solutions_wrong/
        │                            │                  │
        ▼                            ▼                  ▼
commands_v{N}.txt ──▶ synthesize.py ──▶ tests_v{N}.py
                                              │
                                              ▼
                                       run_eval.py ──▶ feedback_v{N}.json
                                              │           │
                                              ▼           ▼
                              （TPR ≥ 1.0 且 TNR ≥ 0.85）├ command_value
                                              │           ├ S_minus_pass_rates
                                              ▼           └ false_positives
                                  export_to_problem_py.py
                                              │
                                              ▼
                                       problem_v{N}.py
                                              │
                                              ▼
                                  cp → backend/problem.py（線上生效）
```

## 想做什麼 → 跑哪個指令

| 我要... | 指令 |
|---|---|
| 看現在 problem.py 的 TPR/TNR | `python -m testgen.run_eval --tests problem --label current` |
| 確認線上服務沒壞 | `python -m testgen.smoke_test` |
| 不啟 server 測 HTTP /submit | `python -m testgen.http_smoke_test` |
| 模擬一個學生提交看完整 trace | `python -m testgen.play --file my_sol.py` |
| 開後端 logger 紀錄真實提交 | `TESTGEN_SESSION_LOG=1 uvicorn main:app --reload` |
| 看 session log | `python -m testgen.view_session --summary` |
| 加新 bug 跑迭代 | 看 `CLAUDE.md` 的「怎麼加新 bug pattern」 |
| 回滾 | `cp problem_old.py problem.py` |

## 看圖看數字

- 完整實驗 4 輪迭代：`PROGRESS.md`
- 本機操作三道關卡：`QUICKSTART.md`
- 前端手動測試清單：`TESTING_GUIDE.md`
- 每輪反饋報告：`feedback_v{N}.json`（裡面有 command_value 跟 S_minus_pass_rates）

## 解耦保證

- 沒設 `TESTGEN_SESSION_LOG=1` → session_logger 是 no-op
- 沒 import testgen → main.py 用 try/except 抓住，照樣跑
- `problem_old.py` 一直保留 → 一秒回滾
