#!/usr/bin/env python3
from typing import Dict, Tuple

class PairCache:
    def __init__(self):
        self.pairs: Dict[str, str] = {}
    
    def store(self, key: str, value: str) -> None:
        self.pairs[key] = value
    
    def retrieve(self, key: str) -> str:
        return self.pairs.get(key)
    
    def size(self) -> int:
        return len(self.pairs)

def main():
    print("🔑 Pair Cache")
    pc = PairCache()
    pc.store("user", "john")
    pc.store("role", "admin")
    print(f"✅ User: {pc.retrieve('user')}, Size: {pc.size()}")

if __name__ == "__main__":
    main()
