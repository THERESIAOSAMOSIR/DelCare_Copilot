"""
DelCare Copilot - CLI Baseline Search
========================================
Jalankan dari root proyek (setelah `uv sync`):

    uv run python -m src.cli
    uv run python -m src.cli --start TRIASE_MERAH --algo astar
    uv run python -m src.cli --compare

Argumen:
    --start   Node awal (default: PENDAFTARAN)
    --algo    ucs | astar (default: ucs)
    --compare Jalankan UCS & A* sekaligus lalu bandingkan nodes_expanded
"""

import argparse

from src.graph_data import NODES, START
from src.search.astar import astar_search
from src.search.ucs import uniform_cost_search


def print_result(label: str, result) -> None:
    print(f"\n=== {label} ===")
    if result.path is None:
        print("Tidak ditemukan lintasan menuju goal manapun.")
        print(f"Node diekspansi: {result.nodes_expanded}")
        return
    print(f"Lintasan     : {' -> '.join(result.path)}")
    print(f"Total biaya  : {result.total_cost} (menit-ekuivalen)")
    print(f"Node diekspansi: {result.nodes_expanded}")
    print("Aksi agen (actuator):")
    for i, action in enumerate(result.actions, 1):
        print(f"  {i}. {action}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DelCare Copilot - Baseline Search (UCS/A*)")
    parser.add_argument("--start", default=START, choices=NODES, help="Node awal")
    parser.add_argument(
        "--algo", default="ucs", choices=["ucs", "astar"], help="Algoritma pencarian"
    )
    parser.add_argument("--compare", action="store_true", help="Bandingkan UCS vs A* sekaligus")
    args = parser.parse_args()

    if args.compare:
        ucs_result = uniform_cost_search(args.start)
        astar_result = astar_search(args.start)
        print_result("UNIFORM COST SEARCH", ucs_result)
        print_result("A* SEARCH", astar_result)

        print("\n=== PERBANDINGAN ===")
        print(f"Total biaya sama?      : {ucs_result.total_cost == astar_result.total_cost}")
        print(f"UCS  nodes_expanded    : {ucs_result.nodes_expanded}")
        print(f"A*   nodes_expanded    : {astar_result.nodes_expanded}")
        return

    if args.algo == "ucs":
        result = uniform_cost_search(args.start)
        print_result(f"UCS dari {args.start}", result)
    else:
        result = astar_search(args.start)
        print_result(f"A* dari {args.start}", result)


if __name__ == "__main__":
    main()
