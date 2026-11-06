"""
tests/test_chunking.py
Unit test untuk verifikasi parser dan pemotong teks korpus SOP.
"""

import os
from src.knowledge.chunking import (
    chunk_text_recursive,
    load_and_chunk_corpus,
    parse_sop_file,
)


def test_chunk_text_overlap():
    sample_text = (
        "Paragraf 1 mengenai penanganan pasien di ruang gawat darurat.\n\n"
        "Paragraf 2 membahas pemberian terapi oksigen dan pemasangan infus kristaloid.\n\n"
        "Paragraf 3 membahas kriteria rujukan menuju RS Mitra terdekat di Porsea."
    )
    chunks = chunk_text_recursive(sample_text, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2
    assert all(len(c) > 0 for c in chunks)


def test_parse_sop_structure(tmp_path):
    dummy_sop = (
        "KODE DOKUMEN: SOP-TEST-001\n"
        "JUDUL: SOP Uji Coba Triase\n"
        "KATEGORI: Kedaruratan\n"
        "TARGET AKSI DELCARE: RUJUK_RS_A\n"
        "REFERENSI TERBUKA: Permenkes Test\n"
        "TAUTAN RESMI: https://peraturan.bpk.go.id\n"
        "TAUTAN ALTERNATIF: https://kemkes.go.id\n"
        "======================================================================\n\n"
        "1. TUJUAN\n"
        "Pengujian ekstraksi header metadata."
    )
    p = tmp_path / "test_sop.txt"
    p.write_text(dummy_sop, encoding="utf-8")

    parsed = parse_sop_file(str(p))
    assert parsed["doc_id"] == "SOP-TEST-001"
    assert parsed["title"] == "SOP Uji Coba Triase"
    assert parsed["target_action"] == "RUJUK_RS_A"
    assert "Pengujian ekstraksi" in parsed["body"]


def test_load_corpus_directory():
    corpus_path = "data/raw_docs"
    if os.path.exists(corpus_path) and os.listdir(corpus_path):
        chunks = load_and_chunk_corpus(corpus_path, chunk_size=500, chunk_overlap=100)
        assert len(chunks) >= 12
        first_chunk = chunks[0]
        assert "doc_id" in first_chunk.metadata
        assert "target_action" in first_chunk.metadata
        assert "ref_url" in first_chunk.metadata
