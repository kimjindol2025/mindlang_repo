#!/usr/bin/env python3
from typing import Dict, List
import time

class HealthCheckReporter:
    def __init__(self):
        self.checks: List[Dict] = []
    
    def add_check_result(self, service: str, status: str, latency: float) -> Dict:
        result = {
            "service": service,
            "status": status,
            "latency": latency,
            "timestamp": time.time()
        }
        self.checks.append(result)
        return result
    
    def get_service_health(self, service: str) -> Dict:
        service_checks = [c for c in self.checks if c["service"] == service]
        if not service_checks:
            return {"service": service, "status": "UNKNOWN"}
        recent = service_checks[-1]
        return {
            "service": service,
            "status": recent["status"],
            "avg_latency": sum(c["latency"] for c in service_checks) / len(service_checks)
        }
    
    def generate_report(self) -> Dict:
        services = set(c["service"] for c in self.checks)
        health_summary = {}
        for svc in services:
            health_summary[svc] = self.get_service_health(svc)["status"]
        return {"total_checks": len(self.checks), "services": list(services), "health": health_summary}

def main():
    print("🏥 Health Check Reporter")
    reporter = HealthCheckReporter()
    reporter.add_check_result("api", "UP", 45.2)
    reporter.add_check_result("db", "UP", 12.5)
    print(f"✅ Report: {reporter.generate_report()}")

if __name__ == "__main__":
    main()
