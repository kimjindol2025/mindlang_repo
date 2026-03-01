#!/usr/bin/env python3

class SequenceGenerator:
    def __init__(self, start: int = 1):
        self.counter = start
    
    def next(self) -> int:
        val = self.counter
        self.counter += 1
        return val
    
    def current(self) -> int:
        return self.counter - 1
    
    def reset(self) -> None:
        self.counter = 1

def main():
    print("🔢 Sequence Generator")
    gen = SequenceGenerator(100)
    print(f"✅ Seq: {gen.next()}, {gen.next()}, {gen.next()}, Current: {gen.current()}")

if __name__ == "__main__":
    main()
