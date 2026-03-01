#!/usr/bin/env python3

class SimpleCounter:
    def __init__(self):
        self.count = 0
    
    def increment(self) -> int:
        self.count += 1
        return self.count
    
    def decrement(self) -> int:
        self.count -= 1
        return self.count
    
    def reset(self) -> None:
        self.count = 0

def main():
    print("🔢 Simple Counter")
    counter = SimpleCounter()
    counter.increment()
    counter.increment()
    print(f"✅ Count: {counter.count}")

if __name__ == "__main__":
    main()
