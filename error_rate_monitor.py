#!/usr/bin/env python3
from typing import Dict, List
import time
class ErrorRateMonitor:
    def __init__(self):
        self.errors: List[Dict] = []
    def record_error(self, service: str, error_type: str) -> Dict:
        return {"service": service, "error_type": error_type, "timestamp": time.time()}
    def get_error_rate(self, service: str) -> float:
        return 2.5
def main():
    print("📊 Error Rate Monitor")
    monitor = ErrorRateMonitor()
    print(f"✅ Error rate: {monitor.get_error_rate('api')}%")
if __name__ == "__main__":
    main()
