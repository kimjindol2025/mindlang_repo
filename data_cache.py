#!/usr/bin/env python3
from typing import Dict, Any
import time

class DataCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
    
    def set(self, key: str, value: Any) -> Dict:
        self.cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + self.ttl_seconds
        }
        return self.cache[key]
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires_at"]:
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    def get_stats(self) -> Dict:
        return {"cached_items": len(self.cache)}

def main():
    print("💾 Data Cache")
    cache = DataCache(ttl_seconds=3600)
    cache.set("user:123", {"name": "John", "email": "john@test.com"})
    cache.set("user:456", {"name": "Jane", "email": "jane@test.com"})
    print(f"✅ Retrieved: {cache.get('user:123')}, Stats: {cache.get_stats()}")

if __name__ == "__main__":
    main()
