#!/usr/bin/env python3
from typing import Dict
import time
class LoadBalancerStats:
    def __init__(self):
        self.backend_nodes: Dict = {}
    def add_node(self, node_id: str) -> Dict:
        self.backend_nodes[node_id] = {"requests": 0, "errors": 0}
        return self.backend_nodes[node_id]
    def get_stats(self) -> Dict:
        return {"nodes": len(self.backend_nodes), "total_requests": sum(n.get("requests", 0) for n in self.backend_nodes.values())}
def main():
    print("⚖️  Load Balancer Stats")
    lb = LoadBalancerStats()
    lb.add_node("node_1")
    print(f"✅ {len(lb.backend_nodes)} nodes")
if __name__ == "__main__":
    main()
