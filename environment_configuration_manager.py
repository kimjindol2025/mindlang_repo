#!/usr/bin/env python3
from typing import Dict
import json
import time

class EnvironmentConfigurationManager:
    def __init__(self):
        self.environments: Dict[str, Dict] = {}
        self.configs: Dict[str, Dict] = {}
    
    def create_environment(self, env_name: str) -> Dict:
        self.environments[env_name] = {"created_at": time.time()}
        self.configs[env_name] = {}
        return self.environments[env_name]
    
    def set_config(self, env_name: str, key: str, value: str) -> Dict:
        if env_name not in self.configs:
            self.create_environment(env_name)
        
        self.configs[env_name][key] = {"value": value, "updated_at": time.time()}
        return self.configs[env_name][key]
    
    def get_config(self, env_name: str, key: str):
        if env_name in self.configs and key in self.configs[env_name]:
            return self.configs[env_name][key]["value"]
        return None
    
    def export_config(self, env_name: str) -> str:
        config = {k: v["value"] for k, v in self.configs.get(env_name, {}).items()}
        return json.dumps(config, indent=2)
    
    def get_stats(self) -> Dict:
        return {"environments": len(self.environments), "total_configs": sum(len(c) for c in self.configs.values())}

def main():
    print("⚙️  Environment Configuration Manager")
    mgr = EnvironmentConfigurationManager()
    mgr.create_environment("production")
    mgr.set_config("production", "database_url", "postgres://prod.db")
    mgr.set_config("production", "api_key", "***")
    print(f"✅ Config: {mgr.get_config('production', 'database_url')}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()
