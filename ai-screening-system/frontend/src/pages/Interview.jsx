// src/pages/Interview.jsx
import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, ChevronRight, Clock, Target, BarChart3, Lightbulb } from 'lucide-react'
import toast from 'react-hot-toast'
import { getNextQuestion, submitAnswer, finishInterview } from '../services/api'

const DIFF_COLOR = { easy: 'var(--success)', medium: 'var(--warning)', hard: 'var(--danger)' }

function DifficultyBadge({ level }) {
  const cls = { easy: 'badge-success', medium: 'badge-warning', hard: 'badge-danger' }
  return <span className={`badge ${cls[level] || 'badge-accent'}`}>{level}</span>
}

function ProgressRing({ current, total }) {
  const pct = (current / total) * 100
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div className="progress-bar" style={{ flex: 1 }}>
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        {current} / {total}
      </span>
    </div>
  )
}

function FeedbackCard({ feedback, score }) {
  const pct = score * 10
  const color = score >= 7 ? 'var(--success)' : score >= 4 ? 'var(--warning)' : 'var(--danger)'
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{ borderColor: color, borderLeftWidth: 3 }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <Lightbulb size={16} color={color} />
        <span style={{ fontWeight: 600, color }}>Score: {score}/10</span>
        <div className="progress-bar" style={{ flex: 1 }}>
          <div className="progress-bar-fill" style={{ width: `${pct}%`, background: color }} />
        </div>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7 }}>{feedback}</p>
    </motion.div>
  )
}

export default function InterviewPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const textareaRef = useRef(null)

  const [phase, setPhase] = useState('loading') // loading | question | feedback | finishing | done
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [history, setHistory] = useState([]) // [{question, answer, score, feedback}]

  // Load first question on mount
  useEffect(() => { loadNextQuestion() }, [])

  const loadNextQuestion = async () => {
    setPhase('loading')
    try {
      const res = await getNextQuestion(sessionId)
      setQuestion(res.data)
      setAnswer('')
      setFeedback(null)
      setPhase('question')
      setTimeout(() => textareaRef.current?.focus(), 300)
    } catch (err) {
      if (err.response?.status === 204) {
        // Interview complete
        await handleFinish()
      }
    }
  }

  const handleSubmitAnswer = async () => {
    if (!answer.trim() || submitting) return
    setSubmitting(true)
    try {
      const res = await submitAnswer(sessionId, question.question_id, answer.trim())
      const { ai_feedback, score, next_question_available } = res.data
      setFeedback({ text: ai_feedback, score })
      setHistory(h => [...h, {
        question: question.question_text,
        answer: answer.trim(),
        score,
        feedback: ai_feedback,
        category: question.category,
        difficulty: question.difficulty,
      }])
      setPhase('feedback')
      if (!next_question_available) {
        // Last question answered
        setTimeout(() => handleFinish(), 3000)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleFinish = async () => {
    setPhase('finishing')
    try {
      await finishInterview(sessionId)
      navigate(`/results/${sessionId}`)
    } catch {
      toast.error('Could not generate summary. Try again.')
      setPhase('feedback')
    }
  }

  const avgScore = history.length
    ? (history.reduce((s, h) => s + h.score, 0) / history.length).toFixed(1)
    : null

  return (
    <div style={{ minHeight: '100vh', display: 'grid', gridTemplateColumns: '1fr', gridTemplateRows: 'auto 1fr', maxWidth: 760, margin: '0 auto', padding: '0 24px' }}>
      {/* ── Sticky Header ──────────────────────────────────────────────── */}
      <header style={{ position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-base)', borderBottom: '1px solid var(--border)', padding: '16px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Target size={16} color="var(--accent)" />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              {question?.category || 'Loading…'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {avgScore && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <BarChart3 size={14} color="var(--accent-3)" />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-3)' }}>avg {avgScore}/10</span>
              </div>
            )}
            {question && <DifficultyBadge level={question.difficulty} />}
          </div>
        </div>
        {question && <ProgressRing current={question.question_number} total={question.total_questions} />}
      </header>

      {/* ── Main Content ────────────────────────────────────────────────── */}
      <main style={{ padding: '32px 0 60px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <AnimatePresence mode="wait">
          {phase === 'loading' && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, paddingTop: 80 }}
            >
              <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
              <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                Generating question…
              </p>
            </motion.div>
          )}

          {phase === 'finishing' && (
            <motion.div key="finishing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, paddingTop: 80 }}
            >
              <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
              <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                Generating your report…
              </p>
            </motion.div>
          )}

          {(phase === 'question' || phase === 'feedback') && question && (
            <motion.div key={`q-${question.question_id}`} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
            >
              {/* Question card */}
              <div className="card" style={{ borderLeft: `3px solid ${DIFF_COLOR[question.difficulty]}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Q{question.question_number}
                  </span>
                  <Clock size={12} color="var(--text-muted)" />
                </div>
                <p style={{ fontSize: 18, fontWeight: 600, lineHeight: 1.5, color: 'var(--text-primary)' }}>
                  {question.question_text}
                </p>
              </div>

              {/* Answer input */}
              {phase === 'question' && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <label className="label">Your answer</label>
                  <textarea
                    ref={textareaRef}
                    className="input"
                    placeholder="Type your answer here… Be thorough and specific."
                    value={answer}
                    onChange={e => setAnswer(e.target.value)}
                    style={{ minHeight: 160 }}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmitAnswer()
                    }}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                      ⌘↵ to submit
                    </span>
                    <button
                      className="btn btn-primary"
                      disabled={!answer.trim() || submitting}
                      onClick={handleSubmitAnswer}
                    >
                      {submitting ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <Send size={14} />}
                      {submitting ? 'Evaluating…' : 'Submit Answer'}
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Feedback */}
              {phase === 'feedback' && feedback && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                  <div className="card" style={{ background: 'var(--bg-hover)', marginBottom: 16 }}>
                    <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Your answer</div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{answer}</p>
                  </div>
                  <FeedbackCard feedback={feedback.text} score={feedback.score} />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
                    <button className="btn btn-primary" onClick={loadNextQuestion}>
                      Next Question <ChevronRight size={14} />
                    </button>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
