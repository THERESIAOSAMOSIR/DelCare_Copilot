"""
Uniform Cost Search (UCS) - DelCare Copilot
=============================================
Mencari lintasan BERBIAYA MINIMUM dari sebuah node awal menuju salah satu
node goal, menggunakan priority queue (heapq) berbasis biaya kumulatif g(n).

Struktur frontier: (g_cost, tie_breaker_counter, node)
    - g_cost         : biaya kumulatif dari start ke node ini
    - tie_breaker    : counter unik agar heapq tidak pernah membandingkan
                        dua node (str) secara langsung ketika g_cost sama
                        (menghindari TypeError & membuat urutan FIFO stabil
                        antar node dengan biaya sama)
    - node           : nama state

GRAPH-SEARCH (bukan tree-search): memakai `explored` set supaya node yang
sudah final tidak diproses ulang -> mencegah infinite loop pada graf yang
punya siklus / banyak lintasan menuju node yang sama.
"""

import heapq
import itertools
from dataclasses import dataclass, field

from src.graph_data import GOALS, GRAPH, get_neighbors


@dataclass
class SearchResult:
    path: list[str] | None
    total_cost: float
    nodes_expanded: int
    actions: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        if self.path is None:
            return f"SearchResult(GAGAL, nodes_expanded={self.nodes_expanded})"
        return (
            f"SearchResult(path={' -> '.join(self.path)}, "
            f"total_cost={self.total_cost}, nodes_expanded={self.nodes_expanded})"
        )


def uniform_cost_search(
    start: str,
    goals: set[str] | None = None,
    graph: dict | None = None,
) -> SearchResult:
    """
    Menjalankan UCS dari `start` menuju node goal terdekat (biaya minimum)
    di antara himpunan `goals`.

    Return SearchResult berisi path node, total biaya, jumlah node yang
    diekspansi (untuk dibandingkan dengan A* di laporan), dan daftar label
    aksi/actuator pada tiap transisi.
    """
    if goals is None:
        goals = GOALS
    if graph is None:
        graph = GRAPH

    counter = itertools.count()  # tie-breaker unik & stabil
    frontier: list[tuple[float, int, str]] = []
    heapq.heappush(frontier, (0.0, next(counter), start))

    came_from: dict[str, str | None] = {start: None}
    action_taken: dict[str, str | None] = {start: None}
    best_cost: dict[str, float] = {start: 0.0}
    explored: set[str] = set()
    nodes_expanded = 0

    while frontier:
        g_cost, _, node = heapq.heappop(frontier)

        if node in explored:
            continue
        explored.add(node)
        nodes_expanded += 1

        if node in goals:
            return _reconstruct(node, g_cost, came_from, action_taken, nodes_expanded)

        for neighbor, edge_cost, action in get_neighbors(node):
            new_cost = g_cost + edge_cost
            if neighbor in explored:
                continue
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = node
                action_taken[neighbor] = action
                heapq.heappush(frontier, (new_cost, next(counter), neighbor))

    return SearchResult(path=None, total_cost=float("inf"), nodes_expanded=nodes_expanded)


def _reconstruct(
    goal_node: str,
    total_cost: float,
    came_from: dict[str, str | None],
    action_taken: dict[str, str | None],
    nodes_expanded: int,
) -> SearchResult:
    path = []
    actions = []
    node = goal_node
    while node is not None:
        path.append(node)
        if action_taken[node] is not None:
            actions.append(action_taken[node])
        node = came_from[node]
    path.reverse()
    actions.reverse()
    return SearchResult(
        path=path, total_cost=total_cost, nodes_expanded=nodes_expanded, actions=actions
    )


if __name__ == "__main__":
    from src.graph_data import START

    result = uniform_cost_search(START)
    print("=== Uniform Cost Search: DelCare Copilot ===")
    print(f"Start : {START}")
    print(result)
    print("\nUrutan aksi (actuator) yang dieksekusi agen:")
    for i, action in enumerate(result.actions, 1):
        print(f"  {i}. {action}")
