#!/usr/bin/env python3
from typing import Dict
import time

class PerformanceBaselineManager:
    def __init__(self):
        self.baselines: Dict = {}
    
    def set_baseline(self, metric_name: str, value: float) -> Dict:
        baseline = {"metric": metric_name, "value": value, "created_at": time.time()}
        self.baselines[metric_name] = baseline
        return baseline
    
    def compare_to_baseline(self, metric_name: str, current: float) -> Dict:
        baseline = self.baselines.get(metric_name, {}).get("value", 0)
        deviation = ((current - baseline) / baseline * 100) if baseline > 0 else 0
        return {"metric": metric_name, "baseline": baseline, "current": current, "deviation_percent": deviation}
    
    def get_stats(self) -> Dict:
        return {"total_baselines": len(self.baselines)}

def main():
    print("📊 Performance Baseline Manager")
    mgr = PerformanceBaselineManager()
    mgr.set_baseline("response_time", 150.0)
    result = mgr.compare_to_baseline("response_time", 165.0)
    print(f"✅ Deviation: {result['deviation_percent']:.1f}%")

if __name__ == "__main__":
    main()
