// src/services/api.js
import axios from 'axios'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // LLM calls can be slow
})

// Response interceptor — surface errors as toasts
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unexpected error occurred.'
    // 204 = no more questions, handle gracefully upstream
    if (err.response?.status !== 204) {
      toast.error(msg)
    }
    return Promise.reject(err)
  }
)

// ── Sessions ──────────────────────────────────────────────────────────────────

export const uploadResume = (formData) =>
  api.post('/sessions/upload-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getSessionStatus = (sessionId) =>
  api.get(`/sessions/${sessionId}`)

// ── Interview ─────────────────────────────────────────────────────────────────

export const getNextQuestion = (sessionId) =>
  api.get(`/interview/${sessionId}/next-question`)

export const submitAnswer = (sessionId, questionId, answer) =>
  api.post(`/interview/${sessionId}/questions/${questionId}/answer`, { answer })

export const finishInterview = (sessionId) =>
  api.post(`/interview/${sessionId}/finish`)

export const getSummary = (sessionId) =>
  api.get(`/interview/${sessionId}/summary`)

// ── Knowledge Base ────────────────────────────────────────────────────────────

export const getKBStatus = () =>
  api.get('/knowledge-base/status')

export const triggerIngest = () =>
  api.post('/knowledge-base/ingest-all')

export default api
