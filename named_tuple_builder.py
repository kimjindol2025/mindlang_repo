#!/usr/bin/env python3
from typing import Dict, Any

class NamedTupleBuilder:
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    def add(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def get(self, key: str) -> Any:
        return self.data.get(key)
    
    def build(self) -> Dict:
        return dict(self.data)

def main():
    print("🏗️  Named Tuple Builder")
    builder = NamedTupleBuilder()
    builder.add("id", 123)
    builder.add("name", "Test")
    print(f"✅ Built: {builder.build()}")

if __name__ == "__main__":
    main()
