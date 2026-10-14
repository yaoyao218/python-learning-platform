# 交接文件（已停用）

> 2026-10-13 起，組員的工作清單、進度與問題紀錄**只看一份**：
> [`docs/superpowers/specs/teammate-guide.md`](superpowers/specs/teammate-guide.md)

這份文件 2026-10-07 版本裡的任務 A–D（評測分流 `score_candidates.py`、人工審核介面 `review.py`、彙整、收尾工具）**已經作廢**：

- 2026-10-13 負責人決定**拿掉人工審核**，研究改為驗證全自動流程能否運行（組員指南問題紀錄 K18）。
- 評測與審核改由 `backend/testgen/auto_review.py` 自動進行，整條流程用 `python -m testgen.pipeline` 一個指令跑完（組員指南任務 E6）。
- 匯出工具已由 `backend/testgen/export_round_to_problem.py` 完成（組員指南任務 E4）。

完整的方法、結果與偏離原計畫的紀錄：[`docs/superpowers/plans/2026-10-07-ai-assisted-testgen.md`](superpowers/plans/2026-10-07-ai-assisted-testgen.md) 第八節。
