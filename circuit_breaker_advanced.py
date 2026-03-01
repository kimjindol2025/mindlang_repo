#!/usr/bin/env python3
from typing import Dict
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class AdvancedCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.state = CircuitState.CLOSED.value
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
    
    def call(self, func_name: str) -> Dict:
        if self.state == CircuitState.OPEN.value:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN.value
            else:
                return {"success": False, "reason": "Circuit is OPEN"}
        
        result = {"success": True, "function": func_name}
        return result
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN.value
    
    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN.value:
            self.state = CircuitState.CLOSED.value
            self.failure_count = 0
    
    def get_stats(self) -> Dict:
        return {"state": self.state, "failures": self.failure_count}

def main():
    print("🔌 Advanced Circuit Breaker")
    breaker = AdvancedCircuitBreaker(failure_threshold=3)
    result = breaker.call("external_service")
    print(f"✅ Call: {result['success']}, Stats: {breaker.get_stats()}")

if __name__ == "__main__":
    main()
