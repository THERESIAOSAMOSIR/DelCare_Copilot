"""
tests/test_retrieval.py
Unit test untuk evaluasi semantik dan presisi guardrail penolakan kueri out-of-domain.
"""

from src.knowledge.retriever import SemanticRetriever
from src.knowledge.vector_store import DelCareVectorStore


def test_semantic_retrieval_and_ood():
    store = DelCareVectorStore(
        persist_directory="data/chroma_db",
        collection_name="delcare_knowledge_base",
    )
    retriever = SemanticRetriever(store, relevance_threshold=0.35)

    if store.count() > 0:
        # 1. Kueri relevan harus lolos guardrail dan similarity >= threshold
        res_med = retriever.search("Pasien sesak napas berat dan bibir membiru", top_k=1)
        assert not res_med["is_out_of_domain"]
        assert res_med["best_similarity"] >= 0.35
        assert len(res_med["matches"]) > 0

        # 2. Kueri OOD harus ditolak oleh guardrail
        res_ood = retriever.search("Cara menginstal linux ubuntu di virtual machine", top_k=1)
        assert res_ood["is_out_of_domain"]
        assert res_ood["status"] == "REJECTED_OOD"
