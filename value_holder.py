#!/usr/bin/env python3
import time

class ValueHolder:
    def __init__(self, initial=None):
        self.value = initial
        self.updated_at = time.time()
    
    def set(self, val):
        self.value = val
        self.updated_at = time.time()
    
    def get(self):
        return self.value

def main():
    print("📦 Value Holder")
    holder = ValueHolder(42)
    holder.set(100)
    print(f"✅ Value: {holder.get()}")

if __name__ == "__main__":
    main()
