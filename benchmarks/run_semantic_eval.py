"""
benchmarks/run_semantic_eval.py
Tolok ukur (benchmarking) 6 kueri bisnis untuk evaluasi akurasi temu balik
dan presisi penolakan kueri out-of-domain (Milestone 3).
"""

import os
from src.knowledge.chunking import load_and_chunk_corpus
from src.knowledge.retriever import SemanticRetriever
from src.knowledge.vector_store import DelCareVectorStore

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "type": "Literal / Relevan",
        "query": "Prosedur penanganan pasien gawat darurat henti napas dan henti jantung",
        "expected_doc": "SOP-TRG-001",
        "expected_ood": False,
    },
    {
        "id": "Q2",
        "type": "Literal / Relevan",
        "query": "Kriteria dan alur rujukan pasien kritis menuju RSUD Porsea RS_A",
        "expected_doc": "SOP-RUJ-005",
        "expected_ood": False,
    },
    {
        "id": "Q3",
        "type": "Sinonim / Bahasa Awam",
        "query": "Dada terasa sesak sekali, napas berbunyi mengi sehabis lari keliling lapangan",
        "expected_doc": "SOP-MED-007",
        "expected_ood": False,
    },
    {
        "id": "Q4",
        "type": "Sinonim / Bahasa Awam",
        "query": "Patah tulang tangan membengkak dan sangat nyeri karena jatuh saat main basket",
        "expected_doc": "SOP-MED-009",
        "expected_ood": False,
    },
    {
        "id": "Q5",
        "type": "Out-of-Domain (OOD)",
        "query": "Bagaimana jadwal pembayaran cicilan uang kuliah tunggal di IT Del?",
        "expected_doc": "NONE",
        "expected_ood": True,
    },
    {
        "id": "Q6",
        "type": "Out-of-Domain (OOD)",
        "query": "Resep bumbu memasak arsik ikan mas khas tradisional Batak Toba",
        "expected_doc": "NONE",
        "expected_ood": True,
    },
]


def run_benchmark():
    print("=" * 82)
    print("BENCHMARK TEMU BALIK SEMANTIK KORPUS SOP DELCARE COPILOT (MILESTONE 3)")
    print("=" * 82)

    store = DelCareVectorStore(
        persist_directory="data/chroma_db",
        collection_name="delcare_knowledge_base",
    )
    if store.count() == 0:
        raw_docs = "data/raw_docs"
        if os.path.exists(raw_docs) and os.listdir(raw_docs):
            print(f"Mengindeks dokumen dari {raw_docs}...")
            chunks = load_and_chunk_corpus(raw_docs, chunk_size=500, chunk_overlap=100)
            store.index_chunks(chunks)
            print(f"Index selesai: {store.count()} chunks terindeks.")

    retriever = SemanticRetriever(store, relevance_threshold=0.35)

    correct_retrievals = 0
    correct_ood_rejections = 0
    total_relevant = sum(1 for q in BENCHMARK_QUERIES if not q["expected_ood"])
    total_ood = sum(1 for q in BENCHMARK_QUERIES if q["expected_ood"])

    header = f"{'ID':<4} | {'Tipe Kueri':<22} | {'Cosine Sim':<10} | {'Status':<14} | {'Top-1 Target'}"
    print(header)
    print("-" * 82)

    for q in BENCHMARK_QUERIES:
        res = retriever.search(q["query"], top_k=1)
        best_match = res["matches"][0] if res["matches"] else None
        sim_score = res["best_similarity"]
        retrieved_doc = best_match["metadata"]["doc_id"] if best_match else "NONE"

        if not q["expected_ood"]:
            is_correct = (retrieved_doc == q["expected_doc"]) and not res["is_out_of_domain"]
            if is_correct:
                correct_retrievals += 1
            status_label = "TERPENUHI" if is_correct else "MISMATCH"
        else:
            is_correct = res["is_out_of_domain"]
            if is_correct:
                correct_ood_rejections += 1
            status_label = "DITOLAK (OOD)" if is_correct else "LOLOS_PALSU"

        print(
            f"{q['id']:<4} | {q['type']:<22} | {sim_score:<10.4f} | {status_label:<14} | {retrieved_doc}"
        )

    acc = (correct_retrievals / total_relevant) * 100 if total_relevant > 0 else 0
    ood_prec = (correct_ood_rejections / total_ood) * 100 if total_ood > 0 else 0

    print("-" * 82)
    print(f"Akurasi Temu Balik Relevan : {acc:.1f}% ({correct_retrievals}/{total_relevant})")
    print(f"Presisi Penolakan Kueri OOD : {ood_prec:.1f}% ({correct_ood_rejections}/{total_ood})")
    print("=" * 82)


if __name__ == "__main__":
    run_benchmark()
