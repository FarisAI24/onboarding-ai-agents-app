"""Security services for PII detection, redaction, and rate limiting."""
import re
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# PII Patterns
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
    "ssn": r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
    "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "date_of_birth": r'\b(?:0[1-9]|1[0-2])[\/\-](?:0[1-9]|[12]\d|3[01])[\/\-](?:19|20)\d{2}\b',
}

# Replacement tokens
PII_REPLACEMENTS = {
    "email": "[EMAIL_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "ip_address": "[IP_REDACTED]",
    "date_of_birth": "[DOB_REDACTED]",
}


def detect_pii(text: str) -> Dict[str, list]:
    """Detect PII patterns in text.
    
    Args:
        text: Input text to scan.
        
    Returns:
        Dictionary mapping PII type to list of found matches.
    """
    findings = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            findings[pii_type] = matches
    
    return findings


def redact_pii(text: str) -> str:
    """Redact PII from text.
    
    Args:
        text: Input text to redact.
        
    Returns:
        Text with PII replaced by tokens.
    """
    redacted = text
    
    for pii_type, pattern in PII_PATTERNS.items():
        replacement = PII_REPLACEMENTS.get(pii_type, "[REDACTED]")
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    
    return redacted


def has_pii(text: str) -> bool:
    """Check if text contains PII.
    
    Args:
        text: Input text to check.
        
    Returns:
        True if PII is detected.
    """
    for pattern in PII_PATTERNS.values():
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(
        self,
        requests_per_window: int = None,
        window_seconds: int = None
    ):
        """Initialize rate limiter.
        
        Args:
            requests_per_window: Maximum requests allowed per window.
            window_seconds: Window duration in seconds.
        """
        self.requests_per_window = requests_per_window or settings.rate_limit_requests
        self.window_seconds = window_seconds or settings.rate_limit_window
        
        # Store request timestamps per user
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(self, user_key: str) -> None:
        """Remove requests older than the window.
        
        Args:
            user_key: User identifier.
        """
        cutoff = time.time() - self.window_seconds
        self._requests[user_key] = [
            ts for ts in self._requests[user_key]
            if ts > cutoff
        ]
    
    def is_allowed(self, user_key: str) -> Tuple[bool, int]:
        """Check if request is allowed for user.
        
        Args:
            user_key: User identifier (e.g., user_id, IP).
            
        Returns:
            Tuple of (is_allowed, remaining_requests).
        """
        self._clean_old_requests(user_key)
        
        current_requests = len(self._requests[user_key])
        remaining = max(0, self.requests_per_window - current_requests)
        
        return current_requests < self.requests_per_window, remaining
    
    def record_request(self, user_key: str) -> None:
        """Record a request for user.
        
        Args:
            user_key: User identifier.
        """
        self._requests[user_key].append(time.time())
    
    def get_retry_after(self, user_key: str) -> int:
        """Get seconds until rate limit resets.
        
        Args:
            user_key: User identifier.
            
        Returns:
            Seconds until oldest request expires.
        """
        if not self._requests[user_key]:
            return 0
        
        oldest = min(self._requests[user_key])
        retry_after = int(oldest + self.window_seconds - time.time())
        return max(0, retry_after)


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/handler.
            
        Returns:
            Response or rate limit error.
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get user identifier (prefer user_id from header, fallback to IP)
        user_key = request.headers.get("X-User-ID") or request.client.host
        
        # Check rate limit
        is_allowed, remaining = rate_limiter.is_allowed(user_key)
        
        if not is_allowed:
            retry_after = rate_limiter.get_retry_after(user_key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record request
        rate_limiter.record_request(user_key)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        
        return response


def check_user_access(user_type: str, resource: str, action: str) -> bool:
    """Check if user has access to a resource.
    
    Args:
        user_type: User type (new_hire, admin, hr_manager).
        resource: Resource being accessed.
        action: Action being performed.
        
    Returns:
        True if access is allowed.
    """
    # Access control matrix
    access_matrix = {
        "new_hire": {
            "own_tasks": ["read", "update"],
            "own_messages": ["read", "create"],
            "own_profile": ["read"],
            "faq": ["read"],
            "chat": ["create"],
        },
        "admin": {
            "all_users": ["read"],
            "all_tasks": ["read"],
            "metrics": ["read"],
            "all_messages": ["read"],  # Redacted
        },
        "hr_manager": {
            "all_users": ["read", "create", "update"],
            "all_tasks": ["read", "create", "update"],
            "metrics": ["read"],
        }
    }
    
    user_permissions = access_matrix.get(user_type, {})
    allowed_actions = user_permissions.get(resource, [])
    
    return action in allowed_actions

