"""Entry point modular CSP solver penjadwalan shift Klinik IT Del (Milestone 2).

Pemakaian (dari root repo):
    uv run python -m src.csp.solver                      # skala kecil
    uv run python -m src.csp.solver --doctors 5 --nurses 12 --weeks 2
    uv run python -m src.csp.solver --leave D1:4 --leave N2:2
    uv run python -m src.csp.solver --no-mrv --no-lcv    # matikan heuristik
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field

from .backtracking import BacktrackingSolver, SolveStats
from .instances import build_instance
from .model import HARI, SHIFT_NAMES, CSPModel, Var


@dataclass
class SolveResult:
    """Hasil solve: solusi (None bila tidak ada), statistik, dan hasil verifikasi."""

    assignment: dict[Var, str] | None
    stats: SolveStats
    violations: list[str] = field(default_factory=list)  # kosong = solusi valid

    @property
    def ok(self) -> bool:
        return self.assignment is not None and not self.violations


def solve(
    model: CSPModel,
    use_ac3: bool = True,
    use_mrv: bool = True,
    use_lcv: bool = True,
    use_fc: bool = True,
    max_nodes: int = 200_000,
) -> SolveResult:
    """Selesaikan CSP, lalu verifikasi solusi secara independen (C1-C7)."""
    solver = BacktrackingSolver(model, use_ac3, use_mrv, use_lcv, use_fc, max_nodes)
    assignment, stats = solver.solve()
    violations = model.verify_solution(assignment) if assignment else []
    return SolveResult(assignment, stats, violations)


def format_schedule(model: CSPModel, assignment: dict[Var, str]) -> str:
    """Tabel jadwal teks: satu baris per (hari, shift)."""
    lines = [f"{'Hari':<14}{'Shift':<7}{'Dokter':<10}Perawat"]
    for d in range(model.num_days):
        for sh in range(model.num_shifts):
            row = [v for v in model.variables if v.day == d and v.shift == sh]
            dokter = ", ".join(assignment[v] for v in row if v.role == "DOKTER")
            perawat = ", ".join(assignment[v] for v in row if v.role == "PERAWAT")
            hari = f"M{d // 5 + 1}-{HARI[d % 5]}" if sh == 0 else ""
            lines.append(f"{hari:<14}{SHIFT_NAMES[sh]:<7}{dokter:<10}{perawat}")
    return "\n".join(lines)


def _parse_leaves(items: list[str]) -> dict[str, set[int]]:
    """Ubah ['D1:4', 'N2:2'] menjadi {'D1': {4}, 'N2': {2}} (hari indeks 0 = Senin)."""
    leaves: dict[str, set[int]] = {}
    for item in items:
        staff_id, day = item.split(":")
        leaves.setdefault(staff_id.strip(), set()).add(int(day))
    return leaves


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CSP solver jadwal shift Klinik IT Del")
    p.add_argument("--doctors", type=int, default=3)
    p.add_argument("--nurses", type=int, default=6)
    p.add_argument("--weeks", type=int, default=1)
    p.add_argument("--leave", action="append", default=[], help="ID:hari_indeks, mis. D1:4 (0=Senin)")
    p.add_argument("--no-ac3", action="store_true")
    p.add_argument("--no-mrv", action="store_true")
    p.add_argument("--no-lcv", action="store_true")
    p.add_argument("--no-fc", action="store_true")
    p.add_argument("--max-nodes", type=int, default=200_000)
    args = p.parse_args(argv)

    model = build_instance(args.doctors, args.nurses, args.weeks, _parse_leaves(args.leave))
    result = solve(
        model,
        use_ac3=not args.no_ac3,
        use_mrv=not args.no_mrv,
        use_lcv=not args.no_lcv,
        use_fc=not args.no_fc,
        max_nodes=args.max_nodes,
    )
    s = result.stats
    print(f"Status      : {s.status}" + (f" ({s.reason})" if s.reason else ""))
    print(f"Node        : {s.nodes} | Backtrack: {s.backtracks} | AC-3 pangkas: {s.ac3_pruned}")
    print(f"Waktu       : {s.time_s * 1000:.2f} ms")
    if result.assignment:
        print(f"Verifikasi  : {'VALID (C1-C7 terpenuhi)' if result.ok else result.violations}")
        print(format_schedule(model, result.assignment))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
