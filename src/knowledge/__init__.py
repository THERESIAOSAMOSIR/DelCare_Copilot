"""
Modul Knowledge Base & RAG untuk DelCare Copilot (Milestone 3).
"""

from src.knowledge.chunking import DocumentChunk, load_and_chunk_corpus

try:
    from src.knowledge.retriever import SemanticRetriever
    from src.knowledge.vector_store import DelCareVectorStore

    __all__ = [
        "DocumentChunk",
        "load_and_chunk_corpus",
        "DelCareVectorStore",
        "SemanticRetriever",
    ]
except ImportError:
    __all__ = [
        "DocumentChunk",
        "load_and_chunk_corpus",
    ]
