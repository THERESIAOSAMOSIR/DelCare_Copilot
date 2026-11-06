"""
src/knowledge/chunking.py
Modul ingestion dan pemotongan dokumen SOP Poliklinik DelCare Copilot.
"""

import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    target_action: str
    text: str
    metadata: dict[str, Any]


def parse_sop_file(filepath: str) -> dict[str, Any]:
    """Membaca berkas SOP .txt dan memisahkan metadata header dengan isi teks."""
    with open(filepath, "r", encoding="utf-8") as file:
        raw_content = file.read()

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

    return {
        "doc_id": os.path.basename(filepath).split("_")[0],
        "title": os.path.basename(filepath),
        "category": "Umum",
        "target_action": "PERIKSA",
        "ref_title": "Internal",
        "ref_url": "",
        "alt_ref": "",
        "body": raw_content.strip(),
    }


def chunk_text_recursive(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[str]:
    """
    Recursive word-aware chunking berbasis paragraf, kalimat, dan kata.

    Ukuran chunk dan overlap dihitung dalam karakter. Setiap chunk tidak
    melebihi chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size harus lebih besar dari 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap tidak boleh negatif")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap harus lebih kecil dari chunk_size")

    separators = ["\n\n", "\n", r"(?<=[.!?])\s+", " "]

    def split_recursive(value: str, separator_index: int = 0) -> list[str]:
        value = value.strip()
        if not value:
            return []
        if len(value) <= chunk_size:
            return [value]
        if separator_index >= len(separators):
            return [value[start : start + chunk_size] for start in range(0, len(value), chunk_size)]

        separator = separators[separator_index]
        parts = (
            re.split(separator, value) if separator.startswith("(?<=") else value.split(separator)
        )
        parts = [part.strip() for part in parts if part.strip()]
        if len(parts) <= 1:
            return split_recursive(value, separator_index + 1)

        result: list[str] = []
        for part in parts:
            if len(part) <= chunk_size:
                result.append(part)
            else:
                result.extend(split_recursive(part, separator_index + 1))
        return result

    def get_overlap(value: str) -> str:
        words = value.split()
        selected: list[str] = []
        length = 0
        for word in reversed(words):
            additional_length = len(word) + (1 if selected else 0)
            if length + additional_length > chunk_overlap:
                break
            selected.insert(0, word)
            length += additional_length
        return " ".join(selected)

    chunks: list[str] = []
    current = ""
    for part in split_recursive(text):
        candidate = f"{current} {part}".strip()
        if not current:
            current = part
        elif len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current)
            current = f"{get_overlap(current)} {part}".strip()
            if len(current) > chunk_size:
                current = part

    if current:
        chunks.append(current)
    return chunks


def load_and_chunk_corpus(
    directory_path: str, chunk_size: int = 500, chunk_overlap: int = 100
) -> list[DocumentChunk]:
    """Memuat seluruh berkas korpus dan menghasilkan daftar DocumentChunk."""
    all_chunks: list[DocumentChunk] = []

    for filename in sorted(os.listdir(directory_path)):
        if not filename.endswith(".txt"):
            continue

        full_path = os.path.join(directory_path, filename)
        parsed = parse_sop_file(full_path)
        text_chunks = chunk_text_recursive(
            parsed["body"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for index, text_chunk in enumerate(text_chunks):
            chunk_id = f"{parsed['doc_id']}_c{index + 1:02d}"
            metadata = {
                "doc_id": parsed["doc_id"],
                "title": parsed["title"],
                "category": parsed["category"],
                "target_action": parsed["target_action"],
                "ref_url": parsed["ref_url"],
                "chunk_index": index + 1,
                "total_chunks": len(text_chunks),
            }
            all_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=parsed["doc_id"],
                    title=parsed["title"],
                    category=parsed["category"],
                    target_action=parsed["target_action"],
                    text=text_chunk,
                    metadata=metadata,
                )
            )

    return all_chunks
