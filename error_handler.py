#!/usr/bin/env python3
from typing import Dict, List
import time

class ErrorHandler:
    def __init__(self):
        self.errors: List[Dict] = []
        self.handlers: Dict[str, str] = {}
    
    def register_handler(self, error_type: str, handler: str) -> Dict:
        self.handlers[error_type] = handler
        return {"error_type": error_type, "handler": handler}
    
    def handle_error(self, error_type: str, message: str) -> Dict:
        error = {
            "type": error_type,
            "message": message,
            "handler": self.handlers.get(error_type, "default"),
            "timestamp": time.time()
        }
        self.errors.append(error)
        return error
    
    def get_stats(self) -> Dict:
        return {"handlers": len(self.handlers), "errors_handled": len(self.errors)}

def main():
    print("🚨 Error Handler")
    handler = ErrorHandler()
    handler.register_handler("timeout", "retry")
    handler.register_handler("not_found", "log")
    handler.handle_error("timeout", "Connection timeout")
    print(f"✅ Stats: {handler.get_stats()}")

if __name__ == "__main__":
    main()
