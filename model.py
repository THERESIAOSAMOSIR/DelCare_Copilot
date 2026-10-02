"""Model formal CSP penjadwalan shift petugas Klinik IT Del (Milestone 2).

Formulasi CSP = (X, D, C):
  X : variabel Var(hari, shift, slot), mis. Var(0, 0, "DOKTER-1")
  D : domain = himpunan id petugas (dipangkas oleh batasan unary C1 & C2)
  C : batasan C1..C7 (lihat docstring tiap method)

Asumsi tim (data sintetis): Senin-Jumat, 2 shift (Pagi 08-12, Sore 13-17),
1 slot Dokter + 2 slot Perawat per shift. Perawat yang bertugas juga
menjalankan triase awal, sehingga triase bukan variabel terpisah.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import NamedTuple

DAYS_PER_WEEK = 5
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
SHIFT_NAMES = ["Pagi", "Sore"]
SLOTS_PER_SHIFT = {"DOKTER": 1, "PERAWAT": 2}


class Var(NamedTuple):
    """Satu slot kerja: (indeks hari, indeks shift, nama slot)."""

    day: int
    shift: int
    slot: str  # contoh: "DOKTER-1", "PERAWAT-2"

    @property
    def role(self) -> str:
        return self.slot.split("-")[0]

    @property
    def week(self) -> int:
        return self.day // DAYS_PER_WEEK

    def __str__(self) -> str:
        hari = HARI[self.day % DAYS_PER_WEEK]
        return f"M{self.week + 1}-{hari}-{SHIFT_NAMES[self.shift]}-{self.slot}"


@dataclass(frozen=True)
class Staff:
    id: str  # kode samaran, mis. "D1", "N3" (aman untuk UU PDP)
    role: str  # "DOKTER" | "PERAWAT"
    max_shifts_per_week: int
    leave_days: frozenset[int] = frozenset()  # indeks hari absolut yang cuti


class CSPModel:
    def __init__(
        self,
        staff: list[Staff],
        num_days: int = DAYS_PER_WEEK,
        num_shifts: int = 2,
        slots_per_shift: dict[str, int] | None = None,
        max_gap: int = 2,
    ) -> None:
        self.staff = {s.id: s for s in staff}
        self.num_days = num_days
        self.num_shifts = num_shifts
        self.slots_per_shift = slots_per_shift or dict(SLOTS_PER_SHIFT)
        self.max_gap = max_gap

        self.variables: list[Var] = [
            Var(d, sh, f"{role}-{i + 1}")
            for d in range(num_days)
            for sh in range(num_shifts)
            for role, n in self.slots_per_shift.items()
            for i in range(n)
        ]
        self.need = Counter(v.role for v in self.variables)  # total slot per peran
        self.staff_by_role: dict[str, list[str]] = defaultdict(list)
        for s in staff:
            self.staff_by_role[s.role].append(s.id)

        # C1 + C2 (unary) diterapkan sekali di awal
        self.domains: dict[Var, set[str]] = {v: self._unary_domain(v) for v in self.variables}

        # Graf batasan: dua variabel bertetangga jika berada di hari yang sama
        by_day: dict[int, list[Var]] = defaultdict(list)
        for v in self.variables:
            by_day[v.day].append(v)
        self.neighbors: dict[Var, list[Var]] = {
            v: [w for w in by_day[v.day] if w != v] for v in self.variables
        }

    # ---------------------------------------------------------------- unary
    def _unary_domain(self, v: Var) -> set[str]:
        """C1 (kualifikasi sesuai peran) dan C2 (tidak sedang cuti)."""
        return {s.id for s in self.staff.values() if s.role == v.role and v.day not in s.leave_days}

    # --------------------------------------------------------------- binary
    @staticmethod
    def binary_ok(a: Var, x: str, b: Var, y: str) -> bool:
        """C3 + C4: satu orang hanya boleh satu slot per hari.

        C3 (tidak 2 slot di shift yang sama) adalah kasus khusus C4
        (tidak 2 shift di hari yang sama), jadi cukup satu pengecekan.
        """
        return not (a.day == b.day and x == y)

    # --------------------------------------------------------------- n-ary
    def is_consistent(
        self,
        var: Var,
        val: str,
        assignment: dict[Var, str],
        week_load: Counter,
        total_load: Counter,
    ) -> bool:
        """Cek batasan terhadap penugasan parsial (dipanggil saat backtracking).

        - C3/C4 : biner terhadap tetangga yang sudah terisi
        - C6    : maks shift per minggu per petugas (n-ary, tak bisa lewat AC-3)
        - C5    : pemerataan beban, dipangkas dengan batas bawah (lihat _balance_ok)
        """
        for nb in self.neighbors[var]:
            if nb in assignment and not self.binary_ok(var, val, nb, assignment[nb]):
                return False
        if week_load[(val, var.week)] + 1 > self.staff[val].max_shifts_per_week:
            return False
        return self._balance_ok(var.role, val, total_load)

    def _balance_ok(self, role: str, val: str, total_load: Counter) -> bool:
        """C5: selisih beban antar petugas sejenis <= max_gap.

        Pada penugasan parsial, petugas dengan beban terendah masih bisa
        menerima paling banyak `remaining` slot lagi. Jika selisih saat ini
        sudah melebihi max_gap + remaining, solusi pasti tidak seimbang
        (pemangkasan valid). Saat remaining = 0 ini menjadi pengecekan C5 persis.
        """
        ids = self.staff_by_role[role]
        loads = [total_load[s] + (1 if s == val else 0) for s in ids]
        remaining = self.need[role] - sum(loads)
        return max(loads) - min(loads) - remaining <= self.max_gap

    # ------------------------------------------------------- pra-pengecekan
    def quick_feasibility(self) -> tuple[bool, str]:
        """Syarat perlu kelayakan (cepat). False berarti pasti tidak ada solusi.

        AC-3 tidak bisa mendeteksi kekurangan kapasitas global (prinsip
        pigeonhole), jadi dicek terpisah di sini.
        """
        for role, per_shift in self.slots_per_shift.items():
            need_day = per_shift * self.num_shifts
            for d in range(self.num_days):
                avail = sum(1 for i in self.staff_by_role[role] if d not in self.staff[i].leave_days)
                if avail < need_day:
                    return False, f"{role} hari ke-{d + 1}: tersedia {avail}, butuh {need_day}"
            for w in range((self.num_days + DAYS_PER_WEEK - 1) // DAYS_PER_WEEK):
                days = range(w * DAYS_PER_WEEK, min((w + 1) * DAYS_PER_WEEK, self.num_days))
                cap = sum(
                    min(self.staff[i].max_shifts_per_week, sum(1 for d in days if d not in self.staff[i].leave_days))
                    for i in self.staff_by_role[role]
                )
                if cap < need_day * len(days):
                    return False, f"{role} minggu ke-{w + 1}: kapasitas {cap} < kebutuhan {need_day * len(days)}"
        return True, "ok"

    # ------------------------------------------------------- verifikasi akhir
    def verify_solution(self, assignment: dict[Var, str]) -> list[str]:
        """Verifikasi independen C1-C7 pada solusi lengkap. List kosong = valid."""
        errors: list[str] = []
        if set(assignment) != set(self.variables):
            errors.append("C7: ada slot yang belum terisi (cakupan dokter/perawat tidak lengkap)")
        per_day: dict[tuple[int, str], int] = Counter()
        week_load: Counter = Counter()
        total: Counter = Counter()
        for v, p in assignment.items():
            s = self.staff[p]
            if s.role != v.role:
                errors.append(f"C1: {p} bukan {v.role} ({v})")
            if v.day in s.leave_days:
                errors.append(f"C2: {p} cuti pada {v}")
            per_day[(v.day, p)] += 1
            week_load[(p, v.week)] += 1
            total[p] += 1
        errors += [f"C3/C4: {p} >1 slot di hari ke-{d + 1}" for (d, p), n in per_day.items() if n > 1]
        for (p, w), n in week_load.items():
            if n > self.staff[p].max_shifts_per_week:
                errors.append(f"C6: {p} {n} shift di minggu ke-{w + 1} (maks {self.staff[p].max_shifts_per_week})")
        for role, ids in self.staff_by_role.items():
            loads = [total[i] for i in ids]
            if max(loads) - min(loads) > self.max_gap:
                errors.append(f"C5: selisih beban {role} = {max(loads) - min(loads)} > {self.max_gap}")
        return errors
