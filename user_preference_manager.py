#!/usr/bin/env python3
from typing import Dict
import json
import time

class UserPreferenceManager:
    def __init__(self):
        self.preferences: Dict[str, Dict] = {}
    
    def set_preference(self, user_id: str, key: str, value: str) -> Dict:
        if user_id not in self.preferences:
            self.preferences[user_id] = {}
        
        self.preferences[user_id][key] = {
            "value": value,
            "updated_at": time.time()
        }
        return self.preferences[user_id][key]
    
    def get_preference(self, user_id: str, key: str, default=None):
        if user_id in self.preferences and key in self.preferences[user_id]:
            return self.preferences[user_id][key]["value"]
        return default
    
    def get_user_preferences(self, user_id: str) -> Dict:
        if user_id not in self.preferences:
            return {}
        return {k: v["value"] for k, v in self.preferences[user_id].items()}
    
    def export_preferences(self, user_id: str) -> str:
        return json.dumps(self.get_user_preferences(user_id), indent=2)
    
    def get_stats(self) -> Dict:
        total_prefs = sum(len(prefs) for prefs in self.preferences.values())
        return {"users": len(self.preferences), "total_preferences": total_prefs}

def main():
    print("⚙️  User Preference Manager")
    mgr = UserPreferenceManager()
    mgr.set_preference("user1", "theme", "dark")
    mgr.set_preference("user1", "language", "en")
    prefs = mgr.get_user_preferences("user1")
    print(f"✅ Preferences: {prefs}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
