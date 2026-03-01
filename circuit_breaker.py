#!/usr/bin/env python3
"""
Circuit Breaker & Resilience Patterns - Fault tolerance and resilience
Implements circuit breaker, bulkhead, timeout, and retry patterns
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import hashlib
import json
import time
import random


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing


class BulkheadType(Enum):
    """Bulkhead types"""
    THREAD_POOL = "THREAD_POOL"
    SEMAPHORE = "SEMAPHORE"
    QUEUE_BASED = "QUEUE_BASED"


class RetryStrategy(Enum):
    """Retry strategies"""
    IMMEDIATE = "IMMEDIATE"
    LINEAR_BACKOFF = "LINEAR_BACKOFF"
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF"
    RANDOM = "RANDOM"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60
    half_open_max_requests: int = 1


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    state_changes: List[tuple] = field(default_factory=list)


@dataclass
class BulkheadConfig:
    """Bulkhead configuration"""
    name: str
    bulkhead_type: BulkheadType
    max_concurrent_calls: int = 10
    max_wait_duration_ms: int = 5000


@dataclass
class RetryConfig:
    """Retry configuration"""
    name: str
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000


@dataclass
class TimeoutConfig:
    """Timeout configuration"""
    name: str
    timeout_ms: int = 5000


class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.metrics = CircuitBreakerMetrics()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        self.metrics.total_requests += 1

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                self.metrics.rejected_requests += 1
                raise Exception(f"Circuit breaker {self.config.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(str(e))
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config.timeout_seconds

    def _on_success(self):
        """Handle successful call"""
        self.metrics.successful_requests += 1
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self, error: str):
        """Handle failed call"""
        self.metrics.failed_requests += 1
        self.metrics.last_error = error
        self.metrics.last_error_time = time.time()
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        if self.state != new_state:
            self.metrics.state_changes.append((time.time(), self.state.value, new_state.value))
            self.state = new_state


class Bulkhead:
    """Bulkhead implementation (resource isolation)"""

    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.active_calls = 0
        self.waiting_calls = 0
        self.rejected_calls = 0

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        if self.active_calls >= self.config.max_concurrent_calls:
            self.rejected_calls += 1
            raise Exception(f"Bulkhead {self.config.name} is full")

        self.active_calls += 1
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            self.active_calls -= 1


class Retry:
    """Retry implementation"""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempts = 0

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                self.attempts = attempt + 1
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay / 1000)

        raise last_exception

    def _calculate_delay(self, attempt: int) -> int:
        """Calculate delay based on strategy"""
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.initial_delay_ms * (attempt + 1)
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.initial_delay_ms * (2 ** attempt)
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.randint(self.config.initial_delay_ms, self.config.max_delay_ms)
        else:
            delay = self.config.initial_delay_ms

        return min(delay, self.config.max_delay_ms)


class Timeout:
    """Timeout implementation (simplified)"""

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.timedout_calls = 0

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout"""
        start_time = time.time()

        result = func(*args, **kwargs)

        elapsed = (time.time() - start_time) * 1000
        if elapsed > self.config.timeout_ms:
            self.timedout_calls += 1
            raise TimeoutError(f"Call exceeded {self.config.timeout_ms}ms timeout")

        return result


class ResilienceManager:
    """
    Resilience Management System

    Provides:
    - Circuit breaker pattern
    - Bulkhead pattern
    - Retry logic
    - Timeout handling
    - Fallback mechanisms
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        self.retries: Dict[str, Retry] = {}
        self.timeouts: Dict[str, Timeout] = {}

    def register_circuit_breaker(self, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Register circuit breaker"""
        cb = CircuitBreaker(config)
        self.circuit_breakers[config.name] = cb
        return cb

    def register_bulkhead(self, config: BulkheadConfig) -> Bulkhead:
        """Register bulkhead"""
        bh = Bulkhead(config)
        self.bulkheads[config.name] = bh
        return bh

    def register_retry(self, config: RetryConfig) -> Retry:
        """Register retry policy"""
        retry = Retry(config)
        self.retries[config.name] = retry
        return retry

    def register_timeout(self, config: TimeoutConfig) -> Timeout:
        """Register timeout"""
        timeout = Timeout(config)
        self.timeouts[config.name] = timeout
        return timeout

    def execute_protected(self,
                         func: Callable,
                         circuit_breaker_name: str = None,
                         bulkhead_name: str = None,
                         retry_name: str = None,
                         timeout_name: str = None,
                         fallback_func: Callable = None,
                         *args, **kwargs) -> Any:
        """Execute function with multiple protections"""
        try:
            # Apply protections in order
            if timeout_name and timeout_name in self.timeouts:
                func = lambda: self.timeouts[timeout_name].execute(func, *args, **kwargs)

            if retry_name and retry_name in self.retries:
                func = lambda: self.retries[retry_name].execute(func, *args, **kwargs)

            if bulkhead_name and bulkhead_name in self.bulkheads:
                func = lambda: self.bulkheads[bulkhead_name].execute(func, *args, **kwargs)

            if circuit_breaker_name and circuit_breaker_name in self.circuit_breakers:
                return self.circuit_breakers[circuit_breaker_name].call(func)

            return func()

        except Exception as e:
            if fallback_func:
                return fallback_func(*args, **kwargs)
            raise

    def get_resilience_stats(self) -> Dict:
        """Get resilience statistics"""
        return {
            "circuit_breakers": len(self.circuit_breakers),
            "open_circuits": sum(1 for cb in self.circuit_breakers.values()
                               if cb.state == CircuitState.OPEN),
            "bulkheads": len(self.bulkheads),
            "retries": len(self.retries),
            "timeouts": len(self.timeouts),
        }

    def generate_resilience_report(self) -> str:
        """Generate resilience report"""
        stats = self.get_resilience_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  RESILIENCE PATTERNS REPORT                                ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Circuit Breakers: {stats['circuit_breakers']}
├─ 🔴 Open: {stats['open_circuits']}
├─ Bulkheads: {stats['bulkheads']}
├─ Retries: {stats['retries']}
└─ Timeouts: {stats['timeouts']}

🔌 CIRCUIT BREAKERS:
"""

        for name, cb in self.circuit_breakers.items():
            state_emoji = "🟢" if cb.state == CircuitState.CLOSED else "🔴"
            report += f"\n  {state_emoji} {name}\n"
            report += f"    State: {cb.state.value}\n"
            report += f"    Total: {cb.metrics.total_requests}\n"
            report += f"    Success: {cb.metrics.successful_requests}\n"
            report += f"    Failed: {cb.metrics.failed_requests}\n"

        return report

    def export_resilience_config(self) -> str:
        """Export resilience configuration"""
        export_data = {
            "timestamp": time.time(),
            "circuit_breakers": [
                {
                    "name": name,
                    "state": cb.state.value,
                    "metrics": {
                        "total": cb.metrics.total_requests,
                        "successful": cb.metrics.successful_requests,
                        "failed": cb.metrics.failed_requests,
                        "rejected": cb.metrics.rejected_requests,
                    }
                }
                for name, cb in self.circuit_breakers.items()
            ],
            "statistics": self.get_resilience_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🛡️  Circuit Breaker & Resilience Patterns - Fault Tolerance")
    print("=" * 70)

    manager = ResilienceManager()

    # Register circuit breakers
    print("\n🔌 Registering circuit breakers...")
    manager.register_circuit_breaker(
        CircuitBreakerConfig("user-service", failure_threshold=5)
    )
    manager.register_circuit_breaker(
        CircuitBreakerConfig("payment-service", failure_threshold=3)
    )
    print(f"✅ Registered {len(manager.circuit_breakers)} circuit breakers")

    # Register bulkheads
    print("\n🛡️  Registering bulkheads...")
    manager.register_bulkhead(
        BulkheadConfig("database", BulkheadType.THREAD_POOL, max_concurrent_calls=10)
    )
    manager.register_bulkhead(
        BulkheadConfig("external-api", BulkheadType.SEMAPHORE, max_concurrent_calls=5)
    )
    print(f"✅ Registered {len(manager.bulkheads)} bulkheads")

    # Register retries
    print("\n🔄 Registering retry policies...")
    manager.register_retry(
        RetryConfig("api-call", max_attempts=3, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
    )
    print(f"✅ Registered {len(manager.retries)} retry policies")

    # Register timeouts
    print("\n⏱️  Registering timeouts...")
    manager.register_timeout(TimeoutConfig("service-call", timeout_ms=5000))
    print(f"✅ Registered {len(manager.timeouts)} timeouts")

    # Simulate function calls
    print("\n📞 Simulating function calls...")

    def failing_operation():
        if random.random() > 0.3:
            raise Exception("Service unavailable")
        return "success"

    def fallback_operation():
        return "fallback response"

    # Call with protections
    for i in range(5):
        try:
            result = manager.execute_protected(
                failing_operation,
                circuit_breaker_name="user-service",
                retry_name="api-call",
                bulkhead_name="external-api",
                fallback_func=fallback_operation
            )
            print(f"  Call {i+1}: {result}")
        except Exception as e:
            print(f"  Call {i+1}: Failed - {str(e)[:50]}")

    # Generate report
    print(manager.generate_resilience_report())

    # Export
    print("\n📄 Exporting resilience config...")
    export = manager.export_resilience_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Resilience patterns ready")


if __name__ == "__main__":
    main()
