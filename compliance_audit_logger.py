#!/usr/bin/env python3
"""
Compliance and Audit Logger - Comprehensive audit logging and compliance tracking
Implements audit logging with tamper detection, retention policies, and compliance reporting
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class AuditEventType(Enum):
    """Audit event types"""
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    RESOURCE_ACCESS = "RESOURCE_ACCESS"
    RESOURCE_MODIFY = "RESOURCE_MODIFY"
    RESOURCE_DELETE = "RESOURCE_DELETE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    SECURITY_EVENT = "SECURITY_EVENT"


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOC2 = "SOC2"
    PCI_DSS = "PCI_DSS"
    ISO_27001 = "ISO_27001"


@dataclass
class AuditEntry:
    """Audit log entry"""
    entry_id: str
    event_type: AuditEventType
    actor: str
    action: str
    resource_id: str
    resource_type: str
    timestamp: float
    status: str  # SUCCESS, FAILURE
    details: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None


@dataclass
class CompliancePolicy:
    """Compliance policy"""
    policy_id: str
    framework: ComplianceFramework
    policy_name: str
    description: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class RetentionPolicy:
    """Data retention policy"""
    policy_id: str
    resource_type: str
    retention_days: int
    encryption_required: bool
    deletion_method: str  # SOFT_DELETE, HARD_DELETE, ARCHIVE
    created_at: float = field(default_factory=time.time)


class ComplianceAuditLogger:
    """
    Compliance and Audit Logger

    Provides:
    - Comprehensive audit logging
    - Tamper detection
    - Compliance policy enforcement
    - Retention policies
    - Access reporting
    - Audit trail verification
    """

    def __init__(self):
        self.audit_logs: List[AuditEntry] = []
        self.compliance_policies: Dict[str, CompliancePolicy] = {}
        self.retention_policies: Dict[str, RetentionPolicy] = {}
        self.compliance_violations: List[Dict] = []
        self.audit_summary: Dict = {}

    def log_event(self,
                 event_type: AuditEventType,
                 actor: str,
                 action: str,
                 resource_id: str,
                 resource_type: str,
                 status: str = "SUCCESS",
                 details: Dict[str, Any] = None) -> AuditEntry:
        """Log audit event"""
        entry_id = hashlib.md5(
            f"{actor}:{resource_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        entry = AuditEntry(
            entry_id=entry_id,
            event_type=event_type,
            actor=actor,
            action=action,
            resource_id=resource_id,
            resource_type=resource_type,
            timestamp=time.time(),
            status=status,
            details=details or {}
        )

        # Calculate checksum for tamper detection
        entry_str = json.dumps({
            "entry_id": entry.entry_id,
            "event_type": entry.event_type.value,
            "actor": entry.actor,
            "resource_id": entry.resource_id,
            "timestamp": entry.timestamp,
        }, sort_keys=True)
        entry.checksum = hashlib.sha256(entry_str.encode()).hexdigest()

        self.audit_logs.append(entry)

        # Check compliance policies
        self._check_compliance(entry)

        return entry

    def _check_compliance(self, entry: AuditEntry):
        """Check if event violates compliance policies"""
        for policy in self.compliance_policies.values():
            if not policy.enabled:
                continue

            for rule in policy.rules:
                if self._check_rule(entry, rule):
                    self.compliance_violations.append({
                        "entry_id": entry.entry_id,
                        "policy_id": policy.policy_id,
                        "framework": policy.framework.value,
                        "violation_type": rule.get("type"),
                        "timestamp": time.time()
                    })

    def _check_rule(self, entry: AuditEntry, rule: Dict) -> bool:
        """Check if entry violates rule"""
        rule_type = rule.get("type")

        if rule_type == "UNAUTHORIZED_ACCESS":
            if entry.status == "FAILURE" and entry.event_type == AuditEventType.RESOURCE_ACCESS:
                return True

        elif rule_type == "UNAUTHORIZED_MODIFICATION":
            if entry.event_type in [AuditEventType.RESOURCE_MODIFY, AuditEventType.RESOURCE_DELETE]:
                if entry.actor not in rule.get("allowed_actors", []):
                    return True

        elif rule_type == "SENSITIVE_DATA_ACCESS":
            if "sensitive" in entry.details:
                return True

        return False

    def register_compliance_policy(self,
                                  framework: ComplianceFramework,
                                  policy_name: str,
                                  description: str,
                                  rules: List[Dict] = None) -> CompliancePolicy:
        """Register compliance policy"""
        policy_id = hashlib.md5(
            f"{framework.value}:{policy_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = CompliancePolicy(
            policy_id=policy_id,
            framework=framework,
            policy_name=policy_name,
            description=description,
            rules=rules or []
        )

        self.compliance_policies[policy_id] = policy
        return policy

    def set_retention_policy(self,
                            resource_type: str,
                            retention_days: int,
                            encryption_required: bool = True,
                            deletion_method: str = "HARD_DELETE") -> RetentionPolicy:
        """Set retention policy for resource type"""
        policy_id = hashlib.md5(
            f"{resource_type}:{retention_days}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = RetentionPolicy(
            policy_id=policy_id,
            resource_type=resource_type,
            retention_days=retention_days,
            encryption_required=encryption_required,
            deletion_method=deletion_method
        )

        self.retention_policies[policy_id] = policy
        return policy

    def enforce_retention(self) -> int:
        """Enforce retention policies"""
        now = time.time()
        deleted_count = 0

        for policy in self.retention_policies.values():
            cutoff_time = now - (policy.retention_days * 86400)  # Convert days to seconds

            entries_to_delete = [e for e in self.audit_logs
                               if e.resource_type == policy.resource_type and
                               e.timestamp < cutoff_time]

            for entry in entries_to_delete:
                if policy.deletion_method == "HARD_DELETE":
                    self.audit_logs.remove(entry)
                    deleted_count += 1

        return deleted_count

    def verify_audit_integrity(self) -> Dict:
        """Verify audit trail integrity"""
        issues = []

        for i in range(len(self.audit_logs) - 1):
            current = self.audit_logs[i]
            next_entry = self.audit_logs[i + 1]

            # Verify timestamp sequence
            if current.timestamp > next_entry.timestamp:
                issues.append({
                    "type": "TIMESTAMP_SEQUENCE",
                    "entry_id": current.entry_id,
                    "issue": "Timestamp not in ascending order"
                })

            # Verify checksum
            entry_str = json.dumps({
                "entry_id": current.entry_id,
                "event_type": current.event_type.value,
                "actor": current.actor,
                "resource_id": current.resource_id,
                "timestamp": current.timestamp,
            }, sort_keys=True)
            calculated_checksum = hashlib.sha256(entry_str.encode()).hexdigest()

            if current.checksum != calculated_checksum:
                issues.append({
                    "type": "CHECKSUM_MISMATCH",
                    "entry_id": current.entry_id,
                    "issue": "Entry may have been tampered with"
                })

        return {
            "total_entries": len(self.audit_logs),
            "integrity_issues": len(issues),
            "issues": issues
        }

    def generate_compliance_report(self, framework: ComplianceFramework = None) -> str:
        """Generate compliance report"""
        frameworks_to_report = [p.framework for p in self.compliance_policies.values()]
        if framework:
            frameworks_to_report = [framework]

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              COMPLIANCE AND AUDIT LOGGER REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 AUDIT STATISTICS:
├─ Total Entries: {len(self.audit_logs)}
├─ Compliance Violations: {len(self.compliance_violations)}
├─ Compliance Policies: {len(self.compliance_policies)}
└─ Retention Policies: {len(self.retention_policies)}

🔒 COMPLIANCE FRAMEWORKS:
"""

        for policy in self.compliance_policies.values():
            violations = sum(1 for v in self.compliance_violations
                           if v["framework"] == policy.framework.value)
            report += f"  {policy.framework.value}: {violations} violations\n"

        report += f"\n📋 RECENT EVENTS:\n"
        for entry in self.audit_logs[-10:]:
            report += f"  [{entry.entry_id}] {entry.event_type.value}\n"
            report += f"    Actor: {entry.actor}, Status: {entry.status}\n"

        integrity = self.verify_audit_integrity()
        report += f"\n🔐 INTEGRITY CHECK:\n"
        report += f"  Issues Found: {integrity['integrity_issues']}\n"

        return report

    def export_audit_config(self) -> str:
        """Export audit configuration"""
        integrity = self.verify_audit_integrity()

        export_data = {
            "timestamp": time.time(),
            "statistics": {
                "total_entries": len(self.audit_logs),
                "violations": len(self.compliance_violations),
                "policies": len(self.compliance_policies),
            },
            "integrity": integrity,
            "compliance_policies": [
                {
                    "framework": p.framework.value,
                    "policy_name": p.policy_name,
                    "enabled": p.enabled,
                    "rules_count": len(p.rules),
                }
                for p in self.compliance_policies.values()
            ],
            "retention_policies": [
                {
                    "resource_type": p.resource_type,
                    "retention_days": p.retention_days,
                }
                for p in self.retention_policies.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔐 Compliance and Audit Logger - Audit Trail Management")
    print("=" * 70)

    logger = ComplianceAuditLogger()

    # Register compliance policies
    print("\n📋 Registering compliance policies...")
    gdpr_policy = logger.register_compliance_policy(
        ComplianceFramework.GDPR,
        "Data Protection",
        "GDPR data protection requirements",
        [
            {"type": "UNAUTHORIZED_ACCESS", "severity": "HIGH"},
            {"type": "SENSITIVE_DATA_ACCESS", "severity": "CRITICAL"}
        ]
    )
    hipaa_policy = logger.register_compliance_policy(
        ComplianceFramework.HIPAA,
        "PHI Protection",
        "Protected Health Information security"
    )
    print(f"✅ Registered {len(logger.compliance_policies)} policies")

    # Set retention policies
    print("\n💾 Setting retention policies...")
    logger.set_retention_policy("user_data", retention_days=365)
    logger.set_retention_policy("transaction_logs", retention_days=2555)
    logger.set_retention_policy("audit_logs", retention_days=2555, encryption_required=True)
    print(f"✅ Set {len(logger.retention_policies)} retention policies")

    # Log audit events
    print("\n📝 Logging audit events...")
    logger.log_event(
        AuditEventType.USER_LOGIN, "user_123", "Login",
        "account_123", "account", status="SUCCESS"
    )
    logger.log_event(
        AuditEventType.RESOURCE_ACCESS, "user_123", "Access",
        "document_456", "document", status="SUCCESS",
        details={"access_level": "READ"}
    )
    logger.log_event(
        AuditEventType.RESOURCE_MODIFY, "user_456", "Update",
        "config_789", "configuration", status="SUCCESS",
        details={"changes": {"timeout": "300s"}}
    )
    logger.log_event(
        AuditEventType.SECURITY_EVENT, "system", "Failed Login",
        "account_123", "account", status="FAILURE",
        details={"attempts": 5, "ip": "192.168.1.100"}
    )
    print(f"✅ Logged {len(logger.audit_logs)} events")
    print(f"   Violations detected: {len(logger.compliance_violations)}")

    # Verify integrity
    print("\n🔐 Verifying audit integrity...")
    integrity = logger.verify_audit_integrity()
    print(f"✅ Integrity check complete: {integrity['integrity_issues']} issues")

    # Enforce retention
    print("\n🧹 Enforcing retention policies...")
    deleted = logger.enforce_retention()
    print(f"✅ Enforced retention: {deleted} entries deleted")

    # Generate report
    print(logger.generate_compliance_report())

    # Export
    print("\n📄 Exporting audit config...")
    export = logger.export_audit_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Compliance and audit logger ready")


if __name__ == "__main__":
    main()
