# DelCare Copilot

Sistem Pendukung Keputusan Cerdas untuk operasional Klinik Kampus IT Del.
Repositori ini memuat:
1. **Milestone 1:** Baseline pencarian alur triase & rujukan klinik (Uniform Cost Search & A* Search).
2. **Milestone 2:** Constraint Satisfaction Problem (CSP) penjadwalan shift petugas medis (AC-3, Backtracking, MRV, LCV, FC).
3. **Milestone 3:** Basis Pengetahuan Vektor Korpus Enterprise & Semantic Search RAG berbasis ChromaDB dan Sentence-Transformers.

---

## Milestone 3 — Vector Knowledge Base & Semantic Search

### Tujuan Bisnis & Latar Belakang
Poliklinik Kampus IT Del melayani ratusan kunjungan mahasiswa dengan variasi keluhan medis. Ketiadaan akses cepat terhadap SOP resmi memicu potensi inkonsistensi keputusan triase. Milestone 3 membangun **Enterprise Semantic Knowledge Base** sebagai fondasi memori korpus yang krusial bagi sistem *Retrieval-Augmented Generation* (RAG) DelCare Copilot.

### Korpus Dokumen Enterprise
Terdiri dari 12 dokumen SOP dan manual regulasi resmi fasyankes primer di `data/raw_docs/`:
- `SOP-TRG-001`: Triase Prioritas MERAH (Gawat Darurat / Resusitasi)
- `SOP-TRG-002`: Triase Prioritas KUNING (Kedaruratan Sedang / Urgensi Tinggi)
- `SOP-TRG-003`: Triase Prioritas HIJAU & Pelayanan Rawat Jalan Mandiri
- `SOP-ADM-004`: Alur Registrasi & Verifikasi Identitas Pasien
- `SOP-RUJ-005`: Kriteria Pemilihan & Alur Rujukan RS Mitra (RS_A, RS_B, RS_C)
- `SOP-EVK-006`: Penggunaan Ambulans Kampus & Prosedur Evakuasi Transportasi
- `SOP-MED-007`: Tatalaksana Serangan Asma Akut & Gangguan Pernapasan
- `SOP-MED-008`: Tatalaksana Sinkop (Pingsan), Hipoglikemia, & Dehidrasi Akut
- `SOP-MED-009`: Tatalaksana Trauma Fisik, Fraktur Tulang, & Cedera Olahraga
- `SOP-OBS-010`: Protokol Ruang Observasi Sementara & Batas Waktu Pemantauan
- `SOP-FAR-011`: Pengelolaan & Dispensing Obat Kedaruratan Terbatas
- `POL-PDP-012`: Kebijakan Kerahasiaan & Pelindungan Data Pribadi Rekam Medis (UU PDP)

Dengan konfigurasi chunking `chunk_size=500` dan `chunk_overlap=100`, korpus
menghasilkan 79 chunk yang terindeks di ChromaDB.

Seluruh dokumen mengacu pada sumber hukum dan regulasi terbuka: UU No. 17/2023, UU No. 27/2022, Permenkes No. 9/2014, Permenkes No. 16/2024, Permenkes No. 24/2022, SISRUTE Kemenkes RI, dan Pedoman WHO ETAT.

### Arsitektur Modul Knowledge Base
```text
delcare-copilot/
├── data/
│   ├── raw_docs/             # 12 dokumen teks SOP resmi
│   └── chroma_db/            # Basis data vektor ChromaDB persisten
├── src/
│   └── knowledge/
│       ├── __init__.py
│       ├── chunking.py       # Word-aware recursive chunker & parser metadata
│       ├── vector_store.py   # Persistent ChromaDB client & Sentence-Transformers
│       └── retriever.py      # Semantic vector search & relevance threshold guardrail
├── benchmarks/
│   └── run_semantic_eval.py  # Tolok ukur 6 kueri bisnis & analisis penolakan OOD
└── tests/
    ├── test_chunking.py      # Pengujian unit chunking & boundary preservation
    ├── test_vector_store.py  # Pengujian persistensi ChromaDB
    └── test_retrieval.py     # Pengujian presisi temu balik & penolakan OOD
```

### Menjalankan Modul Milestone 3
Prasyarat: Python >= 3.11 dan [uv](https://docs.astral.sh/uv/).

```bash
# Instal dependensi baru
uv sync

# Inisialisasi indeks dokumen korpus ke ChromaDB
uv run python -m src.cli --index-kb

# Uji pencarian semantik via CLI
uv run python -m src.cli --query "pasien pingsan tidak sadar di lapangan"
uv run python -m src.cli --query "dada sesak dan mengi sehabis lari"
uv run python -m src.cli --query "jadwal bayar uang kuliah semester baru"  # Kueri Out-of-Domain

# Jalankan benchmark kueri bisnis (Literal, Sinonim, OOD)
uv run python -m benchmarks.run_semantic_eval

# Menjalankan seluruh rangkaian tes otomatis
uv run pytest -v
```

### Relevance Threshold

Sistem menggunakan model embedding multilingual
`paraphrase-multilingual-MiniLM-L12-v2` dan cosine similarity dengan
threshold 0.45.
Query dengan skor similarity terbaik di bawah threshold dikategorikan
sebagai out-of-domain dan ditolak oleh relevance guardrail. Nilai ini
dievaluasi menggunakan query relevan, ambigu, dan out-of-domain pada
benchmark semantic evaluation.

### Rilis
Tag rilis Milestone 3:
```text
v0.3-milestone3
```

---

## Milestone 2 — CSP Penjadwalan Shift
Modul CSP penjadwalan shift dokter dan perawat dengan algoritma AC-3, Backtracking (MRV, LCV, FC), dan batasan C1-C7:
```bash
uv run python -m src.csp.solver
uv run python -m src.csp.solver --leave D1:4 --leave N2:2
```

---

## Milestone 1 — Baseline Search
Modul ruang keadaan alur layanan klinik dengan Uniform Cost Search dan A* Search:
```bash
uv run python -m src.cli --compare
uv run python -m src.cli --start TRIASE_MERAH --algo astar
```

---

## Lisensi
MIT License. Lihat [LICENSE](LICENSE).

<!-- verified milestone 3 -->
