# Knowledge Base

Place role-specific PDF/TXT books and documents here. The RAG pipeline
ingests these and creates per-role ChromaDB collections.

## Expected Structure

```
knowledge_base/
├── ai_ml_engineer/
│   ├── ml_tom_mitchell.pdf
│   ├── hundred_page_ml.pdf
│   └── ml_absolute_beginners.pdf
├── backend_engineer/
│   ├── designing_data_intensive_apps.pdf
│   └── clean_architecture.pdf
├── data_scientist/
│   ├── intro_ml_with_python.pdf
│   └── master_ml_algorithms.pdf
└── full_stack_engineer/
    └── your_docs_here.pdf
```

## Recommended Books (from Assignment)

### AI/ML Engineer
- Machine Learning — Tom Mitchell
- The Hundred-Page Machine Learning Book — Andriy Burkov
- Machine Learning for Absolute Beginners

### Data Scientist
- Introduction to Machine Learning with Python
- Master Machine Learning Algorithms — Jason Brownlee

### Optional (Advanced)
- Pattern Recognition and Machine Learning — Christopher Bishop
- Artificial Intelligence, Machine Learning & Deep Learning

## Ingestion

```bash
# From backend/ directory:

# Ingest everything at once:
python scripts/ingest_kb.py --all

# Ingest a single file:
python scripts/ingest_kb.py --role "AI/ML Engineer" --file knowledge_base/ai_ml_engineer/ml_book.pdf
```

> **Tip:** The system works without a knowledge base (falls back to built-in context),
> but question quality improves dramatically with real books ingested.
