import os
import glob
import chromadb
from chromadb.config import Settings

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documents")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "chroma_db")

def ingest_policy_documents():
    """Ingests all Markdown policy files into ChromaDB with chunking and metadata."""
    print(f"[RAG] Initializing ChromaDB vector store at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    collection_name = "flight_policies"
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    doc_files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    print(f"[RAG] Found {len(doc_files)} policy documents in {DOCS_DIR}")

    documents = []
    metadatas = []
    ids = []

    for file_path in doc_files:
        file_name = os.path.basename(file_path)
        category = file_name.replace("_policy.md", "").replace(".md", "").upper()
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split document into section chunks based on markdown headers
        sections = content.split("## ")
        title = sections[0].strip().replace("# ", "")
        
        for idx, sec in enumerate(sections[1:], start=1):
            chunk_text = f"{title}\n## {sec.strip()}"
            chunk_id = f"{file_name}_chunk_{idx}"
            
            documents.append(chunk_text)
            metadatas.append({
                "source_file": file_name,
                "category": category,
                "title": title,
                "chunk_index": idx
            })
            ids.append(chunk_id)

    if documents:
        # Upsert into ChromaDB
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[RAG] Successfully ingested {len(documents)} policy chunks into ChromaDB collection '{collection_name}'!")
    else:
        print("[RAG] No documents found to ingest.")

if __name__ == "__main__":
    ingest_policy_documents()
