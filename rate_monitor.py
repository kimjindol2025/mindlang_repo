#!/usr/bin/env python3
from typing import Dict
import time

class RateMonitor:
    def __init__(self):
        self.rates: Dict[str, float] = {}
        self.last_check: Dict[str, float] = {}
    
    def record_rate(self, name: str, rate: float) -> Dict:
        self.rates[name] = rate
        self.last_check[name] = time.time()
        return {"name": name, "rate": rate}
    
    def is_exceeding(self, name: str, threshold: float) -> bool:
        return self.rates.get(name, 0) > threshold
    
    def get_stats(self) -> Dict:
        return {"monitored_rates": len(self.rates)}

def main():
    print("📊 Rate Monitor")
    monitor = RateMonitor()
    monitor.record_rate("cpu", 75.5)
    monitor.record_rate("memory", 82.3)
    print(f"✅ CPU exceeds 80%: {monitor.is_exceeding('cpu', 80)}, Stats: {monitor.get_stats()}")

if __name__ == "__main__":
    main()
