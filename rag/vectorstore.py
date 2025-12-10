"""Vector store service using ChromaDB."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from rag.embeddings import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing ChromaDB vector store."""
    
    def __init__(
        self, 
        persist_directory: str = None,
        collection_name: str = "onboarding_docs",
        embedding_service: EmbeddingService = None
    ):
        """Initialize the vector store service.
        
        Args:
            persist_directory: Directory to persist ChromaDB data.
            collection_name: Name of the collection.
            embedding_service: Embedding service to use.
        """
        settings = get_settings()
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Initialize ChromaDB client
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self._collection = None
        
    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def add_documents(
        self, 
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> None:
        """Add documents to the vector store.
        
        Args:
            texts: List of document texts.
            metadatas: List of metadata dicts for each document.
            ids: List of unique IDs for each document.
        """
        if not texts:
            return
            
        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(texts))]
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Add to collection
        logger.info(f"Adding {len(texts)} documents to collection '{self.collection_name}'")
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Collection now has {self.collection.count()} documents")
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Dict[str, Any] = None,
        include: List[str] = None
    ) -> Dict[str, Any]:
        """Query the vector store.
        
        Args:
            query_text: Query text.
            n_results: Number of results to return.
            where: Filter conditions.
            include: What to include in results (documents, metadatas, distances).
            
        Returns:
            Query results with documents, metadatas, and distances.
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query_text)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=include
        )
        
        return results
    
    def query_by_department(
        self,
        query_text: str,
        department: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Query documents filtered by department.
        
        Args:
            query_text: Query text.
            department: Department to filter by.
            n_results: Number of results to return.
            
        Returns:
            Query results filtered by department.
        """
        return self.query(
            query_text=query_text,
            n_results=n_results,
            where={"department": department}
        )
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        logger.warning(f"Deleting collection '{self.collection_name}'")
        self.client.delete_collection(self.collection_name)
        self._collection = None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection stats.
        """
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory
        }


def get_vectorstore_service(
    collection_name: str = "onboarding_docs"
) -> VectorStoreService:
    """Get vector store service instance.
    
    Args:
        collection_name: Name of the collection.
        
    Returns:
        VectorStoreService instance.
    """
    return VectorStoreService(collection_name=collection_name)

