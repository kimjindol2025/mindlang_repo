#!/usr/bin/env python3
from typing import Dict, List
import time

class TaskScheduler:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
    
    def schedule_task(self, task_id: str, scheduled_time: float) -> Dict:
        self.tasks[task_id] = {
            "scheduled_at": scheduled_time,
            "created_at": time.time(),
            "executed": False
        }
        return self.tasks[task_id]
    
    def get_due_tasks(self) -> List[str]:
        now = time.time()
        return [tid for tid, task in self.tasks.items() if task["scheduled_at"] <= now and not task["executed"]]
    
    def mark_executed(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id]["executed"] = True
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"scheduled": len(self.tasks), "executed": sum(1 for t in self.tasks.values() if t["executed"])}

def main():
    print("⏰ Task Scheduler")
    scheduler = TaskScheduler()
    scheduler.schedule_task("task-001", time.time() - 10)
    scheduler.schedule_task("task-002", time.time() + 100)
    due = scheduler.get_due_tasks()
    print(f"✅ Due tasks: {len(due)}, Stats: {scheduler.get_stats()}")

if __name__ == "__main__":
    main()
