#!/usr/bin/env python3
from typing import Dict, List
import time

class ConnectorPool:
    def __init__(self, size: int):
        self.size = size
        self.available: int = size
        self.connections: List[Dict] = []
    
    def acquire(self) -> Dict:
        if self.available > 0:
            conn = {"id": len(self.connections) + 1, "acquired_at": time.time()}
            self.connections.append(conn)
            self.available -= 1
            return conn
        return None
    
    def release(self, conn_id: int) -> bool:
        self.connections = [c for c in self.connections if c["id"] != conn_id]
        self.available += 1
        return True
    
    def get_stats(self) -> Dict:
        return {"pool_size": self.size, "available": self.available, "active": len(self.connections)}

def main():
    print("🔌 Connector Pool")
    pool = ConnectorPool(10)
    conn1 = pool.acquire()
    conn2 = pool.acquire()
    print(f"✅ Acquired 2 connections, Stats: {pool.get_stats()}")

if __name__ == "__main__":
    main()
