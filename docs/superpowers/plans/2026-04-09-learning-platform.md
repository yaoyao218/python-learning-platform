# Python 學習平台 — 實作計畫（已完成）

> **狀態：** 全部 Task 已完成並部署上線。
>
> **線上網址：** https://python-learning-platform-chi.vercel.app/
> **GitHub：** https://github.com/yaoyao218/python-learning-platform

---

## 完成摘要

| Task | 內容 | 狀態 |
|---|---|---|
| 1 | 後端專案建立（requirements, pytest.ini, .env） | ✅ |
| 2 | problem.py — 17 組測試案例（論文方法 v4） | ✅ |
| 3 | executor.py — ThreadPoolExecutor 跨平台執行 + AST 安全過濾 | ✅ |
| 4 | judge.py — asyncio.gather 並行跑 17 組 | ✅ |
| 5 | ai.py — Groq/Gemini 自動切換，4 種 prompt 分支 | ✅ |
| 6 | main.py — FastAPI POST /submit + CORS | ✅ |
| 7 | 前端 Vue 3 + Vite 專案建立 | ✅ |
| 8 | api.js — DEV/PROD URL 自動切換 | ✅ |
| 9 | ProblemStatement.vue | ✅ |
| 10 | CodeEditor.vue — Monaco Editor | ✅ |
| 11 | ResultPanel.vue — 結果 + AI 提示 | ✅ |
| 12 | App.vue — 左右兩欄佈局 | ✅ |
| 13 | 部署 Vercel（前端）+ Render（後端） | ✅ |
| 14 | testgen/ — 論文方法測資生成（TNR 0.49 → 0.88） | ✅ |
| 15 | test_problem_quality.py — 品質守門員 | ✅ |

## 與原始計畫的差異

| 項目 | 原始計畫 | 實際實作 |
|---|---|---|
| 測資數 | 18 筆 hardcoded | 17 筆（論文方法生成，TNR=0.88） |
| executor | asyncio.create_subprocess_exec | ThreadPoolExecutor + subprocess.run（Windows 相容） |
| AI Provider | Groq only | Groq / Gemini 自動切換 |
| API URL | 固定 localhost | DEV/PROD 自動切換 |
| 路徑 | /home/auxe/Desktop/畢業專題/ | 相對路徑（git repo 根目錄） |

## 部署資訊

| 服務 | 平台 | URL |
|---|---|---|
| 前端 | Vercel | https://python-learning-platform-chi.vercel.app/ |
| 後端 | Render | https://python-learning-platform-88vh.onrender.com |
| 原始碼 | GitHub | https://github.com/yaoyao218/python-learning-platform |
