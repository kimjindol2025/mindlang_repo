#!/usr/bin/env python3
from typing import Dict, List
import time

class FaultDetector:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.failure_counts: Dict[str, int] = {}
        self.faults: List[Dict] = []
    
    def record_failure(self, component: str) -> bool:
        self.failure_counts[component] = self.failure_counts.get(component, 0) + 1
        
        if self.failure_counts[component] >= self.threshold:
            fault = {"component": component, "timestamp": time.time()}
            self.faults.append(fault)
            return True
        return False
    
    def reset(self, component: str) -> None:
        self.failure_counts[component] = 0
    
    def get_stats(self) -> Dict:
        return {"faulty_components": len(self.faults)}

def main():
    print("🚨 Fault Detector")
    detector = FaultDetector(threshold=2)
    detector.record_failure("api")
    detector.record_failure("api")
    print(f"✅ Faults detected: {detector.get_stats()}")

if __name__ == "__main__":
    main()
