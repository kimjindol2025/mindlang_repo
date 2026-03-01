#!/usr/bin/env python3
from typing import Dict, List
import time

class RecommendationEngine:
    def __init__(self):
        self.user_behaviors: Dict[str, List[str]] = {}
        self.item_features: Dict[str, List[str]] = {}
    
    def record_interaction(self, user_id: str, item_id: str) -> None:
        if user_id not in self.user_behaviors:
            self.user_behaviors[user_id] = []
        self.user_behaviors[user_id].append(item_id)
    
    def register_item(self, item_id: str, features: List[str]) -> Dict:
        self.item_features[item_id] = features
        return {"item_id": item_id, "features": features}
    
    def get_recommendations(self, user_id: str, count: int = 5) -> List[str]:
        if user_id not in self.user_behaviors:
            return []
        
        user_items = set(self.user_behaviors[user_id])
        recommendations = []
        
        for item_id in self.item_features:
            if item_id not in user_items:
                recommendations.append(item_id)
        
        return recommendations[:count]
    
    def get_stats(self) -> Dict:
        return {"users": len(self.user_behaviors), "items": len(self.item_features)}

def main():
    print("🎯 Recommendation Engine")
    engine = RecommendationEngine()
    engine.register_item("item-1", ["tech", "book"])
    engine.register_item("item-2", ["tech", "video"])
    engine.record_interaction("user1", "item-1")
    recs = engine.get_recommendations("user1")
    print(f"✅ Recommendations: {recs}, Stats: {engine.get_stats()}")

if __name__ == "__main__":
    main()
