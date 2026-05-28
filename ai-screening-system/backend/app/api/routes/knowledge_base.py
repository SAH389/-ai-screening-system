"""
app/api/routes/knowledge_base.py
Endpoints for managing and inspecting the RAG knowledge base.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from pathlib import Path
import aiofiles
import os

from app.models.schemas import KBStatusResponse
from app.services import rag_service
from app.core.config import get_settings

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])
settings = get_settings()


@router.get("/status", response_model=KBStatusResponse)
async def kb_status():
    """Return information about what's currently indexed in the vector store."""
    status = rag_service.kb_status()
    return KBStatusResponse(**status)


@router.post("/ingest-all")
async def ingest_all(background_tasks: BackgroundTasks):
    """
    Trigger a full re-ingestion of all documents in the knowledge_base/ directory.
    Runs in the background; returns immediately.
    """
    background_tasks.add_task(_run_ingest)
    return {"message": "Ingestion started in background. Check /status in a few minutes."}


@router.post("/upload-document")
async def upload_document(
    role: str = Form(..., description="e.g. 'AI/ML Engineer'"),
    document: UploadFile = File(...),
):
    """Upload a new PDF/TXT document and immediately ingest it into the vector store."""
    if document.size and document.size > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 50 MB).")

    safe_role = role.lower().replace(" ", "_").replace("/", "_")
    save_dir = Path(settings.knowledge_base_dir) / safe_role
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / (document.filename or "document.pdf")

    content = await document.read()
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    chunks = rag_service.ingest_document(role, save_path)
    return {"message": f"Ingested {chunks} chunks for role '{role}'.", "file": save_path.name}


def _run_ingest():
    summary = rag_service.ingest_all_knowledge_base()
    total = sum(summary.values())
    print(f"[KB Ingest] Done. Ingested {total} total chunks: {summary}")
