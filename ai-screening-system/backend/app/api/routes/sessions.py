"""
app/api/routes/sessions.py
Endpoints for creating and managing interview sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import (
    SessionCreateResponse,
    SessionStatusResponse,
    ResumeUploadResponse,
)
from app.services import resume_service, interview_service
from sqlalchemy import select
from app.db.database import InterviewSession

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(
    candidate_name: str = Form(...),
    target_role: str = Form(...),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume (PDF/DOCX/TXT), parse it, extract skills,
    create an interview session, and return the session_id.
    """
    if resume.size and resume.size > 5 * 1024 * 1024:
        raise HTTPException(413, "Resume file too large (max 5 MB).")

    content = await resume.read()
    resume_text = resume_service.parse_resume(resume.filename or "resume.pdf", content)

    if not resume_text.strip():
        raise HTTPException(422, "Could not extract text from the uploaded resume.")

    extracted_skills = resume_service.extract_skills(resume_text)

    session_resp = await interview_service.create_session(
        db=db,
        candidate_name=candidate_name,
        target_role=target_role,
        resume_text=resume_text,
        extracted_skills=extracted_skills,
    )

    return ResumeUploadResponse(
        session_id=session_resp.session_id,
        parsed_text_preview=resume_text[:500],
        extracted_skills=extracted_skills,
        message="Session created successfully. Call /sessions/{id}/next-question to begin.",
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found.")

    from sqlalchemy.orm import selectinload
    result2 = await db.execute(
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions))
        .where(InterviewSession.id == session_id)
    )
    session = result2.scalar_one()

    answered = sum(1 for q in session.questions if q.candidate_answer is not None)
    return SessionStatusResponse(
        session_id=session.id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        status=session.status,
        questions_asked=len(session.questions),
        questions_answered=answered,
        created_at=session.created_at,
    )
