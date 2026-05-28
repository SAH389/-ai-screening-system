"""
app/db/database.py
SQLAlchemy async engine + base model definitions.
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── ORM Models ────────────────────────────────────────────────────────────────

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    candidate_name: Mapped[str] = mapped_column(String(255))
    target_role: Mapped[str] = mapped_column(String(100))
    resume_text: Mapped[str] = mapped_column(Text)
    extracted_skills: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="session", cascade="all, delete-orphan"
    )
    summary: Mapped["SessionSummary | None"] = relationship(
        "SessionSummary", back_populates="session", uselist=False
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"))
    question_number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))   # e.g. "algorithms", "ml_concepts"
    difficulty: Mapped[str] = mapped_column(String(50))  # easy | medium | hard
    rag_context: Mapped[str] = mapped_column(Text, default="")  # retrieved chunk used
    candidate_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-10
    asked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="questions"
    )


class SessionSummary(Base):
    __tablename__ = "session_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("interview_sessions.id"), unique=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendation: Mapped[str] = mapped_column(String(50), default="pending")
    narrative: Mapped[str] = mapped_column(Text, default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="summary"
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
