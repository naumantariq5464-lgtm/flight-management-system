# Airline Policy RAG Pipeline (ChromaDB + Python)

This module provides a complete, production-ready **Retrieval-Augmented Generation (RAG)** pipeline for the Flight Management System.

---

## 📁 Architecture Overview

```
rag/documents/ (*.md policy files)
       │
       ▼
[ Chunking & Header Tagging ] (rag/pipeline.py)
       │
       ▼
[ Local Vector Embeddings ] (MiniLM-L6-v2)
       │
       ▼
[ ChromaDB Vector Store ] (backend/chroma_db/)
       │
       ▼
[ Booking-Aware FastAPI Service ] (backend/app/services/rag_chroma_service.py)
  (Combines Chroma context + Live passenger PNR & Fare Rules from Neon DB)
       │
       ▼
[ Human Supervisor Approval Queue ] (rag_approvals table)
```

---

## 🚀 How to Ingest Policies into ChromaDB

Run the pipeline ingestion script from the project root:

```bash
cd "d:\Fligth Management System"
python rag/pipeline.py
```

### What this does:
1. Loads all policy documents from `rag/documents/` (`cancellation`, `baggage`, `schedule_change`, etc.).
2. Splits them into section-level overlapping chunks (450 chars with 80-char overlap).
3. Generates 384-dimensional vector embeddings locally.
4. Saves them persistently into `backend/chroma_db/`.
5. Executes an automatic test vector query to verify retrieval accuracy.
