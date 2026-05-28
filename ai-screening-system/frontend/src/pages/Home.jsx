// src/pages/Home.jsx
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Brain, Zap, Database, FileText, ChevronRight, Cpu } from 'lucide-react'

const ROLES = [
  { label: 'AI/ML Engineer', color: 'var(--accent)', icon: Brain },
  { label: 'Backend Engineer', color: 'var(--accent-2)', icon: Cpu },
  { label: 'Data Scientist', color: 'var(--accent-3)', icon: Database },
  { label: 'Full Stack Engineer', color: 'var(--warning)', icon: Zap },
]

const FEATURES = [
  {
    icon: FileText,
    title: 'Resume-Aware Questions',
    desc: 'Questions adapt to your actual background — not generic templates.',
  },
  {
    icon: Database,
    title: 'RAG-Grounded Context',
    desc: 'Every question is anchored in a curated knowledge base for the role.',
  },
  {
    icon: Brain,
    title: 'AI Answer Evaluation',
    desc: 'Real-time scoring and constructive feedback after each answer.',
  },
  {
    icon: Zap,
    title: 'Adaptive Difficulty',
    desc: 'Interview adapts based on how you're performing as you go.',
  },
]

const stagger = {
  initial: {},
  animate: { transition: { staggerChildren: 0.08 } },
}
const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] } },
}

export default function Home() {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <header style={{ padding: '20px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, background: 'var(--accent)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Brain size={18} color="#fff" />
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18 }}>PG<span style={{ color: 'var(--accent)' }}>AGI</span> Screener</span>
        </div>
        <span className="badge badge-accent">v1.0</span>
      </header>

      <main style={{ flex: 1, maxWidth: 900, margin: '0 auto', padding: '80px 24px 60px', width: '100%' }}>
        <motion.div variants={stagger} initial="initial" animate="animate">
          {/* Eyebrow */}
          <motion.div variants={fadeUp} style={{ marginBottom: 20 }}>
            <span className="badge badge-accent">
              <span className="pulse" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
              AI-Powered Technical Screening
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1 variants={fadeUp} style={{ fontSize: 'clamp(36px, 6vw, 68px)', marginBottom: 24, lineHeight: 1.05 }}>
            Your resume.<br />
            <span style={{ color: 'var(--accent)' }}>Your interview.</span>
          </motion.h1>

          <motion.p variants={fadeUp} style={{ fontSize: 18, color: 'var(--text-secondary)', maxWidth: 560, marginBottom: 48, lineHeight: 1.7 }}>
            Upload your resume, pick a role, and get a fully personalised AI interview grounded in a real knowledge base — with instant feedback on every answer.
          </motion.p>

          {/* CTA */}
          <motion.div variants={fadeUp}>
            <button className="btn btn-primary" style={{ fontSize: 16, padding: '14px 32px' }} onClick={() => navigate('/interview/setup')}>
              Start Interview <ChevronRight size={18} />
            </button>
          </motion.div>

          {/* Role chips */}
          <motion.div variants={fadeUp} style={{ marginTop: 56, display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.1em', alignSelf: 'center' }}>Supported roles:</span>
            {ROLES.map(({ label, color, icon: Icon }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 100, padding: '6px 14px', fontSize: 13 }}>
                <Icon size={13} color={color} />
                {label}
              </div>
            ))}
          </motion.div>

          {/* Divider */}
          <hr className="divider" style={{ marginTop: 72 }} />

          {/* Features */}
          <motion.div variants={fadeUp} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginTop: 40 }}>
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card card-hover" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ width: 36, height: 36, background: 'var(--bg-hover)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={18} color="var(--accent)" />
                </div>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6 }}>{desc}</div>
                </div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </main>

      <footer style={{ padding: '20px 32px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>PGAGI AI Screening System</span>
        <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}>Powered by RAG + LLM</span>
      </footer>
    </div>
  )
}
