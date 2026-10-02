"""Data instance sintetis (DRAF awal; Angga mengembangkan generator skala).

Semua data bersifat sintetis dan memakai kode samaran (D1, N1, ...),
sehingga tidak ada data pegawai asli di repositori (UU PDP No. 27/2022).
"""
from __future__ import annotations

from .model import CSPModel, Staff

DOCTOR_MAX = 4  # asumsi tim: maks 4 shift/minggu (16 jam)
NURSE_MAX = 5  # asumsi tim: maks 5 shift/minggu (20 jam)


def build_instance(
    n_doctors: int = 3,
    n_nurses: int = 6,
    weeks: int = 1,
    leaves: dict[str, set[int]] | None = None,
    doctor_max: int = DOCTOR_MAX,
    nurse_max: int = NURSE_MAX,
) -> CSPModel:
    """Bangun CSPModel. `leaves` memetakan id petugas -> set indeks hari absolut cuti."""
    leaves = leaves or {}
    staff = [
        Staff(f"D{i}", "DOKTER", doctor_max, frozenset(leaves.get(f"D{i}", set())))
        for i in range(1, n_doctors + 1)
    ] + [
        Staff(f"N{i}", "PERAWAT", nurse_max, frozenset(leaves.get(f"N{i}", set())))
        for i in range(1, n_nurses + 1)
    ]
    return CSPModel(staff, num_days=5 * weeks)


def small_instance() -> CSPModel:
    """Skala kecil: 3 dokter, 6 perawat, 1 minggu. D1 cuti Jumat, N2 cuti Rabu."""
    return build_instance(leaves={"D1": {4}, "N2": {2}})
