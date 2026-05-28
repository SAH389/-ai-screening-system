"""
app/services/interview_service.py
Orchestrates the full interview lifecycle:
  start → next_question → submit_answer → finish → summary
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import InterviewSession, Question, SessionSummary
from app.services import rag_service, llm_service
from app.models.schemas import (
    SessionCreateResponse,
    QuestionResponse,
    AnswerSubmitResponse,
    SessionSummaryResponse,
    QuestionSummaryItem,
)

logger = logging.getLogger(__name__)

TOTAL_QUESTIONS = 8  # configurable


# ── Session Creation ──────────────────────────────────────────────────────────

async def create_session(
    db: AsyncSession,
    candidate_name: str,
    target_role: str,
    resume_text: str,
    extracted_skills: dict,
) -> SessionCreateResponse:
    session_id = str(uuid.uuid4())
    session = InterviewSession(
        id=session_id,
        candidate_name=candidate_name,
        target_role=target_role,
        resume_text=resume_text,
        extracted_skills=extracted_skills,
        status="in_progress",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionCreateResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        extracted_skills=session.extracted_skills,
        status=session.status,
        created_at=session.created_at,
    )


# ── Next Question ─────────────────────────────────────────────────────────────

async def get_next_question(
    db: AsyncSession,
    session_id: str,
) -> QuestionResponse | None:
    """
    Generate and persist the next interview question.
    Returns None if the interview is complete.
    """
    session = await _get_session(db, session_id)
    if not session or session.status != "in_progress":
        return None

    answered = [q for q in session.questions if q.candidate_answer is not None]
    question_number = len(session.questions) + 1

    if question_number > TOTAL_QUESTIONS:
        return None

    # Build topic hint from previous answers to adapt questions
    topic_hint = ""
    if answered:
        last = answered[-1]
        if last.score is not None and last.score < 5:
            topic_hint = f"Focus on fundamentals around {last.category}"
        elif last.score is not None and last.score >= 8:
            topic_hint = f"Ask an advanced question about {last.category}"

    # RAG retrieval
    rag_chunks = rag_service.retrieve_context(
        role=session.target_role,
        skills=session.extracted_skills,
        topic_hint=topic_hint,
        top_k=5,
    )

    previous_questions = [q.question_text for q in session.questions]

    # LLM question generation
    q_data = llm_service.generate_question(
        role=session.target_role,
        candidate_skills=session.extracted_skills,
        rag_chunks=rag_chunks,
        previous_questions=previous_questions,
        question_number=question_number,
    )

    rag_context_text = "\n\n".join(c["text"] for c in rag_chunks[:2])

    question = Question(
        session_id=session_id,
        question_number=question_number,
        question_text=q_data["question_text"],
        category=q_data["category"],
        difficulty=q_data["difficulty"],
        rag_context=rag_context_text,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    return QuestionResponse(
        question_id=question.id,
        question_number=question.question_number,
        question_text=question.question_text,
        category=question.category,
        difficulty=question.difficulty,
        total_questions=TOTAL_QUESTIONS,
    )


# ── Submit Answer ─────────────────────────────────────────────────────────────

async def submit_answer(
    db: AsyncSession,
    session_id: str,
    question_id: int,
    answer_text: str,
) -> AnswerSubmitResponse:
    session = await _get_session(db, session_id)
    question = await db.get(Question, question_id)

    if not question or question.session_id != session_id:
        raise ValueError("Question not found in this session.")

    # Evaluate with LLM
    eval_result = llm_service.evaluate_answer(
        role=session.target_role,
        question_text=question.question_text,
        candidate_answer=answer_text,
        rag_context=question.rag_context,
    )

    question.candidate_answer = answer_text
    question.ai_feedback = eval_result["feedback"]
    question.score = eval_result["score"]
    question.answered_at = datetime.utcnow()
    await db.commit()

    # Check if more questions remain
    answered_count = sum(1 for q in session.questions if q.candidate_answer is not None) + 1
    next_available = answered_count < TOTAL_QUESTIONS

    return AnswerSubmitResponse(
        question_id=question_id,
        ai_feedback=eval_result["feedback"],
        score=eval_result["score"],
        next_question_available=next_available,
    )


# ── Finish + Summary ──────────────────────────────────────────────────────────

async def finish_interview(
    db: AsyncSession,
    session_id: str,
) -> SessionSummaryResponse:
    session = await _get_session(db, session_id)

    qa_pairs = [
        {
            "question_text": q.question_text,
            "category": q.category,
            "difficulty": q.difficulty,
            "candidate_answer": q.candidate_answer,
            "score": q.score,
        }
        for q in sorted(session.questions, key=lambda x: x.question_number)
    ]

    summary_data = llm_service.generate_summary(
        role=session.target_role,
        candidate_name=session.candidate_name,
        candidate_skills=session.extracted_skills,
        qa_pairs=qa_pairs,
    )

    # Persist summary
    existing = await db.scalar(
        select(SessionSummary).where(SessionSummary.session_id == session_id)
    )
    if existing:
        existing.overall_score = summary_data["overall_score"]
        existing.strengths = summary_data["strengths"]
        existing.weaknesses = summary_data["weaknesses"]
        existing.recommendation = summary_data["recommendation"]
        existing.narrative = summary_data["narrative"]
    else:
        db_summary = SessionSummary(session_id=session_id, **summary_data)
        db.add(db_summary)

    session.status = "completed"
    session.completed_at = datetime.utcnow()
    await db.commit()

    return _build_summary_response(session, summary_data)


async def get_summary(db: AsyncSession, session_id: str) -> SessionSummaryResponse | None:
    session = await _get_session(db, session_id)
    if not session or not session.summary:
        return None
    s = session.summary
    return _build_summary_response(
        session,
        {
            "overall_score": s.overall_score,
            "strengths": s.strengths,
            "weaknesses": s.weaknesses,
            "recommendation": s.recommendation,
            "narrative": s.narrative,
        },
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_session(db: AsyncSession, session_id: str) -> InterviewSession | None:
    result = await db.execute(
        select(InterviewSession)
        .options(
            selectinload(InterviewSession.questions),
            selectinload(InterviewSession.summary),
        )
        .where(InterviewSession.id == session_id)
    )
    return result.scalar_one_or_none()


def _build_summary_response(session: InterviewSession, summary_data: dict) -> SessionSummaryResponse:
    questions = [
        QuestionSummaryItem(
            question_number=q.question_number,
            question_text=q.question_text,
            category=q.category,
            difficulty=q.difficulty,
            candidate_answer=q.candidate_answer,
            ai_feedback=q.ai_feedback,
            score=q.score,
        )
        for q in sorted(session.questions, key=lambda x: x.question_number)
    ]
    return SessionSummaryResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        overall_score=summary_data.get("overall_score"),
        strengths=summary_data.get("strengths", []),
        weaknesses=summary_data.get("weaknesses", []),
        recommendation=summary_data.get("recommendation", "pending"),
        narrative=summary_data.get("narrative", ""),
        questions=questions,
        completed_at=session.completed_at,
    )
