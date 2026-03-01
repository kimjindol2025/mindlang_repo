#!/usr/bin/env python3
from typing import Dict, List
import time

class MetricsBuffer:
    def __init__(self, flush_interval: int = 60):
        self.buffer: List[Dict] = []
        self.flush_interval = flush_interval
        self.last_flush = time.time()
    
    def add_metric(self, name: str, value: float) -> None:
        self.buffer.append({"name": name, "value": value, "timestamp": time.time()})
    
    def should_flush(self) -> bool:
        return time.time() - self.last_flush > self.flush_interval
    
    def flush(self) -> List[Dict]:
        flushed = self.buffer.copy()
        self.buffer = []
        self.last_flush = time.time()
        return flushed
    
    def get_stats(self) -> Dict:
        return {"buffered_metrics": len(self.buffer)}

def main():
    print("📊 Metrics Buffer")
    buffer = MetricsBuffer()
    buffer.add_metric("cpu", 45.5)
    buffer.add_metric("memory", 78.2)
    print(f"✅ Should flush: {buffer.should_flush()}, Stats: {buffer.get_stats()}")

if __name__ == "__main__":
    main()
