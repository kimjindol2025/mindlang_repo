#!/usr/bin/env python3
from typing import Dict, List
import time
import json

class MetricsExporter:
    def __init__(self):
        self.metrics: List[Dict] = []
    
    def record_metric(self, name: str, value: float, labels: Dict) -> Dict:
        metric = {
            "name": name,
            "value": value,
            "labels": labels,
            "timestamp": time.time()
        }
        self.metrics.append(metric)
        return metric
    
    def export_prometheus(self) -> str:
        lines = []
        for m in self.metrics:
            labels = ",".join(f'{k}="{v}"' for k, v in m["labels"].items())
            lines.append(f'{m["name"]}{{{labels}}} {m["value"]}')
        return "\n".join(lines)
    
    def export_json(self) -> str:
        return json.dumps(self.metrics, indent=2, default=str)
    
    def get_stats(self) -> Dict:
        return {"total_metrics": len(self.metrics)}

def main():
    print("📈 Metrics Exporter")
    exporter = MetricsExporter()
    exporter.record_metric("http_requests_total", 1000, {"method": "GET", "status": "200"})
    exporter.record_metric("http_latency_ms", 45.5, {"endpoint": "/api"})
    print(f"✅ Prometheus Format:\\n{exporter.export_prometheus()}")

if __name__ == "__main__":
    main()
