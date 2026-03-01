#!/usr/bin/env python3
from typing import Dict
import time

class RequestCounter:
    def __init__(self):
        self.counts: Dict[str, int] = {}
        self.timestamps: Dict[str, List] = {}
    
    def increment(self, endpoint: str) -> Dict:
        self.counts[endpoint] = self.counts.get(endpoint, 0) + 1
        if endpoint not in self.timestamps:
            self.timestamps[endpoint] = []
        self.timestamps[endpoint].append(time.time())
        return {"endpoint": endpoint, "count": self.counts[endpoint]}
    
    def get_rate(self, endpoint: str) -> float:
        if endpoint not in self.timestamps or len(self.timestamps[endpoint]) < 2:
            return 0
        times = self.timestamps[endpoint]
        duration = times[-1] - times[0]
        return len(times) / duration if duration > 0 else 0
    
    def get_stats(self) -> Dict:
        return {"endpoints": len(self.counts), "total_requests": sum(self.counts.values())}

def main():
    print("📊 Request Counter")
    counter = RequestCounter()
    counter.increment("/api/users")
    counter.increment("/api/users")
    counter.increment("/api/products")
    print(f"✅ Stats: {counter.get_stats()}")

if __name__ == "__main__":
    main()
