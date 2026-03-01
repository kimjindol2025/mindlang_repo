#!/usr/bin/env python3
from typing import Dict
import time

class CapacityPlanner:
    def __init__(self):
        self.resources: Dict[str, Dict] = {}
    
    def add_resource(self, name: str, capacity: int) -> Dict:
        self.resources[name] = {
            "capacity": capacity,
            "used": 0,
            "created_at": time.time()
        }
        return self.resources[name]
    
    def get_available(self, name: str) -> int:
        if name in self.resources:
            return self.resources[name]["capacity"] - self.resources[name]["used"]
        return 0
    
    def allocate(self, name: str, amount: int) -> bool:
        if name in self.resources and self.get_available(name) >= amount:
            self.resources[name]["used"] += amount
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"resources": len(self.resources)}

def main():
    print("📈 Capacity Planner")
    planner = CapacityPlanner()
    planner.add_resource("memory", 16000)
    planner.allocate("memory", 4000)
    print(f"✅ Available: {planner.get_available('memory')}MB, Stats: {planner.get_stats()}")

if __name__ == "__main__":
    main()
