#!/usr/bin/env python3
"""
Security Incident Response System - Automated incident handling
Manages security incidents with automated response and mitigation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time


class IncidentSeverity(Enum):
    """Incident severity"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentType(Enum):
    """Incident types"""
    DATA_BREACH = "DATA_BREACH"
    MALWARE = "MALWARE"
    DDoS = "DDoS"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    PERFORMANCE_ANOMALY = "PERFORMANCE_ANOMALY"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"


class IncidentStatus(Enum):
    """Incident status"""
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    CONFIRMED = "CONFIRMED"
    CONTAINED = "CONTAINED"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"


class ResponseAction(Enum):
    """Automated response actions"""
    ISOLATE_RESOURCE = "ISOLATE_RESOURCE"
    DISABLE_ACCOUNT = "DISABLE_ACCOUNT"
    BLOCK_IP = "BLOCK_IP"
    RATE_LIMIT = "RATE_LIMIT"
    FAILOVER = "FAILOVER"
    ALERT_TEAM = "ALERT_TEAM"
    REVOKE_TOKENS = "REVOKE_TOKENS"


@dataclass
class SecurityIncident:
    """Security incident"""
    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    detected_at: float
    source_ip: Optional[str] = None
    affected_resource: Optional[str] = None
    affected_users: List[str] = field(default_factory=list)
    status: IncidentStatus = IncidentStatus.DETECTED
    investigation_notes: List[str] = field(default_factory=list)
    response_actions: List[str] = field(default_factory=list)
    resolved_at: Optional[float] = None


@dataclass
class ResponsePlaybook:
    """Automated response playbook"""
    playbook_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    automated_actions: List[ResponseAction] = field(default_factory=list)
    manual_steps: List[str] = field(default_factory=list)
    notification_team: str = "security-team"
    enabled: bool = True


@dataclass
class IncidentTimeline:
    """Incident event timeline"""
    event_id: str
    incident_id: str
    timestamp: float
    event_type: str
    description: str
    actor: str


class SecurityIncidentResponseSystem:
    """
    Security Incident Response System

    Provides:
    - Incident detection and classification
    - Automated response playbooks
    - Investigation workflows
    - Timeline tracking
    - Forensics support
    - Post-incident analysis
    """

    def __init__(self):
        self.incidents: Dict[str, SecurityIncident] = {}
        self.playbooks: Dict[str, ResponsePlaybook] = {}
        self.timelines: Dict[str, List[IncidentTimeline]] = {}
        self.response_history: List[Dict] = []

    def detect_incident(self,
                       incident_type: IncidentType,
                       severity: IncidentSeverity,
                       title: str,
                       description: str,
                       source_ip: str = None,
                       affected_resource: str = None) -> SecurityIncident:
        """Detect and create incident"""
        incident_id = hashlib.md5(
            f"{incident_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        incident = SecurityIncident(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            detected_at=time.time(),
            source_ip=source_ip,
            affected_resource=affected_resource
        )

        self.incidents[incident_id] = incident
        self.timelines[incident_id] = []

        # Create initial timeline event
        self._add_timeline_event(
            incident_id,
            "INCIDENT_DETECTED",
            f"Incident detected: {title}",
            "System"
        )

        return incident

    def register_playbook(self,
                         incident_type: IncidentType,
                         severity: IncidentSeverity,
                         automated_actions: List[ResponseAction],
                         manual_steps: List[str] = None) -> ResponsePlaybook:
        """Register response playbook"""
        playbook_id = hashlib.md5(
            f"{incident_type.value}:{severity.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        playbook = ResponsePlaybook(
            playbook_id=playbook_id,
            incident_type=incident_type,
            severity=severity,
            automated_actions=automated_actions,
            manual_steps=manual_steps or []
        )

        self.playbooks[playbook_id] = playbook
        return playbook

    def execute_playbook(self, incident_id: str) -> List[str]:
        """Execute response playbook for incident"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return []

        # Find matching playbook
        playbook = next((p for p in self.playbooks.values()
                        if p.incident_type == incident.incident_type and
                        p.severity == incident.severity), None)

        if not playbook or not playbook.enabled:
            return []

        executed_actions = []

        # Execute automated actions
        for action in playbook.automated_actions:
            result = self._execute_action(incident, action)
            executed_actions.append(action.value)
            incident.response_actions.append(action.value)

            # Add timeline event
            self._add_timeline_event(
                incident_id,
                "ACTION_EXECUTED",
                f"Executed action: {action.value}",
                "AutomatedResponse"
            )

        # Update incident status
        incident.status = IncidentStatus.CONTAINED

        return executed_actions

    def _execute_action(self, incident: SecurityIncident, action: ResponseAction) -> bool:
        """Execute response action"""
        if action == ResponseAction.ISOLATE_RESOURCE:
            # Isolate affected resource
            pass
        elif action == ResponseAction.DISABLE_ACCOUNT:
            # Disable user accounts
            pass
        elif action == ResponseAction.BLOCK_IP:
            # Block source IP
            pass
        elif action == ResponseAction.RATE_LIMIT:
            # Apply rate limiting
            pass
        elif action == ResponseAction.FAILOVER:
            # Failover to backup
            pass
        elif action == ResponseAction.ALERT_TEAM:
            # Alert security team
            pass
        elif action == ResponseAction.REVOKE_TOKENS:
            # Revoke all tokens
            pass

        return True

    def investigate(self,
                   incident_id: str,
                   findings: str) -> bool:
        """Update incident investigation"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return False

        incident.investigation_notes.append(findings)
        incident.status = IncidentStatus.INVESTIGATING

        self._add_timeline_event(
            incident_id,
            "INVESTIGATION_UPDATE",
            findings,
            "Investigator"
        )

        return True

    def confirm_incident(self, incident_id: str) -> bool:
        """Confirm incident as true positive"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return False

        incident.status = IncidentStatus.CONFIRMED

        self._add_timeline_event(
            incident_id,
            "INCIDENT_CONFIRMED",
            "Incident confirmed as true positive",
            "Investigator"
        )

        return True

    def resolve_incident(self, incident_id: str) -> bool:
        """Mark incident as resolved"""
        incident = self.incidents.get(incident_id)
        if not incident:
            return False

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = time.time()

        self._add_timeline_event(
            incident_id,
            "INCIDENT_RESOLVED",
            "Incident resolved",
            "Investigator"
        )

        # Record response
        self.response_history.append({
            "incident_id": incident_id,
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "duration": incident.resolved_at - incident.detected_at,
            "resolved_at": incident.resolved_at
        })

        return True

    def _add_timeline_event(self,
                           incident_id: str,
                           event_type: str,
                           description: str,
                           actor: str):
        """Add event to incident timeline"""
        event_id = hashlib.md5(
            f"{incident_id}:{event_type}:{time.time()}".encode()
        ).hexdigest()[:8]

        event = IncidentTimeline(
            event_id=event_id,
            incident_id=incident_id,
            timestamp=time.time(),
            event_type=event_type,
            description=description,
            actor=actor
        )

        if incident_id not in self.timelines:
            self.timelines[incident_id] = []

        self.timelines[incident_id].append(event)

    def get_incident_stats(self) -> Dict:
        """Get incident statistics"""
        total = len(self.incidents)
        by_status = {}
        by_severity = {}

        for incident in self.incidents.values():
            status = incident.status.value
            severity = incident.severity.value

            by_status[status] = by_status.get(status, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1

        resolved = sum(1 for i in self.incidents.values() if i.status == IncidentStatus.RESOLVED)
        critical = sum(1 for i in self.incidents.values() if i.severity == IncidentSeverity.CRITICAL)

        return {
            "total_incidents": total,
            "by_status": by_status,
            "by_severity": by_severity,
            "resolved": resolved,
            "critical": critical,
            "responses": len(self.response_history),
        }

    def generate_incident_report(self) -> str:
        """Generate incident report"""
        stats = self.get_incident_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              SECURITY INCIDENT RESPONSE REPORT                             ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Incidents: {stats['total_incidents']}
├─ 🔴 Critical: {stats['critical']}
├─ ✅ Resolved: {stats['resolved']}
├─ Responses: {stats['responses']}
└─ Status Distribution:
"""

        for status, count in stats['by_status'].items():
            report += f"  {status}: {count}\n"

        report += f"\n📋 RECENT INCIDENTS:\n"
        for incident in list(self.incidents.values())[-5:]:
            report += f"\n  [{incident.incident_id}] {incident.title}\n"
            report += f"    Severity: {incident.severity.value}\n"
            report += f"    Status: {incident.status.value}\n"

        return report

    def export_incident_config(self) -> str:
        """Export incident configuration"""
        export_data = {
            "timestamp": time.time(),
            "incidents": [
                {
                    "id": i.incident_id,
                    "type": i.incident_type.value,
                    "severity": i.severity.value,
                    "status": i.status.value,
                }
                for i in self.incidents.values()
            ],
            "playbooks": len(self.playbooks),
            "statistics": self.get_incident_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🛡️  Security Incident Response - Automated Incident Handling")
    print("=" * 70)

    system = SecurityIncidentResponseSystem()

    # Register playbooks
    print("\n📋 Registering response playbooks...")
    playbook1 = system.register_playbook(
        IncidentType.DATA_BREACH,
        IncidentSeverity.CRITICAL,
        [ResponseAction.ISOLATE_RESOURCE, ResponseAction.ALERT_TEAM],
        ["Contact legal team", "Notify affected users"]
    )

    playbook2 = system.register_playbook(
        IncidentType.UNAUTHORIZED_ACCESS,
        IncidentSeverity.HIGH,
        [ResponseAction.DISABLE_ACCOUNT, ResponseAction.REVOKE_TOKENS],
        ["Audit access logs", "Force password reset"]
    )

    print(f"✅ Registered {len(system.playbooks)} playbooks")

    # Detect incidents
    print("\n🚨 Detecting security incidents...")
    incident1 = system.detect_incident(
        IncidentType.DATA_BREACH,
        IncidentSeverity.CRITICAL,
        "Potential data breach detected",
        "Unusual data access patterns from external IP",
        source_ip="192.168.1.100",
        affected_resource="customer_db"
    )

    incident2 = system.detect_incident(
        IncidentType.UNAUTHORIZED_ACCESS,
        IncidentSeverity.HIGH,
        "Unauthorized admin account access",
        "Multiple failed login attempts followed by successful access",
        source_ip="10.0.0.50"
    )

    print(f"✅ Detected {len(system.incidents)} incidents")

    # Execute playbooks
    print("\n⚡ Executing response playbooks...")
    actions1 = system.execute_playbook(incident1.incident_id)
    actions2 = system.execute_playbook(incident2.incident_id)
    print(f"✅ Executed {len(actions1) + len(actions2)} actions")

    # Investigate
    print("\n🔍 Investigating incidents...")
    system.investigate(incident1.incident_id, "Confirmed unauthorized data access from IP 192.168.1.100")
    system.confirm_incident(incident1.incident_id)
    print("✅ Investigation completed")

    # Resolve
    print("\n✅ Resolving incidents...")
    system.resolve_incident(incident1.incident_id)
    system.resolve_incident(incident2.incident_id)
    print("✅ Incidents resolved")

    # Generate report
    print(system.generate_incident_report())

    # Export
    print("\n📄 Exporting incident config...")
    export = system.export_incident_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Security incident response ready")


if __name__ == "__main__":
    main()
