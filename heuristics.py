"""
Heuristik admissible untuk A* Search - DelCare Copilot
========================================================

STRATEGI:
    h(n) = (jumlah_hop_minimum_dari_n_ke_goal_terdekat) * (bobot_sisi_terkecil_di_graf)

BUKTI ADMISSIBLE (h(n) <= biaya_asli_terpendek g*(n)):
    1. jumlah_hop_minimum(n) dihitung via BFS tanpa bobot (unweighted),
       sehingga nilainya SELALU <= jumlah edge pada lintasan TERPENDEK
       (dalam hop) dari n ke goal manapun.
    2. Lintasan optimal (biaya minimum) dari n ke goal, apapun bentuknya,
       pasti terdiri dari >= jumlah_hop_minimum(n) edge (karena BFS
       memberi hop count MINIMUM yang mungkin; tidak ada lintasan lebih
       pendek dalam hitungan edge).
    3. Setiap edge di graf berbobot >= bobot_sisi_terkecil (min_edge_weight).
    4. Karena itu: biaya lintasan optimal
         >= (jumlah edge pada lintasan optimal) * bobot_sisi_terkecil
         >= jumlah_hop_minimum(n) * bobot_sisi_terkecil
         =  h(n)
       Sehingga h(n) <= g*(n) untuk semua n -> h ADMISSIBLE. (QED)

Heuristik ini juga CONSISTENT (monotonic) karena berasal dari BFS hop-count
pada graf yang sama: h(n) <= cost(n, n') + h(n') untuk setiap edge (n, n'),
sebab hop_count(n) <= 1 + hop_count(n') dan cost(n,n') >= min_edge_weight.
"""

from collections import deque

from src.graph_data import GOALS, GRAPH, NODES, min_edge_weight


def _reverse_graph() -> dict[str, list]:
    """Membalik arah graf agar BFS bisa dimulai dari goal menuju semua node."""
    reverse: dict[str, list] = {n: [] for n in NODES}
    for u, edges in GRAPH.items():
        for v, _cost, _label in edges:
            reverse.setdefault(v, []).append(u)
    return reverse


def compute_hop_distances(goals: set[str] | None = None) -> dict[str, int]:
    """
    BFS multi-source dari seluruh goal (via reverse graph) untuk menghitung
    jumlah hop minimum dari SETIAP node menuju goal TERDEKAT.
    Node yang tidak bisa mencapai goal manapun diberi jarak = infinity.
    """
    if goals is None:
        goals = GOALS

    reverse = _reverse_graph()
    dist: dict[str, int] = {n: float("inf") for n in NODES}
    queue = deque()

    for g in goals:
        dist[g] = 0
        queue.append(g)

    while queue:
        current = queue.popleft()
        for prev_node in reverse.get(current, []):
            if dist[prev_node] == float("inf"):
                dist[prev_node] = dist[current] + 1
                queue.append(prev_node)

    return dist


class GoalDistanceHeuristic:
    """
    Heuristik siap pakai: heuristic(node) -> estimasi biaya minimum ke goal.
    Precompute sekali saat inisialisasi supaya efisien dipanggil berkali-kali
    oleh A*.
    """

    def __init__(self, goals: set[str] | None = None):
        self.goals = goals if goals is not None else GOALS
        self.hop_distances = compute_hop_distances(self.goals)
        self.min_weight = min_edge_weight()

    def __call__(self, node: str) -> float:
        hop = self.hop_distances.get(node, float("inf"))
        if hop == float("inf"):
            return float("inf")
        return hop * self.min_weight


if __name__ == "__main__":
    h = GoalDistanceHeuristic()
    print(f"{'NODE':<25} {'HOP KE GOAL':<12} {'h(n)':<8}")
    for node in NODES:
        hop = h.hop_distances[node]
        print(f"{node:<25} {hop!s:<12} {h(node):<8}")
