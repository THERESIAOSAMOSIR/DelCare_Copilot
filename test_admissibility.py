"""
Pembuktian EMPIRIS bahwa heuristik GoalDistanceHeuristic bersifat
admissible: h(n) <= g*(n) untuk SEMUA node n, di mana g*(n) adalah biaya
lintasan optimal (didapat dari hasil UCS, yang terbukti optimal).

Pembuktian MATEMATIS-nya ada di docstring src/search/heuristics.py.
Test ini memverifikasi bahwa implementasi konkretnya benar-benar
memenuhi janji matematis tersebut, untuk seluruh node di graf.
"""

from src.graph_data import GOALS, NODES
from src.search.heuristics import GoalDistanceHeuristic
from src.search.ucs import uniform_cost_search


def test_heuristic_never_overestimates_true_cost():
    heuristic = GoalDistanceHeuristic()

    for node in NODES:
        if node in GOALS:
            # h(goal) harus 0 untuk konsistensi standar A*
            assert heuristic(node) == 0
            continue

        true_cost = uniform_cost_search(node).total_cost
        h_value = heuristic(node)

        assert h_value <= true_cost, (
            f"PELANGGARAN ADMISSIBILITY pada node {node}: h(n)={h_value} > g*(n)={true_cost}"
        )


def test_heuristic_is_consistent():
    """
    Uji konsistensi (monotonicity): untuk setiap edge (n, n') dengan
    bobot cost, harus berlaku h(n) <= cost(n, n') + h(n').
    Konsistensi menjamin f(n) tidak pernah menurun sepanjang lintasan,
    sehingga node yang sudah di-explored tidak perlu dibuka ulang.
    """
    from src.graph_data import GRAPH

    heuristic = GoalDistanceHeuristic()

    for node, edges in GRAPH.items():
        for neighbor, cost, _label in edges:
            h_n = heuristic(node)
            h_neighbor = heuristic(neighbor)
            assert h_n <= cost + h_neighbor, (
                f"PELANGGARAN CONSISTENCY pada edge {node} -> {neighbor}: "
                f"h({node})={h_n} > cost={cost} + h({neighbor})={h_neighbor}"
            )
