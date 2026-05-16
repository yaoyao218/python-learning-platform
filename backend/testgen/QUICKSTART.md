# QUICKSTART — 在本機把新測資集跑起來看效果

> 3 道關卡：預檢 → HTTP 測試 → 真實 server。每關過了再進下一關，
> 出問題時範圍就被縮到很小。

## 關卡 0：先裝套件（5 秒）

```bash
cd backend
pip install -r requirements.txt
```

## 關卡 1：純 Python 預檢（10 秒）

```bash
python -m testgen.smoke_test
```

**全綠的話會看到：**

```
=== 預檢 1：核心模組 import ===
  ✓  import problem / judge / executor  (problem.TEST_CASES = 17 筆)
  ✓  import ai（依賴 openai）

=== 預檢 2：problem.py 格式檢查 ===
  ✓  每筆 schema 齊全（index/input/expected/is_stress）
  ✓  測資 index 不重複

=== 預檢 3：reference 正解全過 ===
  ✓  reference 全過 problem.TEST_CASES  (17/17 通過)

=== 預檢 4：6 個錯誤解都會被攔下 ===
  ✓  always_len.py        (被擋下：#1 input='abcabcbb')
  ✓  count_unique.py      (被擋下：#3 input='pwwkew')
  ✓  inner_return.py      (被擋下：#3 input='pwwkew')
  ✓  no_reset_left.py     (被擋下：#4 input='gogn')
  ✓  no_return.py         (被擋下：#1 input='abcabcbb')
  ✓  off_by_one_window.py (被擋下：#1 input='abcabcbb')

=== 預檢 5：ai.build_prompt 對各失敗類型能組 prompt ===
  ✓  build_prompt for syntax_error  (prompt 長度 = 178)
  ✓  build_prompt for runtime_error (prompt 長度 = 192)
  ✓  build_prompt for no_return     (prompt 長度 = 152)
  ✓  build_prompt for wrong_answer  (prompt 長度 = 458)

=== 預檢結果 ===
  ✓ 所有預檢通過！
```

**有紅字怎麼辦：**
- `ImportError: openai` → `pip install -r requirements.txt` 重跑
- `reference 全過 (16/17)` → 表示新測資有 bug，回 testgen/ 看 feedback_v4.json
- `survivors=[xxx_bug.py]` → 有錯誤解漏網，要補 killer mode

## 關卡 2：HTTP 層測試（10 秒，不啟 uvicorn）

```bash
python -m testgen.http_smoke_test
```

用 FastAPI TestClient 從 HTTP 層測 `/submit`，會跑 4 個劇本：
- 正解全過
- `return len(s)` 在 #1 fail
- `return len(set(s))` 在 #3 fail
- 語法錯誤觸發 syntax_error 分支

關卡 1 跟關卡 2 全綠，表示後端線上行為跟你預期一致。

## 關卡 3：跑真實 server

**Terminal 1：**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

看到 `Uvicorn running on http://0.0.0.0:8000`。

**Terminal 2：**
```bash
cd frontend
npm install   # 第一次
npm run dev
```

打開 `http://localhost:5173`。

把 [TESTING_GUIDE.md](TESTING_GUIDE.md) 裡的 6 段程式碼貼進編輯器，逐個驗證
「第一個失敗位置 + AI 提示」是否如預期。

## 三道全綠後

```bash
git status
git add backend/testgen/ backend/problem.py backend/problem_old.py \
        backend/tests/test_problem_quality.py \
        backend/tests/test_main.py backend/tests/test_judge.py
git commit -m "feat: 套用論文 feedback-driven 方法重做測資集 (TNR 0.49→0.88)"
git push
```

Render / Vercel 自動部署完成後到 https://python-learning-platform-chi.vercel.app/
重新測一次 #1-3 的劇本，確認線上行為一致。

## 邊寫邊紀錄（demo / 報告素材用）

如果你想模擬學生寫程式的整個過程，把每次提交都留下紀錄供事後翻查：

### 方法 A：用真實前端（Monaco 編輯器）+ 後端 logger

啟動後端時打開 `TESTGEN_SESSION_LOG=1`：

```bash
cd backend
# Windows:
set TESTGEN_SESSION_LOG=1 && python -m uvicorn main:app --reload --port 8000
# Linux/Mac:
TESTGEN_SESSION_LOG=1 uvicorn main:app --reload --port 8000
```

正常啟動前端 `npm run dev`，在 Monaco 寫/貼程式碼按提交，每次都會自動寫進
`backend/testgen/sessions/<日期>.jsonl`。

事後翻查：

```bash
python -m testgen.view_session              # 看當天所有提交
python -m testgen.view_session --last 5     # 只看最後 5 次
python -m testgen.view_session --summary    # 統計：AC 比例、平均耗時、最常踩雷的測資
```

### 方法 B：純 CLI 模擬（不用啟 server，最快）

```bash
python -m testgen.play
# （貼程式碼後 Ctrl-D 結束）
```

或從檔案：

```bash
python -m testgen.play --file my_solution.py
```

會印出：
- judge 跑了 17 筆耗時多少
- 第一個失敗位置（學生會看到的）
- 所有失敗的測資（debug 用）
- 組給 Groq 的 AI prompt 長度跟預覽
- Groq 回的 AI 提示
- 完整 trace 自動寫進 session log

這是做 demo 的最理想工具——一個指令就把完整 pipeline 視覺化。

## 回滾

```bash
cd backend
cp problem_old.py problem.py
python -m testgen.smoke_test   # 應該 fail（baseline TNR 0.49 過不了守門員）
```
