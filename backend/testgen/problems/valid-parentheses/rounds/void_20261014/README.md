# 作廢的第一次執行（2026-10-14）

這個資料夾是 valid-parentheses 第一次跑 `pipeline.py` 的完整紀錄，**不計入實驗**，原樣保留備查。

- 第 1 輪 AI（openai/gpt-oss-120b）把回覆多包了一層陣列（`[{"candidates": [...]}]`），`propose.py` 讀不出來，
  卻照樣寫成 `r1_candidates.json`（0 筆候選）。
- `pipeline.py` 因此把第 1 輪當成「沒有保留任何新測資」，判定停滯而結束，並在第 1 輪測資（＝第 0 輪原本的 12 道）上
  跑了驗收池：TNR 0.1389，漏網 無（`heldout_final.json`）。
- 這是工具的 bug，不是方法的結果：一次 API 格式失敗被當成一整輪。已修正 `propose.py`（讀不出 JSON 時另存為
  `rN_candidates.unparsed.*.json` 並失敗退出，pipeline 會從同一輪接續），並加測試
  `tests/test_pipeline.py::test_unparsable_reply_is_not_recorded_as_a_round`。
- 修正後從第 1 輪重跑。**驗收池因此是第二次使用**：第一次只看到上面這個數字，沒有任何人根據它做選擇
  （流程全自動、參數不變），但仍屬偏離「驗收池只跑一次」的規則，於此註明。決定者：目前負責本 repo 的組員（2026-10-14）。
