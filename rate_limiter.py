#!/usr/bin/env python3
"""
Rate Limiter & Quota Manager - Traffic control and usage quotas
Implements token bucket, sliding window, and quota-based rate limiting
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time
import math


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "TOKEN_BUCKET"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    LEAKY_BUCKET = "LEAKY_BUCKET"
    FIXED_WINDOW = "FIXED_WINDOW"


class QuotaType(Enum):
    """Quota types"""
    REQUESTS_PER_MINUTE = "REQUESTS_PER_MINUTE"
    REQUESTS_PER_HOUR = "REQUESTS_PER_HOUR"
    REQUESTS_PER_DAY = "REQUESTS_PER_DAY"
    BYTES_PER_HOUR = "BYTES_PER_HOUR"
    CONCURRENT_CONNECTIONS = "CONCURRENT_CONNECTIONS"


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    bucket_id: str
    client_id: str
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)


@dataclass
class QuotaLimit:
    """Quota limit definition"""
    quota_id: str
    client_id: str
    quota_type: QuotaType
    limit: int
    window_size: int  # seconds
    current_usage: int = 0
    reset_at: float = field(default_factory=time.time)


@dataclass
class RateLimitEvent:
    """Rate limit event"""
    event_id: str
    client_id: str
    timestamp: float
    allowed: bool
    reason: str


class RateLimiter:
    """Rate limiter implementation"""

    def __init__(self,
                 client_id: str,
                 algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
                 limit: int = 1000,
                 window_seconds: int = 60):
        self.client_id = client_id
        self.algorithm = algorithm
        self.limit = limit
        self.window_seconds = window_seconds
        self.request_history: List[float] = []

        if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self.bucket = TokenBucket(
                bucket_id=hashlib.md5(f"{client_id}".encode()).hexdigest()[:8],
                client_id=client_id,
                capacity=limit,
                tokens=limit,
                refill_rate=limit / window_seconds
            )

    def is_allowed(self, tokens_needed: int = 1) -> bool:
        """Check if request is allowed"""
        if self.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._token_bucket_check(tokens_needed)
        elif self.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._sliding_window_check()
        elif self.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return self._leaky_bucket_check()
        else:
            return self._fixed_window_check()

    def _token_bucket_check(self, tokens_needed: int) -> bool:
        """Token bucket algorithm"""
        # Refill tokens
        now = time.time()
        elapsed = now - self.bucket.last_refill
        refilled = elapsed * self.bucket.refill_rate
        self.bucket.tokens = min(self.bucket.capacity, self.bucket.tokens + refilled)
        self.bucket.last_refill = now

        # Check if enough tokens
        if self.bucket.tokens >= tokens_needed:
            self.bucket.tokens -= tokens_needed
            return True
        return False

    def _sliding_window_check(self) -> bool:
        """Sliding window algorithm"""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old requests
        self.request_history = [t for t in self.request_history if t > cutoff]

        if len(self.request_history) < self.limit:
            self.request_history.append(now)
            return True
        return False

    def _leaky_bucket_check(self) -> bool:
        """Leaky bucket algorithm"""
        now = time.time()

        # Calculate leak
        leak_rate = self.limit / self.window_seconds
        elapsed = now - (self.request_history[0] if self.request_history else now)
        leaked = elapsed * leak_rate

        current_level = max(0, len(self.request_history) - leaked)

        if current_level < self.limit:
            self.request_history.append(now)
            return True
        return False

    def _fixed_window_check(self) -> bool:
        """Fixed window algorithm"""
        if not hasattr(self, '_window_start'):
            self._window_start = time.time()
            self._window_count = 0

        now = time.time()

        # Check if window expired
        if now - self._window_start > self.window_seconds:
            self._window_start = now
            self._window_count = 0

        if self._window_count < self.limit:
            self._window_count += 1
            return True
        return False


class RateLimiterManager:
    """
    Rate Limiter Manager

    Provides:
    - Multiple rate limiting algorithms
    - Quota management
    - Per-client limits
    - Distributed rate limiting
    - Rate limit events
    """

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.quotas: Dict[str, QuotaLimit] = {}
        self.events: List[RateLimitEvent] = []

    def create_limiter(self,
                      client_id: str,
                      algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
                      limit: int = 1000,
                      window_seconds: int = 60) -> RateLimiter:
        """Create rate limiter for client"""
        limiter = RateLimiter(client_id, algorithm, limit, window_seconds)
        self.limiters[client_id] = limiter
        return limiter

    def check_rate_limit(self, client_id: str, tokens_needed: int = 1) -> bool:
        """Check if request is allowed"""
        limiter = self.limiters.get(client_id)
        if not limiter:
            return True

        allowed = limiter.is_allowed(tokens_needed)

        # Log event
        self._log_event(client_id, allowed, "Rate limit check")

        return allowed

    def create_quota(self,
                    client_id: str,
                    quota_type: QuotaType,
                    limit: int) -> QuotaLimit:
        """Create quota limit for client"""
        quota_id = hashlib.md5(f"{client_id}:{quota_type.value}".encode()).hexdigest()[:8]

        # Determine window size
        if quota_type == QuotaType.REQUESTS_PER_MINUTE:
            window_size = 60
        elif quota_type == QuotaType.REQUESTS_PER_HOUR:
            window_size = 3600
        elif quota_type == QuotaType.REQUESTS_PER_DAY:
            window_size = 86400
        elif quota_type == QuotaType.BYTES_PER_HOUR:
            window_size = 3600
        else:
            window_size = 3600

        quota = QuotaLimit(
            quota_id=quota_id,
            client_id=client_id,
            quota_type=quota_type,
            limit=limit,
            window_size=window_size
        )

        self.quotas[quota_id] = quota
        return quota

    def check_quota(self, client_id: str, quota_type: QuotaType, usage: int = 1) -> bool:
        """Check if quota allows usage"""
        # Find matching quota
        for quota in self.quotas.values():
            if quota.client_id == client_id and quota.quota_type == quota_type:
                # Check reset
                if time.time() - quota.reset_at > quota.window_size:
                    quota.current_usage = 0
                    quota.reset_at = time.time()

                if quota.current_usage + usage <= quota.limit:
                    quota.current_usage += usage
                    self._log_event(client_id, True, f"Quota check: {quota_type.value}")
                    return True
                else:
                    self._log_event(client_id, False, f"Quota exceeded: {quota_type.value}")
                    return False

        return True

    def _log_event(self, client_id: str, allowed: bool, reason: str):
        """Log rate limit event"""
        event_id = hashlib.md5(f"{client_id}:{time.time()}".encode()).hexdigest()[:8]
        event = RateLimitEvent(
            event_id=event_id,
            client_id=client_id,
            timestamp=time.time(),
            allowed=allowed,
            reason=reason
        )
        self.events.append(event)

    def get_limiter_stats(self, client_id: str) -> Dict:
        """Get limiter statistics for client"""
        limiter = self.limiters.get(client_id)
        if not limiter:
            return {}

        if limiter.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            tokens_left = limiter.bucket.tokens
        else:
            tokens_left = len(limiter.request_history)

        # Count events
        allowed_events = sum(1 for e in self.events if e.client_id == client_id and e.allowed)
        blocked_events = sum(1 for e in self.events if e.client_id == client_id and not e.allowed)

        return {
            "algorithm": limiter.algorithm.value,
            "limit": limiter.limit,
            "tokens_left": tokens_left,
            "allowed_requests": allowed_events,
            "blocked_requests": blocked_events,
            "block_rate": blocked_events / max(1, allowed_events + blocked_events),
        }

    def get_global_stats(self) -> Dict:
        """Get global statistics"""
        total_allowed = sum(1 for e in self.events if e.allowed)
        total_blocked = sum(1 for e in self.events if not e.allowed)

        return {
            "clients": len(self.limiters),
            "quotas": len(self.quotas),
            "total_requests": len(self.events),
            "allowed": total_allowed,
            "blocked": total_blocked,
            "block_rate": total_blocked / max(1, total_allowed + total_blocked),
        }

    def generate_rate_limit_report(self) -> str:
        """Generate rate limit report"""
        stats = self.get_global_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              RATE LIMITER & QUOTA REPORT                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Clients: {stats['clients']}
├─ Quotas: {stats['quotas']}
├─ Total Requests: {stats['total_requests']}
├─ Allowed: {stats['allowed']}
├─ Blocked: {stats['blocked']}
└─ Block Rate: {stats['block_rate']:.2%}

👥 CLIENT LIMITERS:
"""

        for client_id, limiter in self.limiters.items():
            client_stats = self.get_limiter_stats(client_id)
            report += f"\n  {client_id}\n"
            report += f"    Algorithm: {client_stats.get('algorithm', 'N/A')}\n"
            report += f"    Block Rate: {client_stats.get('block_rate', 0):.2%}\n"

        return report

    def export_rate_limit_config(self) -> str:
        """Export rate limiter configuration"""
        export_data = {
            "timestamp": time.time(),
            "clients": len(self.limiters),
            "limiters": [
                {
                    "client_id": client_id,
                    "algorithm": limiter.algorithm.value,
                    "limit": limiter.limit,
                    "window": limiter.window_seconds,
                }
                for client_id, limiter in self.limiters.items()
            ],
            "quotas": [
                {
                    "client_id": q.client_id,
                    "quota_type": q.quota_type.value,
                    "limit": q.limit,
                    "current_usage": q.current_usage,
                }
                for q in self.quotas.values()
            ],
            "statistics": self.get_global_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🚦 Rate Limiter & Quota Manager - Traffic Control")
    print("=" * 70)

    manager = RateLimiterManager()

    # Create limiters
    print("\n📝 Creating rate limiters...")
    limiter1 = manager.create_limiter(
        "client_001",
        RateLimitAlgorithm.TOKEN_BUCKET,
        limit=100,
        window_seconds=60
    )
    limiter2 = manager.create_limiter(
        "client_002",
        RateLimitAlgorithm.SLIDING_WINDOW,
        limit=200,
        window_seconds=60
    )
    print(f"✅ Created {len(manager.limiters)} limiters")

    # Create quotas
    print("\n📋 Creating quotas...")
    manager.create_quota("client_001", QuotaType.REQUESTS_PER_MINUTE, 1000)
    manager.create_quota("client_001", QuotaType.BYTES_PER_HOUR, 1000000)
    manager.create_quota("client_002", QuotaType.REQUESTS_PER_DAY, 10000)
    print(f"✅ Created {len(manager.quotas)} quotas")

    # Simulate requests
    print("\n🔄 Simulating requests...")
    for i in range(150):
        client = "client_001" if i % 2 == 0 else "client_002"
        allowed = manager.check_rate_limit(client)

        # Also check quota
        allowed_quota = manager.check_quota(client, QuotaType.REQUESTS_PER_MINUTE)

        if i % 30 == 0:
            print(f"  Request {i+1}: {'✅ Allowed' if allowed and allowed_quota else '❌ Blocked'}")

    # Generate report
    print(manager.generate_rate_limit_report())

    # Export
    print("\n📄 Exporting rate limiter config...")
    export = manager.export_rate_limit_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Rate limiter ready")


if __name__ == "__main__":
    main()
