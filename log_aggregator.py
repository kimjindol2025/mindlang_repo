#!/usr/bin/env python3
from typing import Dict, List
import time

class LogAggregator:
    def __init__(self):
        self.logs: List[Dict] = []
    
    def add_log(self, level: str, service: str, message: str) -> Dict:
        log = {"level": level, "service": service, "message": message, "timestamp": time.time()}
        self.logs.append(log)
        return log
    
    def filter_by_level(self, level: str) -> List[Dict]:
        return [l for l in self.logs if l["level"] == level]
    
    def filter_by_service(self, service: str) -> List[Dict]:
        return [l for l in self.logs if l["service"] == service]
    
    def get_stats(self) -> Dict:
        levels = {}
        for l in self.logs:
            levels[l["level"]] = levels.get(l["level"], 0) + 1
        return {"total_logs": len(self.logs), "by_level": levels}

def main():
    print("📝 Log Aggregator")
    agg = LogAggregator()
    agg.add_log("ERROR", "api", "Connection timeout")
    agg.add_log("INFO", "db", "Query executed")
    print(f"✅ Stats: {agg.get_stats()}")

if __name__ == "__main__":
    main()
