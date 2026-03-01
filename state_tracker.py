#!/usr/bin/env python3
from typing import Dict
import time

class StateTracker:
    def __init__(self):
        self.states: Dict[str, Dict] = {}
    
    def track_state(self, entity_id: str, state: str) -> Dict:
        self.states[entity_id] = {
            "current": state,
            "updated_at": time.time(),
            "history": [state]
        }
        return self.states[entity_id]
    
    def update_state(self, entity_id: str, new_state: str) -> bool:
        if entity_id in self.states:
            self.states[entity_id]["current"] = new_state
            self.states[entity_id]["updated_at"] = time.time()
            self.states[entity_id]["history"].append(new_state)
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"tracked_entities": len(self.states)}

def main():
    print("📊 State Tracker")
    tracker = StateTracker()
    tracker.track_state("order-001", "PENDING")
    tracker.update_state("order-001", "PROCESSING")
    tracker.update_state("order-001", "COMPLETED")
    print(f"✅ State: {tracker.states['order-001']['current']}, Stats: {tracker.get_stats()}")

if __name__ == "__main__":
    main()
