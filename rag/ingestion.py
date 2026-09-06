import os
import glob
from typing import Dict, Any
import chromadb
from rag.chunking import chunk_markdown_document
from rag.embedding import get_embedding_function

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(CURRENT_DIR, "documents")
CHROMA_DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

def run_ingestion(docs_dir: str = DOCS_DIR, persist_dir: str = CHROMA_DB_DIR) -> Dict[str, Any]:
    """
    Ingests markdown policy documents from documents/ folder,
    chunks them, generates embeddings, and saves them into the chroma_db/ folder.
    """
    os.makedirs(persist_dir, exist_ok=True)
    
    print(f"[RAG Ingestion] Initializing ChromaDB at: {persist_dir}")
    client = chromadb.PersistentClient(path=persist_dir)
    
    embedding_fn = get_embedding_function()
    collection = client.get_or_create_collection(
        name="flight_policies",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    doc_files = glob.glob(os.path.join(docs_dir, "*.md"))
    print(f"[RAG Ingestion] Found {len(doc_files)} policy files in {docs_dir}")

    all_docs = []
    all_metas = []
    all_ids = []

    for file_path in doc_files:
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = chunk_markdown_document(content, file_name)
        for c in chunks:
            all_docs.append(c["text"])
            all_metas.append(c["metadata"])
            all_ids.append(c["id"])

    if all_docs:
        collection.upsert(
            documents=all_docs,
            metadatas=all_metas,
            ids=all_ids
        )
        print(f"[RAG Ingestion] Successfully saved {len(all_docs)} embedded vectors into '{persist_dir}'!")
        return {
            "status": "success",
            "total_files": len(doc_files),
            "total_vectors": len(all_docs),
            "chroma_dir": persist_dir
        }

    return {"status": "no_docs", "total_vectors": 0}

if __name__ == "__main__":
    result = run_ingestion()
    print("Result:", result)
