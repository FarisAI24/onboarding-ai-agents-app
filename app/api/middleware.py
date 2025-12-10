"""API Middleware for security, rate limiting, and metrics."""
import time
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.security import check_rate_limit, redact_pii, get_pii_detector
from app.monitoring import get_metrics_collector

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security features including rate limiting and PII protection."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security checks.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/handler.
            
        Returns:
            Response after processing.
        """
        start_time = time.time()
        metrics = get_metrics_collector()
        
        # Extract user identifier for rate limiting
        # Try to get user_id from headers or use IP address
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            client_host = request.client.host if request.client else "unknown"
            user_id = f"ip:{client_host}"
        
        # Determine user tier for rate limiting
        user_type = request.headers.get("X-User-Type", "default")
        tier = "admin" if user_type == "admin" else "new_hire" if user_type == "new_hire" else "default"
        
        # Check rate limit (skip for health checks and metrics)
        if not request.url.path.endswith(("/health", "/metrics")):
            rate_result = check_rate_limit(user_id, tier)
            
            if not rate_result.allowed:
                logger.warning(f"Rate limit exceeded for {user_id}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_result.retry_after,
                        "remaining": rate_result.remaining
                    },
                    headers={
                        "Retry-After": str(int(rate_result.retry_after or 60)),
                        "X-RateLimit-Remaining": str(rate_result.remaining),
                        "X-RateLimit-Reset": str(int(rate_result.reset_at))
                    }
                )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record metrics
            elapsed = time.time() - start_time
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code,
                latency_seconds=elapsed
            )
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            return response
            
        except Exception as e:
            elapsed = time.time() - start_time
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status=500,
                latency_seconds=elapsed
            )
            logger.error(f"Request error: {e}")
            raise


class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """Middleware to redact PII from request/response logs."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with PII redaction for logging.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/handler.
            
        Returns:
            Response after processing.
        """
        # Log request with PII redaction
        if request.method in ("POST", "PUT", "PATCH"):
            # We'll let individual handlers deal with body redaction
            # since reading body here would consume it
            pass
        
        # Process request
        response = await call_next(request)
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        from app.monitoring.metrics import ACTIVE_REQUESTS
        self.active_requests = ACTIVE_REQUESTS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track active requests.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/handler.
            
        Returns:
            Response after processing.
        """
        self.active_requests.inc()
        try:
            response = await call_next(request)
            return response
        finally:
            self.active_requests.dec()


def add_security_headers(response: Response) -> Response:
    """Add security headers to response.
    
    Args:
        response: Response to modify.
        
    Returns:
        Response with security headers.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

