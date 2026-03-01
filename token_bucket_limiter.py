#!/usr/bin/env python3
from typing import Dict
import time

class TokenBucketLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def allow_request(self, tokens_needed: int = 1) -> bool:
        self.refill()
        if self.tokens >= tokens_needed:
            self.tokens -= tokens_needed
            return True
        return False
    
    def get_stats(self) -> Dict:
        self.refill()
        return {"available_tokens": int(self.tokens), "capacity": self.capacity}

def main():
    print("⏱️  Token Bucket Limiter")
    limiter = TokenBucketLimiter(10, 1.0)
    allowed1 = limiter.allow_request(3)
    allowed2 = limiter.allow_request(3)
    print(f"✅ Request 1: {allowed1}, Request 2: {allowed2}, Stats: {limiter.get_stats()}")

if __name__ == "__main__":
    main()
