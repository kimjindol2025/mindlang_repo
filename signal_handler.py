#!/usr/bin/env python3
from typing import Dict, Callable
import time

class SignalHandler:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.signals: Dict[str, int] = {}
    
    def register(self, signal_type: str, handler: Callable) -> None:
        self.handlers[signal_type] = handler
        self.signals[signal_type] = 0
    
    def emit(self, signal_type: str) -> bool:
        if signal_type in self.handlers:
            self.signals[signal_type] += 1
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"registered": len(self.handlers), "total_signals": sum(self.signals.values())}

def main():
    print("📡 Signal Handler")
    sh = SignalHandler()
    sh.register("click", lambda: print("clicked"))
    sh.emit("click")
    sh.emit("click")
    print(f"✅ Stats: {sh.get_stats()}")

if __name__ == "__main__":
    main()
