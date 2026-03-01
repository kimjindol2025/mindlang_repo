#!/usr/bin/env python3
from typing import Dict, List
import time

class ClusterResourceMonitor:
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
    
    def register_node(self, node_id: str, cpu_cores: int, memory_gb: int) -> Dict:
        self.nodes[node_id] = {
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "cpu_used": 0,
            "memory_used": 0,
            "timestamp": time.time()
        }
        return self.nodes[node_id]
    
    def update_node_usage(self, node_id: str, cpu_used: float, memory_used: float) -> bool:
        if node_id in self.nodes:
            self.nodes[node_id]["cpu_used"] = cpu_used
            self.nodes[node_id]["memory_used"] = memory_used
            return True
        return False
    
    def get_cluster_stats(self) -> Dict:
        total_cpu = sum(n["cpu_cores"] for n in self.nodes.values())
        total_mem = sum(n["memory_gb"] for n in self.nodes.values())
        used_cpu = sum(n["cpu_used"] for n in self.nodes.values())
        used_mem = sum(n["memory_used"] for n in self.nodes.values())
        return {"nodes": len(self.nodes), "total_cpu": total_cpu, "total_memory": total_mem, "used_cpu": used_cpu, "used_memory": used_mem}

def main():
    print("💻 Cluster Resource Monitor")
    monitor = ClusterResourceMonitor()
    monitor.register_node("node-1", 8, 32)
    monitor.update_node_usage("node-1", 4.5, 20.0)
    print(f"✅ Cluster: {monitor.get_cluster_stats()}")

if __name__ == "__main__":
    main()
