#!/usr/bin/env python3
from typing import Dict, List

class EnumRegistry:
    def __init__(self):
        self.enums: Dict[str, List[str]] = {}
    
    def register(self, name: str, values: List[str]) -> None:
        self.enums[name] = values
    
    def get(self, name: str) -> List[str]:
        return self.enums.get(name, [])
    
    def has(self, name: str, value: str) -> bool:
        return value in self.enums.get(name, [])

def main():
    print("📋 Enum Registry")
    reg = EnumRegistry()
    reg.register("status", ["PENDING", "ACTIVE", "DONE"])
    print(f"✅ Status enum: {reg.get('status')}, Has ACTIVE: {reg.has('status', 'ACTIVE')}")

if __name__ == "__main__":
    main()
