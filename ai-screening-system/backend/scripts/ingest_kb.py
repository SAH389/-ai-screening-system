#!/usr/bin/env python3
"""
scripts/ingest_kb.py
CLI tool to ingest knowledge base documents into ChromaDB.

Usage:
    python scripts/ingest_kb.py                          # ingest all
    python scripts/ingest_kb.py --role "AI/ML Engineer" --file path/to/book.pdf
"""
import sys
import argparse
import logging
from pathlib import Path

# Make sure backend app is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge base documents into ChromaDB.")
    parser.add_argument("--role", type=str, help="Role name (e.g. 'AI/ML Engineer')")
    parser.add_argument("--file", type=str, help="Path to a single document to ingest")
    parser.add_argument("--all", action="store_true", help="Ingest all documents in knowledge_base/")
    args = parser.parse_args()

    # Must import after path setup
    from app.services.rag_service import ingest_document, ingest_all_knowledge_base

    if args.file and args.role:
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error("File not found: %s", args.file)
            sys.exit(1)
        chunks = ingest_document(args.role, filepath)
        logger.info("Done. Ingested %d chunks for role '%s'.", chunks, args.role)

    elif args.all or (not args.file and not args.role):
        logger.info("Ingesting all documents from knowledge_base/ directory…")
        summary = ingest_all_knowledge_base()
        if not summary:
            logger.warning(
                "No documents found. Place PDFs in: knowledge_base/<role_name>/<file>.pdf\n"
                "Example: knowledge_base/ai_ml_engineer/ml_book.pdf"
            )
        else:
            for role, count in summary.items():
                logger.info("  %-30s %d chunks", role, count)
            logger.info("Total: %d chunks across %d roles.", sum(summary.values()), len(summary))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
