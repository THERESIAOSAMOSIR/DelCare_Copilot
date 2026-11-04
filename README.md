# DelCare Copilot

Sistem Pendukung Keputusan Cerdas untuk operasional Klinik Kampus IT Del.
Repositori ini memuat baseline pencarian Milestone 1 dan modul **Constraint
Satisfaction Problem (CSP) penjadwalan shift petugas** untuk Milestone 2.

## Milestone 2 — CSP Penjadwalan Shift

### Tujuan bisnis

Klinik membutuhkan jadwal dokter dan perawat yang memenuhi kebutuhan setiap
shift, menghormati cuti, batas kerja mingguan, dan pemerataan beban. Solver
menghasilkan jadwal yang **layak dan terverifikasi**. Solver ini bukan
optimizer berbasis fungsi biaya; optimalitas dalam arti biaya/keuntungan tidak
diklaim karena tugas Milestone 2 memilih pendekatan CSP.

Data staf di repositori bersifat sintetis dan menggunakan kode anonim.

### Pemodelan matematis

Model yang digunakan adalah CSP `P = (X, D, C)`.

- `X`: variabel `x(d, s, r)` untuk setiap hari `d`, shift `s`, dan slot peran
  `r`. Dalam konfigurasi default terdapat 5 hari, 2 shift, 1 slot dokter, dan
  2 slot perawat per shift, sehingga terdapat 30 variabel.
- `D(x)`: himpunan ID staf dengan peran sesuai slot dan tidak cuti pada hari
  tersebut.
- `C1`: staf yang mengisi slot harus memiliki peran yang sesuai.
- `C2`: staf tidak boleh ditugaskan pada hari cuti.
- `C3`: staf tidak boleh mengisi dua slot dalam shift yang sama.
- `C4`: staf tidak boleh bekerja pada dua shift di hari yang sama.
- `C5`: selisih total beban staf dengan peran sama tidak boleh melebihi
  `max_gap` (default 2).
- `C6`: jumlah shift seorang staf dalam satu minggu tidak boleh melebihi
  `max_shifts_per_week`.
- `C7`: seluruh variabel harus terisi.

C3 dan C4 diterapkan sebagai constraint biner untuk AC-3. C5 dan C6 adalah
constraint dengan konteks penugasan yang lebih luas, sehingga diperiksa saat
backtracking dan diverifikasi ulang setelah solusi ditemukan.

### Algoritma

1. `quick_feasibility` menolak kekurangan staf atau kapasitas sebelum pencarian.
2. AC-3 menghapus nilai domain yang tidak memiliki pasangan kompatibel.
3. Backtracking memilih variabel dengan MRV, mengurutkan nilai dengan LCV, dan
   menggunakan forward checking.
4. `verify_solution` memeriksa C1-C7 secara independen.

Implementasi utama:

```text
src/csp/model.py        Model X, D, dan C1-C7
src/csp/ac3.py          Propagasi AC-3
src/csp/backtracking.py Backtracking, MRV, LCV, forward checking
src/csp/solver.py       API solve dan CLI jadwal
src/csp/instances.py    Generator instance sintetis
```

### Menjalankan solver

Prasyarat: [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m src.csp.solver
uv run python -m src.csp.solver --doctors 5 --nurses 12 --weeks 2
uv run python -m src.csp.solver --leave D1:4 --leave N2:2
uv run pytest -v
```

Exit code solver adalah `0` jika jadwal valid dan `1` jika instance infeasible
atau terkena batas node.

## Analisis sensitivitas

Benchmark mengukur pengaruh skala horizon dan heuristik terhadap jumlah
variabel, percobaan node, backtracking, domain yang dipangkas AC-3, dan waktu
eksekusi. Setiap skala dibuat feasible dengan generator sintetis:

| Horizon | Dokter | Perawat | Variabel |
|---:|---:|---:|---:|
| 1 minggu | 4 | 8 | 30 |
| 2 minggu | 5 | 10 | 60 |
| 4 minggu | 7 | 14 | 120 |

Jalankan benchmark berikut untuk menghasilkan tabel yang dapat dimasukkan ke
laporan:

```bash
uv run python -m src.csp.benchmark
uv run python -m src.csp.benchmark --weeks 1 2 4 --csv > benchmark.csv
```

Konfigurasi yang dibandingkan adalah seluruh heuristik aktif, tanpa AC-3,
tanpa MRV, dan tanpa forward checking. `time_ms` bergantung pada perangkat,
sedangkan `nodes`, `backtracks`, dan `ac3_pruned` adalah metrik algoritmik.
Gunakan hasil benchmark aktual pada perangkat kelompok untuk grafik laporan;
jangan menyalin angka waktu dari perangkat lain.

## Pengujian

Test mencakup:

- kebenaran model, domain unary, AC-3, dan solver;
- kombinasi heuristik;
- validasi C1-C7 dan determinisme;
- kapasitas tidak cukup, semua staf cuti, staf nol, batas node, serta horizon
  dua minggu;
- benchmark dua ukuran masalah dan empat konfigurasi heuristik.

```bash
uv run pytest -q
```

## Milestone 1 — Baseline Search

Modul `src/search` mempertahankan model ruang keadaan layanan klinik dari
Milestone 1 dengan Uniform Cost Search dan A*. Baseline dapat dijalankan:

```bash
uv run python -m src.cli --compare
uv run python -m src.cli --start TRIASE_MERAH --algo astar
```

## Rilis

Tag rilis Milestone 2:

```text
v0.2-milestone2
```

Sebelum pengumpulan, sertakan tautan repositori dan laporan PDF dengan format
`Grup{KodeKelompok}-Tugas02.pdf`. Laporan perlu memuat pemodelan formal,
algoritma, tabel/grafik sensitivitas, edge case, keterbatasan, dan kesimpulan.

## Lisensi

MIT License. Lihat [LICENSE](LICENSE).
