#!/usr/bin/env python3
from typing import Dict
import time

class ContextManager:
    def __init__(self):
        self.contexts: Dict[str, Dict] = {}
    
    def create_context(self, ctx_id: str) -> Dict:
        self.contexts[ctx_id] = {
            "created_at": time.time(),
            "data": {},
            "active": True
        }
        return self.contexts[ctx_id]
    
    def set_value(self, ctx_id: str, key: str, value) -> bool:
        if ctx_id in self.contexts:
            self.contexts[ctx_id]["data"][key] = value
            return True
        return False
    
    def get_value(self, ctx_id: str, key: str):
        if ctx_id in self.contexts:
            return self.contexts[ctx_id]["data"].get(key)
        return None
    
    def get_stats(self) -> Dict:
        return {"active_contexts": len(self.contexts)}

def main():
    print("📍 Context Manager")
    mgr = ContextManager()
    mgr.create_context("ctx-001")
    mgr.set_value("ctx-001", "user_id", "user123")
    print(f"✅ Value: {mgr.get_value('ctx-001', 'user_id')}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
