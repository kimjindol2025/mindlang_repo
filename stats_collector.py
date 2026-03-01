#!/usr/bin/env python3
from typing import Dict, List
import time

class StatsCollector:
    def __init__(self):
        self.stats: Dict[str, List[float]] = {}
    
    def record(self, name: str, value: float) -> None:
        if name not in self.stats:
            self.stats[name] = []
        self.stats[name].append(value)
    
    def get_summary(self, name: str) -> Dict:
        if name not in self.stats:
            return {}
        values = self.stats[name]
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }
    
    def get_all_stats(self) -> Dict:
        return {k: self.get_summary(k) for k in self.stats.keys()}

def main():
    print("📊 Stats Collector")
    collector = StatsCollector()
    for val in [10, 20, 30, 40]:
        collector.record("latency", val)
    summary = collector.get_summary("latency")
    print(f"✅ Latency stats: avg={summary['avg']}, min={summary['min']}, max={summary['max']}")

if __name__ == "__main__":
    main()
