"""
Complete Modular RAG Pipeline with ChromaDB & Groq LLM (LLaMA-3.3)
------------------------------------------------------------------
1. Chunking: rag/chunking.py (Markdown semantic splitting)
2. Embedding: rag/embedding.py (Local sentence-transformer embeddings)
3. Ingestion: rag/ingestion.py (Persists vectors to rag/chroma_db/)
4. Retrieval: rag/retriever.py (Vector similarity queries)
5. Groq LLM: High-speed policy generation with LLaMA-3.3-70b-versatile
"""

import os
from typing import Dict, Any, Optional
from rag.ingestion import run_ingestion
from rag.retriever import PolicyRetriever

class PolicyRAGPipeline:
    def __init__(self):
        self.retriever = PolicyRetriever()

    def ingest(self) -> Dict[str, Any]:
        """Runs ingestion from rag/documents/ into rag/chroma_db/"""
        return run_ingestion()

    def query(self, query: str, top_k: int = 3) -> list:
        """Retrieves matching policy chunks from ChromaDB."""
        return self.retriever.retrieve(query=query, top_k=top_k)

if __name__ == "__main__":
    print("🚀 Initializing Policy RAG Pipeline...")
    pipeline = PolicyRAGPipeline()
    res = pipeline.ingest()
    print("Ingestion Result:", res)

    print("\n🔍 Running test vector query: 'What is the baggage limit for Economy?'")
    matches = pipeline.query("What is the baggage limit for Economy?", top_k=2)
    for idx, m in enumerate(matches, start=1):
        print(f"\n--- Match #{idx} (Score: {m['similarity_score']}) ---")
        print(m["text"])
