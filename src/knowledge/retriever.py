"""
src/knowledge/retriever.py
Fungsi temu balik semantik vektor dan relevance guardrail penolakan kueri out-of-domain.
"""

from typing import Any, Dict, List
from src.knowledge.vector_store import DelCareVectorStore


class SemanticRetriever:
    """
    Retriever semantik yang menghitung Cosine Similarity dan menyaring
    kueri di luar domain melalui relevance threshold guardrail.
    """

    def __init__(
        self,
        vector_store: DelCareVectorStore,
        relevance_threshold: float = 0.35,  # Batas minimum skor Cosine Similarity
    ):
        self.store = vector_store
        self.threshold = relevance_threshold

    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Melakukan temu balik semantik dan mengonversi Cosine Distance ke Cosine Similarity.
        Jika skor tertinggi di bawah threshold, kueri ditandai OUT_OF_DOMAIN.
        """
        results = self.store.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return {
                "query": query,
                "is_out_of_domain": True,
                "status": "NO_MATCH",
                "best_similarity": 0.0,
                "matches": [],
            }

        matches: List[Dict[str, Any]] = []
        for doc_id, text, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Dalam hnsw:space "cosine", distance = 1 - cosine_similarity
            similarity = max(0.0, min(1.0, 1.0 - dist))
            matches.append({
                "chunk_id": doc_id,
                "text": text,
                "metadata": meta,
                "similarity_score": round(similarity, 4),
            })

        best_score = matches[0]["similarity_score"]
        is_out_of_domain = best_score < self.threshold

        return {
            "query": query,
            "is_out_of_domain": is_out_of_domain,
            "status": "REJECTED_OOD" if is_out_of_domain else "ACCEPTED",
            "best_similarity": best_score,
            "matches": matches,
        }
