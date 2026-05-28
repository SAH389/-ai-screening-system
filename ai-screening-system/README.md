# AI-Powered Role-Based Candidate Screening System

> PGAGI AI/ML & Backend Intern Assignment — Full Implementation

A production-grade intelligent screening platform that conducts personalised, RAG-grounded technical interviews. Every question is dynamically generated from the candidate's resume and a curated role-specific knowledge base.

---

## Demo Flow

```
Upload Resume → Select Role → RAG Retrieval → AI Question Generation
   → Candidate Answers → Real-time LLM Evaluation → Adaptive Next Question
      → Final AI Report (Score + Strengths/Weaknesses + Recommendation)
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)              │
│  Home → Setup → Interview (Live Q&A) → Results Dashboard    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  /sessions  │  /interview  │  /knowledge-base               │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ Resume Parser│  │ RAG Service   │  │  LLM Service     │ │
│  │ (pdfplumber) │  │ (ChromaDB +   │  │  (OpenAI /       │ │
│  │             │  │  SentenceXF)  │  │   Anthropic /    │ │
│  └──────────────┘  └───────────────┘  │   Groq)          │ │
│                                       └──────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              SQLite (via SQLAlchemy async)            │  │
│  │  interview_sessions │ questions │ session_summaries   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- An API key for at least one LLM provider (Groq is free)

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd ai-screening-system
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit environment config
cp .env.example .env
# Edit .env — set your LLM_PROVIDER and API key
```

**Minimum `.env` for Groq (free tier):**
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

**Get a free Groq key:** https://console.groq.com

### 3. Add Knowledge Base Documents

```bash
# Create role directories and place PDFs from the assignment:
mkdir -p knowledge_base/ai_ml_engineer
mkdir -p knowledge_base/backend_engineer
mkdir -p knowledge_base/data_scientist

# Copy your downloaded PDFs into the appropriate folders
# Then ingest them:
python scripts/ingest_kb.py --all
```

> **Note:** The system works without a knowledge base — it falls back to built-in context.
> But with real books ingested, question quality is dramatically better.

### 4. Start the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 5. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Open: http://localhost:3000

---

## Docker (One-command deployment)

```bash
# From project root
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

---

## API Reference

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sessions/upload-resume` | Upload resume + create session |
| GET  | `/api/v1/sessions/{id}` | Get session status |

### Interview Flow

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/v1/interview/{id}/next-question` | Generate & return next question |
| POST | `/api/v1/interview/{id}/questions/{qid}/answer` | Submit an answer |
| POST | `/api/v1/interview/{id}/finish` | Finalise + generate summary |
| GET  | `/api/v1/interview/{id}/summary` | Retrieve completed summary |

### Knowledge Base

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/v1/knowledge-base/status` | View indexed roles & chunk count |
| POST | `/api/v1/knowledge-base/ingest-all` | Trigger background re-ingestion |
| POST | `/api/v1/knowledge-base/upload-document` | Upload & ingest a new document |

---

## Key Design Decisions

### RAG Pipeline

**Chunking Strategy:** Sliding-window word-level chunking (800 words, 150-word overlap).
- Rationale: Word-level chunking is safer than character-level for semantic preservation at boundaries. 150-word overlap ensures concepts that span chunk boundaries are captured in at least one complete chunk.

**Embedding Model:** `all-MiniLM-L6-v2` (SentenceTransformers, local, free).
- Rationale: Excellent semantic performance for technical text. No API cost, runs locally, 384-dim embeddings are fast to index and query.

**Vector Store:** ChromaDB (persistent on disk).
- Rationale: Zero infrastructure overhead, ships as a Python package, persists across restarts. Production upgrade path: swap to Pinecone/Weaviate without changing the RAG interface.

**Query Construction:** Combines role name + candidate's top skills + optional topic hint derived from performance on previous questions.
- This ensures retrieval is grounded in what the candidate actually knows, not just the role in general.

### LLM Strategy

**Provider abstraction:** A single `_call_llm()` function routes to OpenAI, Anthropic, or Groq based on `LLM_PROVIDER` env var — zero code change to switch providers.

**JSON-structured prompts:** All LLM calls return JSON (question metadata, scores, summaries) rather than free text, making parsing deterministic and the pipeline traceable.

**Adaptive difficulty:** After each answer, the system checks the score. Score < 5 → next query hints at "fundamentals". Score ≥ 8 → hints at "advanced" topics. This creates a real adaptive interview loop.

### Database

**Async SQLAlchemy + SQLite:** SQLite is perfect for a single-node deployment. The async driver (`aiosqlite`) means FastAPI never blocks. Switching to PostgreSQL requires only changing `DATABASE_URL`.

**Traceability:** Every `Question` row stores the `rag_context` used to generate it, making the pipeline fully auditable (context → question → answer → feedback).

### Backend Structure

```
app/
├── core/config.py          # Centralised settings (pydantic-settings)
├── db/database.py          # ORM models + async engine
├── models/schemas.py       # Pydantic request/response schemas
├── services/
│   ├── resume_service.py   # PDF/DOCX parsing + skill extraction
│   ├── rag_service.py      # ChromaDB ingestion + retrieval
│   ├── llm_service.py      # LLM abstraction (Q gen, eval, summary)
│   └── interview_service.py # Orchestration (session lifecycle)
└── api/routes/
    ├── sessions.py         # Session creation endpoints
    ├── interview.py        # Interview flow endpoints
    └── knowledge_base.py   # KB management endpoints
```

Strict separation of concerns: routes only call services; services never import each other circularly; all config flows from `core/config.py`.

---

## Project Structure

```
ai-screening-system/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI route handlers
│   │   ├── core/            # Config
│   │   ├── db/              # SQLAlchemy models
│   │   ├── models/          # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── knowledge_base/      # PDF books go here
│   ├── scripts/
│   │   └── ingest_kb.py     # CLI ingestion tool
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Home, Setup, Interview, Results
│   │   ├── services/api.js  # Axios API layer
│   │   └── styles/          # Global design system CSS
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Supported LLM Providers

| Provider | Model | Notes |
|----------|-------|-------|
| **Groq** | `llama3-70b-8192` | Free tier, very fast. Recommended for dev. |
| **Anthropic** | `claude-3-5-sonnet-20241022` | Excellent reasoning, paid. |
| **OpenAI** | `gpt-4o` | Industry standard, paid. |

Switch by changing `LLM_PROVIDER` in `.env` — no code changes needed.

---

## Extending the System

- **Add a new role:** Create `knowledge_base/<role_name>/` and run ingest. No code changes.
- **Add a new LLM:** Add a branch in `llm_service._call_llm()`.
- **Change question count:** Update `TOTAL_QUESTIONS` in `interview_service.py`.
- **Production DB:** Change `DATABASE_URL` in `.env` to a PostgreSQL URL.
