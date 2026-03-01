#!/usr/bin/env python3
from typing import Dict, List
import time

class ResourceUsageTracker:
    def __init__(self):
        self.usage_history: List[Dict] = []
    
    def record_usage(self, component: str, cpu: float, memory: float, disk: float) -> Dict:
        record = {
            "component": component,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "timestamp": time.time()
        }
        self.usage_history.append(record)
        return record
    
    def get_component_stats(self, component: str) -> Dict:
        records = [r for r in self.usage_history if r["component"] == component]
        if not records:
            return {"component": component, "records": 0}
        
        avg_cpu = sum(r["cpu"] for r in records) / len(records)
        avg_mem = sum(r["memory"] for r in records) / len(records)
        max_disk = max(r["disk"] for r in records)
        
        return {
            "component": component,
            "records": len(records),
            "avg_cpu": avg_cpu,
            "avg_memory": avg_mem,
            "peak_disk": max_disk
        }
    
    def get_stats(self) -> Dict:
        components = set(r["component"] for r in self.usage_history)
        return {"total_records": len(self.usage_history), "components": list(components)}

def main():
    print("📈 Resource Usage Tracker")
    tracker = ResourceUsageTracker()
    tracker.record_usage("worker", 45.5, 2048, 50)
    tracker.record_usage("worker", 52.3, 2150, 55)
    stats = tracker.get_component_stats("worker")
    print(f"✅ Worker Stats: {stats}")

if __name__ == "__main__":
    main()
