"""
app/main.py
FastAPI application factory — wires up middleware, routers, and startup events.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db
from app.api.routes import sessions, interview, knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("Initialising database …")
    os.makedirs("./data", exist_ok=True)
    await init_db()
    logger.info("Database ready.")
    logger.info("LLM provider: %s | model: %s", settings.llm_provider, settings.active_model)
    yield
    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down …")


app = FastAPI(
    title="AI Screening System",
    description=(
        "Role-based AI-powered candidate screening with RAG-grounded question generation, "
        "live answer evaluation, and structured session summaries."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(interview.router, prefix="/api/v1")
app.include_router(knowledge_base.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "AI Screening System", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "llm_provider": settings.llm_provider}
