#!/usr/bin/env python3
from typing import Dict, List
import time

class TransactionLog:
    def __init__(self):
        self.logs: List[Dict] = []
    
    def log_transaction(self, tx_id: str, operation: str, status: str) -> Dict:
        log_entry = {"tx_id": tx_id, "operation": operation, "status": status, "timestamp": time.time()}
        self.logs.append(log_entry)
        return log_entry
    
    def get_transaction_history(self, tx_id: str) -> List[Dict]:
        return [l for l in self.logs if l["tx_id"] == tx_id]
    
    def rollback_to(self, tx_id: str) -> bool:
        return len(self.get_transaction_history(tx_id)) > 0
    
    def get_stats(self) -> Dict:
        return {"total_logs": len(self.logs), "unique_transactions": len(set(l["tx_id"] for l in self.logs))}

def main():
    print("📋 Transaction Log")
    log = TransactionLog()
    log.log_transaction("tx-001", "INSERT", "COMMITTED")
    log.log_transaction("tx-001", "UPDATE", "COMMITTED")
    print(f"✅ TX-001 History: {len(log.get_transaction_history('tx-001'))}, Stats: {log.get_stats()}")

if __name__ == "__main__":
    main()
