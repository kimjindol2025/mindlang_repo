#!/usr/bin/env python3
from typing import Dict, List
import time

class EventProcessor:
    def __init__(self):
        self.events: List[Dict] = []
        self.processed: int = 0
    
    def add_event(self, event_type: str, data: str) -> Dict:
        event = {"type": event_type, "data": data, "timestamp": time.time()}
        self.events.append(event)
        return event
    
    def process_events(self) -> int:
        count = len(self.events)
        self.processed += count
        self.events = []
        return count
    
    def get_stats(self) -> Dict:
        return {"pending_events": len(self.events), "total_processed": self.processed}

def main():
    print("⚙️  Event Processor")
    processor = EventProcessor()
    processor.add_event("click", "button_clicked")
    processor.add_event("load", "page_loaded")
    count = processor.process_events()
    print(f"✅ Processed {count} events, Stats: {processor.get_stats()}")

if __name__ == "__main__":
    main()
