#!/usr/bin/env python3
from typing import Dict, List
import time

class ComplianceChecker:
    def __init__(self):
        self.rules: Dict[str, Dict] = {}
        self.checks: List[Dict] = []
    
    def add_rule(self, rule_id: str, description: str, severity: str) -> Dict:
        self.rules[rule_id] = {"description": description, "severity": severity}
        return self.rules[rule_id]
    
    def check_compliance(self, resource: str, rule_id: str, compliant: bool) -> Dict:
        check = {
            "resource": resource,
            "rule_id": rule_id,
            "compliant": compliant,
            "timestamp": time.time()
        }
        self.checks.append(check)
        return check
    
    def get_compliance_report(self) -> Dict:
        total = len(self.checks)
        compliant = sum(1 for c in self.checks if c["compliant"])
        return {
            "total_checks": total,
            "compliant": compliant,
            "non_compliant": total - compliant,
            "compliance_rate": (compliant / total * 100) if total > 0 else 0
        }
    
    def get_stats(self) -> Dict:
        return {"rules": len(self.rules), "checks_performed": len(self.checks)}

def main():
    print("✅ Compliance Checker")
    checker = ComplianceChecker()
    checker.add_rule("rule-001", "Data encryption", "HIGH")
    checker.check_compliance("db-prod", "rule-001", True)
    report = checker.get_compliance_report()
    print(f"✅ Compliance Rate: {report['compliance_rate']:.1f}%, Stats: {checker.get_stats()}")

if __name__ == "__main__":
    main()
