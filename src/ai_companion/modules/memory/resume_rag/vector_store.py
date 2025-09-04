import os
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import List, Optional

from ai_companion.settings import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of a document stored in the vector store."""

    text: str
    metadata: dict
    score: Optional[float] = None

    @property
    def id(self) -> Optional[str]:
        return self.metadata.get("id")

    @property
    def filename(self) -> Optional[str]:
        return self.metadata.get("filename")

    @property
    def chunk_index(self) -> Optional[int]:
        return self.metadata.get("chunk_index")


class ResumeRagVectorStore:
    """A class to handle vector storage operations for resume RAG using Qdrant."""

    REQUIRED_ENV_VARS = ["QDRANT_URL", "QDRANT_API_KEY"]
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = "resume-rag"  # This is the key change to use "resume-rag"
    SIMILARITY_THRESHOLD = 0.7  # Adjustable threshold for document chunk similarity

    _instance: Optional["ResumeRagVectorStore"] = None
    _initialized: bool = False

    def __new__(cls) -> "ResumeRagVectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._validate_env_vars()
            self.model = SentenceTransformer(self.EMBEDDING_MODEL)
            self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            self._initialized = True
            self._create_collection_if_not_exists()


    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def _collection_exists(self) -> bool:
        """Check if the resume-rag collection exists."""
        collections = self.client.get_collections().collections
        return any(col.name == self.COLLECTION_NAME for col in collections)

    def _create_collection_if_not_exists(self) -> None:
        """Create a new collection for storing resume document chunks if it doesn't exist."""
        if not self._collection_exists():
            sample_embedding = self.model.encode("sample text")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=len(sample_embedding),
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Qdrant collection '{self.COLLECTION_NAME}' created.")


    def store_chunks(self, chunks: List[str], filename: str) -> None:
        """Store document chunks in the vector store.

        Args:
            chunks: A list of text chunks from a document.
            filename: The name of the original PDF file.
        """
        if not chunks:
            return

        points = []
        for i, chunk in enumerate(chunks):
            embedding = self.model.encode(chunk).tolist()
            point = PointStruct(
                id=f"{filename}_{i}",  # Unique ID for each chunk
                vector=embedding,
                payload={
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk,
                    "timestamp": datetime.now().isoformat(),  # Add timestamp for tracking
                },
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
            wait=True,
        )
        logger.info(f"Upserted {len(points)} chunks from '{filename}' to '{self.COLLECTION_NAME}' collection.")


    def search_documents(self, query: str, k: int = 5) -> List[DocumentChunk]:
        """Search for similar document chunks in the vector store.

        Args:
            query: Text to search for
            k: Number of results to return

        Returns:
            List of DocumentChunk objects
        """
        if not self._collection_exists():
            return []

        query_embedding = self.model.encode(query)
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding.tolist(),
            limit=k,
        )

        return [
            DocumentChunk(
                text=hit.payload["text"],
                metadata={k: v for k, v in hit.payload.items() if k != "text"},
                score=hit.score,
            )
            for hit in results
        ]

@lru_cache
def get_resume_rag_vector_store() -> ResumeRagVectorStore:
    """Get or create the ResumeRagVectorStore singleton instance."""
    return ResumeRagVectorStore()
