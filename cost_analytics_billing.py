#!/usr/bin/env python3
"""Cost Analytics and Billing - Cloud cost tracking and optimization"""
from typing import Dict, List
import json, time

class CostAnalyticsBilling:
    def __init__(self):
        self.costs: List[Dict] = []
    
    def record_cost(self, service: str, amount: float) -> Dict:
        cost = {"service": service, "amount": amount, "timestamp": time.time()}
        self.costs.append(cost)
        return cost
    
    def get_total_cost(self) -> float:
        return sum(c["amount"] for c in self.costs)
    
    def get_stats(self) -> Dict:
        return {"total_cost": self.get_total_cost(), "records": len(self.costs)}

def main():
    print("💰 Cost Analytics and Billing")
    system = CostAnalyticsBilling()
    system.record_cost("ec2", 150.0)
    system.record_cost("s3", 45.0)
    print(f"✅ Total cost: ${system.get_total_cost()}")

if __name__ == "__main__":
    main()
