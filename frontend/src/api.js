import axios from 'axios'

const BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000'
  : 'https://python-learning-platform-88vh.onrender.com'

export async function fetchProblemList() {
  const response = await axios.get(`${BASE_URL}/problems`)
  return response.data  // [{ id, title, difficulty }, ...]
}

export async function fetchProblem(problemId) {
  const response = await axios.get(`${BASE_URL}/problems/${problemId}`)
  return response.data  // { id, title, difficulty, description, examples, constraints, starter_code }
}

export async function submitCode(code, problemId) {
  const response = await axios.post(
    `${BASE_URL}/submit`,
    { code, problem_id: problemId },
    { timeout: 60000 }
  )
  return response.data  // { results: [...], hint: string|null }
}
