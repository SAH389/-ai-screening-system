"""
app/models/schemas.py
Pydantic v2 schemas — request bodies and response shapes.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── Enums / Literals ──────────────────────────────────────────────────────────

ROLES = ["AI/ML Engineer", "Backend Engineer", "Data Scientist", "Full Stack Engineer"]
DIFFICULTY = ["easy", "medium", "hard"]


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    candidate_name: str = Field(..., min_length=2, max_length=255)
    target_role: str = Field(..., description="One of the supported roles")


class SessionCreateResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    extracted_skills: dict[str, Any]
    status: str
    created_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    status: str
    questions_asked: int
    questions_answered: int
    created_at: datetime


# ── Resume ────────────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    session_id: str
    parsed_text_preview: str   # first 500 chars
    extracted_skills: dict[str, Any]
    message: str


# ── Questions ─────────────────────────────────────────────────────────────────

class QuestionResponse(BaseModel):
    question_id: int
    question_number: int
    question_text: str
    category: str
    difficulty: str
    total_questions: int


class AnswerSubmitRequest(BaseModel):
    answer: str = Field(..., min_length=1)


class AnswerSubmitResponse(BaseModel):
    question_id: int
    ai_feedback: str
    score: int
    next_question_available: bool


# ── Summary ───────────────────────────────────────────────────────────────────

class QuestionSummaryItem(BaseModel):
    question_number: int
    question_text: str
    category: str
    difficulty: str
    candidate_answer: str | None
    ai_feedback: str | None
    score: int | None


class SessionSummaryResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    overall_score: int | None
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    narrative: str
    questions: list[QuestionSummaryItem]
    completed_at: datetime | None


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KBStatusResponse(BaseModel):
    roles_indexed: list[str]
    total_chunks: int
    embedding_model: str
