"""Rate limiting module for API protection."""
import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float  # Unix timestamp when limit resets
    retry_after: Optional[float] = None  # Seconds until retry is allowed


class RateLimiter:
    """Token bucket rate limiter with sliding window."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        window_seconds: int = 60
    ):
        """Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute.
            burst_size: Maximum burst size.
            window_seconds: Time window in seconds.
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.window_seconds = window_seconds
        
        # Per-user token buckets
        self._buckets: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": burst_size,
            "last_update": time.time(),
            "request_times": []
        })
        self._lock = Lock()
        
        # Rate at which tokens are added (per second)
        self._refill_rate = requests_per_minute / 60.0
    
    def _refill_bucket(self, bucket: Dict) -> None:
        """Refill tokens based on elapsed time.
        
        Args:
            bucket: The token bucket to refill.
        """
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self._refill_rate
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_update"] = now
        
        # Clean up old request times
        bucket["request_times"] = [
            t for t in bucket["request_times"]
            if now - t < self.window_seconds
        ]
    
    def check(self, identifier: str) -> RateLimitResult:
        """Check if a request is allowed.
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP address).
            
        Returns:
            RateLimitResult indicating if request is allowed.
        """
        with self._lock:
            bucket = self._buckets[identifier]
            self._refill_bucket(bucket)
            
            now = time.time()
            
            # Check sliding window limit
            recent_requests = len(bucket["request_times"])
            if recent_requests >= self.requests_per_minute:
                oldest_request = min(bucket["request_times"])
                reset_at = oldest_request + self.window_seconds
                retry_after = reset_at - now
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after
                )
            
            # Check token bucket
            if bucket["tokens"] < 1:
                tokens_needed = 1 - bucket["tokens"]
                retry_after = tokens_needed / self._refill_rate
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=now + retry_after,
                    retry_after=retry_after
                )
            
            # Request allowed - consume a token
            bucket["tokens"] -= 1
            bucket["request_times"].append(now)
            
            remaining = min(
                int(bucket["tokens"]),
                self.requests_per_minute - len(bucket["request_times"])
            )
            
            # Calculate reset time (when the oldest request expires)
            if bucket["request_times"]:
                reset_at = min(bucket["request_times"]) + self.window_seconds
            else:
                reset_at = now + self.window_seconds
            
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_at=reset_at
            )
    
    def get_usage(self, identifier: str) -> Dict:
        """Get current rate limit usage for an identifier.
        
        Args:
            identifier: Unique identifier.
            
        Returns:
            Usage statistics.
        """
        with self._lock:
            bucket = self._buckets[identifier]
            self._refill_bucket(bucket)
            
            return {
                "tokens_available": bucket["tokens"],
                "requests_in_window": len(bucket["request_times"]),
                "limit_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size
            }
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for an identifier.
        
        Args:
            identifier: Unique identifier.
        """
        with self._lock:
            if identifier in self._buckets:
                del self._buckets[identifier]
    
    def reset_all(self) -> None:
        """Reset all rate limits."""
        with self._lock:
            self._buckets.clear()


class TieredRateLimiter:
    """Rate limiter with different tiers for different user types."""
    
    # Default tier configurations - generous limits for production use
    DEFAULT_TIERS = {
        "new_hire": {"requests_per_minute": 120, "burst_size": 30},
        "admin": {"requests_per_minute": 300, "burst_size": 50},
        "api": {"requests_per_minute": 180, "burst_size": 40},
        "default": {"requests_per_minute": 100, "burst_size": 25}
    }
    
    def __init__(self, tier_configs: Dict[str, Dict] = None):
        """Initialize the tiered rate limiter.
        
        Args:
            tier_configs: Configuration per tier.
        """
        self.tier_configs = tier_configs or self.DEFAULT_TIERS
        self._limiters: Dict[str, RateLimiter] = {}
        
        # Create a limiter for each tier
        for tier_name, config in self.tier_configs.items():
            self._limiters[tier_name] = RateLimiter(
                requests_per_minute=config["requests_per_minute"],
                burst_size=config["burst_size"]
            )
    
    def check(
        self,
        identifier: str,
        tier: str = "default"
    ) -> RateLimitResult:
        """Check if a request is allowed for a given tier.
        
        Args:
            identifier: Unique identifier.
            tier: Rate limit tier.
            
        Returns:
            RateLimitResult indicating if request is allowed.
        """
        if tier not in self._limiters:
            tier = "default"
        
        return self._limiters[tier].check(identifier)
    
    def get_tier_config(self, tier: str) -> Dict:
        """Get configuration for a tier.
        
        Args:
            tier: Tier name.
            
        Returns:
            Tier configuration.
        """
        return self.tier_configs.get(tier, self.tier_configs["default"])


# Global rate limiter instances
_rate_limiter: Optional[TieredRateLimiter] = None


def get_rate_limiter() -> TieredRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TieredRateLimiter()
    return _rate_limiter


def check_rate_limit(
    identifier: str,
    tier: str = "default"
) -> RateLimitResult:
    """Check rate limit for an identifier.
    
    Args:
        identifier: Unique identifier.
        tier: Rate limit tier.
        
    Returns:
        RateLimitResult.
    """
    return get_rate_limiter().check(identifier, tier)

