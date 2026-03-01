#!/usr/bin/env python3
from typing import Dict, List, Set
import json

class DependencyGraphAnalyzer:
    def __init__(self):
        self.services: Dict[str, Set[str]] = {}
    
    def add_service(self, service: str, dependencies: List[str]) -> Dict:
        self.services[service] = set(dependencies)
        return {"service": service, "dependencies": dependencies}
    
    def get_dependents(self, service: str) -> List[str]:
        return [s for s, deps in self.services.items() if service in deps]
    
    def analyze_graph(self) -> Dict:
        critical_services = [s for s in self.services if len(self.services.get(s, [])) > 2]
        return {"total_services": len(self.services), "critical_services": critical_services}
    
    def export_graph(self) -> str:
        graph = {k: list(v) for k, v in self.services.items()}
        return json.dumps(graph, indent=2)

def main():
    print("🔗 Dependency Graph Analyzer")
    analyzer = DependencyGraphAnalyzer()
    analyzer.add_service("api", ["db", "cache", "auth"])
    analyzer.add_service("auth", ["db"])
    print(f"✅ Graph: {analyzer.analyze_graph()}")

if __name__ == "__main__":
    main()
