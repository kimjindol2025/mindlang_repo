#!/usr/bin/env python3
from typing import Dict, List, Any
import time

class ApiResponseValidator:
    def __init__(self):
        self.schemas: Dict[str, Dict] = {}
        self.validations: List[Dict] = []
    
    def define_schema(self, endpoint: str, required_fields: List[str]) -> Dict:
        self.schemas[endpoint] = {"required_fields": required_fields}
        return self.schemas[endpoint]
    
    def validate_response(self, endpoint: str, response: Dict[str, Any]) -> Dict:
        result = {
            "endpoint": endpoint,
            "valid": True,
            "errors": [],
            "timestamp": time.time()
        }
        
        if endpoint in self.schemas:
            schema = self.schemas[endpoint]
            for field in schema["required_fields"]:
                if field not in response:
                    result["valid"] = False
                    result["errors"].append(f"Missing field: {field}")
        
        self.validations.append(result)
        return result
    
    def get_stats(self) -> Dict:
        valid = sum(1 for v in self.validations if v["valid"])
        return {"total_validations": len(self.validations), "valid": valid, "invalid": len(self.validations) - valid}

def main():
    print("✔️  API Response Validator")
    validator = ApiResponseValidator()
    validator.define_schema("user", ["id", "name", "email"])
    result = validator.validate_response("user", {"id": 1, "name": "John", "email": "john@test.com"})
    print(f"✅ Valid: {result['valid']}, Stats: {validator.get_stats()}")

if __name__ == "__main__":
    main()
