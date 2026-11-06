"""
src/knowledge/chunking.py
Modul ingestion dan pemotongan dokumen SOP Poliklinik DelCare Copilot.
Menerapkan word-aware recursive chunking dengan overlap dan ekstraksi metadata terstruktur.
"""

from dataclasses import dataclass
import os
import re
from typing import Any, Dict, List


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    target_action: str
    text: str
    metadata: Dict[str, Any]


def parse_sop_file(filepath: str) -> Dict[str, Any]:
    """Membaca berkas SOP .txt dan memisahkan metadata header dengan isi teks."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw_content = f.read()

    header_pattern = re.compile(
        r"KODE DOKUMEN:\s*(.*?)\n"
        r"JUDUL:\s*(.*?)\n"
        r"KATEGORI:\s*(.*?)\n"
        r"TARGET AKSI DELCARE:\s*(.*?)\n"
        r"REFERENSI TERBUKA:\s*(.*?)\n"
        r"TAUTAN RESMI:\s*(.*?)\n"
        r"TAUTAN ALTERNATIF:\s*(.*?)\n"
        r"={40,}\n\n(.*)",
        re.DOTALL,
    )

    match = header_pattern.search(raw_content)
    if match:
        return {
            "doc_id": match.group(1).strip(),
            "title": match.group(2).strip(),
            "category": match.group(3).strip(),
            "target_action": match.group(4).strip(),
            "ref_title": match.group(5).strip(),
            "ref_url": match.group(6).strip(),
            "alt_ref": match.group(7).strip(),
            "body": match.group(8).strip(),
        }
    else:
        doc_id = os.path.basename(filepath).split("_")[0]
        return {
            "doc_id": doc_id,
            "title": os.path.basename(filepath),
            "category": "Umum",
            "target_action": "PERIKSA",
            "ref_title": "Internal",
            "ref_url": "",
            "alt_ref": "",
            "body": raw_content.strip(),
        }


def chunk_text_recursive(
    text: str, chunk_size: int = 500, chunk_overlap: int = 100
) -> List[str]:
    """
    Word-aware chunking dengan pembagian berdasarkan batas paragraf dan kalimat,
    menjaga keutuhan konteks klinis dan klausul SOP.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            words = current_chunk.split()
            overlap_prefix = " ".join(words[-15:]) if len(words) >= 15 else current_chunk

            if len(para) > chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub_chunk = overlap_prefix
                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) + 1 <= chunk_size:
                        sub_chunk = f"{sub_chunk} {sentence}".strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sentence
                current_chunk = sub_chunk
            else:
                current_chunk = f"{overlap_prefix}\n\n{para}".strip() if overlap_prefix else para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def load_and_chunk_corpus(
    directory_path: str, chunk_size: int = 500, chunk_overlap: int = 100
) -> List[DocumentChunk]:
    """Memuat seluruh berkas korpus dari direktori dan menghasilkan daftar DocumentChunk."""
    all_chunks: List[DocumentChunk] = []

    for filename in sorted(os.listdir(directory_path)):
        if filename.endswith(".txt"):
            full_path = os.path.join(directory_path, filename)
            parsed = parse_sop_file(full_path)
            text_chunks = chunk_text_recursive(
                parsed["body"], chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            for idx, t_chunk in enumerate(text_chunks):
                c_id = f"{parsed['doc_id']}_c{idx+1:02d}"
                metadata = {
                    "doc_id": parsed["doc_id"],
                    "title": parsed["title"],
                    "category": parsed["category"],
                    "target_action": parsed["target_action"],
                    "ref_url": parsed["ref_url"],
                    "chunk_index": idx + 1,
                    "total_chunks": len(text_chunks),
                }
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=c_id,
                        doc_id=parsed["doc_id"],
                        title=parsed["title"],
                        category=parsed["category"],
                        target_action=parsed["target_action"],
                        text=t_chunk,
                        metadata=metadata,
                    )
                )

    return all_chunks
