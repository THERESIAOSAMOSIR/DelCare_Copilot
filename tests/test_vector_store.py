"""
tests/test_vector_store.py
Unit test untuk verifikasi penyimpanan persisten ChromaDB dan ekstraksi embeddings.
"""

from src.knowledge.chunking import DocumentChunk
from src.knowledge.vector_store import DelCareVectorStore


def test_chroma_persistence(tmp_path):
    db_dir = str(tmp_path / "test_chroma")
    store = DelCareVectorStore(persist_directory=db_dir, collection_name="test_col")

    chunk = DocumentChunk(
        chunk_id="TEST_01",
        doc_id="SOP-01",
        title="Uji SOP",
        category="Triase",
        target_action="RUJUK",
        text="Pasien gawat darurat membutuhkan oksigen dan penanganan segera.",
        metadata={"doc_id": "SOP-01", "ref_url": "https://peraturan.bpk.go.id"},
    )
    store.index_chunks([chunk])
    assert store.count() == 1

    # Reload client dari path yang sama untuk membuktikan database tersimpan persisten
    store_reloaded = DelCareVectorStore(persist_directory=db_dir, collection_name="test_col")
    assert store_reloaded.count() == 1
