#!/usr/bin/env python3
from typing import Dict, List, Set

class DependencyResolver:
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}
    
    def add_dependency(self, component: str, depends_on: str) -> None:
        if component not in self.dependencies:
            self.dependencies[component] = set()
        self.dependencies[component].add(depends_on)
        if depends_on not in self.dependencies:
            self.dependencies[depends_on] = set()
    
    def resolve_order(self) -> List[str]:
        resolved = []
        remaining = set(self.dependencies.keys())
        
        while remaining:
            found = False
            for comp in list(remaining):
                deps = self.dependencies.get(comp, set())
                if deps.issubset(set(resolved)):
                    resolved.append(comp)
                    remaining.remove(comp)
                    found = True
                    break
            if not found:
                break
        
        return resolved
    
    def get_stats(self) -> Dict:
        return {"components": len(self.dependencies)}

def main():
    print("🔗 Dependency Resolver")
    resolver = DependencyResolver()
    resolver.add_dependency("service-a", "database")
    resolver.add_dependency("service-b", "service-a")
    order = resolver.resolve_order()
    print(f"✅ Resolution order: {order}, Stats: {resolver.get_stats()}")

if __name__ == "__main__":
    main()
