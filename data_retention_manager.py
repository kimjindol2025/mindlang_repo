#!/usr/bin/env python3
from typing import Dict, List
import time

class DataRetentionManager:
    def __init__(self):
        self.policies: Dict[str, Dict] = {}
        self.records: List[Dict] = []
    
    def create_policy(self, policy_name: str, retention_days: int) -> Dict:
        self.policies[policy_name] = {
            "retention_days": retention_days,
            "created_at": time.time()
        }
        return self.policies[policy_name]
    
    def add_record(self, data_type: str, data: str, policy: str) -> Dict:
        record = {
            "id": len(self.records) + 1,
            "data_type": data_type,
            "data": data,
            "policy": policy,
            "created_at": time.time()
        }
        self.records.append(record)
        return record
    
    def cleanup_expired(self) -> int:
        now = time.time()
        initial_count = len(self.records)
        
        self.records = [
            r for r in self.records
            if (now - r["created_at"]) / 86400 < self.policies.get(r["policy"], {}).get("retention_days", 365)
        ]
        
        return initial_count - len(self.records)
    
    def get_stats(self) -> Dict:
        return {"policies": len(self.policies), "records": len(self.records)}

def main():
    print("🗄️  Data Retention Manager")
    mgr = DataRetentionManager()
    mgr.create_policy("logs", 30)
    mgr.add_record("log", "error log", "logs")
    deleted = mgr.cleanup_expired()
    print(f"✅ Deleted: {deleted}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
