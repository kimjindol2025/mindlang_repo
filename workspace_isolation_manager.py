#!/usr/bin/env python3
"""
Workspace Isolation Manager - Logical workspace isolation and management
Manages workspace isolation, permissions, and resource boundaries
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time


class WorkspaceType(Enum):
    """Workspace types"""
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    TESTING = "TESTING"


class MemberRole(Enum):
    """Member roles"""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class ResourceCategory(Enum):
    """Resource categories"""
    COMPUTE = "COMPUTE"
    STORAGE = "STORAGE"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    SECRETS = "SECRETS"


@dataclass
class Workspace:
    """Workspace"""
    workspace_id: str
    workspace_name: str
    workspace_type: WorkspaceType
    created_at: float
    created_by: str
    description: str = ""
    is_active: bool = True


@dataclass
class WorkspaceMember:
    """Workspace member"""
    member_id: str
    workspace_id: str
    user_id: str
    role: MemberRole
    joined_at: float = field(default_factory=time.time)
    permissions: List[str] = field(default_factory=list)


@dataclass
class IsolationBoundary:
    """Isolation boundary"""
    boundary_id: str
    workspace_id: str
    resource_category: ResourceCategory
    restriction_rules: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class WorkspaceIsolationManager:
    """
    Workspace Isolation Manager

    Provides:
    - Workspace creation and management
    - Member and permission management
    - Resource isolation boundaries
    - Cross-workspace access control
    - Workspace-level monitoring
    - Audit logging
    """

    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.members: Dict[str, WorkspaceMember] = {}
        self.isolation_boundaries: List[IsolationBoundary] = []
        self.access_logs: List[Dict] = []
        self.workspace_metrics: Dict[str, Dict] = {}

    def create_workspace(self,
                        workspace_name: str,
                        workspace_type: WorkspaceType,
                        created_by: str,
                        description: str = "") -> Workspace:
        """Create workspace"""
        workspace_id = hashlib.md5(
            f"{workspace_name}:{workspace_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        workspace = Workspace(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            workspace_type=workspace_type,
            created_at=time.time(),
            created_by=created_by,
            description=description
        )

        self.workspaces[workspace_id] = workspace
        self.workspace_metrics[workspace_id] = {
            "members": 0,
            "resources": 0,
            "access_log_entries": 0
        }

        return workspace

    def add_member(self,
                  workspace_id: str,
                  user_id: str,
                  role: MemberRole) -> Optional[WorkspaceMember]:
        """Add member to workspace"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None

        member_id = hashlib.md5(
            f"{workspace_id}:{user_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        member = WorkspaceMember(
            member_id=member_id,
            workspace_id=workspace_id,
            user_id=user_id,
            role=role
        )

        # Set default permissions based on role
        if role == MemberRole.OWNER:
            member.permissions = ["read", "write", "delete", "manage_members", "manage_settings"]
        elif role == MemberRole.ADMIN:
            member.permissions = ["read", "write", "delete", "manage_members"]
        elif role == MemberRole.DEVELOPER:
            member.permissions = ["read", "write", "delete"]
        elif role == MemberRole.VIEWER:
            member.permissions = ["read"]

        self.members[member_id] = member
        self.workspace_metrics[workspace_id]["members"] += 1

        return member

    def remove_member(self, member_id: str) -> bool:
        """Remove member from workspace"""
        member = self.members.get(member_id)
        if not member:
            return False

        workspace_id = member.workspace_id
        del self.members[member_id]

        self.workspace_metrics[workspace_id]["members"] -= 1
        return True

    def set_isolation_boundary(self,
                              workspace_id: str,
                              resource_category: ResourceCategory,
                              restrictions: Dict[str, str]) -> Optional[IsolationBoundary]:
        """Set isolation boundary for resource category"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None

        boundary_id = hashlib.md5(
            f"{workspace_id}:{resource_category.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        boundary = IsolationBoundary(
            boundary_id=boundary_id,
            workspace_id=workspace_id,
            resource_category=resource_category,
            restriction_rules=restrictions
        )

        self.isolation_boundaries.append(boundary)
        return boundary

    def verify_access(self,
                     workspace_id: str,
                     user_id: str,
                     action: str) -> Dict:
        """Verify user access in workspace"""
        # Find member
        member = next((m for m in self.members.values()
                      if m.workspace_id == workspace_id and
                      m.user_id == user_id), None)

        if not member:
            self.access_logs.append({
                "workspace_id": workspace_id,
                "user_id": user_id,
                "action": action,
                "result": "DENIED",
                "reason": "NOT_MEMBER",
                "timestamp": time.time()
            })
            return {"allowed": False, "reason": "NOT_MEMBER"}

        # Check permission
        if action not in member.permissions:
            self.access_logs.append({
                "workspace_id": workspace_id,
                "user_id": user_id,
                "action": action,
                "result": "DENIED",
                "reason": "INSUFFICIENT_PERMISSION",
                "timestamp": time.time()
            })
            return {"allowed": False, "reason": "INSUFFICIENT_PERMISSION"}

        self.access_logs.append({
            "workspace_id": workspace_id,
            "user_id": user_id,
            "action": action,
            "result": "ALLOWED",
            "timestamp": time.time()
        })

        return {"allowed": True}

    def get_workspace_stats(self, workspace_id: str) -> Dict:
        """Get workspace statistics"""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return {}

        members = [m for m in self.members.values()
                  if m.workspace_id == workspace_id]

        by_role = {}
        for member in members:
            role = member.role.value
            by_role[role] = by_role.get(role, 0) + 1

        boundaries = [b for b in self.isolation_boundaries
                     if b.workspace_id == workspace_id]

        workspace_accesses = [l for l in self.access_logs
                             if l.get("workspace_id") == workspace_id]
        denied_accesses = sum(1 for l in workspace_accesses
                             if l.get("result") == "DENIED")

        return {
            "workspace_id": workspace_id,
            "name": workspace.workspace_name,
            "type": workspace.workspace_type.value,
            "members": len(members),
            "by_role": by_role,
            "boundaries": len(boundaries),
            "total_accesses": len(workspace_accesses),
            "denied_accesses": denied_accesses,
        }

    def get_isolation_stats(self) -> Dict:
        """Get isolation statistics"""
        total_workspaces = len(self.workspaces)
        total_members = len(self.members)

        by_type = {}
        for workspace in self.workspaces.values():
            ws_type = workspace.workspace_type.value
            by_type[ws_type] = by_type.get(ws_type, 0) + 1

        denied_accesses = sum(1 for log in self.access_logs
                             if log.get("result") == "DENIED")

        return {
            "total_workspaces": total_workspaces,
            "total_members": total_members,
            "by_type": by_type,
            "isolation_boundaries": len(self.isolation_boundaries),
            "access_logs": len(self.access_logs),
            "denied_accesses": denied_accesses,
        }

    def generate_isolation_report(self) -> str:
        """Generate isolation report"""
        stats = self.get_isolation_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              WORKSPACE ISOLATION MANAGER REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Workspaces: {stats['total_workspaces']}
├─ Total Members: {stats['total_members']}
├─ Isolation Boundaries: {stats['isolation_boundaries']}
├─ Access Logs: {stats['access_logs']}
└─ Denied Accesses: {stats['denied_accesses']}

🔒 BY TYPE:
"""

        for ws_type, count in stats['by_type'].items():
            report += f"  {ws_type}: {count}\n"

        report += f"\n👥 WORKSPACE DETAILS:\n"
        for workspace in list(self.workspaces.values())[:5]:
            ws_stats = self.get_workspace_stats(workspace.workspace_id)
            report += f"\n  {workspace.workspace_name}\n"
            report += f"    Members: {ws_stats['members']}\n"
            report += f"    Boundaries: {ws_stats['boundaries']}\n"

        return report

    def export_isolation_config(self) -> str:
        """Export isolation configuration"""
        stats = self.get_isolation_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "workspaces": [
                {
                    "id": w.workspace_id,
                    "name": w.workspace_name,
                    "type": w.workspace_type.value,
                    "members": sum(1 for m in self.members.values()
                                  if m.workspace_id == w.workspace_id),
                }
                for w in self.workspaces.values()
            ],
            "isolation_boundaries": [
                {
                    "workspace_id": b.workspace_id,
                    "resource_category": b.resource_category.value,
                    "rules_count": len(b.restriction_rules),
                }
                for b in self.isolation_boundaries
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🏢 Workspace Isolation Manager - Workspace Management")
    print("=" * 70)

    manager = WorkspaceIsolationManager()

    # Create workspaces
    print("\n📋 Creating workspaces...")
    dev_ws = manager.create_workspace("Development", WorkspaceType.DEVELOPMENT, "admin", "Development environment")
    prod_ws = manager.create_workspace("Production", WorkspaceType.PRODUCTION, "admin", "Production environment")
    test_ws = manager.create_workspace("Testing", WorkspaceType.TESTING, "admin", "Testing environment")
    print(f"✅ Created {len(manager.workspaces)} workspaces")

    # Add members
    print("\n👥 Adding members...")
    manager.add_member(dev_ws.workspace_id, "alice@company.com", MemberRole.DEVELOPER)
    manager.add_member(dev_ws.workspace_id, "bob@company.com", MemberRole.DEVELOPER)
    manager.add_member(prod_ws.workspace_id, "charlie@company.com", MemberRole.ADMIN)
    manager.add_member(test_ws.workspace_id, "david@company.com", MemberRole.VIEWER)
    print(f"✅ Added {len(manager.members)} members")

    # Set isolation boundaries
    print("\n🔒 Setting isolation boundaries...")
    manager.set_isolation_boundary(
        prod_ws.workspace_id,
        ResourceCategory.DATABASE,
        {"access_level": "read_only", "encryption": "required"}
    )
    manager.set_isolation_boundary(
        prod_ws.workspace_id,
        ResourceCategory.SECRETS,
        {"access_level": "admin_only"}
    )
    print(f"✅ Set {len(manager.isolation_boundaries)} boundaries")

    # Verify access
    print("\n🔐 Verifying access...")
    access1 = manager.verify_access(dev_ws.workspace_id, "alice@company.com", "write")
    access2 = manager.verify_access(prod_ws.workspace_id, "alice@company.com", "write")
    access3 = manager.verify_access(test_ws.workspace_id, "david@company.com", "delete")
    print(f"✅ Access checks completed")

    # Generate report
    print(manager.generate_isolation_report())

    # Export
    print("\n📄 Exporting isolation config...")
    export = manager.export_isolation_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Workspace isolation manager ready")


if __name__ == "__main__":
    main()
