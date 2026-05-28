"""
app/services/resume_service.py
Parses uploaded resume files (PDF / TXT / DOCX) and extracts
structured information (skills, technologies, domain exposure).
"""
from __future__ import annotations
import io
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Skill taxonomy for extraction ─────────────────────────────────────────────
SKILL_TAXONOMY: dict[str, list[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "ruby", "scala", "kotlin", "swift", "r", "matlab", "sql", "bash",
    ],
    "ml_frameworks": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost",
        "lightgbm", "catboost", "hugging face", "transformers", "langchain",
        "spacy", "nltk", "opencv", "detectron",
    ],
    "backend_frameworks": [
        "fastapi", "flask", "django", "express", "spring", "rails", "gin",
        "fiber", "nest.js", "nestjs", "actix",
    ],
    "databases": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
        "cassandra", "dynamodb", "firebase", "supabase", "pinecone", "chroma",
        "weaviate", "qdrant",
    ],
    "cloud_devops": [
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "github actions",
        "ci/cd", "jenkins", "helm", "airflow",
    ],
    "ai_concepts": [
        "machine learning", "deep learning", "nlp", "computer vision", "rag",
        "retrieval augmented generation", "llm", "fine-tuning", "transformers",
        "reinforcement learning", "generative ai", "diffusion models",
        "embeddings", "vector search",
    ],
    "soft_skills": [
        "leadership", "communication", "team", "agile", "scrum", "mentoring",
    ],
}


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract raw text from PDF bytes using pdfplumber (fallback: pypdf)."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        logger.error("PDF parse failed: %s", e)
        return ""


def _extract_text_from_docx(content: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.error("DOCX parse failed: %s", e)
        return ""


def parse_resume(filename: str, content: bytes) -> str:
    """Return raw text from a resume file regardless of format."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(content)
    if ext in (".docx", ".doc"):
        return _extract_text_from_docx(content)
    # Plain text / markdown
    return content.decode("utf-8", errors="replace")


def extract_skills(resume_text: str) -> dict[str, list[str]]:
    """
    Scan the raw resume text against the skill taxonomy.
    Returns a dict: category → list of found skills.
    """
    text_lower = resume_text.lower()
    found: dict[str, list[str]] = {}

    for category, skills in SKILL_TAXONOMY.items():
        matched = []
        for skill in skills:
            # whole-word match to avoid "r" matching "performance"
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_lower):
                matched.append(skill)
        if matched:
            found[category] = matched

    # also try to grab years of experience
    yoe_match = re.search(r"(\d+)\+?\s*years?\s*(of\s*)?experience", text_lower)
    if yoe_match:
        found["years_experience"] = [yoe_match.group(1)]

    return found


def build_skill_summary(extracted: dict[str, list[str]]) -> str:
    """Return a short human-readable skill summary for prompt injection."""
    lines = []
    for cat, skills in extracted.items():
        if skills:
            lines.append(f"{cat.replace('_', ' ').title()}: {', '.join(skills)}")
    return "\n".join(lines) if lines else "No specific skills detected."
