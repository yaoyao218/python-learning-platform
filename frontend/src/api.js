import axios from 'axios'

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : 'https://python-learning-platform-88vh.onrender.com'

export async function submitCode(code) {
  const response = await axios.post(`${BASE_URL}/submit`, { code }, { timeout: 60000 })
  return response.data  // { results: [...], hint: string|object|null }
}

export async function submitHint(code, results, selectedText, attempt) {
  const response = await axios.post(
    `${BASE_URL}/hint`,
    { code, results, selected_text: selectedText, attempt },
    { timeout: 30000 },
  )
  return response.data  // { correct: bool, hint?: string, message?: string, options?: [...] }
}
