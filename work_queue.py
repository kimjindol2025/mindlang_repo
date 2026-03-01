#!/usr/bin/env python3
from typing import Dict, List
import time

class WorkQueue:
    def __init__(self):
        self.queue: List[Dict] = []
        self.processed: int = 0
    
    def enqueue_work(self, job_id: str, task: str) -> Dict:
        job = {"job_id": job_id, "task": task, "enqueued_at": time.time()}
        self.queue.append(job)
        return job
    
    def dequeue_work(self) -> Dict:
        if self.queue:
            job = self.queue.pop(0)
            self.processed += 1
            return job
        return None
    
    def get_stats(self) -> Dict:
        return {"pending_jobs": len(self.queue), "processed": self.processed}

def main():
    print("📦 Work Queue")
    queue = WorkQueue()
    queue.enqueue_work("job-001", "process_data")
    queue.enqueue_work("job-002", "send_email")
    queue.dequeue_work()
    print(f"✅ Stats: {queue.get_stats()}")

if __name__ == "__main__":
    main()
