from src.graph_data import GOALS, NODES, START
from src.search.astar import astar_search
from src.search.ucs import uniform_cost_search


def test_astar_finds_path_from_start():
    result = astar_search(START)
    assert result.path is not None
    assert result.path[0] == START
    assert result.path[-1] in GOALS


def test_astar_is_optimal_matches_ucs_cost():
    """
    Karena heuristik consistent, A* WAJIB menghasilkan total_cost yang
    identik dengan UCS (sama-sama optimal) untuk setiap node awal.
    """
    for node in NODES:
        if node in GOALS:
            continue
        ucs_result = uniform_cost_search(node)
        astar_result = astar_search(node)
        assert ucs_result.total_cost == astar_result.total_cost, (
            f"Biaya berbeda dari node {node}: "
            f"UCS={ucs_result.total_cost} vs A*={astar_result.total_cost}"
        )


def test_astar_expands_no_more_nodes_than_ucs():
    """
    Dengan heuristik admissible & consistent, A* seharusnya mengekspansi
    node <= jumlah yang diekspansi UCS (efisiensi pencarian meningkat).
    """
    ucs_result = uniform_cost_search(START)
    astar_result = astar_search(START)
    assert astar_result.nodes_expanded <= ucs_result.nodes_expanded


def test_astar_picks_cheapest_referral_for_merah():
    result = astar_search("KEPUTUSAN_RUJUK_MERAH")
    assert "RUJUK_RS_C_MERAH" not in result.path
    assert "RUJUK_RS_A_MERAH" in result.path
