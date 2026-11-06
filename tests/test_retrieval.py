"""
tests/test_retrieval.py
Unit test untuk evaluasi semantik dan presisi guardrail penolakan kueri out-of-domain.
"""

from src.knowledge.chunking import load_and_chunk_corpus
from src.knowledge.retriever import SemanticRetriever
from src.knowledge.vector_store import DelCareVectorStore


def test_semantic_retrieval_and_ood(tmp_path):
    store = DelCareVectorStore(
        persist_directory=str(tmp_path / "chroma_db"),
        collection_name="test_knowledge_base",
    )

    chunks = load_and_chunk_corpus("data/raw_docs", chunk_size=500, chunk_overlap=100)
    store.index_chunks(chunks)
    assert store.count() > 0

    retriever = SemanticRetriever(store, relevance_threshold=0.35)
    res_med = retriever.search("Pasien sesak napas berat dan bibir membiru", top_k=1)
    assert not res_med["is_out_of_domain"]
    assert res_med["best_similarity"] >= 0.35
    assert len(res_med["matches"]) > 0

    res_ood = retriever.search(
        "Cara menginstal Linux Ubuntu di virtual machine",
        top_k=1,
    )
    assert res_ood["is_out_of_domain"]
    assert res_ood["status"] == "REJECTED_OOD"
