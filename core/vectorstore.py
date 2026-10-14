"""ChromaDB vector store for policy / guideline documents."""
from __future__ import annotations

from typing import List

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from core.embeddings import get_embeddings


class VectorStoreManager:
    """Thin wrapper so ingest scripts and the RAG tool share one code path."""

    def __init__(self) -> None:
        self.embeddings = get_embeddings()
        self._vectorstore: Chroma | None = None

    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name="retail_docs",
                embedding_function=self.embeddings,
                persist_directory=str(settings.VECTORDB_PATH),
            )
        return self._vectorstore

    def ingest_documents(self) -> int:
        """Load .txt and .md under data/documents, chunk, and embed.

        Why both extensions: policies are easier to write as Markdown; older
        samples may still be plain text.
        """
        documents: list[Document] = []
        for pattern in ("**/*.txt", "**/*.md"):
            loader = DirectoryLoader(
                str(settings.DOCUMENTS_DIR),
                glob=pattern,
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            documents.extend(loader.load())

        if not documents:
            raise FileNotFoundError(
                f"No .txt/.md documents found in {settings.DOCUMENTS_DIR}"
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)
        self.vectorstore.add_documents(chunks)
        return len(chunks)

    def search(self, query: str, k: int | None = None) -> List[Document]:
        k = k or settings.RETRIEVAL_K
        return self.vectorstore.similarity_search(query, k=k)

    def chunk_count(self) -> int:
        return len(self.vectorstore.get()["ids"])
