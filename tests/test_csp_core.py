"""Tes inti CSP: model (C1-C7), AC-3, dan kebenaran solver pada kasus normal."""
import pytest

from src.csp.ac3 import ac3, revise
from src.csp.instances import build_instance, small_instance
from src.csp.model import Var
from src.csp.solver import solve

HEURISTIC_CONFIGS = [
    {"use_ac3": False, "use_mrv": False, "use_lcv": False, "use_fc": False},
    {"use_ac3": False, "use_mrv": False, "use_lcv": False, "use_fc": True},
    {"use_ac3": False, "use_mrv": True, "use_lcv": False, "use_fc": True},
    {},  # semua aktif
]


def test_model_has_30_variables_for_one_week():
    # 5 hari x 2 shift x (1 dokter + 2 perawat) = 30
    assert len(small_instance().variables) == 30


def test_unary_constraints_c1_c2_prune_initial_domains():
    m = small_instance()  # D1 cuti Jumat (4), N2 cuti Rabu (2)
    assert "D1" not in m.domains[Var(4, 0, "DOKTER-1")]  # C2
    assert "N2" not in m.domains[Var(2, 1, "PERAWAT-1")]  # C2
    assert all(p.startswith("D") for p in m.domains[Var(0, 0, "DOKTER-1")])  # C1
    assert all(p.startswith("N") for p in m.domains[Var(0, 0, "PERAWAT-2")])  # C1


def test_revise_removes_unsupported_value():
    m = small_instance()
    a, b = Var(0, 0, "DOKTER-1"), Var(0, 1, "DOKTER-1")  # hari sama -> bertetangga
    domains = {v: set(d) for v, d in m.domains.items()}
    domains[b] = {"D1"}  # b hanya bisa D1, maka a tidak boleh D1
    assert revise(m, domains, a, b) is True
    assert "D1" not in domains[a]


def test_ac3_detects_inconsistency():
    m = small_instance()
    a, b = Var(0, 0, "DOKTER-1"), Var(0, 1, "DOKTER-1")
    domains = {v: set(d) for v, d in m.domains.items()}
    domains[a] = {"D1"}
    domains[b] = {"D1"}  # keduanya wajib D1 di hari sama -> mustahil
    consistent, _ = ac3(m, domains)
    assert consistent is False


def test_ac3_keeps_consistent_problem_consistent():
    m = small_instance()
    domains = {v: set(d) for v, d in m.domains.items()}
    consistent, _ = ac3(m, domains)
    assert consistent is True


@pytest.mark.parametrize("cfg", HEURISTIC_CONFIGS)
def test_solver_finds_valid_solution_for_every_heuristic_combo(cfg):
    m = small_instance()
    r = solve(m, **cfg)
    assert r.stats.status == "solved"
    assert r.violations == []  # verifikasi independen C1-C7
    assert len(r.assignment) == len(m.variables)  # C7: semua slot terisi


def test_solution_respects_leave_and_workload_limits():
    m = small_instance()
    r = solve(m)
    # C2: tidak ada petugas bertugas saat cuti
    assert all(v.day not in m.staff[p].leave_days for v, p in r.assignment.items())
    # C6: dokter maks 4 shift per minggu
    for doc in m.staff_by_role["DOKTER"]:
        assert sum(1 for p in r.assignment.values() if p == doc) <= 4


def test_solution_is_balanced_c5():
    m = small_instance()
    r = solve(m)
    for role, ids in m.staff_by_role.items():
        loads = [sum(1 for p in r.assignment.values() if p == i) for i in ids]
        assert max(loads) - min(loads) <= m.max_gap, role


def test_solver_is_deterministic():
    a = solve(small_instance()).assignment
    b = solve(small_instance()).assignment
    assert a == b


def test_mrv_and_fc_reduce_search_effort():
    plain = solve(small_instance(), use_ac3=False, use_mrv=False, use_lcv=False, use_fc=False)
    smart = solve(small_instance())
    assert smart.stats.nodes < plain.stats.nodes
    assert smart.stats.backtracks <= plain.stats.backtracks


def test_verify_solution_catches_tampered_schedule():
    m = small_instance()
    sol = dict(solve(m).assignment)
    # sisipkan pelanggaran C3/C4: dokter yang sama dua shift di hari Senin
    sol[Var(0, 1, "DOKTER-1")] = sol[Var(0, 0, "DOKTER-1")]
    assert any("C3/C4" in e for e in m.verify_solution(sol))


@pytest.mark.parametrize("weeks,doctors,nurses", [(2, 5, 12), (4, 8, 20)])
def test_solver_scales_to_larger_instances(weeks, doctors, nurses):
    m = build_instance(doctors, nurses, weeks)
    r = solve(m)
    assert r.ok
