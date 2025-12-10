"""Hybrid search combining semantic and keyword-based retrieval."""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time
import hashlib

from rank_bm25 import BM25Okapi
from cachetools import TTLCache
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Result from hybrid search."""
    document: str
    metadata: Dict[str, Any]
    semantic_score: float
    bm25_score: float
    combined_score: float
    rank: int


@dataclass 
class HybridSearchResponse:
    """Response from hybrid search pipeline."""
    results: List[HybridSearchResult]
    query: str
    semantic_time_ms: float
    bm25_time_ms: float
    rerank_time_ms: float
    total_time_ms: float
    cache_hit: bool = False


class BM25Index:
    """BM25 index for keyword-based retrieval."""
    
    def __init__(self):
        """Initialize the BM25 index."""
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self._tokenized_docs: List[List[str]] = []
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25.
        
        Args:
            text: Text to tokenize.
            
        Returns:
            List of tokens.
        """
        # Simple tokenization: lowercase, split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> None:
        """Add documents to the BM25 index.
        
        Args:
            documents: List of document texts.
            metadatas: List of metadata dicts.
            ids: List of document IDs.
        """
        if metadatas is None:
            metadatas = [{}] * len(documents)
        if ids is None:
            ids = [f"doc_{len(self.documents) + i}" for i in range(len(documents))]
            
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.doc_ids.extend(ids)
        
        # Rebuild BM25 index
        self._tokenized_docs = [self._tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(self._tokenized_docs)
        
        logger.info(f"BM25 index now has {len(self.documents)} documents")
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        department_filter: str = None
    ) -> List[Tuple[int, float]]:
        """Search the BM25 index.
        
        Args:
            query: Query text.
            n_results: Number of results to return.
            department_filter: Optional department filter.
            
        Returns:
            List of (doc_index, score) tuples.
        """
        if self.bm25 is None or len(self.documents) == 0:
            return []
        
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # Apply department filter if specified
        if department_filter:
            for i, meta in enumerate(self.metadatas):
                if meta.get("department", "").upper() != department_filter.upper():
                    scores[i] = 0.0
        
        # Get top results
        top_indices = np.argsort(scores)[::-1][:n_results * 2]  # Get more for filtering
        results = [(int(idx), float(scores[idx])) for idx in top_indices if scores[idx] > 0]
        
        return results[:n_results]
    
    def get_document(self, index: int) -> Tuple[str, Dict[str, Any]]:
        """Get document by index.
        
        Args:
            index: Document index.
            
        Returns:
            Tuple of (document_text, metadata).
        """
        return self.documents[index], self.metadatas[index]


class HybridSearchEngine:
    """Hybrid search engine combining semantic and BM25 retrieval."""
    
    def __init__(
        self,
        vectorstore,
        bm25_index: BM25Index = None,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        cache_ttl: int = 300,
        cache_maxsize: int = 1000
    ):
        """Initialize the hybrid search engine.
        
        Args:
            vectorstore: Vector store service for semantic search.
            bm25_index: BM25 index for keyword search.
            semantic_weight: Weight for semantic scores (0-1).
            bm25_weight: Weight for BM25 scores (0-1).
            cache_ttl: Cache TTL in seconds.
            cache_maxsize: Maximum cache size.
        """
        self.vectorstore = vectorstore
        self.bm25_index = bm25_index or BM25Index()
        self.semantic_weight = semantic_weight
        self.bm25_weight = bm25_weight
        
        # Query cache
        self._cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        
        # Metrics
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_semantic_time_ms": 0,
            "avg_bm25_time_ms": 0,
            "avg_total_time_ms": 0
        }
    
    def _get_cache_key(self, query: str, department: str, n_results: int) -> str:
        """Generate cache key for a query.
        
        Args:
            query: Query text.
            department: Department filter.
            n_results: Number of results.
            
        Returns:
            Cache key string.
        """
        key_str = f"{query.lower().strip()}|{department or 'all'}|{n_results}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range.
        
        Args:
            scores: List of scores.
            
        Returns:
            Normalized scores.
        """
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        department_filter: str = None,
        use_cache: bool = True
    ) -> HybridSearchResponse:
        """Perform hybrid search.
        
        Args:
            query: Query text.
            n_results: Number of results to return.
            department_filter: Optional department filter.
            use_cache: Whether to use query cache.
            
        Returns:
            HybridSearchResponse with ranked results.
        """
        start_time = time.time()
        self.metrics["total_queries"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(query, department_filter, n_results)
        if use_cache and cache_key in self._cache:
            self.metrics["cache_hits"] += 1
            cached = self._cache[cache_key]
            cached.cache_hit = True
            return cached
        
        # Step 1: Semantic search
        semantic_start = time.time()
        semantic_results = self.vectorstore.query(
            query_text=query,
            n_results=n_results * 2,  # Get more for fusion
            where={"department": department_filter} if department_filter else None
        )
        semantic_time = (time.time() - semantic_start) * 1000
        
        # Step 2: BM25 search
        bm25_start = time.time()
        bm25_results = self.bm25_index.search(
            query=query,
            n_results=n_results * 2,
            department_filter=department_filter
        )
        bm25_time = (time.time() - bm25_start) * 1000
        
        # Step 3: Fuse results using Reciprocal Rank Fusion (RRF)
        rerank_start = time.time()
        
        doc_scores = defaultdict(lambda: {"semantic": 0, "bm25": 0, "doc": None, "meta": None})
        
        # Process semantic results
        semantic_docs = semantic_results.get("documents", [[]])[0]
        semantic_metas = semantic_results.get("metadatas", [[]])[0]
        semantic_distances = semantic_results.get("distances", [[]])[0]
        
        # Convert distances to similarity scores (ChromaDB uses L2/cosine distance)
        semantic_scores = [1 / (1 + d) for d in semantic_distances]
        
        for i, (doc, meta, score) in enumerate(zip(semantic_docs, semantic_metas, semantic_scores)):
            doc_key = hashlib.md5(doc.encode()).hexdigest()[:16]
            doc_scores[doc_key]["semantic"] = score
            doc_scores[doc_key]["doc"] = doc
            doc_scores[doc_key]["meta"] = meta
        
        # Process BM25 results
        for idx, score in bm25_results:
            doc, meta = self.bm25_index.get_document(idx)
            doc_key = hashlib.md5(doc.encode()).hexdigest()[:16]
            doc_scores[doc_key]["bm25"] = score
            doc_scores[doc_key]["doc"] = doc
            doc_scores[doc_key]["meta"] = meta
        
        # Normalize and combine scores
        all_semantic = [v["semantic"] for v in doc_scores.values()]
        all_bm25 = [v["bm25"] for v in doc_scores.values()]
        
        norm_semantic = self._normalize_scores(all_semantic)
        norm_bm25 = self._normalize_scores(all_bm25)
        
        results = []
        for i, (doc_key, data) in enumerate(doc_scores.items()):
            if data["doc"] is None:
                continue
                
            combined_score = (
                self.semantic_weight * norm_semantic[i] +
                self.bm25_weight * norm_bm25[i]
            )
            
            results.append(HybridSearchResult(
                document=data["doc"],
                metadata=data["meta"],
                semantic_score=data["semantic"],
                bm25_score=data["bm25"],
                combined_score=combined_score,
                rank=0
            ))
        
        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results[:n_results]):
            result.rank = i + 1
        
        rerank_time = (time.time() - rerank_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        # Update metrics
        self._update_metrics(semantic_time, bm25_time, total_time)
        
        response = HybridSearchResponse(
            results=results[:n_results],
            query=query,
            semantic_time_ms=semantic_time,
            bm25_time_ms=bm25_time,
            rerank_time_ms=rerank_time,
            total_time_ms=total_time,
            cache_hit=False
        )
        
        # Cache the response
        if use_cache:
            self._cache[cache_key] = response
        
        return response
    
    def _update_metrics(self, semantic_time: float, bm25_time: float, total_time: float):
        """Update running average metrics."""
        n = self.metrics["total_queries"]
        self.metrics["avg_semantic_time_ms"] = (
            (self.metrics["avg_semantic_time_ms"] * (n - 1) + semantic_time) / n
        )
        self.metrics["avg_bm25_time_ms"] = (
            (self.metrics["avg_bm25_time_ms"] * (n - 1) + bm25_time) / n
        )
        self.metrics["avg_total_time_ms"] = (
            (self.metrics["avg_total_time_ms"] * (n - 1) + total_time) / n
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get search metrics.
        
        Returns:
            Dictionary of metrics.
        """
        return {
            **self.metrics,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / max(1, self.metrics["total_queries"])
            )
        }
    
    def clear_cache(self):
        """Clear the query cache."""
        self._cache.clear()


# Global instance
_hybrid_search_engine: Optional[HybridSearchEngine] = None


def get_hybrid_search_engine(vectorstore=None) -> HybridSearchEngine:
    """Get or create the hybrid search engine singleton.
    
    Args:
        vectorstore: Vector store service.
        
    Returns:
        HybridSearchEngine instance.
    """
    global _hybrid_search_engine
    
    if _hybrid_search_engine is None:
        from rag.vectorstore import get_vectorstore_service
        vs = vectorstore or get_vectorstore_service()
        _hybrid_search_engine = HybridSearchEngine(vectorstore=vs)
    
    return _hybrid_search_engine


def initialize_bm25_index(documents: List[str], metadatas: List[Dict[str, Any]]):
    """Initialize the BM25 index with documents.
    
    Args:
        documents: List of document texts.
        metadatas: List of metadata dicts.
    """
    engine = get_hybrid_search_engine()
    engine.bm25_index.add_documents(documents, metadatas)
    logger.info(f"Initialized BM25 index with {len(documents)} documents")

