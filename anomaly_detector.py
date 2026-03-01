#!/usr/bin/env python3
from typing import List, Dict
import time

class AnomalyDetector:
    def __init__(self):
        self.data_points: List[float] = []
        self.anomalies: List[Dict] = []
    
    def add_datapoint(self, value: float) -> None:
        self.data_points.append(value)
    
    def detect_anomalies(self, threshold: float = 2.0) -> List[Dict]:
        if len(self.data_points) < 2:
            return []
        
        mean = sum(self.data_points) / len(self.data_points)
        variance = sum((x - mean) ** 2 for x in self.data_points) / len(self.data_points)
        stddev = variance ** 0.5
        
        self.anomalies = [
            {"value": p, "timestamp": time.time(), "sigma": abs((p - mean) / stddev) if stddev > 0 else 0}
            for p in self.data_points if abs(p - mean) > threshold * stddev
        ]
        return self.anomalies
    
    def get_stats(self) -> Dict:
        return {"total_points": len(self.data_points), "anomalies_found": len(self.anomalies)}

def main():
    print("🚨 Anomaly Detector")
    detector = AnomalyDetector()
    for val in [100, 105, 102, 103, 450, 101]:
        detector.add_datapoint(val)
    anomalies = detector.detect_anomalies(1.5)
    print(f"✅ Stats: {detector.get_stats()}")

if __name__ == "__main__":
    main()
