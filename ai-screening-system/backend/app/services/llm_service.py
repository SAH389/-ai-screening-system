"""
app/services/llm_service.py
Unified LLM interface supporting OpenAI, Anthropic, and Groq.
Responsibilities:
  - Question generation (RAG-grounded)
  - Answer evaluation + scoring
  - Session summary generation
"""
from __future__ import annotations
import json
import logging
import re
from typing import Any

from app.core.config import get_settings
from app.services.resume_service import build_skill_summary

logger = logging.getLogger(__name__)
settings = get_settings()


# ── LLM client factory ────────────────────────────────────────────────────────

def _call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """
    Route to the configured LLM provider and return the text response.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    raise ValueError(f"Unsupported LLM provider: {provider}")


def _safe_json(text: str) -> Any:
    """Strip markdown fences and parse JSON safely."""
    clean = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(clean)


# ── Question Generation ───────────────────────────────────────────────────────

QUESTION_SYSTEM = """You are a senior technical interviewer at a top-tier tech company.
Your task is to generate a high-quality, contextual interview question for a candidate.

Rules:
- The question must be directly grounded in the retrieved knowledge base context.
- It must be relevant to the candidate's background (skills and experience).
- Avoid generic, Googleable questions. Probe for depth, trade-offs, and real understanding.
- Vary question types: conceptual, applied, debugging, design, trade-off analysis.
- Return ONLY valid JSON with keys: question_text, category, difficulty (easy|medium|hard), rationale.
"""


def generate_question(
    role: str,
    candidate_skills: dict,
    rag_chunks: list[dict],
    previous_questions: list[str],
    question_number: int,
) -> dict[str, str]:
    """
    Generate one interview question grounded in RAG context.
    Returns dict with question_text, category, difficulty, rationale.
    """
    context_text = "\n\n---\n\n".join(c["text"] for c in rag_chunks[:3])
    skill_summary = build_skill_summary(candidate_skills)
    prev_q_text = "\n".join(f"- {q}" for q in previous_questions[-5:]) or "None yet."

    user_prompt = f"""
Role: {role}
Question Number: {question_number} of 8

Candidate's Skill Profile:
{skill_summary}

Retrieved Knowledge Base Context:
{context_text}

Previously Asked Questions (do NOT repeat these):
{prev_q_text}

Generate question #{question_number}. Return JSON only.
"""
    raw = _call_llm(QUESTION_SYSTEM, user_prompt, max_tokens=600)
    try:
        result = _safe_json(raw)
        return {
            "question_text": result.get("question_text", raw),
            "category": result.get("category", "general"),
            "difficulty": result.get("difficulty", "medium"),
            "rationale": result.get("rationale", ""),
        }
    except Exception:
        logger.warning("JSON parse failed for question generation, using raw text.")
        return {
            "question_text": raw.strip(),
            "category": "general",
            "difficulty": "medium",
            "rationale": "",
        }


# ── Answer Evaluation ─────────────────────────────────────────────────────────

EVAL_SYSTEM = """You are a strict but fair technical interviewer evaluating a candidate's answer.
Score the answer from 0–10 and provide actionable feedback.
Return ONLY valid JSON with keys: score (int 0-10), feedback (string, 2-4 sentences).
"""


def evaluate_answer(
    role: str,
    question_text: str,
    candidate_answer: str,
    rag_context: str,
) -> dict[str, Any]:
    """Evaluate an answer, return {score, feedback}."""
    user_prompt = f"""
Role: {role}
Question: {question_text}
Candidate's Answer: {candidate_answer}

Reference Context (from knowledge base):
{rag_context[:1000]}

Evaluate the answer and return JSON only.
"""
    raw = _call_llm(EVAL_SYSTEM, user_prompt, max_tokens=400)
    try:
        result = _safe_json(raw)
        return {
            "score": max(0, min(10, int(result.get("score", 5)))),
            "feedback": result.get("feedback", ""),
        }
    except Exception:
        return {"score": 5, "feedback": raw.strip()}


# ── Session Summary ───────────────────────────────────────────────────────────

SUMMARY_SYSTEM = """You are an AI hiring assistant. Analyse the complete interview transcript
and produce a structured evaluation.
Return ONLY valid JSON with keys:
  overall_score (int 0-100),
  strengths (list of strings),
  weaknesses (list of strings),
  recommendation ("strong_yes" | "yes" | "maybe" | "no"),
  narrative (string, 3-5 sentences summarising the candidate's performance).
"""


def generate_summary(
    role: str,
    candidate_name: str,
    candidate_skills: dict,
    qa_pairs: list[dict],
) -> dict[str, Any]:
    """Generate a final session summary."""
    skill_summary = build_skill_summary(candidate_skills)
    transcript = "\n\n".join(
        f"Q{i+1} [{qa['difficulty']} | {qa['category']}]: {qa['question_text']}\n"
        f"Answer: {qa.get('candidate_answer', '(no answer)')}\n"
        f"Score: {qa.get('score', 'N/A')}/10"
        for i, qa in enumerate(qa_pairs)
    )
    avg_score = (
        sum(qa.get("score", 0) for qa in qa_pairs if qa.get("score") is not None)
        / max(len(qa_pairs), 1)
    ) * 10  # scale to 100

    user_prompt = f"""
Candidate: {candidate_name}
Role Applied: {role}
Candidate Skill Profile:
{skill_summary}

Interview Transcript:
{transcript}

Average Raw Score: {avg_score:.1f}/100

Generate a structured summary. Return JSON only.
"""
    raw = _call_llm(SUMMARY_SYSTEM, user_prompt, max_tokens=800)
    try:
        result = _safe_json(raw)
        return {
            "overall_score": max(0, min(100, int(result.get("overall_score", int(avg_score))))),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "recommendation": result.get("recommendation", "maybe"),
            "narrative": result.get("narrative", ""),
        }
    except Exception:
        return {
            "overall_score": int(avg_score),
            "strengths": [],
            "weaknesses": [],
            "recommendation": "maybe",
            "narrative": raw.strip(),
        }
