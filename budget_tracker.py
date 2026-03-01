#!/usr/bin/env python3
from typing import Dict, List
import time

class BudgetTracker:
    def __init__(self):
        self.budgets: Dict[str, Dict] = {}
        self.expenses: List[Dict] = []
    
    def set_budget(self, category: str, amount: float, period: str) -> Dict:
        self.budgets[category] = {
            "amount": amount,
            "period": period,
            "set_at": time.time(),
            "spent": 0
        }
        return self.budgets[category]
    
    def add_expense(self, category: str, amount: float, description: str) -> Dict:
        expense = {
            "category": category,
            "amount": amount,
            "description": description,
            "timestamp": time.time()
        }
        self.expenses.append(expense)
        
        if category in self.budgets:
            self.budgets[category]["spent"] += amount
        
        return expense
    
    def check_budget(self, category: str) -> Dict:
        if category not in self.budgets:
            return {"category": category, "exists": False}
        
        budget = self.budgets[category]
        remaining = budget["amount"] - budget["spent"]
        percentage = (budget["spent"] / budget["amount"] * 100) if budget["amount"] > 0 else 0
        
        return {
            "category": category,
            "budget": budget["amount"],
            "spent": budget["spent"],
            "remaining": remaining,
            "percentage_used": percentage
        }
    
    def get_stats(self) -> Dict:
        total_spent = sum(b["spent"] for b in self.budgets.values())
        total_budget = sum(b["amount"] for b in self.budgets.values())
        return {"categories": len(self.budgets), "total_spent": total_spent, "total_budget": total_budget}

def main():
    print("💰 Budget Tracker")
    tracker = BudgetTracker()
    tracker.set_budget("marketing", 10000, "monthly")
    tracker.add_expense("marketing", 3000, "ad campaign")
    check = tracker.check_budget("marketing")
    print(f"✅ Used: {check['percentage_used']:.1f}%, Stats: {tracker.get_stats()}")

if __name__ == "__main__":
    main()
