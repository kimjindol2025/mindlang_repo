#!/usr/bin/env python3
from typing import Dict, List
import time

class RequestRouter:
    def __init__(self):
        self.routes: Dict[str, List[str]] = {}
        self.request_count: Dict[str, int] = {}
    
    def add_route(self, path: str, handlers: List[str]) -> Dict:
        self.routes[path] = handlers
        self.request_count[path] = 0
        return {"path": path, "handlers": len(handlers)}
    
    def route_request(self, path: str) -> List[str]:
        if path in self.routes:
            self.request_count[path] += 1
            return self.routes[path]
        return []
    
    def get_stats(self) -> Dict:
        return {"routes": len(self.routes), "total_requests": sum(self.request_count.values())}

def main():
    print("🔀 Request Router")
    router = RequestRouter()
    router.add_route("/api/users", ["auth", "db", "cache"])
    router.add_route("/api/products", ["db", "cache"])
    router.route_request("/api/users")
    print(f"✅ Stats: {router.get_stats()}")

if __name__ == "__main__":
    main()
