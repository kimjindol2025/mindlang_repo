#!/usr/bin/env python3
from typing import Dict, List
import time

class DisasterRecoveryPlanner:
    def __init__(self):
        self.recovery_plans: Dict[str, Dict] = {}
        self.test_results: List[Dict] = []
    
    def create_plan(self, plan_id: str, rto_minutes: int, rpo_minutes: int) -> Dict:
        self.recovery_plans[plan_id] = {
            "rto": rto_minutes,
            "rpo": rpo_minutes,
            "created_at": time.time(),
            "tested": False
        }
        return self.recovery_plans[plan_id]
    
    def test_plan(self, plan_id: str) -> Dict:
        if plan_id not in self.recovery_plans:
            return {"success": False}
        
        result = {
            "plan_id": plan_id,
            "test_duration": 30,
            "success": True,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        self.recovery_plans[plan_id]["tested"] = True
        return result
    
    def get_stats(self) -> Dict:
        tested = sum(1 for p in self.recovery_plans.values() if p["tested"])
        return {"total_plans": len(self.recovery_plans), "tested": tested}

def main():
    print("🆘 Disaster Recovery Planner")
    planner = DisasterRecoveryPlanner()
    planner.create_plan("plan-001", 4, 1)
    planner.test_plan("plan-001")
    print(f"✅ Stats: {planner.get_stats()}")

if __name__ == "__main__":
    main()
