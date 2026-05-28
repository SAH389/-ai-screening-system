// src/App.jsx
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Setup from './pages/Setup'
import InterviewPage from './pages/Interview'
import Results from './pages/Results'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/interview/setup" element={<Setup />} />
      <Route path="/interview/:sessionId" element={<InterviewPage />} />
      <Route path="/results/:sessionId" element={<Results />} />
    </Routes>
  )
}
