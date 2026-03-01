#!/usr/bin/env python3
from typing import Dict
import time

class UsageQuotaManager:
    def __init__(self):
        self.quotas: Dict[str, Dict] = {}
        self.usage: Dict[str, Dict] = {}
    
    def set_quota(self, user_id: str, limit: int, period: str) -> Dict:
        self.quotas[user_id] = {"limit": limit, "period": period, "set_at": time.time()}
        self.usage[user_id] = {"count": 0, "reset_at": time.time()}
        return self.quotas[user_id]
    
    def consume(self, user_id: str, amount: int = 1) -> Dict:
        if user_id not in self.quotas:
            return {"allowed": False, "reason": "No quota"}
        
        quota = self.quotas[user_id]
        usage = self.usage[user_id]
        
        if usage["count"] + amount <= quota["limit"]:
            usage["count"] += amount
            return {"allowed": True, "remaining": quota["limit"] - usage["count"]}
        
        return {"allowed": False, "remaining": quota["limit"] - usage["count"]}
    
    def get_stats(self) -> Dict:
        return {"users": len(self.quotas), "active_quotas": len([u for u in self.usage.values() if u["count"] > 0])}

def main():
    print("📊 Usage Quota Manager")
    mgr = UsageQuotaManager()
    mgr.set_quota("user1", 100, "daily")
    result = mgr.consume("user1", 10)
    print(f"✅ Allowed: {result['allowed']}, Remaining: {result['remaining']}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
