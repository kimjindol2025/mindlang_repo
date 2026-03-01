#!/usr/bin/env python3
from typing import Dict, List
import time

class FeatureUsageTracker:
    def __init__(self):
        self.features: Dict[str, List[Dict]] = {}
    
    def track_usage(self, feature_name: str, user_id: str, success: bool) -> Dict:
        if feature_name not in self.features:
            self.features[feature_name] = []
        
        usage = {
            "user_id": user_id,
            "success": success,
            "timestamp": time.time()
        }
        self.features[feature_name].append(usage)
        return usage
    
    def get_feature_stats(self, feature_name: str) -> Dict:
        if feature_name not in self.features:
            return {"feature": feature_name, "usages": 0}
        
        usages = self.features[feature_name]
        successful = sum(1 for u in usages if u["success"])
        
        return {
            "feature": feature_name,
            "total_usages": len(usages),
            "successful": successful,
            "success_rate": (successful / len(usages) * 100) if usages else 0
        }
    
    def get_stats(self) -> Dict:
        total_usages = sum(len(u) for u in self.features.values())
        return {"tracked_features": len(self.features), "total_usages": total_usages}

def main():
    print("📊 Feature Usage Tracker")
    tracker = FeatureUsageTracker()
    tracker.track_usage("export_pdf", "user1", True)
    tracker.track_usage("export_pdf", "user2", True)
    stats = tracker.get_feature_stats("export_pdf")
    print(f"✅ Success Rate: {stats['success_rate']:.1f}%, Stats: {tracker.get_stats()}")

if __name__ == "__main__":
    main()
