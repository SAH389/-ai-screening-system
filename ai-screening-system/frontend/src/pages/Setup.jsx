// src/pages/Setup.jsx
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, X, ChevronRight, Brain, Cpu, Database, Zap, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { uploadResume } from '../services/api'

const ROLES = [
  { value: 'AI/ML Engineer',       icon: Brain,    color: 'var(--accent)',   desc: 'ML pipelines, model training, RAG systems' },
  { value: 'Backend Engineer',      icon: Cpu,      color: 'var(--accent-2)', desc: 'APIs, databases, system design' },
  { value: 'Data Scientist',        icon: Database, color: 'var(--accent-3)', desc: 'Analysis, modelling, feature engineering' },
  { value: 'Full Stack Engineer',   icon: Zap,      color: 'var(--warning)',  desc: 'Frontend + backend integration' },
]

export default function Setup() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [role, setRole] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  })

  const canSubmit = name.trim() && role && file && !loading

  const handleStart = async () => {
    if (!canSubmit) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('candidate_name', name.trim())
      fd.append('target_role', role)
      fd.append('resume', file)
      const res = await uploadResume(fd)
      const { session_id } = res.data
      toast.success('Session created! Starting interview…')
      navigate(`/interview/${session_id}`)
    } catch {
      // toast shown by interceptor
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 24px' }}>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ width: '100%', maxWidth: 640 }}
      >
        {/* Header */}
        <div style={{ marginBottom: 40 }}>
          <div className="badge badge-accent" style={{ marginBottom: 16 }}>Setup</div>
          <h1 style={{ fontSize: 36, marginBottom: 8 }}>Start your interview</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Fill in your details to get a personalised, RAG-grounded technical interview.</p>
        </div>

        {/* Name */}
        <div style={{ marginBottom: 24 }}>
          <label className="label">Your name</label>
          <input
            className="input"
            placeholder="e.g. Arjun Sharma"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        {/* Role selection */}
        <div style={{ marginBottom: 24 }}>
          <label className="label">Target role</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {ROLES.map(({ value, icon: Icon, color, desc }) => (
              <button
                key={value}
                onClick={() => setRole(value)}
                style={{
                  background: role === value ? `rgba(${color === 'var(--accent)' ? '124,109,240' : color === 'var(--accent-2)' ? '240,131,109' : color === 'var(--accent-3)' ? '78,205,196' : '240,194,109'},.15)` : 'var(--bg-card)',
                  border: `1px solid ${role === value ? color : 'var(--border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Icon size={16} color={color} />
                  {role === value && <CheckCircle2 size={14} color={color} />}
                </div>
                <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{value}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Resume upload */}
        <div style={{ marginBottom: 32 }}>
          <label className="label">Resume (PDF / DOCX / TXT)</label>
          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="card"
                style={{ display: 'flex', alignItems: 'center', gap: 12 }}
              >
                <div style={{ width: 36, height: 36, background: 'var(--accent-glow)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FileText size={18} color="var(--accent)" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 500, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</div>
                </div>
                <button onClick={() => setFile(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 4 }}>
                  <X size={16} />
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="dropzone"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                {...getRootProps()}
                style={{
                  border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '36px 24px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: isDragActive ? 'var(--accent-glow)' : 'var(--bg-card)',
                  transition: 'all var(--transition)',
                }}
              >
                <input {...getInputProps()} />
                <Upload size={28} color="var(--accent)" style={{ margin: '0 auto 12px' }} />
                <div style={{ fontWeight: 500 }}>
                  {isDragActive ? 'Drop it here' : 'Drag & drop your resume'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>or click to browse · PDF, DOCX, TXT · max 5 MB</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Submit */}
        <button
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center', fontSize: 15, padding: '14px' }}
          disabled={!canSubmit}
          onClick={handleStart}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16 }} />
              Analysing resume…
            </>
          ) : (
            <>Begin Interview <ChevronRight size={16} /></>
          )}
        </button>
      </motion.div>
    </div>
  )
}
