#!/usr/bin/env python3
from typing import Dict, List
import time

class AlertAggregator:
    def __init__(self):
        self.alerts: List[Dict] = []
        self.aggregated: Dict[str, int] = {}
    
    def add_alert(self, source: str, severity: str, message: str) -> Dict:
        alert = {
            "source": source,
            "severity": severity,
            "message": message,
            "timestamp": time.time()
        }
        self.alerts.append(alert)
        
        key = f"{source}:{severity}"
        self.aggregated[key] = self.aggregated.get(key, 0) + 1
        
        return alert
    
    def get_aggregated_alerts(self) -> Dict:
        return dict(self.aggregated)
    
    def get_critical_alerts(self) -> List[Dict]:
        return [a for a in self.alerts if a["severity"] == "CRITICAL"]
    
    def get_stats(self) -> Dict:
        return {
            "total_alerts": len(self.alerts),
            "critical": len(self.get_critical_alerts()),
            "unique_sources": len(set(a["source"] for a in self.alerts))
        }

def main():
    print("🚨 Alert Aggregator")
    agg = AlertAggregator()
    agg.add_alert("api", "ERROR", "Timeout")
    agg.add_alert("db", "CRITICAL", "Connection failed")
    agg.add_alert("api", "WARNING", "Slow query")
    print(f"✅ Aggregated: {agg.get_aggregated_alerts()}, Stats: {agg.get_stats()}")

if __name__ == "__main__":
    main()
