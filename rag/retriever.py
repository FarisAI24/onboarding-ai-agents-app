"""Production-grade RAG retriever with hybrid search and confidence scoring."""
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from rag.vectorstore import VectorStoreService, get_vectorstore_service
from rag.hybrid_search import (
    HybridSearchEngine, 
    HybridSearchResponse, 
    get_hybrid_search_engine
)

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence levels for RAG responses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class RetrievalResult:
    """Result from document retrieval."""
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]
    retrieval_time_ms: float
    hybrid_response: Optional[HybridSearchResponse] = None


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    sources: List[Dict[str, str]]
    retrieval_result: RetrievalResult
    total_time_ms: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.5
    retrieval_metrics: Dict[str, Any] = field(default_factory=dict)


class RAGRetriever:
    """Production-grade RAG retriever with hybrid search and confidence scoring."""
    
    SYSTEM_PROMPT = """You are an AI assistant helping new employees with onboarding questions.
Your job is to answer questions based ONLY on the provided context documents.

IMPORTANT RULES:
1. Only answer based on the information in the context below.
2. If the context doesn't contain enough information to answer, say "I don't have enough information to answer that. Please contact the relevant department for assistance."
3. Always cite your sources by mentioning the document section.
4. Be concise but helpful.
5. If asked about something not in the policies, don't make up information.
6. Format your response using Markdown for better readability:
   - Use **bold** for important terms
   - Use bullet points or numbered lists for steps
   - Use headers (##) for sections if the answer is long

User's Role: {user_role}
User's Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the context above. Include references to the relevant document sections. Use Markdown formatting for clarity."""

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.7
    MEDIUM_CONFIDENCE_THRESHOLD = 0.4
    MIN_DOCS_FOR_HIGH_CONFIDENCE = 2

    def __init__(
        self,
        vectorstore: VectorStoreService = None,
        hybrid_engine: HybridSearchEngine = None,
        top_k: int = None,
        llm_model: str = None,
        temperature: float = None,
        use_hybrid_search: bool = True
    ):
        """Initialize the RAG retriever.
        
        Args:
            vectorstore: Vector store service to use.
            hybrid_engine: Hybrid search engine.
            top_k: Number of documents to retrieve.
            llm_model: OpenAI model to use.
            temperature: LLM temperature.
            use_hybrid_search: Whether to use hybrid search.
        """
        settings = get_settings()
        self.vectorstore = vectorstore or get_vectorstore_service()
        self.top_k = top_k or settings.top_k_retrieval
        self.use_hybrid_search = use_hybrid_search
        
        # Initialize hybrid search engine
        if use_hybrid_search:
            self.hybrid_engine = hybrid_engine or get_hybrid_search_engine(self.vectorstore)
        else:
            self.hybrid_engine = None
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model or settings.llm_model,
            temperature=temperature if temperature is not None else settings.llm_temperature,
            api_key=settings.openai_api_key
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", self.USER_PROMPT)
        ])
        
        # Create chain
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        # Metrics tracking
        self._query_count = 0
        self._total_latency_ms = 0
        self._confidence_distribution = {
            ConfidenceLevel.HIGH: 0,
            ConfidenceLevel.MEDIUM: 0,
            ConfidenceLevel.LOW: 0,
            ConfidenceLevel.NONE: 0
        }
    
    def retrieve(
        self,
        query: str,
        department_filter: str = None,
        top_k: int = None
    ) -> RetrievalResult:
        """Retrieve relevant documents for a query.
        
        Args:
            query: User query.
            department_filter: Optional department to filter by.
            top_k: Number of results to return.
            
        Returns:
            RetrievalResult with documents and metadata.
        """
        k = top_k or self.top_k
        start_time = time.time()
        
        documents = []
        metadatas = []
        distances = []
        hybrid_response = None
        
        # Use hybrid search if enabled
        if self.use_hybrid_search and self.hybrid_engine:
            try:
                hybrid_response = self.hybrid_engine.search(
                    query=query,
                    n_results=k,
                    department_filter=department_filter
                )
                
                documents = [r.document for r in hybrid_response.results]
                metadatas = [r.metadata for r in hybrid_response.results]
                distances = [1 - r.combined_score for r in hybrid_response.results]
                
                logger.info(
                    f"Hybrid search returned {len(documents)} documents "
                    f"(cache_hit={hybrid_response.cache_hit})"
                )
            except Exception as e:
                logger.warning(f"Hybrid search failed, falling back to semantic: {e}")
        
        # Fallback to semantic search
        if not documents:
            if department_filter:
                results = self.vectorstore.query_by_department(
                    query_text=query,
                    department=department_filter,
                    n_results=k
                )
            else:
                results = self.vectorstore.query(
                    query_text=query,
                    n_results=k
                )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            logger.info(f"Semantic search returned {len(documents)} documents")
        
        # If still no results with filter, try without
        if not documents and department_filter:
            logger.info("No results with department filter, trying general search")
            results = self.vectorstore.query(
                query_text=query,
                n_results=k
            )
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            documents=documents,
            metadatas=metadatas,
            distances=distances,
            retrieval_time_ms=retrieval_time,
            hybrid_response=hybrid_response
        )
    
    def calculate_confidence(
        self,
        retrieval_result: RetrievalResult,
        query: str
    ) -> tuple[ConfidenceLevel, float]:
        """Calculate confidence level for the retrieval.
        
        Args:
            retrieval_result: Retrieval results.
            query: Original query.
            
        Returns:
            Tuple of (ConfidenceLevel, confidence_score).
        """
        if not retrieval_result.documents:
            return ConfidenceLevel.NONE, 0.0
        
        # Calculate average relevance score
        if retrieval_result.hybrid_response:
            # Use combined scores from hybrid search
            scores = [r.combined_score for r in retrieval_result.hybrid_response.results]
        else:
            # Convert distances to similarity scores
            scores = [1 / (1 + d) for d in retrieval_result.distances]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        top_score = scores[0] if scores else 0
        
        # Calculate confidence based on multiple factors
        num_docs = len(retrieval_result.documents)
        
        # Confidence formula: weighted combination of top score, avg score, and doc count
        confidence_score = (
            0.5 * top_score +
            0.3 * avg_score +
            0.2 * min(1.0, num_docs / self.MIN_DOCS_FOR_HIGH_CONFIDENCE)
        )
        
        # Determine confidence level
        if confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD:
            level = ConfidenceLevel.HIGH
        elif confidence_score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        return level, confidence_score
    
    def format_context(self, retrieval_result: RetrievalResult) -> str:
        """Format retrieved documents as context string.
        
        Args:
            retrieval_result: Retrieved documents.
            
        Returns:
            Formatted context string.
        """
        context_parts = []
        
        for i, (doc, meta) in enumerate(zip(
            retrieval_result.documents, 
            retrieval_result.metadatas
        ), 1):
            source = meta.get("filename", "Unknown")
            section = meta.get("section", "")
            department = meta.get("department", "")
            
            header = f"[Document {i}] Source: {source}"
            if section:
                header += f" | Section: {section}"
            if department:
                header += f" | Department: {department}"
            
            context_parts.append(f"{header}\n{doc}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def extract_sources(self, retrieval_result: RetrievalResult) -> List[Dict[str, str]]:
        """Extract source references from retrieval result.
        
        Args:
            retrieval_result: Retrieved documents.
            
        Returns:
            List of source dictionaries.
        """
        sources = []
        seen = set()
        
        for meta in retrieval_result.metadatas:
            source_key = (meta.get("filename", ""), meta.get("section", ""))
            if source_key not in seen:
                seen.add(source_key)
                sources.append({
                    "document": meta.get("filename", "Unknown"),
                    "section": meta.get("section", ""),
                    "department": meta.get("department", "")
                })
        
        return sources
    
    def answer(
        self,
        question: str,
        user_role: str = "Employee",
        user_department: str = "General",
        department_filter: str = None
    ) -> RAGResponse:
        """Answer a question using RAG.
        
        Args:
            question: User question.
            user_role: User's job role.
            user_department: User's department.
            department_filter: Optional department to filter documents by.
            
        Returns:
            RAGResponse with answer, sources, and confidence.
        """
        start_time = time.time()
        self._query_count += 1
        
        # Retrieve relevant documents
        retrieval_result = self.retrieve(question, department_filter)
        
        # Calculate confidence
        confidence_level, confidence_score = self.calculate_confidence(
            retrieval_result, question
        )
        self._confidence_distribution[confidence_level] += 1
        
        if not retrieval_result.documents:
            return RAGResponse(
                answer="I couldn't find any relevant information in our policy documents. Please contact the appropriate department for assistance.",
                sources=[],
                retrieval_result=retrieval_result,
                total_time_ms=(time.time() - start_time) * 1000,
                confidence=ConfidenceLevel.NONE,
                confidence_score=0.0,
                retrieval_metrics=self._get_retrieval_metrics(retrieval_result)
            )
        
        # Format context
        context = self.format_context(retrieval_result)
        
        # Generate answer
        llm_start = time.time()
        answer = self.chain.invoke({
            "context": context,
            "question": question,
            "user_role": user_role,
            "user_department": user_department
        })
        llm_time = (time.time() - llm_start) * 1000
        
        # Extract sources
        sources = self.extract_sources(retrieval_result)
        
        total_time = (time.time() - start_time) * 1000
        self._total_latency_ms += total_time
        
        # Prepare retrieval metrics
        retrieval_metrics = self._get_retrieval_metrics(retrieval_result)
        retrieval_metrics["llm_time_ms"] = llm_time
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            retrieval_result=retrieval_result,
            total_time_ms=total_time,
            confidence=confidence_level,
            confidence_score=confidence_score,
            retrieval_metrics=retrieval_metrics
        )
    
    def _get_retrieval_metrics(self, retrieval_result: RetrievalResult) -> Dict[str, Any]:
        """Get metrics for a retrieval operation."""
        metrics = {
            "num_documents": len(retrieval_result.documents),
            "retrieval_time_ms": retrieval_result.retrieval_time_ms
        }
        
        if retrieval_result.hybrid_response:
            metrics["hybrid_search"] = {
                "semantic_time_ms": retrieval_result.hybrid_response.semantic_time_ms,
                "bm25_time_ms": retrieval_result.hybrid_response.bm25_time_ms,
                "rerank_time_ms": retrieval_result.hybrid_response.rerank_time_ms,
                "cache_hit": retrieval_result.hybrid_response.cache_hit
            }
        
        return metrics
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overall retriever metrics.
        
        Returns:
            Dictionary of metrics.
        """
        avg_latency = (
            self._total_latency_ms / self._query_count 
            if self._query_count > 0 else 0
        )
        
        metrics = {
            "total_queries": self._query_count,
            "avg_latency_ms": avg_latency,
            "confidence_distribution": {
                k.value: v for k, v in self._confidence_distribution.items()
            }
        }
        
        if self.hybrid_engine:
            metrics["hybrid_search"] = self.hybrid_engine.get_metrics()
        
        return metrics


# Global instance
_rag_retriever: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    """Get RAG retriever singleton instance."""
    global _rag_retriever
    
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    
    return _rag_retriever
