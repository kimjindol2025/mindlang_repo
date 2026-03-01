#!/usr/bin/env python3
from typing import Dict, List, Set
import json

class ServiceDependencyMapper:
    def __init__(self):
        self.services: Dict[str, Set[str]] = {}
        self.health: Dict[str, str] = {}
    
    def register_service(self, service_name: str, dependencies: List[str]) -> Dict:
        self.services[service_name] = set(dependencies)
        self.health[service_name] = "UP"
        return {"service": service_name, "dependencies": dependencies}
    
    def update_health(self, service_name: str, status: str) -> bool:
        if service_name in self.services:
            self.health[service_name] = status
            return True
        return False
    
    def get_dependent_services(self, service_name: str) -> List[str]:
        return [s for s, deps in self.services.items() if service_name in deps]
    
    def find_critical_path(self) -> List[str]:
        return sorted(self.services.keys(), key=lambda s: len(self.services.get(s, [])), reverse=True)
    
    def get_stats(self) -> Dict:
        up_services = sum(1 for h in self.health.values() if h == "UP")
        return {"total_services": len(self.services), "healthy": up_services}

def main():
    print("🔗 Service Dependency Mapper")
    mapper = ServiceDependencyMapper()
    mapper.register_service("api", ["db", "cache"])
    mapper.register_service("db", [])
    print(f"✅ Dependents of api: {mapper.get_dependent_services('api')}, Stats: {mapper.get_stats()}")

if __name__ == "__main__":
    main()
