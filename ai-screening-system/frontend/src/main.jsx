// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontFamily: 'var(--font-body)',
            fontSize: 14,
          },
          success: { iconTheme: { primary: 'var(--success)', secondary: 'transparent' } },
          error:   { iconTheme: { primary: 'var(--danger)',  secondary: 'transparent' } },
        }}
      />
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
