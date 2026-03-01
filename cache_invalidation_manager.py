#!/usr/bin/env python3
from typing import Dict, Set, List
import time

class CacheInvalidationManager:
    def __init__(self):
        self.cache_keys: Dict[str, float] = {}
        self.invalidation_rules: Dict[str, List[str]] = {}
    
    def register_cache_key(self, key: str, ttl: float) -> Dict:
        self.cache_keys[key] = time.time() + ttl
        return {"key": key, "expires_at": self.cache_keys[key]}
    
    def add_invalidation_rule(self, source: str, affected_keys: List[str]) -> None:
        self.invalidation_rules[source] = affected_keys
    
    def invalidate_on_event(self, event_source: str) -> List[str]:
        invalidated = self.invalidation_rules.get(event_source, [])
        for key in invalidated:
            if key in self.cache_keys:
                del self.cache_keys[key]
        return invalidated
    
    def get_stats(self) -> Dict:
        expired = sum(1 for t in self.cache_keys.values() if t < time.time())
        return {"total_keys": len(self.cache_keys), "expired": expired, "rules": len(self.invalidation_rules)}

def main():
    print("🗑️  Cache Invalidation Manager")
    mgr = CacheInvalidationManager()
    mgr.register_cache_key("user:123", 3600)
    mgr.add_invalidation_rule("user_update", ["user:123"])
    invalidated = mgr.invalidate_on_event("user_update")
    print(f"✅ Invalidated: {len(invalidated)} keys, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
