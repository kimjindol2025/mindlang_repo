#!/usr/bin/env python3
from typing import List

class ObjectPool:
    def __init__(self, size: int):
        self.available: List = [f"obj-{i}" for i in range(size)]
        self.inuse: List = []
    
    def acquire(self):
        if self.available:
            obj = self.available.pop(0)
            self.inuse.append(obj)
            return obj
        return None
    
    def release(self, obj):
        if obj in self.inuse:
            self.inuse.remove(obj)
            self.available.append(obj)
            return True
        return False

def main():
    print("🔄 Object Pool")
    pool = ObjectPool(5)
    obj1 = pool.acquire()
    obj2 = pool.acquire()
    pool.release(obj1)
    print(f"✅ Acquired 2, Released 1")

if __name__ == "__main__":
    main()
