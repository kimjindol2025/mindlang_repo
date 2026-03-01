#!/usr/bin/env python3
from typing import Dict, Any
import hashlib
import time

class ResponseCache:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def compute_key(self, request: str) -> str:
        return hashlib.md5(request.encode()).hexdigest()
    
    def cache_response(self, request: str, response: Dict) -> str:
        key = self.compute_key(request)
        self.cache[key] = {"response": response, "cached_at": time.time()}
        return key
    
    def get_cached_response(self, request: str) -> Dict:
        key = self.compute_key(request)
        if key in self.cache:
            return self.cache[key]["response"]
        return None
    
    def get_stats(self) -> Dict:
        return {"cached_responses": len(self.cache)}

def main():
    print("💾 Response Cache")
    cache = ResponseCache()
    cache.cache_response("SELECT * FROM users", {"rows": 100})
    cached = cache.get_cached_response("SELECT * FROM users")
    print(f"✅ Cached: {cached is not None}, Stats: {cache.get_stats()}")

if __name__ == "__main__":
    main()
