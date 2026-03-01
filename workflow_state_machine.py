#!/usr/bin/env python3
from typing import Dict, List
import time

class WorkflowStateMachine:
    def __init__(self):
        self.workflows: Dict[str, Dict] = {}
        self.transitions: Dict[str, List[str]] = {}
    
    def create_workflow(self, workflow_id: str, initial_state: str) -> Dict:
        self.workflows[workflow_id] = {
            "state": initial_state,
            "created_at": time.time(),
            "history": [initial_state]
        }
        return self.workflows[workflow_id]
    
    def define_transition(self, from_state: str, to_state: str) -> None:
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        self.transitions[from_state].append(to_state)
    
    def transition(self, workflow_id: str, to_state: str) -> bool:
        if workflow_id not in self.workflows:
            return False
        workflow = self.workflows[workflow_id]
        current = workflow["state"]
        if to_state in self.transitions.get(current, []):
            workflow["state"] = to_state
            workflow["history"].append(to_state)
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"total_workflows": len(self.workflows), "transitions": len(self.transitions)}

def main():
    print("🔄 Workflow State Machine")
    sm = WorkflowStateMachine()
    sm.define_transition("PENDING", "APPROVED")
    sm.define_transition("APPROVED", "COMPLETED")
    sm.create_workflow("wf-001", "PENDING")
    sm.transition("wf-001", "APPROVED")
    print(f"✅ Stats: {sm.get_stats()}")

if __name__ == "__main__":
    main()
