from src.graph_data import GOALS, NODES, START
from src.search.ucs import uniform_cost_search


def test_ucs_finds_path_from_start():
    result = uniform_cost_search(START)
    assert result.path is not None
    assert result.path[0] == START
    assert result.path[-1] in GOALS


def test_ucs_total_cost_matches_manual_sum():
    """Total cost harus sama dengan penjumlahan bobot sisi sepanjang path."""
    from src.graph_data import GRAPH

    result = uniform_cost_search(START)
    manual_sum = 0
    for u, v in zip(result.path, result.path[1:]):
        edge = next(e for e in GRAPH[u] if e[0] == v)
        manual_sum += edge[1]
    assert manual_sum == result.total_cost


def test_ucs_picks_cheapest_referral_for_merah():
    """
    Kasus MERAH: RS_C sengaja dibuat sangat mahal (25 menit-ekuivalen).
    UCS harus memilih RS_A (termurah: 7) untuk kasus gawat darurat,
    BUKAN RS_C, walau urutan pendefinisian RS_C ada di graf.
    """
    result = uniform_cost_search("KEPUTUSAN_RUJUK_MERAH")
    assert "RUJUK_RS_C_MERAH" not in result.path
    assert "RUJUK_RS_A_MERAH" in result.path


def test_ucs_no_path_returns_none_gracefully():
    result = uniform_cost_search("SELESAI_RAWAT_JALAN", goals={"PENDAFTARAN"})
    assert result.path is None
    assert result.total_cost == float("inf")


def test_ucs_reaches_every_node_that_has_a_path_to_a_goal():
    """Sanity check: dari semua node kecuali goal itu sendiri, UCS harus
    berhasil menemukan sebuah goal (graf DelCare bersifat acyclic menuju goal)."""
    for node in NODES:
        if node in GOALS:
            continue
        result = uniform_cost_search(node)
        assert result.path is not None, f"Tidak ada path dari {node} ke goal manapun"
