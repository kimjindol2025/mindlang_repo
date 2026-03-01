#!/usr/bin/env python3
"""
API Rate Limiting Analytics - Rate limiting analysis and insights
Analyzes rate limiting patterns, identifies bottlenecks, and provides optimization recommendations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import hashlib
import json
import time
import statistics


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "TOKEN_BUCKET"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    FIXED_WINDOW = "FIXED_WINDOW"
    LEAKY_BUCKET = "LEAKY_BUCKET"


class ClientTier(Enum):
    """Client tiers"""
    FREE = "FREE"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"


@dataclass
class RateLimitEvent:
    """Rate limit event"""
    event_id: str
    client_id: str
    endpoint: str
    timestamp: float
    allowed: bool
    remaining_quota: int
    reset_time: float


@dataclass
class ClientQuota:
    """Client quota information"""
    client_id: str
    tier: ClientTier
    requests_per_window: int
    window_size_seconds: int
    current_usage: int
    peak_usage: int
    reset_at: float


@dataclass
class EndpointMetrics:
    """Endpoint rate limiting metrics"""
    endpoint: str
    total_requests: int
    allowed_requests: int
    rejected_requests: int
    rejection_rate: float
    avg_response_time: float
    p99_response_time: float
    unique_clients: int


class APIRateLimitingAnalytics:
    """
    API Rate Limiting Analytics

    Provides:
    - Rate limiting pattern analysis
    - Client behavior analysis
    - Bottleneck identification
    - Quota optimization
    - Anomaly detection
    - Recommendations engine
    """

    def __init__(self):
        self.events: List[RateLimitEvent] = []
        self.client_quotas: Dict[str, ClientQuota] = {}
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        self.anomalies: List[Dict] = []
        self.recommendations: List[Dict] = []

    def record_rate_limit_event(self,
                               client_id: str,
                               endpoint: str,
                               allowed: bool,
                               remaining_quota: int,
                               reset_time: float = None) -> RateLimitEvent:
        """Record rate limit event"""
        event_id = hashlib.md5(
            f"{client_id}:{endpoint}:{time.time()}".encode()
        ).hexdigest()[:8]

        event = RateLimitEvent(
            event_id=event_id,
            client_id=client_id,
            endpoint=endpoint,
            timestamp=time.time(),
            allowed=allowed,
            remaining_quota=remaining_quota,
            reset_time=reset_time or time.time() + 3600
        )

        self.events.append(event)
        return event

    def set_client_quota(self,
                        client_id: str,
                        tier: ClientTier,
                        requests_per_window: int,
                        window_size_seconds: int = 3600) -> ClientQuota:
        """Set client quota"""
        quota = ClientQuota(
            client_id=client_id,
            tier=tier,
            requests_per_window=requests_per_window,
            window_size_seconds=window_size_seconds,
            current_usage=0,
            peak_usage=0,
            reset_at=time.time() + window_size_seconds
        )

        self.client_quotas[client_id] = quota
        return quota

    def update_client_usage(self, client_id: str, increment: int = 1) -> Optional[ClientQuota]:
        """Update client usage"""
        quota = self.client_quotas.get(client_id)
        if not quota:
            return None

        quota.current_usage += increment
        quota.peak_usage = max(quota.peak_usage, quota.current_usage)

        # Reset if window expired
        if time.time() > quota.reset_at:
            quota.current_usage = increment
            quota.reset_at = time.time() + quota.window_size_seconds

        return quota

    def analyze_client_behavior(self, client_id: str) -> Dict:
        """Analyze client behavior patterns"""
        client_events = [e for e in self.events if e.client_id == client_id]

        if not client_events:
            return {}

        allowed = sum(1 for e in client_events if e.allowed)
        rejected = sum(1 for e in client_events if not e.allowed)
        total = len(client_events)

        # Time-based analysis
        timestamps = [e.timestamp for e in client_events]
        if len(timestamps) > 1:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval = statistics.mean(intervals)
        else:
            avg_interval = 0

        return {
            "client_id": client_id,
            "total_requests": total,
            "allowed": allowed,
            "rejected": rejected,
            "rejection_rate": (rejected / total * 100) if total > 0 else 0,
            "avg_request_interval": avg_interval,
            "tier": self.client_quotas.get(client_id, {}).tier.value if client_id in self.client_quotas else None,
        }

    def analyze_endpoint_metrics(self, endpoint: str) -> EndpointMetrics:
        """Analyze endpoint metrics"""
        endpoint_events = [e for e in self.events if e.endpoint == endpoint]

        allowed = sum(1 for e in endpoint_events if e.allowed)
        rejected = sum(1 for e in endpoint_events if not e.allowed)
        total = len(endpoint_events)

        unique_clients = len(set(e.client_id for e in endpoint_events))

        metrics = EndpointMetrics(
            endpoint=endpoint,
            total_requests=total,
            allowed_requests=allowed,
            rejected_requests=rejected,
            rejection_rate=(rejected / total * 100) if total > 0 else 0,
            avg_response_time=50.0,  # Simulated
            p99_response_time=200.0,  # Simulated
            unique_clients=unique_clients
        )

        self.endpoint_metrics[endpoint] = metrics
        return metrics

    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalous patterns"""
        anomalies = []

        # Check for spike in rejections
        recent_events = self.events[-100:]
        rejection_rate = sum(1 for e in recent_events if not e.allowed) / max(1, len(recent_events))

        if rejection_rate > 0.3:
            anomalies.append({
                "type": "HIGH_REJECTION_RATE",
                "value": rejection_rate,
                "threshold": 0.3,
                "severity": "HIGH",
                "detected_at": time.time()
            })

        # Check for client quota overuse
        for client_id, quota in self.client_quotas.items():
            if quota.current_usage > quota.requests_per_window:
                anomalies.append({
                    "type": "QUOTA_EXCEEDED",
                    "client_id": client_id,
                    "usage": quota.current_usage,
                    "limit": quota.requests_per_window,
                    "severity": "MEDIUM",
                    "detected_at": time.time()
                })

        self.anomalies.extend(anomalies)
        return anomalies

    def generate_recommendations(self) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []

        # Analyze high-rejection endpoints
        for endpoint, metrics in self.endpoint_metrics.items():
            if metrics.rejection_rate > 0.2:
                recommendations.append({
                    "type": "INCREASE_QUOTA",
                    "endpoint": endpoint,
                    "reason": f"High rejection rate: {metrics.rejection_rate:.1f}%",
                    "suggested_increase": 20,
                    "estimated_improvement": "Reduce rejection rate by ~5%"
                })

        # Identify underutilized tiers
        tier_usage = {}
        for client_id, quota in self.client_quotas.items():
            tier = quota.tier.value
            if tier not in tier_usage:
                tier_usage[tier] = {"used": 0, "allocated": 0, "clients": 0}

            tier_usage[tier]["used"] += quota.current_usage
            tier_usage[tier]["allocated"] += quota.requests_per_window
            tier_usage[tier]["clients"] += 1

        for tier, usage in tier_usage.items():
            utilization = (usage["used"] / usage["allocated"] * 100) if usage["allocated"] > 0 else 0
            if utilization < 20:
                recommendations.append({
                    "type": "OPTIMIZE_QUOTA",
                    "tier": tier,
                    "current_utilization": utilization,
                    "suggestion": f"Consider reducing quota for {tier} tier",
                })

        self.recommendations.extend(recommendations)
        return recommendations

    def get_analytics_stats(self) -> Dict:
        """Get analytics statistics"""
        total_events = len(self.events)
        allowed = sum(1 for e in self.events if e.allowed)
        rejected = total_events - allowed

        return {
            "total_events": total_events,
            "allowed_requests": allowed,
            "rejected_requests": rejected,
            "rejection_rate": (rejected / total_events * 100) if total_events > 0 else 0,
            "unique_clients": len(set(e.client_id for e in self.events)),
            "endpoints_tracked": len(self.endpoint_metrics),
            "anomalies_detected": len(self.anomalies),
            "recommendations": len(self.recommendations),
        }

    def generate_analytics_report(self) -> str:
        """Generate analytics report"""
        stats = self.get_analytics_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              API RATE LIMITING ANALYTICS REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Events: {stats['total_events']}
├─ Allowed: {stats['allowed_requests']}
├─ Rejected: {stats['rejected_requests']}
├─ Rejection Rate: {stats['rejection_rate']:.2f}%
├─ Unique Clients: {stats['unique_clients']}
├─ Endpoints: {stats['endpoints_tracked']}
├─ Anomalies: {stats['anomalies_detected']}
└─ Recommendations: {stats['recommendations']}

📈 TOP ENDPOINTS:
"""

        for endpoint, metrics in sorted(self.endpoint_metrics.items(),
                                       key=lambda x: x[1].rejection_rate,
                                       reverse=True)[:5]:
            report += f"\n  {endpoint}\n"
            report += f"    Rejection Rate: {metrics.rejection_rate:.2f}%\n"
            report += f"    Unique Clients: {metrics.unique_clients}\n"
            report += f"    Total Requests: {metrics.total_requests}\n"

        return report

    def export_analytics_config(self) -> str:
        """Export analytics configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_analytics_stats(),
            "endpoints": [
                {
                    "endpoint": m.endpoint,
                    "rejection_rate": m.rejection_rate,
                    "unique_clients": m.unique_clients,
                }
                for m in self.endpoint_metrics.values()
            ],
            "client_quotas": [
                {
                    "client_id": q.client_id,
                    "tier": q.tier.value,
                    "requests_per_window": q.requests_per_window,
                    "current_usage": q.current_usage,
                }
                for q in self.client_quotas.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 API Rate Limiting Analytics - Usage Analysis")
    print("=" * 70)

    analytics = APIRateLimitingAnalytics()

    # Setup quotas
    print("\n📋 Setting up client quotas...")
    analytics.set_client_quota("client_a", ClientTier.FREE, 100, 3600)
    analytics.set_client_quota("client_b", ClientTier.PREMIUM, 10000, 3600)
    analytics.set_client_quota("client_c", ClientTier.STANDARD, 1000, 3600)
    print(f"✅ Setup {len(analytics.client_quotas)} quotas")

    # Record events
    print("\n📝 Recording rate limit events...")
    for i in range(150):
        allowed = i < 100
        analytics.record_rate_limit_event(
            "client_a", "/api/users",
            allowed, max(0, 100 - i)
        )

    for i in range(200):
        analytics.record_rate_limit_event(
            "client_b", "/api/products",
            True, 10000 - i
        )

    print(f"✅ Recorded {len(analytics.events)} events")

    # Analyze
    print("\n🔍 Analyzing patterns...")
    analytics.analyze_endpoint_metrics("/api/users")
    analytics.analyze_endpoint_metrics("/api/products")
    behavior = analytics.analyze_client_behavior("client_a")
    print(f"✅ Client A rejection rate: {behavior['rejection_rate']:.2f}%")

    # Detect anomalies
    print("\n🚨 Detecting anomalies...")
    anomalies = analytics.detect_anomalies()
    print(f"✅ Detected {len(anomalies)} anomalies")

    # Generate recommendations
    print("\n💡 Generating recommendations...")
    recommendations = analytics.generate_recommendations()
    print(f"✅ Generated {len(recommendations)} recommendations")

    # Generate report
    print(analytics.generate_analytics_report())

    # Export
    print("\n📄 Exporting analytics config...")
    export = analytics.export_analytics_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ API rate limiting analytics ready")


if __name__ == "__main__":
    main()
