#!/usr/bin/env python3
from typing import Dict, List
import time

class AvailabilityCalculator:
    def __init__(self):
        self.service_history: List[Dict] = []
    
    def record_status(self, service: str, available: bool, duration: float) -> Dict:
        record = {
            "service": service,
            "available": available,
            "duration": duration,
            "timestamp": time.time()
        }
        self.service_history.append(record)
        return record
    
    def calculate_uptime(self, service: str) -> Dict:
        records = [r for r in self.service_history if r["service"] == service]
        if not records:
            return {"service": service, "uptime_percent": 0}
        
        total_time = sum(r["duration"] for r in records)
        available_time = sum(r["duration"] for r in records if r["available"])
        uptime_percent = (available_time / total_time * 100) if total_time > 0 else 0
        
        return {
            "service": service,
            "uptime_percent": round(uptime_percent, 2),
            "samples": len(records)
        }
    
    def get_stats(self) -> Dict:
        services = set(r["service"] for r in self.service_history)
        return {"services": list(services), "total_records": len(self.service_history)}

def main():
    print("⏱️  Availability Calculator")
    calc = AvailabilityCalculator()
    calc.record_status("api", True, 3600)
    calc.record_status("api", False, 120)
    calc.record_status("api", True, 3600)
    uptime = calc.calculate_uptime("api")
    print(f"✅ API Uptime: {uptime['uptime_percent']}%")

if __name__ == "__main__":
    main()
