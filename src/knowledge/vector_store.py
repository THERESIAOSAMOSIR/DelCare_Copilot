"""
src/knowledge/vector_store.py
Manajemen basis data vektor persisten ChromaDB untuk DelCare Copilot.
"""

import os
from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from src.knowledge.chunking import DocumentChunk


class DelCareVectorStore:
    """
    Wrapper basis data vektor ChromaDB dengan penyimpanan persisten pada disk
    dan integrasi Sentence-Transformers embeddings.
    """

    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "delcare_knowledge_base",
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(persist_directory, exist_ok=True)

        # Inisialisasi Persistent Client ChromaDB (bukan in-memory)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Inisialisasi embedding function berbasis Sentence-Transformers
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )

        # Buat atau muat koleksi dengan metrik Cosine Distance
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def index_chunks(self, chunks: List[DocumentChunk], batch_size: int = 50) -> None:
        """Menyimpan potongan teks, metadata, dan vektor embedding ke ChromaDB."""
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        for i in range(0, len(chunks), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    def count(self) -> int:
        """Mengembalikan jumlah dokumen chunk yang terindeks."""
        return self.collection.count()
