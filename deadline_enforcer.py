#!/usr/bin/env python3
from typing import Dict, List
import time

class DeadlineEnforcer:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
    
    def create_task(self, task_id: str, deadline: float) -> Dict:
        self.tasks[task_id] = {
            "deadline": deadline,
            "created_at": time.time(),
            "status": "ACTIVE"
        }
        return self.tasks[task_id]
    
    def check_deadline(self, task_id: str) -> Dict:
        if task_id not in self.tasks:
            return {"exists": False}
        
        task = self.tasks[task_id]
        now = time.time()
        exceeded = now > task["deadline"]
        remaining = max(0, task["deadline"] - now)
        
        return {
            "task_id": task_id,
            "exceeded": exceeded,
            "remaining_seconds": remaining,
            "status": "EXCEEDED" if exceeded else "ACTIVE"
        }
    
    def complete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "COMPLETED"
            return True
        return False
    
    def get_stats(self) -> Dict:
        exceeded = sum(1 for t in self.tasks.values() if time.time() > t["deadline"])
        return {"total_tasks": len(self.tasks), "exceeded_deadlines": exceeded}

def main():
    print("⏱️  Deadline Enforcer")
    enforcer = DeadlineEnforcer()
    future_deadline = time.time() + 3600
    enforcer.create_task("task-001", future_deadline)
    check = enforcer.check_deadline("task-001")
    print(f"✅ Exceeded: {check['exceeded']}, Remaining: {check['remaining_seconds']:.0f}s, Stats: {enforcer.get_stats()}")

if __name__ == "__main__":
    main()
