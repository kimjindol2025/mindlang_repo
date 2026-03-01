#!/usr/bin/env python3
from typing import Dict, List
import time

class ServiceRegistryAdvanced:
    def __init__(self):
        self.services: Dict[str, Dict] = {}
    
    def register(self, name: str, host: str, port: int, tags: List[str]) -> Dict:
        self.services[name] = {
            "host": host,
            "port": port,
            "tags": tags,
            "registered_at": time.time(),
            "healthy": True
        }
        return self.services[name]
    
    def deregister(self, name: str) -> bool:
        if name in self.services:
            del self.services[name]
            return True
        return False
    
    def discover_by_tag(self, tag: str) -> List[Dict]:
        return [{"name": k, **v} for k, v in self.services.items() if tag in v.get("tags", [])]
    
    def get_stats(self) -> Dict:
        return {"total_services": len(self.services), "healthy": sum(1 for s in self.services.values() if s["healthy"])}

def main():
    print("🔍 Service Registry Advanced")
    registry = ServiceRegistryAdvanced()
    registry.register("auth-service", "localhost", 8001, ["auth", "core"])
    registry.register("user-service", "localhost", 8002, ["users", "core"])
    print(f"✅ Core services: {len(registry.discover_by_tag('core'))}, Stats: {registry.get_stats()}")

if __name__ == "__main__":
    main()
