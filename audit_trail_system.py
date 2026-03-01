#!/usr/bin/env python3
from typing import Dict, List
import time
import json

class AuditTrailSystem:
    def __init__(self):
        self.trails: List[Dict] = []
    
    def log_action(self, user_id: str, action: str, resource: str, details: Dict) -> Dict:
        trail = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details,
            "timestamp": time.time(),
            "id": len(self.trails) + 1
        }
        self.trails.append(trail)
        return trail
    
    def get_user_trails(self, user_id: str) -> List[Dict]:
        return [t for t in self.trails if t["user_id"] == user_id]
    
    def get_resource_trails(self, resource: str) -> List[Dict]:
        return [t for t in self.trails if t["resource"] == resource]
    
    def export_trails(self) -> str:
        return json.dumps(self.trails, indent=2, default=str)
    
    def get_stats(self) -> Dict:
        return {"total_trails": len(self.trails), "users": len(set(t["user_id"] for t in self.trails))}

def main():
    print("📋 Audit Trail System")
    audit = AuditTrailSystem()
    audit.log_action("user1", "CREATE", "document", {"doc_id": "doc-123"})
    audit.log_action("user1", "UPDATE", "document", {"doc_id": "doc-123"})
    print(f"✅ User Trails: {len(audit.get_user_trails('user1'))}, Stats: {audit.get_stats()}")

if __name__ == "__main__":
    main()
