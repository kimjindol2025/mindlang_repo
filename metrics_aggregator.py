#!/usr/bin/env python3
from typing import Dict, List
import time
class MetricsAggregator:
    def __init__(self):
        self.metrics: List[Dict] = []
    def add_metric(self, name: str, value: float) -> Dict:
        metric = {"name": name, "value": value, "timestamp": time.time()}
        self.metrics.append(metric)
        return metric
    def get_average(self, name: str) -> float:
        values = [m["value"] for m in self.metrics if m["name"] == name]
        return sum(values) / len(values) if values else 0
def main():
    print("📈 Metrics Aggregator")
    agg = MetricsAggregator()
    agg.add_metric("latency", 50)
    agg.add_metric("latency", 75)
    print(f"✅ Avg latency: {agg.get_average('latency')}ms")
if __name__ == "__main__":
    main()
