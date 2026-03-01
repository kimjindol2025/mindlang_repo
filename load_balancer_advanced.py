#!/usr/bin/env python3
from typing import Dict, List
import time

class LoadBalancerAdvanced:
    def __init__(self):
        self.servers: Dict[str, Dict] = {}
    
    def register_server(self, server_id: str, weight: int = 1) -> Dict:
        self.servers[server_id] = {"weight": weight, "load": 0, "registered_at": time.time()}
        return self.servers[server_id]
    
    def distribute(self, request_id: str) -> str:
        if not self.servers:
            return None
        
        selected = min(self.servers.items(), key=lambda x: x[1]["load"] / x[1]["weight"])
        selected[1]["load"] += 1
        return selected[0]
    
    def get_stats(self) -> Dict:
        total_load = sum(s["load"] for s in self.servers.values())
        return {"servers": len(self.servers), "total_load": total_load}

def main():
    print("⚖️ Load Balancer Advanced")
    lb = LoadBalancerAdvanced()
    lb.register_server("srv-1", weight=2)
    lb.register_server("srv-2", weight=1)
    lb.distribute("req-001")
    print(f"✅ Stats: {lb.get_stats()}")

if __name__ == "__main__":
    main()
