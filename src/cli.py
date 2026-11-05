"""
DelCare Copilot - CLI Terpadu (Baseline Search, CSP, & Semantic Search RAG)
==========================================================================
Jalankan dari root proyek:

    # 1. Baseline Search (Milestone 1)
    uv run python -m src.cli --start TRIASE_MERAH --algo astar
    uv run python -m src.cli --compare

    # 2. Constraint Satisfaction Problem (Milestone 2)
    uv run python -m src.csp.solver

    # 3. Semantic Search Knowledge Base (Milestone 3)
    uv run python -m src.cli --query "pasien sesak napas mengi setelah lari"
    uv run python -m src.cli --index-kb
"""

import argparse
import os

from src.graph_data import NODES, START
from src.search.astar import astar_search
from src.search.ucs import uniform_cost_search


def print_search_result(label: str, result) -> None:
    print(f"\n=== {label} ===")
    if result.path is None:
        print("Tidak ditemukan lintasan menuju goal manapun.")
        print(f"Node diekspansi: {result.nodes_expanded}")
        return
    print(f"Lintasan       : {' -> '.join(result.path)}")
    print(f"Total biaya    : {result.total_cost} (menit-ekuivalen)")
    print(f"Node diekspansi: {result.nodes_expanded}")
    print("Aksi agen (actuator):")
    for i, action in enumerate(result.actions, 1):
        print(f"  {i}. {action}")


def handle_knowledge_query(query: str, top_k: int = 3) -> None:
    from src.knowledge.chunking import load_and_chunk_corpus
    from src.knowledge.retriever import SemanticRetriever
    from src.knowledge.vector_store import DelCareVectorStore

    store = DelCareVectorStore()
    if store.count() == 0:
        raw_docs = "data/raw_docs"
        if os.path.exists(raw_docs) and os.listdir(raw_docs):
            print("Basis data vektor kosong. Mengindeks dokumen dari data/raw_docs/...")
            chunks = load_and_chunk_corpus(raw_docs)
            store.index_chunks(chunks)

    retriever = SemanticRetriever(store)
    res = retriever.search(query, top_k=top_k)

    print("\n" + "=" * 70)
    print("HASIL TEMU BALIK SEMANTIK BASIS PENGETAHUAN DELCARE COPILOT")
    print("=" * 70)
    print(f"Kueri           : {query}")
    print(f"Status Evaluasi : {res['status']}")
    print(f"Cosine Sim Tertinggi: {res['best_similarity']}")

    if res["is_out_of_domain"]:
        print("\n[PERINGATAN RELEVANCE GUARDRAIL]")
        print("Kueri ini berada di luar cakupan operasional/SOP Poliklinik IT Del.")
        print("Sistem menolak rekomendasi tindakan medis untuk kueri out-of-domain.")
    else:
        print(f"\nMenampilkan {len(res['matches'])} dokumen target paling relevan:")
        for idx, m in enumerate(res["matches"], 1):
            meta = m["metadata"]
            print(f"\n[{idx}] {meta['title']} ({meta['doc_id']})")
            print(f"    Kategori        : {meta['category']}")
            print(f"    Target Aksi     : {meta['target_action']}")
            print(f"    Cosine Sim      : {m['similarity_score']}")
            print(f"    Kutipan Teks    : {m['text'][:180]}...")


def handle_index_corpus() -> None:
    from src.knowledge.chunking import load_and_chunk_corpus
    from src.knowledge.vector_store import DelCareVectorStore

    raw_docs = "data/raw_docs"
    if not os.path.exists(raw_docs) or not os.listdir(raw_docs):
        print(f"Direktori {raw_docs} tidak ditemukan atau kosong.")
        return

    print("Memulai proses ingestion dan chunking dokumen korpus...")
    chunks = load_and_chunk_corpus(raw_docs, chunk_size=500, chunk_overlap=100)
    print(f"Total chunk berhasil dibuat: {len(chunks)}")

    store = DelCareVectorStore()
    store.index_chunks(chunks)
    print(f"Penyimpanan persisten selesai. Total dokumen di ChromaDB: {store.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DelCare Copilot - SPK Cerdas Klinik IT Del (Search & RAG Knowledge Base)"
    )
    # Argumen Baseline Search
    parser.add_argument("--start", default=START, choices=NODES, help="Node awal baseline search")
    parser.add_argument(
        "--algo", default="ucs", choices=["ucs", "astar"], help="Algoritma pencarian"
    )
    parser.add_argument("--compare", action="store_true", help="Bandingkan UCS vs A* sekaligus")

    # Argumen Knowledge Base & Semantic Search (Milestone 3)
    parser.add_argument(
        "--query", "-q", type=str, help="Kueri temu balik semantik ke basis pengetahuan SOP"
    )
    parser.add_argument(
        "--index-kb", action="store_true", help="Re-index seluruh dokumen SOP ke ChromaDB"
    )
    parser.add_argument("--top-k", type=int, default=3, help="Jumlah dokumen teratas yang diambil")

    args = parser.parse_args()

    if args.index_kb:
        handle_index_corpus()
        return

    if args.query:
        handle_knowledge_query(args.query, top_k=args.top_k)
        return

    if args.compare:
        ucs_result = uniform_cost_search(args.start)
        astar_result = astar_search(args.start)
        print_search_result("UNIFORM COST SEARCH", ucs_result)
        print_search_result("A* SEARCH", astar_result)

        print("\n=== PERBANDINGAN ===")
        print(f"Total biaya sama?      : {ucs_result.total_cost == astar_result.total_cost}")
        print(f"UCS  nodes_expanded    : {ucs_result.nodes_expanded}")
        print(f"A*   nodes_expanded    : {astar_result.nodes_expanded}")
        return

    if args.algo == "ucs":
        result = uniform_cost_search(args.start)
        print_search_result(f"UCS dari {args.start}", result)
    else:
        result = astar_search(args.start)
        print_search_result(f"A* dari {args.start}", result)


if __name__ == "__main__":
    main()
