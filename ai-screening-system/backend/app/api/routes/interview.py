"""
app/api/routes/interview.py
Endpoints driving the live interview flow.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import (
    QuestionResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    SessionSummaryResponse,
)
from app.services import interview_service

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.get("/{session_id}/next-question", response_model=QuestionResponse)
async def next_question(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate and return the next interview question for the given session.
    Returns 204 when all questions have been asked.
    """
    question = await interview_service.get_next_question(db, session_id)
    if question is None:
        raise HTTPException(
            status_code=204,
            detail="Interview complete. Call /interview/{id}/finish to generate the summary.",
        )
    return question


@router.post("/{session_id}/questions/{question_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    session_id: str,
    question_id: int,
    body: AnswerSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit the candidate's answer to a specific question."""
    try:
        return await interview_service.submit_answer(
            db=db,
            session_id=session_id,
            question_id=question_id,
            answer_text=body.answer,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/{session_id}/finish", response_model=SessionSummaryResponse)
async def finish_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Finalise the interview: generate the AI summary and persist it.
    Safe to call multiple times (idempotent).
    """
    return await interview_service.finish_interview(db, session_id)


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve an already-generated summary."""
    summary = await interview_service.get_summary(db, session_id)
    if not summary:
        raise HTTPException(404, "Summary not found. Complete the interview first.")
    return summary
