"""Propagasi batasan AC-3 (Arc Consistency #3) untuk CSP penjadwalan.

AC-3 hanya menangani batasan biner (C3/C4). Batasan n-ary (C5, C6)
dicek terpisah di CSPModel.is_consistent() saat backtracking.
"""
from __future__ import annotations

from collections import deque

from .model import CSPModel, Var

Domains = dict[Var, set[str]]


def revise(model: CSPModel, domains: Domains, xi: Var, xj: Var) -> bool:
    """Hapus nilai x dari D(xi) bila tidak ada y di D(xj) yang kompatibel.

    Return True jika ada nilai yang dihapus.
    """
    removed = False
    for x in list(domains[xi]):
        # x didukung jika ada y di D(xj) yang memenuhi batasan biner
        if not any(model.binary_ok(xi, x, xj, y) for y in domains[xj]):
            domains[xi].discard(x)
            removed = True
    return removed


def ac3(model: CSPModel, domains: Domains) -> tuple[bool, int]:
    """Jalankan AC-3 pada `domains` (diubah in-place).

    Return (konsisten, jumlah_nilai_terpangkas). konsisten=False berarti
    ada domain kosong, jadi CSP pasti tidak punya solusi.
    """
    queue: deque[tuple[Var, Var]] = deque(
        (xi, xj) for xi in model.variables for xj in model.neighbors[xi]
    )
    before = sum(len(d) for d in domains.values())
    while queue:
        xi, xj = queue.popleft()
        if revise(model, domains, xi, xj):
            if not domains[xi]:
                return False, before - sum(len(d) for d in domains.values())
            # domain xi berubah: arc (xk, xi) harus dicek ulang
            queue.extend((xk, xi) for xk in model.neighbors[xi] if xk != xj)
    return True, before - sum(len(d) for d in domains.values())
