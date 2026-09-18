"""
A* Search - DelCare Copilot
=============================
Sama seperti UCS, tetapi urutan prioritas frontier memakai f(n) = g(n) + h(n),
dengan h(n) dari heuristics.GoalDistanceHeuristic (admissible & consistent,
lihat pembuktian di heuristics.py).

Karena h consistent, A* dengan graph-search + explored set dijamin tetap
OPTIMAL (hasil total_cost identik dengan UCS), namun idealnya nodes_expanded
lebih sedikit atau sama dibanding UCS -- ini menjadi bahan perbandingan
di laporan (Tahap 4 pada instruksi pengerjaan).
"""

import heapq
import itertools
from collections.abc import Callable

from src.graph_data import GOALS, GRAPH, get_neighbors
from src.search.heuristics import GoalDistanceHeuristic
from src.search.ucs import SearchResult, _reconstruct


def astar_search(
    start: str,
    goals: set[str] | None = None,
    graph: dict | None = None,
    heuristic: Callable[[str], float] | None = None,
) -> SearchResult:
    if goals is None:
        goals = GOALS
    if graph is None:
        graph = GRAPH
    if heuristic is None:
        heuristic = GoalDistanceHeuristic(goals)

    counter = itertools.count()
    frontier: list[tuple[float, int, str]] = []
    # f_cost = g + h ; kita simpan g terpisah lewat best_cost
    heapq.heappush(frontier, (heuristic(start), next(counter), start))

    came_from: dict[str, str | None] = {start: None}
    action_taken: dict[str, str | None] = {start: None}
    best_cost: dict[str, float] = {start: 0.0}
    explored: set[str] = set()
    nodes_expanded = 0

    while frontier:
        _f_cost, _, node = heapq.heappop(frontier)

        if node in explored:
            continue
        explored.add(node)
        nodes_expanded += 1
        g_cost = best_cost[node]

        if node in goals:
            return _reconstruct(node, g_cost, came_from, action_taken, nodes_expanded)

        for neighbor, edge_cost, action in get_neighbors(node):
            new_g = g_cost + edge_cost
            if neighbor in explored:
                continue
            if neighbor not in best_cost or new_g < best_cost[neighbor]:
                best_cost[neighbor] = new_g
                came_from[neighbor] = node
                action_taken[neighbor] = action
                f_cost = new_g + heuristic(neighbor)
                heapq.heappush(frontier, (f_cost, next(counter), neighbor))

    return SearchResult(path=None, total_cost=float("inf"), nodes_expanded=nodes_expanded)


if __name__ == "__main__":
    from src.graph_data import START

    result = astar_search(START)
    print("=== A* Search: DelCare Copilot ===")
    print(f"Start : {START}")
    print(result)
    print("\nUrutan aksi (actuator) yang dieksekusi agen:")
    for i, action in enumerate(result.actions, 1):
        print(f"  {i}. {action}")
