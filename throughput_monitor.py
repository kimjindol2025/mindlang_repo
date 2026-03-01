#!/usr/bin/env python3
from typing import Dict, List
import time

class ThroughputMonitor:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.events: List[Dict] = []
    
    def record_event(self, event_type: str) -> Dict:
        event = {"type": event_type, "timestamp": time.time()}
        self.events.append(event)
        return event
    
    def get_throughput(self) -> float:
        now = time.time()
        cutoff = now - self.window_seconds
        recent = [e for e in self.events if e["timestamp"] > cutoff]
        return len(recent) / self.window_seconds if recent else 0
    
    def get_stats(self) -> Dict:
        return {"total_events": len(self.events), "throughput_per_sec": round(self.get_throughput(), 2)}

def main():
    print("⚡ Throughput Monitor")
    monitor = ThroughputMonitor()
    for i in range(10):
        monitor.record_event("request")
    print(f"✅ Stats: {monitor.get_stats()}")

if __name__ == "__main__":
    main()
