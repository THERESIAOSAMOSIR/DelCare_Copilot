"""Tes kasus ekstrem (edge cases) CSP solver. Semua kasus infeasible harus
ditolak dengan anggun (tanpa crash, tanpa loop tak berujung)."""
from src.csp.instances import build_instance
from src.csp.solver import main, solve


def test_too_few_doctors_is_infeasible():
    # 2 dokter x maks 4 shift = 8 < kebutuhan 10 slot dokter per minggu
    r = solve(build_instance(n_doctors=2))
    assert r.stats.status == "infeasible"
    assert r.assignment is None
    assert "kapasitas" in r.stats.reason


def test_all_doctors_on_leave_same_day_is_infeasible():
    leaves = {f"D{i}": {2} for i in (1, 2, 3)}  # semua dokter cuti Rabu
    r = solve(build_instance(leaves=leaves))
    assert r.stats.status == "infeasible"
    assert r.stats.nodes == 0  # ditolak sebelum pencarian dimulai


def test_single_nurse_is_infeasible():
    r = solve(build_instance(n_nurses=1))  # butuh 4 perawat berbeda per hari
    assert r.stats.status == "infeasible"


def test_zero_doctors_is_infeasible_without_crash():
    r = solve(build_instance(n_doctors=0))
    assert r.stats.status == "infeasible"


def test_zero_staff_at_all_is_infeasible_without_crash():
    r = solve(build_instance(n_doctors=0, n_nurses=0))
    assert r.stats.status == "infeasible"


def test_exactly_enough_nurses_per_day_is_feasible():
    # 4 slot perawat per hari -> 4 perawat pas, tiap orang kerja 5 hari (maks 5)
    r = solve(build_instance(n_nurses=4))
    assert r.ok


def test_tight_doctor_capacity_still_solvable():
    # 3 dokter x 4 = 12 >= 10: layak walau ketat
    assert solve(build_instance(n_doctors=3)).ok


def test_one_doctor_on_leave_reduces_capacity_but_stays_feasible():
    # D1 cuti Jumat: kapasitas D1 = 4 hari tersedia -> tetap layak
    assert solve(build_instance(leaves={"D1": {4}})).ok


def test_two_doctors_on_leave_same_day_is_infeasible():
    # Rabu hanya D3 tersedia, tapi butuh 2 dokter berbeda (Pagi + Sore) -> infeasible
    leaves = {"D1": {2}, "D2": {2}}
    r = solve(build_instance(leaves=leaves))
    assert r.stats.status == "infeasible"


def test_node_limit_stops_search_gracefully():
    r = solve(build_instance(), use_ac3=False, use_mrv=False, use_lcv=False, use_fc=False, max_nodes=5)
    assert r.stats.status == "node_limit"
    assert r.assignment is None


def test_tight_workload_cap_makes_problem_infeasible():
    # semua perawat maks 2 shift: 6 x 2 = 12 < 20 slot perawat
    r = solve(build_instance(nurse_max=2))
    assert r.stats.status == "infeasible"


def test_two_week_horizon_is_feasible_and_respects_weekly_cap():
    m = build_instance(n_doctors=4, n_nurses=8, weeks=2)
    r = solve(m)
    assert r.ok
    for week in range(2):
        for doc in m.staff_by_role["DOKTER"]:
            n = sum(1 for v, p in r.assignment.items() if p == doc and v.week == week)
            assert n <= 4


def test_cli_exit_codes(capsys):
    assert main([]) == 0  # skala kecil: sukses
    assert "VALID" in capsys.readouterr().out
    assert main(["--doctors", "2"]) == 1  # infeasible: kode keluar 1
