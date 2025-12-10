"""Prometheus metrics for production monitoring."""
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)


# Create a custom registry
REGISTRY = CollectorRegistry()

# ============================================================================
# Request Metrics
# ============================================================================

REQUEST_COUNT = Counter(
    'onboarding_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status'],
    registry=REGISTRY
)

REQUEST_LATENCY = Histogram(
    'onboarding_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY
)

ACTIVE_REQUESTS = Gauge(
    'onboarding_active_requests',
    'Number of active requests',
    registry=REGISTRY
)

# ============================================================================
# Chat/Agent Metrics
# ============================================================================

CHAT_MESSAGES = Counter(
    'onboarding_chat_messages_total',
    'Total number of chat messages',
    ['user_type', 'department'],
    registry=REGISTRY
)

AGENT_CALLS = Counter(
    'onboarding_agent_calls_total',
    'Total number of agent calls',
    ['agent_name', 'success'],
    registry=REGISTRY
)

AGENT_LATENCY = Histogram(
    'onboarding_agent_latency_seconds',
    'Agent processing latency in seconds',
    ['agent_name'],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=REGISTRY
)

# ============================================================================
# Routing Metrics
# ============================================================================

ROUTING_PREDICTIONS = Counter(
    'onboarding_routing_predictions_total',
    'Total routing model predictions',
    ['predicted_department', 'final_department', 'was_overridden'],
    registry=REGISTRY
)

ROUTING_CONFIDENCE = Histogram(
    'onboarding_routing_confidence',
    'Routing model confidence distribution',
    ['department'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=REGISTRY
)

# ============================================================================
# RAG Metrics
# ============================================================================

RAG_QUERIES = Counter(
    'onboarding_rag_queries_total',
    'Total RAG queries',
    ['department_filter', 'cache_hit'],
    registry=REGISTRY
)

RAG_RETRIEVAL_LATENCY = Histogram(
    'onboarding_rag_retrieval_latency_seconds',
    'RAG retrieval latency in seconds',
    ['search_type'],  # semantic, bm25, hybrid
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    registry=REGISTRY
)

RAG_DOCUMENTS_RETRIEVED = Histogram(
    'onboarding_rag_documents_retrieved',
    'Number of documents retrieved per query',
    buckets=[1, 2, 3, 4, 5, 7, 10],
    registry=REGISTRY
)

RAG_CONFIDENCE = Histogram(
    'onboarding_rag_confidence',
    'RAG response confidence distribution',
    ['confidence_level'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=REGISTRY
)

# ============================================================================
# Task/Progress Metrics
# ============================================================================

TASK_STATUS_UPDATES = Counter(
    'onboarding_task_status_updates_total',
    'Total task status updates',
    ['department', 'old_status', 'new_status'],
    registry=REGISTRY
)

USER_PROGRESS = Gauge(
    'onboarding_user_progress_percent',
    'User onboarding progress percentage',
    ['user_id', 'department'],
    registry=REGISTRY
)

OVERDUE_TASKS = Gauge(
    'onboarding_overdue_tasks_total',
    'Total number of overdue tasks',
    ['department'],
    registry=REGISTRY
)

# ============================================================================
# User Metrics
# ============================================================================

ACTIVE_USERS = Gauge(
    'onboarding_active_users',
    'Number of active users',
    ['user_type'],
    registry=REGISTRY
)

NEW_USERS = Counter(
    'onboarding_new_users_total',
    'Total new users registered',
    ['department'],
    registry=REGISTRY
)

# ============================================================================
# System Metrics
# ============================================================================

SYSTEM_INFO = Info(
    'onboarding_system',
    'System information',
    registry=REGISTRY
)

DB_QUERY_LATENCY = Histogram(
    'onboarding_db_query_latency_seconds',
    'Database query latency in seconds',
    ['operation'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY
)


class MetricsCollector:
    """Collector for application metrics with aggregation support."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = Lock()
        self._start_time = datetime.now()
        
        # In-memory aggregations for dashboard
        self._hourly_requests = defaultdict(int)
        self._department_queries = defaultdict(int)
        self._response_times: list = []
        self._error_count = 0
        
        # Set system info
        SYSTEM_INFO.info({
            'version': '1.0.0',
            'environment': 'production'
        })
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        latency_seconds: float
    ):
        """Record an HTTP request.
        
        Args:
            endpoint: API endpoint.
            method: HTTP method.
            status: Response status code.
            latency_seconds: Request latency.
        """
        REQUEST_COUNT.labels(
            endpoint=endpoint,
            method=method,
            status=str(status)
        ).inc()
        
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency_seconds)
        
        # Update in-memory aggregations
        with self._lock:
            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
            self._hourly_requests[hour_key] += 1
            self._response_times.append(latency_seconds)
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]
            if status >= 400:
                self._error_count += 1
    
    def record_chat_message(
        self,
        user_type: str,
        department: str
    ):
        """Record a chat message.
        
        Args:
            user_type: Type of user (new_hire, admin).
            department: Routed department.
        """
        CHAT_MESSAGES.labels(
            user_type=user_type,
            department=department
        ).inc()
        
        with self._lock:
            self._department_queries[department] += 1
    
    def record_agent_call(
        self,
        agent_name: str,
        success: bool,
        latency_seconds: float
    ):
        """Record an agent call.
        
        Args:
            agent_name: Name of the agent.
            success: Whether the call succeeded.
            latency_seconds: Agent processing time.
        """
        AGENT_CALLS.labels(
            agent_name=agent_name,
            success=str(success).lower()
        ).inc()
        
        AGENT_LATENCY.labels(agent_name=agent_name).observe(latency_seconds)
    
    def record_routing(
        self,
        predicted_department: str,
        final_department: str,
        confidence: float,
        was_overridden: bool
    ):
        """Record a routing decision.
        
        Args:
            predicted_department: ML model prediction.
            final_department: Final routing decision.
            confidence: Prediction confidence.
            was_overridden: Whether prediction was overridden.
        """
        ROUTING_PREDICTIONS.labels(
            predicted_department=predicted_department,
            final_department=final_department,
            was_overridden=str(was_overridden).lower()
        ).inc()
        
        ROUTING_CONFIDENCE.labels(
            department=final_department
        ).observe(confidence)
    
    def record_rag_query(
        self,
        department_filter: str,
        cache_hit: bool,
        retrieval_time_seconds: float,
        search_type: str,
        num_documents: int,
        confidence: float,
        confidence_level: str
    ):
        """Record a RAG query.
        
        Args:
            department_filter: Department filter used.
            cache_hit: Whether result was from cache.
            retrieval_time_seconds: Retrieval latency.
            search_type: Type of search (semantic, bm25, hybrid).
            num_documents: Number of documents retrieved.
            confidence: Confidence score.
            confidence_level: Confidence level string.
        """
        RAG_QUERIES.labels(
            department_filter=department_filter or "all",
            cache_hit=str(cache_hit).lower()
        ).inc()
        
        RAG_RETRIEVAL_LATENCY.labels(
            search_type=search_type
        ).observe(retrieval_time_seconds)
        
        RAG_DOCUMENTS_RETRIEVED.observe(num_documents)
        
        RAG_CONFIDENCE.labels(
            confidence_level=confidence_level
        ).observe(confidence)
    
    def record_task_update(
        self,
        department: str,
        old_status: str,
        new_status: str
    ):
        """Record a task status update.
        
        Args:
            department: Task department.
            old_status: Previous status.
            new_status: New status.
        """
        TASK_STATUS_UPDATES.labels(
            department=department,
            old_status=old_status,
            new_status=new_status
        ).inc()
    
    def set_user_progress(
        self,
        user_id: int,
        department: str,
        progress: float
    ):
        """Set user progress gauge.
        
        Args:
            user_id: User ID.
            department: Department.
            progress: Progress percentage (0-100).
        """
        USER_PROGRESS.labels(
            user_id=str(user_id),
            department=department
        ).set(progress)
    
    def set_overdue_tasks(self, department: str, count: int):
        """Set overdue tasks gauge.
        
        Args:
            department: Department.
            count: Number of overdue tasks.
        """
        OVERDUE_TASKS.labels(department=department).set(count)
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics for dashboard display.
        
        Returns:
            Dictionary of dashboard metrics.
        """
        with self._lock:
            # Calculate percentiles for response times
            sorted_times = sorted(self._response_times) if self._response_times else [0]
            p50_idx = int(len(sorted_times) * 0.5)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            
            uptime = datetime.now() - self._start_time
            
            return {
                "uptime_seconds": uptime.total_seconds(),
                "total_requests": sum(self._hourly_requests.values()),
                "error_count": self._error_count,
                "error_rate": (
                    self._error_count / max(1, sum(self._hourly_requests.values()))
                ),
                "response_times": {
                    "p50_ms": sorted_times[p50_idx] * 1000 if sorted_times else 0,
                    "p95_ms": sorted_times[p95_idx] * 1000 if sorted_times else 0,
                    "p99_ms": sorted_times[p99_idx] * 1000 if sorted_times else 0,
                    "avg_ms": (
                        sum(self._response_times) / len(self._response_times) * 1000
                        if self._response_times else 0
                    )
                },
                "department_queries": dict(self._department_queries),
                "hourly_requests": dict(
                    list(self._hourly_requests.items())[-24:]  # Last 24 hours
                )
            }
    
    def get_prometheus_metrics(self) -> bytes:
        """Get Prometheus-formatted metrics.
        
        Returns:
            Prometheus metrics as bytes.
        """
        return generate_latest(REGISTRY)


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_time(metric_name: str = None):
    """Decorator to track function execution time.
    
    Args:
        metric_name: Optional name for the metric.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                logger.debug(f"{func.__name__} took {elapsed*1000:.2f}ms")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                logger.debug(f"{func.__name__} took {elapsed*1000:.2f}ms")
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is a coroutine function."""
    import asyncio
    return asyncio.iscoroutinefunction(func)

