#!/usr/bin/env python3
from typing import Dict

class ThresholdChecker:
    def __init__(self):
        self.thresholds: Dict[str, float] = {}
    
    def set_threshold(self, name: str, value: float) -> None:
        self.thresholds[name] = value
    
    def check(self, name: str, value: float) -> bool:
        if name in self.thresholds:
            return value < self.thresholds[name]
        return False
    
    def exceed(self, name: str, value: float) -> bool:
        if name in self.thresholds:
            return value > self.thresholds[name]
        return False

def main():
    print("📏 Threshold Checker")
    tc = ThresholdChecker()
    tc.set_threshold("cpu", 80)
    print(f"✅ CPU 75 < 80: {tc.check('cpu', 75)}, CPU 85 > 80: {tc.exceed('cpu', 85)}")

if __name__ == "__main__":
    main()
