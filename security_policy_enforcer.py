#!/usr/bin/env python3
from typing import Dict, List
import time

class SecurityPolicyEnforcer:
    def __init__(self):
        self.policies: Dict[str, Dict] = {}
        self.violations: List[Dict] = []
    
    def add_policy(self, policy_name: str, rule: str) -> Dict:
        self.policies[policy_name] = {"rule": rule, "created_at": time.time(), "violations": 0}
        return self.policies[policy_name]
    
    def check_policy(self, policy_name: str, data: Dict) -> bool:
        if policy_name not in self.policies:
            return True
        
        policy = self.policies[policy_name]
        is_valid = True
        
        if "min_length" in policy["rule"] and len(str(data)) < 8:
            is_valid = False
            policy["violations"] += 1
        
        if not is_valid:
            self.violations.append({
                "policy": policy_name,
                "timestamp": time.time(),
                "data": str(data)[:50]
            })
        
        return is_valid
    
    def get_stats(self) -> Dict:
        total_violations = sum(p["violations"] for p in self.policies.values())
        return {"policies": len(self.policies), "total_violations": total_violations}

def main():
    print("🔐 Security Policy Enforcer")
    enforcer = SecurityPolicyEnforcer()
    enforcer.add_policy("password_policy", "min_length:8")
    result = enforcer.check_policy("password_policy", {"pwd": "secure123"})
    print(f"✅ Policy Check: {result}, Stats: {enforcer.get_stats()}")

if __name__ == "__main__":
    main()
