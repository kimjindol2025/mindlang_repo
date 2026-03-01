#!/usr/bin/env python3
from typing import Dict, List
import time

class MessageQueueManager:
    def __init__(self):
        self.queues: Dict[str, List[Dict]] = {}
    
    def create_queue(self, queue_name: str) -> Dict:
        self.queues[queue_name] = []
        return {"queue": queue_name, "created_at": time.time()}
    
    def enqueue(self, queue_name: str, message: str, priority: int = 0) -> Dict:
        if queue_name not in self.queues:
            self.create_queue(queue_name)
        msg = {"body": message, "priority": priority, "timestamp": time.time()}
        self.queues[queue_name].append(msg)
        return msg
    
    def dequeue(self, queue_name: str) -> Dict:
        if queue_name in self.queues and self.queues[queue_name]:
            return self.queues[queue_name].pop(0)
        return None
    
    def get_stats(self) -> Dict:
        total_msgs = sum(len(msgs) for msgs in self.queues.values())
        return {"queues": len(self.queues), "total_messages": total_msgs}

def main():
    print("📬 Message Queue Manager")
    mgr = MessageQueueManager()
    mgr.enqueue("events", "Order placed")
    mgr.enqueue("events", "Payment confirmed")
    print(f"✅ Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
