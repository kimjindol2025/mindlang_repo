#!/usr/bin/env python3
from typing import List, Dict
import time
import json

class EventLogManager:
    def __init__(self):
        self.events: List[Dict] = []
    
    def log_event(self, event_type: str, source: str, details: str) -> Dict:
        event = {
            "id": len(self.events) + 1,
            "type": event_type,
            "source": source,
            "details": details,
            "timestamp": time.time()
        }
        self.events.append(event)
        return event
    
    def filter_events(self, event_type: str) -> List[Dict]:
        return [e for e in self.events if e["type"] == event_type]
    
    def get_stats(self) -> Dict:
        event_types = {}
        for e in self.events:
            event_types[e["type"]] = event_types.get(e["type"], 0) + 1
        return {"total_events": len(self.events), "by_type": event_types}
    
    def export_logs(self) -> str:
        return json.dumps(self.events, indent=2, default=str)

def main():
    print("📝 Event Log Manager")
    manager = EventLogManager()
    manager.log_event("ERROR", "api", "Connection timeout")
    manager.log_event("INFO", "worker", "Task completed")
    print(f"✅ Stats: {manager.get_stats()}")

if __name__ == "__main__":
    main()
