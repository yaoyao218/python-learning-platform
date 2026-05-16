# Python 學習平台 — 前端

Vue 3 + Vite 前端，對應後端 `POST /submit` API。

## 啟動

```bash
npm install
npm run dev
# http://localhost:5173
```

## 元件說明

| 元件 | 功能 |
|---|---|
| `App.vue` | 左右兩欄佈局、提交邏輯、冷啟動偵測（>5秒顯示提示） |
| `ProblemStatement.vue` | 題目描述 + 3 個 LeetCode 官方範例卡片 |
| `CodeEditor.vue` | Monaco Editor（Python, vs-dark theme） |
| `ResultPanel.vue` | 測試結果（顯示到第一個 FAIL）+ AI 提示卡 |

## API 端點切換

`api.js` 透過 `import.meta.env.DEV` 自動切換：
- 本機開發 → `http://localhost:8000`
- 線上部署 → `https://python-learning-platform-88vh.onrender.com`

## 線上網址

https://python-learning-platform-chi.vercel.app/
