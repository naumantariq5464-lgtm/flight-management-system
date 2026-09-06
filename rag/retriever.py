import os
from typing import List, Dict, Any, Optional
import chromadb
from rag.embedding import get_embedding_function

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(CURRENT_DIR, "chroma_db")

class PolicyRetriever:
    def __init__(self, persist_dir: str = CHROMA_DB_DIR):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name="flight_policies",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve(self, query: str, top_k: int = 3, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the top-k most semantically relevant policy chunks from ChromaDB.
        """
        where_filter = {"category": category.upper()} if category else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )

        matches = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for i in range(len(docs)):
                similarity = round(1.0 - distances[i], 4) if distances[i] is not None else 1.0
                matches.append({
                    "id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i],
                    "similarity_score": similarity
                })

        return matches
