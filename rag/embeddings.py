"""Embedding service using HuggingFace sentence-transformers."""
import logging
import hashlib
from typing import List, Dict, Optional
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from cachetools import LRUCache
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using HuggingFace models with caching."""
    
    # Class-level embedding cache (shared across instances)
    _embedding_cache: Dict[str, List[float]] = LRUCache(maxsize=10000)
    _cache_hits = 0
    _cache_misses = 0
    
    def __init__(self, model_name: str = None):
        """Initialize the embedding service.
        
        Args:
            model_name: HuggingFace model name. Defaults to config setting.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model = None
        
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded. Embedding dimension: {self._model.get_sentence_embedding_dimension()}")
        return self._model
    
    @property
    def embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text with caching.
        
        Args:
            text: Input text to embed.
            use_cache: Whether to use embedding cache.
            
        Returns:
            List of floats representing the embedding.
        """
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                EmbeddingService._cache_hits += 1
                return self._embedding_cache[cache_key]
            EmbeddingService._cache_misses += 1
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        result = embedding.tolist()
        
        if use_cache:
            self._embedding_cache[cache_key] = result
        
        return result
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get embedding cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / max(1, total)
        return {
            "cache_size": len(self._embedding_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate, 3)
        }
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed.
            batch_size: Batch size for encoding.
            
        Returns:
            List of embeddings.
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.model.encode(
            texts, 
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=True
        )
        return embeddings.tolist()
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding.
            embedding2: Second embedding.
            
        Returns:
            Cosine similarity score.
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service instance."""
    return EmbeddingService()

