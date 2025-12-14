"""Semantic caching service for similar query responses."""
import hashlib
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models import SemanticCache

logger = logging.getLogger(__name__)


class SemanticCacheService:
    """Service for semantic caching of query responses."""
    
    def __init__(
        self,
        db: Session,
        embedding_model=None,
        similarity_threshold: float = 0.92,
        cache_ttl_hours: int = 24
    ):
        self.db = db
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.cache_ttl_hours = cache_ttl_hours
        self._embeddings_cache: Dict[str, np.ndarray] = {}
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent hashing."""
        return query.lower().strip()
    
    def _compute_hash(self, query: str) -> str:
        """Compute SHA-256 hash of normalized query."""
        normalized = self._normalize_query(query)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _get_embedding(self, query: str) -> Optional[List[float]]:
        """Get embedding for a query."""
        if not self.embedding_model:
            return None
        
        normalized = self._normalize_query(query)
        if normalized in self._embeddings_cache:
            return self._embeddings_cache[normalized].tolist()
        
        try:
            embedding = self.embedding_model.embed_query(normalized)
            self._embeddings_cache[normalized] = np.array(embedding)
            return embedding
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response for a similar query."""
        query_hash = self._compute_hash(query)
        now = datetime.utcnow()
        
        # First, try exact hash match
        exact_match = self.db.query(SemanticCache).filter(
            and_(
                SemanticCache.query_hash == query_hash,
                SemanticCache.is_valid == True,
                SemanticCache.expires_at > now
            )
        ).first()
        
        if exact_match:
            exact_match.hit_count += 1
            exact_match.last_accessed = now
            self.db.commit()
            logger.info(f"Semantic cache hit (exact): {query[:50]}...")
            return {
                "response": exact_match.response,
                "sources": exact_match.sources,
                "department": exact_match.department,
                "cache_type": "exact",
                "confidence": 1.0
            }
        
        # Try semantic similarity match
        if self.embedding_model:
            query_embedding = self._get_embedding(query)
            if query_embedding:
                # Get recent valid cache entries
                cache_entries = self.db.query(SemanticCache).filter(
                    and_(
                        SemanticCache.is_valid == True,
                        SemanticCache.expires_at > now,
                        SemanticCache.query_embedding.isnot(None)
                    )
                ).limit(100).all()
                
                best_match = None
                best_similarity = 0.0
                
                for entry in cache_entries:
                    if entry.query_embedding:
                        try:
                            similarity = self._cosine_similarity(
                                query_embedding, 
                                entry.query_embedding
                            )
                            if similarity > best_similarity and similarity >= self.similarity_threshold:
                                best_similarity = similarity
                                best_match = entry
                        except Exception as e:
                            logger.error(f"Error computing similarity: {e}")
                            continue
                
                if best_match:
                    best_match.hit_count += 1
                    best_match.last_accessed = now
                    self.db.commit()
                    logger.info(f"Semantic cache hit (similar, {best_similarity:.2f}): {query[:50]}...")
                    return {
                        "response": best_match.response,
                        "sources": best_match.sources,
                        "department": best_match.department,
                        "cache_type": "semantic",
                        "confidence": best_similarity
                    }
        
        return None
    
    def cache_response(
        self,
        query: str,
        response: str,
        sources: Optional[List[Dict]] = None,
        department: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> SemanticCache:
        """Cache a query response."""
        query_hash = self._compute_hash(query)
        expires_at = datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)
        
        # Get embedding
        query_embedding = self._get_embedding(query)
        
        # Check for existing entry
        existing = self.db.query(SemanticCache).filter(
            SemanticCache.query_hash == query_hash
        ).first()
        
        if existing:
            existing.response = response
            existing.sources = sources
            existing.department = department
            existing.query_embedding = query_embedding
            existing.confidence_score = confidence_score
            existing.expires_at = expires_at
            existing.is_valid = True
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        cache_entry = SemanticCache(
            query_hash=query_hash,
            query_text=query,
            query_embedding=query_embedding,
            response=response,
            sources=sources,
            department=department,
            confidence_score=confidence_score,
            expires_at=expires_at
        )
        
        self.db.add(cache_entry)
        self.db.commit()
        self.db.refresh(cache_entry)
        
        logger.info(f"Cached response for: {query[:50]}...")
        return cache_entry
    
    def invalidate_cache(self, department: Optional[str] = None):
        """Invalidate cache entries, optionally by department."""
        query = self.db.query(SemanticCache)
        
        if department:
            query = query.filter(SemanticCache.department == department)
        
        query.update({"is_valid": False})
        self.db.commit()
        
        logger.info(f"Cache invalidated for department: {department or 'all'}")
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        now = datetime.utcnow()
        count = self.db.query(SemanticCache).filter(
            SemanticCache.expires_at < now
        ).delete()
        self.db.commit()
        
        logger.info(f"Cleaned up {count} expired cache entries")
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow()
        
        total = self.db.query(SemanticCache).count()
        valid = self.db.query(SemanticCache).filter(
            and_(
                SemanticCache.is_valid == True,
                SemanticCache.expires_at > now
            )
        ).count()
        
        total_hits = self.db.query(
            SemanticCache.hit_count
        ).with_entities(
            SemanticCache.hit_count
        ).all()
        
        hits = sum(h[0] for h in total_hits)
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": total - valid,
            "total_hits": hits,
            "avg_hits_per_entry": hits / total if total > 0 else 0
        }

