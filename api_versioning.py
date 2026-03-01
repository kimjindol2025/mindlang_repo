#!/usr/bin/env python3
"""
API Versioning Manager - Multi-version API support and lifecycle management
Manages API versions, deprecation, and backward compatibility
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class APIStatus(Enum):
    """API version status"""
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"


class BreakingChange(Enum):
    """Types of breaking changes"""
    FIELD_REMOVED = "FIELD_REMOVED"
    FIELD_RENAMED = "FIELD_RENAMED"
    TYPE_CHANGED = "TYPE_CHANGED"
    ENDPOINT_REMOVED = "ENDPOINT_REMOVED"
    REQUIRED_PARAMETER_ADDED = "REQUIRED_PARAMETER_ADDED"
    RESPONSE_FORMAT_CHANGED = "RESPONSE_FORMAT_CHANGED"


@dataclass
class APIEndpoint:
    """API endpoint definition"""
    endpoint_id: str
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str
    parameters: Dict[str, str]
    response_schema: Dict[str, Any]
    deprecated: bool = False
    replacement_endpoint: Optional[str] = None


@dataclass
class APIVersion:
    """API version"""
    version_id: str
    version: str  # v1, v2, v1.1
    status: APIStatus
    endpoints: Dict[str, APIEndpoint] = field(default_factory=dict)
    released_at: float = field(default_factory=time.time)
    sunset_date: Optional[float] = None
    breaking_changes: List[str] = field(default_factory=list)
    migration_guide: str = ""


@dataclass
class APIClient:
    """API client"""
    client_id: str
    client_name: str
    supported_versions: List[str]
    current_version: str
    migration_status: str = "NONE"  # NONE, IN_PROGRESS, COMPLETED


@dataclass
class APIUsageMetric:
    """API usage metric"""
    metric_id: str
    version: str
    endpoint: str
    timestamp: float
    request_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0


@dataclass
class MigrationPlan:
    """API migration plan for client"""
    plan_id: str
    client_id: str
    from_version: str
    to_version: str
    timeline_days: int
    breaking_changes_count: int
    estimated_effort: str  # LOW, MEDIUM, HIGH
    status: str = "PLANNING"  # PLANNING, IN_PROGRESS, COMPLETED


class APIVersioningManager:
    """
    API Versioning Manager

    Provides:
    - Multi-version API support
    - Breaking change tracking
    - Deprecation management
    - Migration planning
    - Usage tracking
    - Backward compatibility
    """

    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.clients: Dict[str, APIClient] = {}
        self.usage_metrics: List[APIUsageMetric] = []
        self.migration_plans: Dict[str, MigrationPlan] = {}
        self.breaking_changes: Dict[str, List[str]] = {}  # version -> changes

    def create_version(self,
                      version: str,
                      status: APIStatus = APIStatus.BETA,
                      endpoints: Dict[str, APIEndpoint] = None) -> APIVersion:
        """Create API version"""
        version_id = hashlib.md5(f"{version}:{time.time()}".encode()).hexdigest()[:8]

        api_version = APIVersion(
            version_id=version_id,
            version=version,
            status=status,
            endpoints=endpoints or {}
        )

        self.versions[version_id] = api_version
        self.breaking_changes[version] = []

        return api_version

    def add_endpoint(self,
                    version_id: str,
                    path: str,
                    method: str,
                    description: str,
                    parameters: Dict[str, str],
                    response_schema: Dict[str, Any]) -> Optional[APIEndpoint]:
        """Add endpoint to version"""
        version = self.versions.get(version_id)
        if not version:
            return None

        endpoint_id = hashlib.md5(
            f"{version_id}:{path}:{method}".encode()
        ).hexdigest()[:8]

        endpoint = APIEndpoint(
            endpoint_id=endpoint_id,
            path=path,
            method=method,
            description=description,
            parameters=parameters,
            response_schema=response_schema
        )

        version.endpoints[endpoint_id] = endpoint
        return endpoint

    def detect_breaking_changes(self,
                               from_version: str,
                               to_version: str) -> List[BreakingChange]:
        """Detect breaking changes between versions"""
        changes = []

        from_ver = self._get_version_by_name(from_version)
        to_ver = self._get_version_by_name(to_version)

        if not from_ver or not to_ver:
            return changes

        # Check for removed endpoints
        from_paths = set(ep.path for ep in from_ver.endpoints.values())
        to_paths = set(ep.path for ep in to_ver.endpoints.values())

        removed = from_paths - to_paths
        for path in removed:
            changes.append(BreakingChange.ENDPOINT_REMOVED)

        # Check for response schema changes
        for from_ep in from_ver.endpoints.values():
            to_ep = next((ep for ep in to_ver.endpoints.values()
                         if ep.path == from_ep.path and ep.method == from_ep.method), None)

            if to_ep:
                # Check for removed fields
                from_fields = set(from_ep.response_schema.keys())
                to_fields = set(to_ep.response_schema.keys())

                removed_fields = from_fields - to_fields
                if removed_fields:
                    changes.append(BreakingChange.FIELD_REMOVED)

                # Check for type changes
                for field_name in from_fields & to_fields:
                    if from_ep.response_schema[field_name] != to_ep.response_schema[field_name]:
                        changes.append(BreakingChange.TYPE_CHANGED)

        return changes

    def register_client(self,
                       client_name: str,
                       current_version: str,
                       supported_versions: List[str] = None) -> APIClient:
        """Register API client"""
        client_id = hashlib.md5(f"{client_name}:{time.time()}".encode()).hexdigest()[:8]

        supported = supported_versions or [current_version]

        client = APIClient(
            client_id=client_id,
            client_name=client_name,
            current_version=current_version,
            supported_versions=supported
        )

        self.clients[client_id] = client
        return client

    def plan_migration(self,
                      client_id: str,
                      from_version: str,
                      to_version: str) -> MigrationPlan:
        """Plan API migration for client"""
        plan_id = hashlib.md5(
            f"{client_id}:{from_version}:{to_version}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Detect breaking changes
        breaking_changes = self.detect_breaking_changes(from_version, to_version)

        # Estimate effort
        if len(breaking_changes) == 0:
            effort = "LOW"
            timeline = 7
        elif len(breaking_changes) <= 3:
            effort = "MEDIUM"
            timeline = 14
        else:
            effort = "HIGH"
            timeline = 30

        plan = MigrationPlan(
            plan_id=plan_id,
            client_id=client_id,
            from_version=from_version,
            to_version=to_version,
            timeline_days=timeline,
            breaking_changes_count=len(breaking_changes),
            estimated_effort=effort
        )

        self.migration_plans[plan_id] = plan

        # Update client migration status
        client = self.clients.get(client_id)
        if client:
            client.migration_status = "IN_PROGRESS"

        return plan

    def complete_migration(self, plan_id: str) -> bool:
        """Mark migration as completed"""
        plan = self.migration_plans.get(plan_id)
        if not plan:
            return False

        plan.status = "COMPLETED"

        client = self.clients.get(plan.client_id)
        if client:
            client.current_version = plan.to_version
            client.migration_status = "COMPLETED"

        return True

    def deprecate_version(self,
                         version_id: str,
                         sunset_days: int = 90) -> bool:
        """Deprecate API version"""
        version = self.versions.get(version_id)
        if not version:
            return False

        version.status = APIStatus.DEPRECATED
        version.sunset_date = time.time() + (sunset_days * 86400)

        return True

    def record_usage(self,
                    version: str,
                    endpoint: str,
                    request_count: int = 1,
                    error_count: int = 0,
                    response_time_ms: float = 0.0):
        """Record API usage metric"""
        metric_id = hashlib.md5(
            f"{version}:{endpoint}:{time.time()}".encode()
        ).hexdigest()[:8]

        metric = APIUsageMetric(
            metric_id=metric_id,
            version=version,
            endpoint=endpoint,
            timestamp=time.time(),
            request_count=request_count,
            error_count=error_count,
            avg_response_time_ms=response_time_ms
        )

        self.usage_metrics.append(metric)

    def _get_version_by_name(self, version_name: str) -> Optional[APIVersion]:
        """Get version by name"""
        for version in self.versions.values():
            if version.version == version_name:
                return version
        return None

    def get_versioning_stats(self) -> Dict:
        """Get versioning statistics"""
        return {
            "total_versions": len(self.versions),
            "active_versions": sum(1 for v in self.versions.values() if v.status == APIStatus.ACTIVE),
            "deprecated_versions": sum(1 for v in self.versions.values() if v.status == APIStatus.DEPRECATED),
            "clients": len(self.clients),
            "migrations": len(self.migration_plans),
            "completed_migrations": sum(1 for p in self.migration_plans.values() if p.status == "COMPLETED"),
            "api_calls": sum(m.request_count for m in self.usage_metrics),
        }

    def generate_versioning_report(self) -> str:
        """Generate versioning report"""
        stats = self.get_versioning_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              API VERSIONING REPORT                                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Versions: {stats['total_versions']}
├─ 🟢 Active: {stats['active_versions']}
├─ 🟡 Deprecated: {stats['deprecated_versions']}
├─ Clients: {stats['clients']}
├─ API Calls: {stats['api_calls']}
└─ Migrations: {stats['completed_migrations']}/{stats['migrations']}

📌 API VERSIONS:
"""

        for version in self.versions.values():
            status_emoji = "🟢" if version.status == APIStatus.ACTIVE else "🟡"
            report += f"\n  {status_emoji} {version.version}\n"
            report += f"    Status: {version.status.value}\n"
            report += f"    Endpoints: {len(version.endpoints)}\n"
            if version.sunset_date:
                days_left = (version.sunset_date - time.time()) / 86400
                report += f"    Sunset: {days_left:.0f} days\n"

        return report

    def export_versioning_config(self) -> str:
        """Export versioning configuration"""
        export_data = {
            "timestamp": time.time(),
            "versions": [
                {
                    "version": v.version,
                    "status": v.status.value,
                    "endpoints": len(v.endpoints),
                    "released_at": v.released_at,
                }
                for v in self.versions.values()
            ],
            "clients": [
                {
                    "name": c.client_name,
                    "current_version": c.current_version,
                    "supported_versions": c.supported_versions,
                }
                for c in self.clients.values()
            ],
            "statistics": self.get_versioning_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 API Versioning Manager - Multi-Version API Lifecycle")
    print("=" * 70)

    manager = APIVersioningManager()

    # Create versions
    print("\n📝 Creating API versions...")

    # Version 1.0
    v1 = manager.create_version("v1.0", APIStatus.ACTIVE)
    manager.add_endpoint(
        v1.version_id,
        "/api/users",
        "GET",
        "Get all users",
        {"limit": "int", "offset": "int"},
        {"users": ["object"], "total": "int"}
    )
    manager.add_endpoint(
        v1.version_id,
        "/api/users/{id}",
        "GET",
        "Get user by ID",
        {"id": "string"},
        {"id": "string", "name": "string", "email": "string"}
    )
    print(f"✅ Created v1.0 with {len(v1.endpoints)} endpoints")

    # Version 2.0 (with breaking changes)
    v2 = manager.create_version("v2.0", APIStatus.ACTIVE)
    manager.add_endpoint(
        v2.version_id,
        "/api/v2/users",
        "GET",
        "Get all users",
        {"limit": "int", "offset": "int", "filter": "string"},
        {"data": ["object"], "pagination": "object"}  # Changed response format
    )
    manager.add_endpoint(
        v2.version_id,
        "/api/v2/users/{id}",
        "GET",
        "Get user by ID",
        {"id": "string"},
        {"data": "object"}
    )
    print(f"✅ Created v2.0 with {len(v2.endpoints)} endpoints")

    # Detect breaking changes
    print("\n🔍 Detecting breaking changes...")
    changes = manager.detect_breaking_changes("v1.0", "v2.0")
    print(f"✅ Found {len(changes)} breaking changes")

    # Register clients
    print("\n👥 Registering API clients...")
    client1 = manager.register_client("mobile-app", "v1.0", ["v1.0", "v2.0"])
    client2 = manager.register_client("web-app", "v1.0", ["v1.0"])
    print(f"✅ Registered {len(manager.clients)} clients")

    # Plan migrations
    print("\n🔄 Planning migrations...")
    plan = manager.plan_migration(client1.client_id, "v1.0", "v2.0")
    print(f"✅ Migration plan: {plan.estimated_effort} effort, {plan.timeline_days} days")

    # Record usage
    print("\n📊 Recording usage...")
    manager.record_usage("v1.0", "/api/users", request_count=1000, error_count=10)
    manager.record_usage("v2.0", "/api/v2/users", request_count=500, error_count=5)
    print(f"✅ Recorded usage metrics")

    # Complete migration
    print("\n✅ Completing migration...")
    manager.complete_migration(plan.plan_id)
    print(f"✅ Migration completed")

    # Generate report
    print(manager.generate_versioning_report())

    # Export
    print("\n📄 Exporting versioning config...")
    export = manager.export_versioning_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ API versioning manager ready")


if __name__ == "__main__":
    main()
