#!/usr/bin/env python3
"""
Resource Quota Manager - Fine-grained resource allocation and quota enforcement
Manages resource quotas with monitoring, enforcement, and auto-scaling triggers
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time


class ResourceType(Enum):
    """Resource types"""
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK_BANDWIDTH = "NETWORK_BANDWIDTH"
    CONNECTIONS = "CONNECTIONS"
    REQUESTS_PER_SECOND = "REQUESTS_PER_SECOND"


@dataclass
class ResourceQuota:
    """Resource quota"""
    quota_id: str
    namespace: str
    resource_type: ResourceType
    limit: float
    request: float = 0.0
    used: float = 0.0
    created_at: float = field(default_factory=time.time)


@dataclass
class QuotaViolation:
    """Quota violation record"""
    violation_id: str
    quota_id: str
    namespace: str
    exceeded_by: float
    timestamp: float
    action_taken: str


@dataclass
class AutoScalingPolicy:
    """Auto-scaling policy"""
    policy_id: str
    namespace: str
    resource_type: ResourceType
    scale_up_threshold: float  # Percentage
    scale_down_threshold: float
    created_at: float = field(default_factory=time.time)


class ResourceQuotaManager:
    """
    Resource Quota Manager

    Provides:
    - Fine-grained quotas
    - Quota enforcement
    - Auto-scaling policies
    - Usage tracking
    - Violation alerts
    - Fair resource allocation
    """

    def __init__(self):
        self.quotas: Dict[str, ResourceQuota] = {}
        self.violations: List[QuotaViolation] = []
        self.auto_scaling_policies: Dict[str, AutoScalingPolicy] = {}
        self.usage_history: List[Dict] = []
        self.scaling_actions: List[Dict] = []

    def create_quota(self,
                    namespace: str,
                    resource_type: ResourceType,
                    limit: float,
                    request: float = 0.0) -> ResourceQuota:
        """Create resource quota"""
        quota_id = hashlib.md5(
            f"{namespace}:{resource_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        quota = ResourceQuota(
            quota_id=quota_id,
            namespace=namespace,
            resource_type=resource_type,
            limit=limit,
            request=request
        )

        self.quotas[quota_id] = quota
        return quota

    def allocate_resource(self,
                         quota_id: str,
                         amount: float) -> bool:
        """Allocate resource from quota"""
        quota = self.quotas.get(quota_id)
        if not quota:
            return False

        # Check if allocation would exceed quota
        if quota.used + amount > quota.limit:
            exceeded = (quota.used + amount) - quota.limit

            violation = QuotaViolation(
                violation_id=hashlib.md5(f"{quota_id}:{time.time()}".encode()).hexdigest()[:8],
                quota_id=quota_id,
                namespace=quota.namespace,
                exceeded_by=exceeded,
                timestamp=time.time(),
                action_taken="REJECTED"
            )

            self.violations.append(violation)

            # Check auto-scaling policy
            self._trigger_auto_scaling(quota)

            return False

        quota.used += amount

        self.usage_history.append({
            "quota_id": quota_id,
            "action": "ALLOCATED",
            "amount": amount,
            "total_used": quota.used,
            "timestamp": time.time()
        })

        return True

    def release_resource(self, quota_id: str, amount: float) -> bool:
        """Release resource back to quota"""
        quota = self.quotas.get(quota_id)
        if not quota:
            return False

        quota.used = max(0, quota.used - amount)

        self.usage_history.append({
            "quota_id": quota_id,
            "action": "RELEASED",
            "amount": amount,
            "total_used": quota.used,
            "timestamp": time.time()
        })

        return True

    def set_auto_scaling_policy(self,
                               namespace: str,
                               resource_type: ResourceType,
                               scale_up_threshold: float = 80.0,
                               scale_down_threshold: float = 20.0) -> AutoScalingPolicy:
        """Set auto-scaling policy"""
        policy_id = hashlib.md5(
            f"{namespace}:{resource_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = AutoScalingPolicy(
            policy_id=policy_id,
            namespace=namespace,
            resource_type=resource_type,
            scale_up_threshold=scale_up_threshold,
            scale_down_threshold=scale_down_threshold
        )

        self.auto_scaling_policies[policy_id] = policy
        return policy

    def _trigger_auto_scaling(self, quota: ResourceQuota):
        """Trigger auto-scaling if policy exists"""
        policy = next((p for p in self.auto_scaling_policies.values()
                      if p.namespace == quota.namespace and
                      p.resource_type == quota.resource_type), None)

        if not policy:
            return

        utilization = (quota.used / quota.limit * 100) if quota.limit > 0 else 0

        if utilization > policy.scale_up_threshold:
            # Scale up
            new_limit = quota.limit * 1.5

            self.scaling_actions.append({
                "quota_id": quota.quota_id,
                "action": "SCALE_UP",
                "old_limit": quota.limit,
                "new_limit": new_limit,
                "utilization": utilization,
                "timestamp": time.time()
            })

            quota.limit = new_limit

        elif utilization < policy.scale_down_threshold:
            # Scale down
            new_limit = quota.limit * 0.8

            self.scaling_actions.append({
                "quota_id": quota.quota_id,
                "action": "SCALE_DOWN",
                "old_limit": quota.limit,
                "new_limit": new_limit,
                "utilization": utilization,
                "timestamp": time.time()
            })

            quota.limit = new_limit

    def get_namespace_stats(self, namespace: str) -> Dict:
        """Get resource statistics for namespace"""
        namespace_quotas = [q for q in self.quotas.values()
                          if q.namespace == namespace]

        total_limit = sum(q.limit for q in namespace_quotas)
        total_used = sum(q.used for q in namespace_quotas)

        by_resource = {}
        for quota in namespace_quotas:
            resource = quota.resource_type.value
            utilization = (quota.used / quota.limit * 100) if quota.limit > 0 else 0
            by_resource[resource] = {
                "limit": quota.limit,
                "used": quota.used,
                "utilization": utilization
            }

        return {
            "namespace": namespace,
            "total_limit": total_limit,
            "total_used": total_used,
            "overall_utilization": (total_used / total_limit * 100) if total_limit > 0 else 0,
            "quotas_count": len(namespace_quotas),
            "by_resource": by_resource,
        }

    def get_quota_stats(self) -> Dict:
        """Get quota statistics"""
        total_quotas = len(self.quotas)
        total_violations = len(self.violations)

        by_resource = {}
        for quota in self.quotas.values():
            resource = quota.resource_type.value
            by_resource[resource] = by_resource.get(resource, 0) + 1

        total_limit = sum(q.limit for q in self.quotas.values())
        total_used = sum(q.used for q in self.quotas.values())

        return {
            "total_quotas": total_quotas,
            "total_violations": total_violations,
            "by_resource_type": by_resource,
            "total_limit": total_limit,
            "total_used": total_used,
            "overall_utilization": (total_used / total_limit * 100) if total_limit > 0 else 0,
            "scaling_actions": len(self.scaling_actions),
        }

    def generate_quota_report(self) -> str:
        """Generate quota report"""
        stats = self.get_quota_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              RESOURCE QUOTA MANAGER REPORT                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Quotas: {stats['total_quotas']}
├─ Total Violations: {stats['total_violations']}
├─ Overall Utilization: {stats['overall_utilization']:.1f}%
├─ Total Limit: {stats['total_limit']:.2f}
├─ Total Used: {stats['total_used']:.2f}
└─ Scaling Actions: {stats['scaling_actions']}

📋 BY RESOURCE TYPE:
"""

        for resource, count in stats['by_resource_type'].items():
            report += f"  {resource}: {count}\n"

        return report

    def export_quota_config(self) -> str:
        """Export quota configuration"""
        stats = self.get_quota_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "quotas": [
                {
                    "namespace": q.namespace,
                    "resource_type": q.resource_type.value,
                    "limit": q.limit,
                    "used": q.used,
                    "utilization": (q.used / q.limit * 100) if q.limit > 0 else 0,
                }
                for q in self.quotas.values()
            ],
            "auto_scaling_policies": [
                {
                    "namespace": p.namespace,
                    "resource_type": p.resource_type.value,
                    "scale_up_threshold": p.scale_up_threshold,
                }
                for p in self.auto_scaling_policies.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("💾 Resource Quota Manager - Resource Allocation")
    print("=" * 70)

    manager = ResourceQuotaManager()

    # Create quotas
    print("\n📋 Creating resource quotas...")
    cpu_quota = manager.create_quota("production", ResourceType.CPU, 1000.0, 500.0)
    mem_quota = manager.create_quota("production", ResourceType.MEMORY, 50000.0, 25000.0)
    req_quota = manager.create_quota("production", ResourceType.REQUESTS_PER_SECOND, 10000.0, 5000.0)
    print(f"✅ Created {len(manager.quotas)} quotas")

    # Set auto-scaling policies
    print("\n⚙️  Setting auto-scaling policies...")
    manager.set_auto_scaling_policy("production", ResourceType.CPU, 80.0, 20.0)
    manager.set_auto_scaling_policy("production", ResourceType.MEMORY, 85.0, 25.0)
    print(f"✅ Set {len(manager.auto_scaling_policies)} policies")

    # Allocate resources
    print("\n📦 Allocating resources...")
    manager.allocate_resource(cpu_quota.quota_id, 300.0)
    manager.allocate_resource(mem_quota.quota_id, 15000.0)
    manager.allocate_resource(req_quota.quota_id, 3000.0)
    print("✅ Resources allocated")

    # Try to exceed quota
    print("\n⚠️  Testing quota enforcement...")
    exceeded = not manager.allocate_resource(cpu_quota.quota_id, 750.0)
    print(f"✅ Quota enforcement: {'WORKING' if exceeded else 'FAILED'}")

    # Release resources
    print("\n🔄 Releasing resources...")
    manager.release_resource(cpu_quota.quota_id, 100.0)
    print("✅ Resources released")

    # Get stats
    print("\n📊 Getting namespace statistics...")
    ns_stats = manager.get_namespace_stats("production")
    print(f"✅ Namespace utilization: {ns_stats['overall_utilization']:.1f}%")

    # Generate report
    print(manager.generate_quota_report())

    # Export
    print("\n📄 Exporting quota config...")
    export = manager.export_quota_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Resource quota manager ready")


if __name__ == "__main__":
    main()
