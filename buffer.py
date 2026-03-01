#!/usr/bin/env python3
from typing import List

class Buffer:
    def __init__(self, size: int):
        self.size = size
        self.data: List = []
    
    def write(self, item) -> bool:
        if len(self.data) < self.size:
            self.data.append(item)
            return True
        return False
    
    def read(self):
        return self.data.pop(0) if self.data else None
    
    def get_stats(self) -> dict:
        return {"capacity": self.size, "current": len(self.data), "available": self.size - len(self.data)}

def main():
    print("🔲 Buffer")
    buf = Buffer(10)
    buf.write("item1")
    buf.write("item2")
    print(f"✅ Stats: {buf.get_stats()}")

if __name__ == "__main__":
    main()
