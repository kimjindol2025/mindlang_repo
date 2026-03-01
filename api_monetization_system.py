#!/usr/bin/env python3
"""
API Monetization System - API call metering and billing
Meters API calls, tracks usage, and manages billing for API consumers
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class PricingModel(Enum):
    """Pricing models"""
    PAY_PER_REQUEST = "PAY_PER_REQUEST"
    TIERED = "TIERED"
    MONTHLY_SUBSCRIPTION = "MONTHLY_SUBSCRIPTION"
    HYBRID = "HYBRID"


class BillingCycle(Enum):
    """Billing cycles"""
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


@dataclass
class PricingTier:
    """Pricing tier"""
    tier_id: str
    name: str
    pricing_model: PricingModel
    base_price: float
    price_per_request: float = 0.0
    request_limit: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class APIConsumer:
    """API consumer/customer"""
    consumer_id: str
    consumer_name: str
    tier_id: str
    api_key: str
    created_at: float
    status: str = "ACTIVE"
    total_requests: int = 0
    total_spent: float = 0.0


@dataclass
class APICall:
    """API call record"""
    call_id: str
    consumer_id: str
    endpoint: str
    timestamp: float
    response_time_ms: float
    status_code: int
    cost: float = 0.0


class APIMonetizationSystem:
    """
    API Monetization System

    Provides:
    - Usage metering
    - Flexible pricing models
    - Billing management
    - Rate limiting by tier
    - Usage analytics
    - Invoice generation
    """

    def __init__(self):
        self.pricing_tiers: Dict[str, PricingTier] = {}
        self.api_consumers: Dict[str, APIConsumer] = {}
        self.api_calls: List[APICall] = []
        self.invoices: List[Dict] = []
        self.usage_reports: Dict[str, Dict] = {}

    def create_pricing_tier(self,
                           name: str,
                           pricing_model: PricingModel,
                           base_price: float,
                           price_per_request: float = 0.0,
                           request_limit: int = 0) -> PricingTier:
        """Create pricing tier"""
        tier_id = hashlib.md5(
            f"{name}:{pricing_model.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        tier = PricingTier(
            tier_id=tier_id,
            name=name,
            pricing_model=pricing_model,
            base_price=base_price,
            price_per_request=price_per_request,
            request_limit=request_limit
        )

        self.pricing_tiers[tier_id] = tier
        return tier

    def create_consumer(self,
                       consumer_name: str,
                       tier_id: str) -> Optional[APIConsumer]:
        """Create API consumer"""
        if tier_id not in self.pricing_tiers:
            return None

        consumer_id = hashlib.md5(
            f"{consumer_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        api_key = hashlib.sha256(
            f"{consumer_id}:{time.time()}".encode()
        ).hexdigest()

        consumer = APIConsumer(
            consumer_id=consumer_id,
            consumer_name=consumer_name,
            tier_id=tier_id,
            api_key=api_key,
            created_at=time.time()
        )

        self.api_consumers[consumer_id] = consumer
        self.usage_reports[consumer_id] = {
            "requests": 0,
            "total_cost": 0.0,
            "period_start": time.time()
        }

        return consumer

    def record_api_call(self,
                       consumer_id: str,
                       endpoint: str,
                       response_time_ms: float,
                       status_code: int) -> Optional[APICall]:
        """Record API call and calculate cost"""
        consumer = self.api_consumers.get(consumer_id)
        if not consumer:
            return None

        tier = self.pricing_tiers.get(consumer.tier_id)
        if not tier:
            return None

        call_id = hashlib.md5(
            f"{consumer_id}:{endpoint}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Calculate cost
        cost = 0.0
        if tier.pricing_model == PricingModel.PAY_PER_REQUEST:
            cost = tier.price_per_request
        elif tier.pricing_model == PricingModel.TIERED:
            if consumer.total_requests < tier.request_limit:
                cost = tier.price_per_request

        call = APICall(
            call_id=call_id,
            consumer_id=consumer_id,
            endpoint=endpoint,
            timestamp=time.time(),
            response_time_ms=response_time_ms,
            status_code=status_code,
            cost=cost
        )

        self.api_calls.append(call)

        # Update consumer stats
        consumer.total_requests += 1
        consumer.total_spent += cost

        # Update usage report
        if consumer_id in self.usage_reports:
            self.usage_reports[consumer_id]["requests"] += 1
            self.usage_reports[consumer_id]["total_cost"] += cost

        return call

    def check_rate_limit(self, consumer_id: str) -> Dict:
        """Check rate limit for consumer"""
        consumer = self.api_consumers.get(consumer_id)
        if not consumer:
            return {"allowed": False, "reason": "CONSUMER_NOT_FOUND"}

        tier = self.pricing_tiers.get(consumer.tier_id)
        if not tier or tier.request_limit == 0:
            return {"allowed": True}

        if consumer.total_requests >= tier.request_limit:
            return {
                "allowed": False,
                "reason": "RATE_LIMIT_EXCEEDED",
                "limit": tier.request_limit,
                "current": consumer.total_requests
            }

        return {"allowed": True}

    def generate_invoice(self, consumer_id: str, period_start: float, period_end: float) -> Optional[Dict]:
        """Generate invoice for consumer"""
        consumer = self.api_consumers.get(consumer_id)
        if not consumer:
            return None

        period_calls = [c for c in self.api_calls
                       if c.consumer_id == consumer_id and
                       period_start <= c.timestamp <= period_end]

        total_cost = sum(c.cost for c in period_calls)

        tier = self.pricing_tiers.get(consumer.tier_id)
        if tier and tier.pricing_model in [PricingModel.MONTHLY_SUBSCRIPTION, PricingModel.HYBRID]:
            total_cost += tier.base_price

        invoice = {
            "invoice_id": hashlib.md5(f"{consumer_id}:{period_start}".encode()).hexdigest()[:8],
            "consumer_id": consumer_id,
            "consumer_name": consumer.consumer_name,
            "period_start": period_start,
            "period_end": period_end,
            "api_calls": len(period_calls),
            "usage_cost": sum(c.cost for c in period_calls),
            "base_cost": tier.base_price if tier else 0.0,
            "total_cost": total_cost,
            "generated_at": time.time()
        }

        self.invoices.append(invoice)
        return invoice

    def get_monetization_stats(self) -> Dict:
        """Get monetization statistics"""
        total_calls = len(self.api_calls)
        total_revenue = sum(c.cost for c in self.api_calls)

        by_tier = {}
        for consumer in self.api_consumers.values():
            tier_name = self.pricing_tiers[consumer.tier_id].name
            if tier_name not in by_tier:
                by_tier[tier_name] = {"consumers": 0, "revenue": 0.0}

            by_tier[tier_name]["consumers"] += 1
            by_tier[tier_name]["revenue"] += consumer.total_spent

        return {
            "total_consumers": len(self.api_consumers),
            "total_api_calls": total_calls,
            "total_revenue": total_revenue,
            "by_tier": by_tier,
            "invoices_generated": len(self.invoices),
            "pricing_tiers": len(self.pricing_tiers),
        }

    def generate_monetization_report(self) -> str:
        """Generate monetization report"""
        stats = self.get_monetization_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              API MONETIZATION SYSTEM REPORT                                ║
╚════════════════════════════════════════════════════════════════════════════╝

💰 STATISTICS:
├─ Total Consumers: {stats['total_consumers']}
├─ Total API Calls: {stats['total_api_calls']}
├─ Total Revenue: ${stats['total_revenue']:.2f}
├─ Invoices: {stats['invoices_generated']}
└─ Pricing Tiers: {stats['pricing_tiers']}

📊 BY TIER:
"""

        for tier_name, stats_data in stats['by_tier'].items():
            report += f"  {tier_name}: {stats_data['consumers']} consumers (${stats_data['revenue']:.2f})\n"

        return report

    def export_monetization_config(self) -> str:
        """Export monetization configuration"""
        stats = self.get_monetization_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "pricing_tiers": [
                {
                    "name": t.name,
                    "model": t.pricing_model.value,
                    "base_price": t.base_price,
                    "price_per_request": t.price_per_request,
                }
                for t in self.pricing_tiers.values()
            ],
            "consumers": [
                {
                    "name": c.consumer_name,
                    "tier": self.pricing_tiers[c.tier_id].name,
                    "total_requests": c.total_requests,
                    "total_spent": c.total_spent,
                }
                for c in self.api_consumers.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("💰 API Monetization System - Usage Metering & Billing")
    print("=" * 70)

    system = APIMonetizationSystem()

    # Create pricing tiers
    print("\n📊 Creating pricing tiers...")
    free_tier = system.create_pricing_tier("Free", PricingModel.TIERED, 0.0, 0.001, 10000)
    pro_tier = system.create_pricing_tier("Pro", PricingModel.MONTHLY_SUBSCRIPTION, 99.0, 0.0005, 1000000)
    enterprise_tier = system.create_pricing_tier("Enterprise", PricingModel.HYBRID, 500.0, 0.0001)
    print(f"✅ Created {len(system.pricing_tiers)} pricing tiers")

    # Create consumers
    print("\n👥 Creating API consumers...")
    consumer1 = system.create_consumer("StartupCorp", free_tier.tier_id)
    consumer2 = system.create_consumer("TechInc", pro_tier.tier_id)
    consumer3 = system.create_consumer("GlobalCorp", enterprise_tier.tier_id)
    print(f"✅ Created {len(system.api_consumers)} consumers")

    # Record API calls
    print("\n📞 Recording API calls...")
    for i in range(500):
        if consumer1:
            system.record_api_call(consumer1.consumer_id, "/api/users", 45.5, 200)
        if consumer2:
            system.record_api_call(consumer2.consumer_id, "/api/data", 120.0, 200)

    print(f"✅ Recorded {len(system.api_calls)} API calls")

    # Check rate limits
    print("\n⏱️  Checking rate limits...")
    if consumer1:
        limit_check = system.check_rate_limit(consumer1.consumer_id)
        print(f"✅ Rate limit check: {limit_check['allowed']}")

    # Generate invoices
    print("\n📄 Generating invoices...")
    period_start = time.time() - (30 * 86400)
    period_end = time.time()
    if consumer1:
        invoice1 = system.generate_invoice(consumer1.consumer_id, period_start, period_end)
    if consumer2:
        invoice2 = system.generate_invoice(consumer2.consumer_id, period_start, period_end)
    print(f"✅ Generated {len(system.invoices)} invoices")

    # Generate report
    print(system.generate_monetization_report())

    # Export
    print("\n📄 Exporting monetization config...")
    export = system.export_monetization_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ API monetization system ready")


if __name__ == "__main__":
    main()
