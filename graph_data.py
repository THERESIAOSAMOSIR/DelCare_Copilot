"""
DelCare Copilot - Graf Domain Bisnis
=====================================
Merepresentasikan alur layanan Klinik Kampus IT Del: dari pendaftaran,
triase, pemeriksaan, hingga keputusan akhir (rawat jalan mandiri atau
rujukan ke salah satu RS mitra).

Setiap NODE adalah sebuah *state* gabungan (bukan hanya "tahap layanan"
tunggal) agar ruang keadaan tidak trivial/linear:

    state = (tahap, kategori_triase)

Untuk node keputusan rujukan, node dipecah lagi menjadi kandidat RS
tujuan, sehingga agen benar-benar memilih *jalur* (bukan cuma urutan
tahap), sesuai tuntutan rubrik "Formulasi Ruang Keadaan & Algoritma
Search".

Bobot sisi (EDGE COST) dalam SATUAN MENIT-EKUIVALEN, gabungan dari:
    biaya_waktu (menit tunggu/proses)
  + biaya_jarak (menit tempuh, dikonversi dari km RS rujukan)
  + penalti_risiko (menit ekuivalen risiko klinis jika kategori
    berat tertunda -> dibuat besar untuk kategori MERAH agar UCS/A*
    'memaksa' agen memilih jalur rujukan cepat, bukan jalur murah
    tapi lambat)

Sumber angka: estimasi berbasis wawancara petugas Poliklinik +
SOP internal (silakan ganti dengan data hasil wawancara kelompok
kalian sendiri agar problem framing lebih kuat).
"""


# ---------------------------------------------------------------------------
# 1. DAFTAR NODE (STATE)
# ---------------------------------------------------------------------------
# Format nama node: "TAHAP_KATEGORI" atau nama eksplisit untuk node terminal.

START = "PENDAFTARAN"

NODES: list[str] = [
    "PENDAFTARAN",
    "TRIASE",
    "TRIASE_HIJAU",
    "TRIASE_KUNING",
    "TRIASE_MERAH",
    "PERIKSA_HIJAU",
    "PERIKSA_KUNING",
    "PERIKSA_MERAH",
    "OBSERVASI_KUNING",
    "KEPUTUSAN_RAWAT_JALAN",
    "KEPUTUSAN_RUJUK_KUNING",
    "KEPUTUSAN_RUJUK_MERAH",
    "RUJUK_RS_A_KUNING",
    "RUJUK_RS_B_KUNING",
    "RUJUK_RS_C_KUNING",
    "RUJUK_RS_A_MERAH",
    "RUJUK_RS_B_MERAH",
    "RUJUK_RS_C_MERAH",
    "SELESAI_RAWAT_JALAN",
    "SELESAI_RUJUK_A",
    "SELESAI_RUJUK_B",
    "SELESAI_RUJUK_C",
]

# ---------------------------------------------------------------------------
# 2. GOAL STATES
# ---------------------------------------------------------------------------
# Ada banyak kemungkinan "selesai" tergantung kategori triase & RS pilihan.
GOALS = {
    "SELESAI_RAWAT_JALAN",
    "SELESAI_RUJUK_A",
    "SELESAI_RUJUK_B",
    "SELESAI_RUJUK_C",
}

# ---------------------------------------------------------------------------
# 3. GRAF BERARAH BERBOBOT: node -> [(neighbor, cost, label_aksi), ...]
# ---------------------------------------------------------------------------
# label_aksi menjelaskan ACTUATOR yang dieksekusi agen pada transisi itu.

GRAPH: dict[str, list[tuple[str, float, str]]] = {
    "PENDAFTARAN": [
        ("TRIASE", 5, "daftar_dan_antre_triase"),
    ],
    "TRIASE": [
        ("TRIASE_HIJAU", 3, "tetapkan_kategori_hijau"),
        ("TRIASE_KUNING", 4, "tetapkan_kategori_kuning"),
        ("TRIASE_MERAH", 2, "tetapkan_kategori_merah_prioritas"),
    ],
    # --- Jalur HIJAU (ringan) ---
    "TRIASE_HIJAU": [
        ("PERIKSA_HIJAU", 10, "antre_periksa_umum"),
    ],
    "PERIKSA_HIJAU": [
        ("KEPUTUSAN_RAWAT_JALAN", 8, "periksa_dan_putuskan_rawat_jalan"),
    ],
    "KEPUTUSAN_RAWAT_JALAN": [
        ("SELESAI_RAWAT_JALAN", 5, "terbitkan_resep_dan_edukasi"),
    ],
    # --- Jalur KUNING (sedang) ---
    "TRIASE_KUNING": [
        ("PERIKSA_KUNING", 12, "antre_periksa_prioritas_sedang"),
    ],
    "PERIKSA_KUNING": [
        ("OBSERVASI_KUNING", 15, "observasi_lanjutan"),
        ("KEPUTUSAN_RUJUK_KUNING", 6, "putuskan_rujuk_langsung"),
    ],
    "OBSERVASI_KUNING": [
        ("KEPUTUSAN_RAWAT_JALAN", 10, "membaik_lanjut_rawat_jalan"),
        ("KEPUTUSAN_RUJUK_KUNING", 8, "memburuk_lanjut_rujuk"),
    ],
    "KEPUTUSAN_RUJUK_KUNING": [
        ("RUJUK_RS_A_KUNING", 6, "pilih_rujukan_RS_A"),
        ("RUJUK_RS_B_KUNING", 9, "pilih_rujukan_RS_B"),
        ("RUJUK_RS_C_KUNING", 14, "pilih_rujukan_RS_C"),
    ],
    "RUJUK_RS_A_KUNING": [("SELESAI_RUJUK_A", 4, "serah_terima_pasien_RS_A")],
    "RUJUK_RS_B_KUNING": [("SELESAI_RUJUK_B", 4, "serah_terima_pasien_RS_B")],
    "RUJUK_RS_C_KUNING": [("SELESAI_RUJUK_C", 4, "serah_terima_pasien_RS_C")],
    # --- Jalur MERAH (gawat darurat, prioritas & penalti tinggi jika lambat) ---
    "TRIASE_MERAH": [
        ("PERIKSA_MERAH", 4, "periksa_cepat_prioritas_utama"),
    ],
    "PERIKSA_MERAH": [
        ("KEPUTUSAN_RUJUK_MERAH", 3, "putuskan_rujuk_segera"),
    ],
    "KEPUTUSAN_RUJUK_MERAH": [
        # Bobot RS_C sengaja besar (jarak jauh) -> menunjukkan UCS/A*
        # akan MENGHINDARI RS_C untuk kasus merah walau mungkin satu-
        # satunya yang punya kapasitas, memperlihatkan trade-off nyata.
        ("RUJUK_RS_A_MERAH", 7, "pilih_rujukan_darurat_RS_A"),
        ("RUJUK_RS_B_MERAH", 11, "pilih_rujukan_darurat_RS_B"),
        ("RUJUK_RS_C_MERAH", 25, "pilih_rujukan_darurat_RS_C"),
    ],
    "RUJUK_RS_A_MERAH": [("SELESAI_RUJUK_A", 3, "serah_terima_gawat_darurat_RS_A")],
    "RUJUK_RS_B_MERAH": [("SELESAI_RUJUK_B", 3, "serah_terima_gawat_darurat_RS_B")],
    "RUJUK_RS_C_MERAH": [("SELESAI_RUJUK_C", 3, "serah_terima_gawat_darurat_RS_C")],
}


def get_neighbors(node: str) -> list[tuple[str, float, str]]:
    """Mengembalikan daftar tetangga (neighbor, cost, label_aksi) dari sebuah node."""
    return GRAPH.get(node, [])


def all_nodes() -> list[str]:
    return list(NODES)


def min_edge_weight() -> float:
    """Bobot sisi terkecil di seluruh graf - dipakai heuristik admissible."""
    return min(cost for edges in GRAPH.values() for _, cost, _ in edges)


if __name__ == "__main__":
    print(f"Jumlah node : {len(NODES)}")
    print(f"Jumlah goal : {len(GOALS)} -> {sorted(GOALS)}")
    print(f"Bobot sisi terkecil (untuk heuristik): {min_edge_weight()}")
