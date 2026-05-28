// src/pages/Results.jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { CheckCircle2, XCircle, Minus, ChevronDown, ChevronUp, RefreshCw, Home } from 'lucide-react'
import { getSummary } from '../services/api'

const RECO_CONFIG = {
  strong_yes: { label: 'Strong Hire',     color: 'var(--success)', icon: CheckCircle2 },
  yes:        { label: 'Hire',            color: 'var(--accent)',  icon: CheckCircle2 },
  maybe:      { label: 'Consider',        color: 'var(--warning)', icon: Minus },
  no:         { label: 'Not Recommended', color: 'var(--danger)',  icon: XCircle },
}

function ScoreGauge({ score }) {
  const color = score >= 75 ? 'var(--success)' : score >= 50 ? 'var(--warning)' : 'var(--danger)'
  const data = [{ value: score, fill: color }]
  return (
    <div style={{ position: 'relative', width: 180, height: 180, margin: '0 auto' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" startAngle={90} endAngle={-270} data={data}>
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: 'var(--border)' }} dataKey="value" cornerRadius={8} angleAxisId={0} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <span style={{ fontSize: 36, fontWeight: 800, color, fontFamily: 'var(--font-display)' }}>{score}</span>
        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>/ 100</span>
      </div>
    </div>
  )
}

function QuestionAccordion({ q, index }) {
  const [open, setOpen] = useState(false)
  const scoreColor = q.score >= 7 ? 'var(--success)' : q.score >= 4 ? 'var(--warning)' : 'var(--danger)'
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left', color: 'var(--text-primary)' }}
      >
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>Q{index + 1}</span>
        <span style={{ flex: 1, fontSize: 14, fontWeight: 500, lineHeight: 1.4 }}>{q.question_text}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {q.score !== null && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: scoreColor, fontWeight: 600 }}>{q.score}/10</span>
          )}
          {open ? <ChevronUp size={14} color="var(--text-muted)" /> : <ChevronDown size={14} color="var(--text-muted)" />}
        </div>
      </button>
      {open && (
        <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} style={{ overflow: 'hidden' }}>
          <div style={{ padding: '0 20px 16px', display: 'flex', flexDirection: 'column', gap: 12, borderTop: '1px solid var(--border)' }}>
            <div style={{ paddingTop: 12 }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Candidate Answer</div>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7 }}>{q.candidate_answer || '(no answer)'}</p>
            </div>
            {q.ai_feedback && (
              <div style={{ background: 'var(--bg-hover)', padding: 12, borderRadius: 'var(--radius-sm)', borderLeft: `2px solid ${scoreColor}` }}>
                <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>AI Feedback</div>
                <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7 }}>{q.ai_feedback}</p>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default function Results() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSummary(sessionId)
      .then(r => setSummary(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Loading results…</p>
      </div>
    )
  }

  if (!summary) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'var(--text-muted)' }}>Results not found.</p>
    </div>
  )

  const reco = RECO_CONFIG[summary.recommendation] || RECO_CONFIG.maybe
  const RecoIcon = reco.icon

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '48px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

        {/* Header */}
        <div>
          <div className="badge badge-accent" style={{ marginBottom: 12 }}>Interview Complete</div>
          <h1 style={{ fontSize: 32, marginBottom: 4 }}>{summary.candidate_name}</h1>
          <p style={{ color: 'var(--text-secondary)' }}>{summary.target_role} · {summary.questions.length} questions</p>
        </div>

        {/* Score + Recommendation */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overall Score</div>
            <ScoreGauge score={summary.overall_score ?? 0} />
          </div>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Recommendation</div>
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: `${reco.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RecoIcon size={28} color={reco.color} />
            </div>
            <div style={{ fontWeight: 700, fontSize: 20, color: reco.color }}>{reco.label}</div>
          </div>
        </div>

        {/* Narrative */}
        {summary.narrative && (
          <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>AI Assessment</div>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>{summary.narrative}</p>
          </div>
        )}

        {/* Strengths & Weaknesses */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div className="card">
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--success)', textTransform: 'uppercase', marginBottom: 12 }}>Strengths</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {summary.strengths.length ? summary.strengths.map((s, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
                  <CheckCircle2 size={14} color="var(--success)" style={{ flexShrink: 0, marginTop: 2 }} />
                  {s}
                </li>
              )) : <li style={{ color: 'var(--text-muted)', fontSize: 13 }}>None identified</li>}
            </ul>
          </div>
          <div className="card">
            <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--danger)', textTransform: 'uppercase', marginBottom: 12 }}>Areas to Improve</div>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {summary.weaknesses.length ? summary.weaknesses.map((w, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
                  <XCircle size={14} color="var(--danger)" style={{ flexShrink: 0, marginTop: 2 }} />
                  {w}
                </li>
              )) : <li style={{ color: 'var(--text-muted)', fontSize: 13 }}>None identified</li>}
            </ul>
          </div>
        </div>

        {/* Q&A Transcript */}
        <div>
          <h2 style={{ fontSize: 18, marginBottom: 16 }}>Interview Transcript</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {summary.questions.map((q, i) => (
              <QuestionAccordion key={i} q={q} index={i} />
            ))}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/')}>
            <Home size={14} /> Home
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/interview/setup')}>
            <RefreshCw size={14} /> New Interview
          </button>
        </div>
      </motion.div>
    </div>
  )
}
