#!/usr/bin/env python3
"""
Traffic Mirroring System - Real-time traffic mirroring and analysis
Mirrors production traffic to test environments for validation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time
import random


class MirrorTarget(Enum):
    """Mirror target types"""
    CANARY = "CANARY"
    STAGING = "STAGING"
    SHADOW = "SHADOW"
    TEST = "TEST"


class MirrorStatus(Enum):
    """Mirror status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


@dataclass
class MirroredRequest:
    """Mirrored request"""
    request_id: str
    original_request_id: str
    timestamp: float
    path: str
    method: str
    headers: Dict[str, str]
    body: Optional[str] = None
    mirrored_to: str = ""


@dataclass
class MirrorResponse:
    """Mirror response"""
    response_id: str
    mirrored_request_id: str
    target: MirrorTarget
    status_code: int
    response_time_ms: float
    body: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MirrorComparison:
    """Comparison between original and mirrored response"""
    comparison_id: str
    original_response_id: str
    mirrored_response_id: str
    timestamp: float
    status_match: bool
    response_time_diff_ms: float
    body_match: bool
    differences: List[str] = field(default_factory=list)


@dataclass
class MirrorPolicy:
    """Traffic mirror policy"""
    policy_id: str
    policy_name: str
    source_service: str
    target: MirrorTarget
    percentage: float  # 0-100
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


class TrafficMirroringSystem:
    """
    Traffic Mirroring System

    Provides:
    - Real-time traffic mirroring
    - Response comparison
    - Canary testing
    - Shadow traffic analysis
    - Performance validation
    """

    def __init__(self):
        self.policies: Dict[str, MirrorPolicy] = {}
        self.mirrored_requests: Dict[str, MirroredRequest] = {}
        self.mirror_responses: List[MirrorResponse] = []
        self.comparisons: List[MirrorComparison] = []

    def create_policy(self,
                     policy_name: str,
                     source_service: str,
                     target: MirrorTarget,
                     percentage: float = 100.0) -> MirrorPolicy:
        """Create traffic mirror policy"""
        policy_id = hashlib.md5(
            f"{policy_name}:{source_service}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = MirrorPolicy(
            policy_id=policy_id,
            policy_name=policy_name,
            source_service=source_service,
            target=target,
            percentage=min(100, max(0, percentage))
        )

        self.policies[policy_id] = policy
        return policy

    def should_mirror(self, policy_id: str) -> bool:
        """Determine if request should be mirrored"""
        policy = self.policies.get(policy_id)
        if not policy or not policy.enabled:
            return False

        return random.random() * 100 < policy.percentage

    def mirror_request(self,
                      policy_id: str,
                      original_request_id: str,
                      path: str,
                      method: str,
                      headers: Dict[str, str],
                      body: Optional[str] = None) -> Optional[MirroredRequest]:
        """Mirror incoming request"""
        if not self.should_mirror(policy_id):
            return None

        policy = self.policies.get(policy_id)
        if not policy:
            return None

        request_id = hashlib.md5(
            f"{original_request_id}:{policy_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        mirrored = MirroredRequest(
            request_id=request_id,
            original_request_id=original_request_id,
            timestamp=time.time(),
            path=path,
            method=method,
            headers=headers,
            body=body,
            mirrored_to=policy.target.value
        )

        self.mirrored_requests[request_id] = mirrored

        # Simulate mirrored request execution
        self._process_mirrored_request(mirrored, policy)

        return mirrored

    def _process_mirrored_request(self, mirrored: MirroredRequest, policy: MirrorPolicy):
        """Process mirrored request"""
        response_id = hashlib.md5(
            f"{mirrored.request_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Simulate response
        success = random.random() > 0.05  # 95% success
        status_code = 200 if success else random.choice([400, 404, 500])
        response_time = random.uniform(10, 100)

        response = MirrorResponse(
            response_id=response_id,
            mirrored_request_id=mirrored.request_id,
            target=policy.target,
            status_code=status_code,
            response_time_ms=response_time
        )

        self.mirror_responses.append(response)

    def record_original_response(self,
                                original_request_id: str,
                                status_code: int,
                                response_time_ms: float) -> List[MirrorComparison]:
        """Record original response and compare with mirrors"""
        comparisons = []

        # Find mirrored requests
        mirrored = [r for r in self.mirrored_requests.values()
                   if r.original_request_id == original_request_id]

        for mirror in mirrored:
            # Find corresponding response
            mirror_response = next((r for r in self.mirror_responses
                                  if r.mirrored_request_id == mirror.request_id), None)

            if mirror_response:
                comparison_id = hashlib.md5(
                    f"{original_request_id}:{mirror.request_id}:{time.time()}".encode()
                ).hexdigest()[:8]

                differences = []
                if status_code != mirror_response.status_code:
                    differences.append(f"Status: {status_code} vs {mirror_response.status_code}")

                time_diff = abs(response_time_ms - mirror_response.response_time_ms)
                if time_diff > response_time_ms * 0.2:  # >20% difference
                    differences.append(f"Response time: {response_time_ms}ms vs {mirror_response.response_time_ms}ms")

                comparison = MirrorComparison(
                    comparison_id=comparison_id,
                    original_response_id=original_request_id,
                    mirrored_response_id=mirror_response.response_id,
                    timestamp=time.time(),
                    status_match=status_code == mirror_response.status_code,
                    response_time_diff_ms=time_diff,
                    body_match=True,  # Simplified
                    differences=differences
                )

                self.comparisons.append(comparison)
                comparisons.append(comparison)

        return comparisons

    def get_mirror_stats(self) -> Dict:
        """Get mirror statistics"""
        total_mirrored = len(self.mirrored_requests)
        total_comparisons = len(self.comparisons)
        matching = sum(1 for c in self.comparisons if c.status_match and c.body_match)

        avg_time_diff = sum(c.response_time_diff_ms for c in self.comparisons) / max(1, total_comparisons)

        return {
            "policies": len(self.policies),
            "active_policies": sum(1 for p in self.policies.values() if p.enabled),
            "mirrored_requests": total_mirrored,
            "mirror_responses": len(self.mirror_responses),
            "comparisons": total_comparisons,
            "matching_responses": matching,
            "match_rate": matching / max(1, total_comparisons),
            "avg_response_time_diff": avg_time_diff,
        }

    def generate_mirror_report(self) -> str:
        """Generate mirror report"""
        stats = self.get_mirror_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              TRAFFIC MIRRORING REPORT                                      ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Policies: {stats['active_policies']}/{stats['policies']}
├─ Mirrored Requests: {stats['mirrored_requests']}
├─ Comparisons: {stats['comparisons']}
├─ ✅ Matching: {stats['matching_responses']}/{stats['comparisons']}
├─ Match Rate: {stats['match_rate']:.2%}
└─ Avg Response Time Diff: {stats['avg_response_time_diff']:.2f}ms

🎯 MIRROR POLICIES:
"""

        for policy in self.policies.values():
            status = "🟢" if policy.enabled else "🔴"
            report += f"\n  {status} {policy.policy_name}\n"
            report += f"    Target: {policy.target.value}\n"
            report += f"    Percentage: {policy.percentage:.0f}%\n"

        return report

    def export_mirror_config(self) -> str:
        """Export mirror configuration"""
        export_data = {
            "timestamp": time.time(),
            "policies": [
                {
                    "name": p.policy_name,
                    "source": p.source_service,
                    "target": p.target.value,
                    "percentage": p.percentage,
                    "enabled": p.enabled,
                }
                for p in self.policies.values()
            ],
            "statistics": self.get_mirror_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Traffic Mirroring System - Real-Time Traffic Analysis")
    print("=" * 70)

    system = TrafficMirroringSystem()

    # Create policies
    print("\n📝 Creating mirror policies...")
    canary_policy = system.create_policy(
        "Canary to v2.0",
        "api-service",
        MirrorTarget.CANARY,
        percentage=10.0
    )

    staging_policy = system.create_policy(
        "Staging Mirror",
        "api-service",
        MirrorTarget.STAGING,
        percentage=100.0
    )

    shadow_policy = system.create_policy(
        "Shadow Test",
        "api-service",
        MirrorTarget.SHADOW,
        percentage=50.0
    )
    print(f"✅ Created {len(system.policies)} policies")

    # Simulate requests
    print("\n📨 Simulating requests...")
    for i in range(20):
        original_req_id = hashlib.md5(
            f"request_{i}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Try to mirror with each policy
        for policy_id in system.policies.keys():
            mirror = system.mirror_request(
                policy_id,
                original_req_id,
                f"/api/endpoint{i}",
                "GET",
                {"Authorization": "Bearer token"}
            )

        # Record original response
        status_code = 200 if i % 10 != 0 else 500
        response_time = random.uniform(50, 200)

        comparisons = system.record_original_response(original_req_id, status_code, response_time)
        if comparisons:
            print(f"  Request {i+1}: {len(comparisons)} comparison(s)")

    # Generate report
    print(system.generate_mirror_report())

    # Export
    print("\n📄 Exporting mirror config...")
    export = system.export_mirror_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Traffic mirroring ready")


if __name__ == "__main__":
    main()
