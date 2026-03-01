#!/usr/bin/env python3
"""
Multi-tenant Isolation Manager - Tenant isolation and resource management
Manages tenant isolation, quota enforcement, and resource boundaries in multi-tenant systems
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time


class IsolationLevel(Enum):
    """Isolation levels"""
    LOGICAL = "LOGICAL"
    SCHEMA = "SCHEMA"
    DATABASE = "DATABASE"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class ResourceType(Enum):
    """Resource types"""
    STORAGE = "STORAGE"
    COMPUTE = "COMPUTE"
    NETWORK = "NETWORK"
    MEMORY = "MEMORY"
    BANDWIDTH = "BANDWIDTH"


@dataclass
class Tenant:
    """Tenant information"""
    tenant_id: str
    tenant_name: str
    isolation_level: IsolationLevel
    created_at: float
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class ResourceQuota:
    """Resource quota for tenant"""
    quota_id: str
    tenant_id: str
    resource_type: ResourceType
    allocated: float
    used: float
    reserved: float
    max_burst: float = 0


@dataclass
class IsolationBoundary:
    """Isolation boundary definition"""
    boundary_id: str
    tenant_id: str
    resource_type: ResourceType
    namespace: str
    access_level: str
    created_at: float


class MultiTenantIsolationManager:
    """
    Multi-tenant Isolation Manager

    Provides:
    - Multi-level tenant isolation
    - Resource quota enforcement
    - Isolation boundary management
    - Cross-tenant access control
    - Quota usage tracking
    - Tenant resource monitoring
    """

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.quotas: Dict[str, ResourceQuota] = {}
        self.boundaries: Dict[str, IsolationBoundary] = {}
        self.access_logs: List[Dict] = []
        self.quota_violations: List[Dict] = []

    def register_tenant(self,
                       tenant_name: str,
                       isolation_level: IsolationLevel = IsolationLevel.LOGICAL) -> Tenant:
        """Register new tenant"""
        tenant_id = hashlib.md5(
            f"{tenant_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        tenant = Tenant(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            isolation_level=isolation_level,
            created_at=time.time()
        )

        self.tenants[tenant_id] = tenant
        return tenant

    def set_resource_quota(self,
                          tenant_id: str,
                          resource_type: ResourceType,
                          allocated: float,
                          max_burst: float = 0) -> Optional[ResourceQuota]:
        """Set resource quota for tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        quota_id = hashlib.md5(
            f"{tenant_id}:{resource_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        quota = ResourceQuota(
            quota_id=quota_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            allocated=allocated,
            used=0,
            reserved=0,
            max_burst=max_burst
        )

        self.quotas[quota_id] = quota
        return quota

    def allocate_resource(self,
                         tenant_id: str,
                         resource_type: ResourceType,
                         amount: float) -> bool:
        """Allocate resource to tenant"""
        quota = next((q for q in self.quotas.values()
                     if q.tenant_id == tenant_id and
                     q.resource_type == resource_type), None)

        if not quota:
            return False

        # Check if allocation is within quota
        if quota.used + amount > quota.allocated:
            # Log violation
            self.quota_violations.append({
                "tenant_id": tenant_id,
                "resource_type": resource_type.value,
                "requested": amount,
                "available": quota.allocated - quota.used,
                "timestamp": time.time()
            })
            return False

        quota.used += amount
        return True

    def release_resource(self,
                        tenant_id: str,
                        resource_type: ResourceType,
                        amount: float) -> bool:
        """Release resource from tenant"""
        quota = next((q for q in self.quotas.values()
                     if q.tenant_id == tenant_id and
                     q.resource_type == resource_type), None)

        if not quota:
            return False

        quota.used = max(0, quota.used - amount)
        return True

    def create_isolation_boundary(self,
                                 tenant_id: str,
                                 resource_type: ResourceType,
                                 namespace: str,
                                 access_level: str = "PRIVATE") -> Optional[IsolationBoundary]:
        """Create isolation boundary for tenant resource"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        boundary_id = hashlib.md5(
            f"{tenant_id}:{namespace}:{time.time()}".encode()
        ).hexdigest()[:8]

        boundary = IsolationBoundary(
            boundary_id=boundary_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            namespace=namespace,
            access_level=access_level,
            created_at=time.time()
        )

        self.boundaries[boundary_id] = boundary
        return boundary

    def verify_access(self,
                     requesting_tenant_id: str,
                     resource_namespace: str,
                     resource_type: ResourceType) -> bool:
        """Verify if tenant can access resource"""
        boundary = next((b for b in self.boundaries.values()
                        if b.namespace == resource_namespace and
                        b.resource_type == resource_type), None)

        if not boundary:
            return False

        # Own resources
        if boundary.tenant_id == requesting_tenant_id:
            self.access_logs.append({
                "requesting_tenant": requesting_tenant_id,
                "resource_namespace": resource_namespace,
                "access_allowed": True,
                "reason": "OWN_RESOURCE",
                "timestamp": time.time()
            })
            return True

        # Shared resources
        if boundary.access_level == "SHARED":
            self.access_logs.append({
                "requesting_tenant": requesting_tenant_id,
                "resource_namespace": resource_namespace,
                "access_allowed": True,
                "reason": "SHARED_RESOURCE",
                "timestamp": time.time()
            })
            return True

        # Access denied
        self.access_logs.append({
            "requesting_tenant": requesting_tenant_id,
            "resource_namespace": resource_namespace,
            "access_allowed": False,
            "reason": "ACCESS_DENIED",
            "timestamp": time.time()
        })
        return False

    def get_tenant_metrics(self, tenant_id: str) -> Dict:
        """Get metrics for tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {}

        tenant_quotas = [q for q in self.quotas.values()
                        if q.tenant_id == tenant_id]

        quota_metrics = {}
        for quota in tenant_quotas:
            quota_metrics[quota.resource_type.value] = {
                "allocated": quota.allocated,
                "used": quota.used,
                "available": quota.allocated - quota.used,
                "utilization": (quota.used / quota.allocated * 100) if quota.allocated > 0 else 0,
            }

        boundaries = [b for b in self.boundaries.values()
                     if b.tenant_id == tenant_id]

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.tenant_name,
            "isolation_level": tenant.isolation_level.value,
            "quotas": quota_metrics,
            "boundaries": len(boundaries),
            "is_active": tenant.is_active,
        }

    def get_isolation_stats(self) -> Dict:
        """Get isolation statistics"""
        total_tenants = len(self.tenants)
        active_tenants = sum(1 for t in self.tenants.values() if t.is_active)

        by_isolation = {}
        for tenant in self.tenants.values():
            iso_level = tenant.isolation_level.value
            by_isolation[iso_level] = by_isolation.get(iso_level, 0) + 1

        total_boundaries = len(self.boundaries)
        access_denials = sum(1 for log in self.access_logs if not log.get("access_allowed", False))

        return {
            "total_tenants": total_tenants,
            "active_tenants": active_tenants,
            "by_isolation_level": by_isolation,
            "total_boundaries": total_boundaries,
            "quota_violations": len(self.quota_violations),
            "access_logs": len(self.access_logs),
            "access_denials": access_denials,
        }

    def generate_isolation_report(self) -> str:
        """Generate isolation report"""
        stats = self.get_isolation_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              MULTI-TENANT ISOLATION MANAGER REPORT                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Tenants: {stats['total_tenants']}
├─ Active Tenants: {stats['active_tenants']}
├─ Total Boundaries: {stats['total_boundaries']}
├─ Quota Violations: {stats['quota_violations']}
├─ Access Logs: {stats['access_logs']}
└─ Access Denials: {stats['access_denials']}

🔐 BY ISOLATION LEVEL:
"""

        for level, count in stats['by_isolation_level'].items():
            report += f"  {level}: {count}\n"

        report += f"\n📈 TENANT QUOTAS:\n"
        for tenant_id in list(self.tenants.keys())[:5]:
            metrics = self.get_tenant_metrics(tenant_id)
            if metrics:
                report += f"\n  {metrics['tenant_name']}\n"
                for resource_type, quota_info in metrics['quotas'].items():
                    report += f"    {resource_type}: {quota_info['utilization']:.1f}% utilized\n"

        return report

    def export_isolation_config(self) -> str:
        """Export isolation configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_isolation_stats(),
            "tenants": [
                {
                    "id": t.tenant_id,
                    "name": t.tenant_name,
                    "isolation_level": t.isolation_level.value,
                    "is_active": t.is_active,
                }
                for t in self.tenants.values()
            ],
            "recent_violations": [
                {
                    "tenant_id": v["tenant_id"],
                    "resource_type": v["resource_type"],
                    "timestamp": v["timestamp"],
                }
                for v in self.quota_violations[-10:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🏢 Multi-Tenant Isolation Manager - Tenant Resource Management")
    print("=" * 70)

    manager = MultiTenantIsolationManager()

    # Register tenants
    print("\n🏭 Registering tenants...")
    tenant1 = manager.register_tenant("ACME Corp", IsolationLevel.SCHEMA)
    tenant2 = manager.register_tenant("TechStart Inc", IsolationLevel.DATABASE)
    tenant3 = manager.register_tenant("Global Ltd", IsolationLevel.INFRASTRUCTURE)
    print(f"✅ Registered {len(manager.tenants)} tenants")

    # Set quotas
    print("\n💾 Setting resource quotas...")
    manager.set_resource_quota(tenant1.tenant_id, ResourceType.STORAGE, 1000.0)
    manager.set_resource_quota(tenant1.tenant_id, ResourceType.COMPUTE, 100.0)
    manager.set_resource_quota(tenant2.tenant_id, ResourceType.STORAGE, 5000.0)
    manager.set_resource_quota(tenant2.tenant_id, ResourceType.BANDWIDTH, 500.0)
    print(f"✅ Set {len(manager.quotas)} quotas")

    # Allocate resources
    print("\n📦 Allocating resources...")
    manager.allocate_resource(tenant1.tenant_id, ResourceType.STORAGE, 250.0)
    manager.allocate_resource(tenant1.tenant_id, ResourceType.COMPUTE, 30.0)
    manager.allocate_resource(tenant2.tenant_id, ResourceType.STORAGE, 2000.0)
    print("✅ Resources allocated")

    # Create boundaries
    print("\n🔒 Creating isolation boundaries...")
    b1 = manager.create_isolation_boundary(tenant1.tenant_id, ResourceType.STORAGE, "acme_db", "PRIVATE")
    b2 = manager.create_isolation_boundary(tenant2.tenant_id, ResourceType.STORAGE, "techstart_db", "PRIVATE")
    b3 = manager.create_isolation_boundary(tenant3.tenant_id, ResourceType.STORAGE, "shared_data", "SHARED")
    print(f"✅ Created {len(manager.boundaries)} boundaries")

    # Verify access
    print("\n🔐 Verifying access control...")
    access1 = manager.verify_access(tenant1.tenant_id, "acme_db", ResourceType.STORAGE)
    access2 = manager.verify_access(tenant2.tenant_id, "acme_db", ResourceType.STORAGE)
    access3 = manager.verify_access(tenant1.tenant_id, "shared_data", ResourceType.STORAGE)
    print(f"✅ Access checks completed")

    # Generate report
    print(manager.generate_isolation_report())

    # Export
    print("\n📄 Exporting isolation config...")
    export = manager.export_isolation_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Multi-tenant isolation manager ready")


if __name__ == "__main__":
    main()
