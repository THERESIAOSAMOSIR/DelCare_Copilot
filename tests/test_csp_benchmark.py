from src.csp.benchmark import run_benchmark


def test_benchmark_covers_scales_and_heuristics():
    rows = run_benchmark([1, 2])

    assert len(rows) == 8
    assert {row.weeks for row in rows} == {1, 2}
    assert {row.configuration for row in rows} == {
        "all_heuristics",
        "without_ac3",
        "without_mrv",
        "without_forward_checking",
    }
    assert all(row.status == "solved" for row in rows)
    assert all(row.variables == row.weeks * 30 for row in rows)
    assert all(row.time_ms >= 0 for row in rows)


def test_benchmark_rejects_non_positive_scale():
    try:
        run_benchmark([0])
    except ValueError as error:
        assert "positif" in str(error)
    else:
        raise AssertionError("benchmark harus menolak skala tidak valid")
