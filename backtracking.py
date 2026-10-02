"""Backtracking search dengan MRV, LCV, dan Forward Checking.

Setiap heuristik bisa dimatikan lewat flag, supaya benchmark sensitivitas
dapat membandingkan: tanpa heuristik vs dengan MRV/LCV/FC.
"""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass

from .ac3 import ac3
from .model import CSPModel, Var


class NodeLimitExceeded(Exception):
    """Dilempar bila jumlah node melebihi batas (mencegah loop sangat lama)."""


@dataclass
class SolveStats:
    status: str = "unsolved"  # solved | infeasible | node_limit
    nodes: int = 0  # jumlah percobaan penugasan nilai
    backtracks: int = 0  # jumlah kali mundur
    ac3_pruned: int = 0  # nilai domain terpangkas oleh AC-3
    time_s: float = 0.0
    reason: str = ""


class BacktrackingSolver:
    def __init__(
        self,
        model: CSPModel,
        use_ac3: bool = True,
        use_mrv: bool = True,
        use_lcv: bool = True,
        use_fc: bool = True,
        max_nodes: int = 200_000,
    ) -> None:
        self.model = model
        self.use_ac3, self.use_mrv, self.use_lcv, self.use_fc = use_ac3, use_mrv, use_lcv, use_fc
        self.max_nodes = max_nodes

    # ------------------------------------------------------------------ API
    def solve(self) -> tuple[dict[Var, str] | None, SolveStats]:
        t0 = time.perf_counter()
        stats = SolveStats()
        self.stats = stats
        self.assignment: dict[Var, str] = {}
        self.week_load: Counter = Counter()
        self.total_load: Counter = Counter()
        domains = {v: set(d) for v, d in self.model.domains.items()}

        ok, reason = self.model.quick_feasibility()
        if not ok:
            return self._finish(None, "infeasible", t0, reason)
        if any(not d for d in domains.values()):
            return self._finish(None, "infeasible", t0, "domain kosong setelah C1/C2")
        if self.use_ac3:
            ok, stats.ac3_pruned = ac3(self.model, domains)
            if not ok:
                return self._finish(None, "infeasible", t0, "AC-3 menemukan domain kosong")
        try:
            found = self._search(domains)
        except NodeLimitExceeded:
            return self._finish(None, "node_limit", t0, f"melebihi {self.max_nodes} node")
        if found:
            return self._finish(dict(self.assignment), "solved", t0, "")
        return self._finish(None, "infeasible", t0, "ruang pencarian habis")

    def _finish(self, sol, status, t0, reason):
        self.stats.status, self.stats.reason = status, reason
        self.stats.time_s = time.perf_counter() - t0
        return sol, self.stats

    # --------------------------------------------------------------- search
    def _search(self, domains: dict[Var, set[str]]) -> bool:
        if len(self.assignment) == len(self.model.variables):
            return True
        var = self._select_variable(domains)
        for val in self._order_values(var, domains):
            self.stats.nodes += 1
            if self.stats.nodes > self.max_nodes:
                raise NodeLimitExceeded
            if not self.model.is_consistent(var, val, self.assignment, self.week_load, self.total_load):
                continue
            self._assign(var, val)
            removed: list[tuple[Var, str]] = []
            if (not self.use_fc or self._forward_check(var, val, domains, removed)) and self._search(domains):
                return True
            self._unassign(var, val)
            for w, x in removed:  # kembalikan domain
                domains[w].add(x)
            self.stats.backtracks += 1
        return False

    def _assign(self, var: Var, val: str) -> None:
        self.assignment[var] = val
        self.week_load[(val, var.week)] += 1
        self.total_load[val] += 1

    def _unassign(self, var: Var, val: str) -> None:
        del self.assignment[var]
        self.week_load[(val, var.week)] -= 1
        self.total_load[val] -= 1

    # ------------------------------------------------------------ heuristik
    def _select_variable(self, domains: dict[Var, set[str]]) -> Var:
        """MRV: pilih variabel dengan sisa nilai legal paling sedikit."""
        unassigned = [v for v in self.model.variables if v not in self.assignment]
        if not self.use_mrv:
            return unassigned[0]  # urutan statis
        # tie-break: derajat tertinggi (paling banyak tetangga belum terisi)
        return min(
            unassigned,
            key=lambda v: (
                len(domains[v]),
                -sum(1 for n in self.model.neighbors[v] if n not in self.assignment),
            ),
        )

    def _order_values(self, var: Var, domains: dict[Var, set[str]]) -> list[str]:
        """LCV: coba dulu nilai yang paling sedikit membatasi tetangga.

        Tie-break: petugas dengan beban total lebih kecil (membantu C5).
        """
        vals = sorted(domains[var])
        if not self.use_lcv:
            return vals

        def constraining(val: str) -> int:
            return sum(
                1 for n in self.model.neighbors[var] if n not in self.assignment and val in domains[n]
            )

        return sorted(vals, key=lambda x: (constraining(x), self.total_load[x], x))

    # ------------------------------------------------------ forward checking
    def _forward_check(
        self, var: Var, val: str, domains: dict[Var, set[str]], removed: list[tuple[Var, str]]
    ) -> bool:
        """Pangkas domain variabel yang belum terisi setelah (var=val).

        1. C3/C4: val dihapus dari tetangga di hari yang sama.
        2. C6: bila beban mingguan val sudah penuh, val dihapus dari
           semua variabel belum terisi di minggu itu.
        Return False bila ada domain menjadi kosong (dead end lebih dini).
        """
        full = self.week_load[(val, var.week)] >= self.model.staff[val].max_shifts_per_week
        for w in self.model.variables:
            if w in self.assignment or val not in domains[w]:
                continue
            if w.day == var.day or (full and w.week == var.week):
                domains[w].discard(val)
                removed.append((w, val))
                if not domains[w]:
                    return False
        return True
