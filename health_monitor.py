#!/usr/bin/env python3
from typing import Dict
import time

class HealthMonitor:
    def __init__(self):
        self.health_checks: Dict[str, Dict] = {}
    
    def register_check(self, name: str, interval: int) -> Dict:
        self.health_checks[name] = {
            "interval": interval,
            "last_check": time.time(),
            "status": "UP"
        }
        return self.health_checks[name]
    
    def check_health(self, name: str, status: str) -> Dict:
        if name in self.health_checks:
            self.health_checks[name]["status"] = status
            self.health_checks[name]["last_check"] = time.time()
            return self.health_checks[name]
        return None
    
    def get_stats(self) -> Dict:
        up = sum(1 for c in self.health_checks.values() if c["status"] == "UP")
        return {"checks": len(self.health_checks), "healthy": up}

def main():
    print("💚 Health Monitor")
    monitor = HealthMonitor()
    monitor.register_check("api", 30)
    monitor.register_check("db", 60)
    monitor.check_health("api", "UP")
    print(f"✅ Stats: {monitor.get_stats()}")

if __name__ == "__main__":
    main()
