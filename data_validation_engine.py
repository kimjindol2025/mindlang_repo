#!/usr/bin/env python3
from typing import Dict, List, Any
import re

class DataValidationEngine:
    def __init__(self):
        self.rules: Dict[str, Dict] = {}
        self.validations: List[Dict] = []
    
    def add_rule(self, field: str, rule_type: str, params: Dict) -> Dict:
        self.rules[field] = {"type": rule_type, "params": params}
        return self.rules[field]
    
    def validate(self, field: str, value: Any) -> Dict:
        if field not in self.rules:
            return {"field": field, "valid": True}
        
        rule = self.rules[field]
        valid = True
        error = None
        
        if rule["type"] == "email":
            valid = bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)))
            error = "Invalid email" if not valid else None
        elif rule["type"] == "min_length":
            valid = len(str(value)) >= rule["params"].get("length", 0)
            error = f"Too short" if not valid else None
        
        result = {"field": field, "value": value, "valid": valid, "error": error}
        self.validations.append(result)
        return result
    
    def get_stats(self) -> Dict:
        valid = sum(1 for v in self.validations if v["valid"])
        return {"total_validations": len(self.validations), "valid": valid}

def main():
    print("✔️  Data Validation Engine")
    engine = DataValidationEngine()
    engine.add_rule("email", "email", {})
    engine.add_rule("password", "min_length", {"length": 8})
    engine.validate("email", "user@example.com")
    print(f"✅ Stats: {engine.get_stats()}")

if __name__ == "__main__":
    main()
