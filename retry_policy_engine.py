#!/usr/bin/env python3
from typing import Dict
import time

class RetryPolicyEngine:
    def __init__(self):
        self.policies: Dict[str, Dict] = {}
        self.attempts: Dict[str, int] = {}
    
    def add_policy(self, name: str, max_retries: int, backoff_ms: int) -> Dict:
        self.policies[name] = {"max_retries": max_retries, "backoff_ms": backoff_ms}
        self.attempts[name] = 0
        return self.policies[name]
    
    def should_retry(self, policy_name: str) -> bool:
        if policy_name not in self.policies:
            return False
        return self.attempts.get(policy_name, 0) < self.policies[policy_name]["max_retries"]
    
    def record_attempt(self, policy_name: str) -> int:
        self.attempts[policy_name] = self.attempts.get(policy_name, 0) + 1
        return self.attempts[policy_name]
    
    def get_backoff_time(self, policy_name: str, attempt: int) -> float:
        if policy_name not in self.policies:
            return 0
        return self.policies[policy_name]["backoff_ms"] * (2 ** attempt) / 1000

def main():
    print("🔄 Retry Policy Engine")
    engine = RetryPolicyEngine()
    engine.add_policy("api_call", 3, 100)
    print(f"✅ Should retry: {engine.should_retry('api_call')}, Backoff: {engine.get_backoff_time('api_call', 1):.2f}s")

if __name__ == "__main__":
    main()
