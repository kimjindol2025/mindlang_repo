#!/usr/bin/env python3
from typing import Dict, List
import time

class PriorityQueue:
    def __init__(self):
        self.queue: List[Dict] = []
    
    def enqueue(self, item: str, priority: int) -> Dict:
        entry = {"item": item, "priority": priority, "timestamp": time.time()}
        self.queue.append(entry)
        self.queue.sort(key=lambda x: -x["priority"])
        return entry
    
    def dequeue(self) -> Dict:
        return self.queue.pop(0) if self.queue else None
    
    def peek(self) -> Dict:
        return self.queue[0] if self.queue else None
    
    def get_stats(self) -> Dict:
        return {"items": len(self.queue)}

def main():
    print("⭐ Priority Queue")
    pq = PriorityQueue()
    pq.enqueue("task1", 5)
    pq.enqueue("urgent", 10)
    pq.enqueue("task2", 3)
    print(f"✅ Next: {pq.peek()['item']}, Stats: {pq.get_stats()}")

if __name__ == "__main__":
    main()
