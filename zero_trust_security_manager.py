#!/usr/bin/env python3
"""
Zero Trust Security Manager - Zero trust security model implementation
Implements zero trust principles with continuous verification and least privilege access
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time


class AccessLevel(Enum):
    """Access levels"""
    NONE = "NONE"
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    EXECUTE = "EXECUTE"


class TrustStatus(Enum):
    """Trust status"""
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    SUSPICIOUS = "SUSPICIOUS"
    COMPROMISED = "COMPROMISED"


class VerificationType(Enum):
    """Verification types"""
    MFA = "MFA"
    DEVICE_POSTURE = "DEVICE_POSTURE"
    LOCATION = "LOCATION"
    BEHAVIOR = "BEHAVIOR"
    NETWORK = "NETWORK"


@dataclass
class Principal:
    """User or service principal"""
    principal_id: str
    principal_name: str
    principal_type: str  # USER, SERVICE, WORKLOAD
    trust_status: TrustStatus = TrustStatus.UNVERIFIED
    created_at: float = field(default_factory=time.time)
    last_verified_at: Optional[float] = None
    risk_score: float = 0.0


@dataclass
class AccessPolicy:
    """Zero trust access policy"""
    policy_id: str
    resource_id: str
    principal_id: str
    access_level: AccessLevel
    conditions: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class VerificationChallenge:
    """Verification challenge"""
    challenge_id: str
    principal_id: str
    verification_types: List[VerificationType]
    issued_at: float
    expires_at: float
    completed_at: Optional[float] = None
    verification_results: Dict[str, bool] = field(default_factory=dict)


class ZeroTrustSecurityManager:
    """
    Zero Trust Security Manager

    Provides:
    - Zero trust access control
    - Continuous verification
    - Least privilege enforcement
    - Device posture checking
    - Anomaly detection
    - Trust scoring
    """

    def __init__(self):
        self.principals: Dict[str, Principal] = {}
        self.access_policies: List[AccessPolicy] = []
        self.verification_challenges: Dict[str, VerificationChallenge] = {}
        self.device_inventory: Dict[str, Dict] = {}
        self.access_logs: List[Dict] = []
        self.trust_scores: Dict[str, float] = {}

    def register_principal(self,
                         principal_name: str,
                         principal_type: str) -> Principal:
        """Register principal (user or service)"""
        principal_id = hashlib.md5(
            f"{principal_name}:{principal_type}:{time.time()}".encode()
        ).hexdigest()[:8]

        principal = Principal(
            principal_id=principal_id,
            principal_name=principal_name,
            principal_type=principal_type
        )

        self.principals[principal_id] = principal
        return principal

    def create_access_policy(self,
                            resource_id: str,
                            principal_id: str,
                            access_level: AccessLevel,
                            conditions: Dict[str, str] = None) -> Optional[AccessPolicy]:
        """Create zero trust access policy"""
        if principal_id not in self.principals:
            return None

        policy_id = hashlib.md5(
            f"{resource_id}:{principal_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = AccessPolicy(
            policy_id=policy_id,
            resource_id=resource_id,
            principal_id=principal_id,
            access_level=access_level,
            conditions=conditions or {}
        )

        self.access_policies.append(policy)
        return policy

    def issue_verification_challenge(self,
                                    principal_id: str,
                                    verification_types: List[VerificationType],
                                    ttl_minutes: int = 5) -> Optional[VerificationChallenge]:
        """Issue verification challenge"""
        principal = self.principals.get(principal_id)
        if not principal:
            return None

        challenge_id = hashlib.md5(
            f"{principal_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        now = time.time()
        challenge = VerificationChallenge(
            challenge_id=challenge_id,
            principal_id=principal_id,
            verification_types=verification_types,
            issued_at=now,
            expires_at=now + (ttl_minutes * 60)
        )

        self.verification_challenges[challenge_id] = challenge
        return challenge

    def complete_verification(self,
                             challenge_id: str,
                             results: Dict[str, bool]) -> Optional[VerificationChallenge]:
        """Complete verification challenge"""
        challenge = self.verification_challenges.get(challenge_id)
        if not challenge:
            return None

        if time.time() > challenge.expires_at:
            return None

        challenge.verification_results = results
        challenge.completed_at = time.time()

        # Update principal trust status
        principal = self.principals.get(challenge.principal_id)
        if principal:
            all_passed = all(results.values())
            if all_passed:
                principal.trust_status = TrustStatus.VERIFIED
                principal.last_verified_at = time.time()
            else:
                principal.trust_status = TrustStatus.SUSPICIOUS

        return challenge

    def evaluate_access_request(self,
                               principal_id: str,
                               resource_id: str,
                               requested_access: AccessLevel) -> Dict:
        """Evaluate access request based on zero trust principles"""
        principal = self.principals.get(principal_id)
        if not principal:
            return {"allowed": False, "reason": "PRINCIPAL_NOT_FOUND"}

        # Check trust status
        if principal.trust_status == TrustStatus.UNVERIFIED:
            return {"allowed": False, "reason": "UNVERIFIED"}

        if principal.trust_status == TrustStatus.COMPROMISED:
            return {"allowed": False, "reason": "COMPROMISED"}

        # Check access policies
        applicable_policies = [p for p in self.access_policies
                              if p.principal_id == principal_id and
                              p.resource_id == resource_id]

        if not applicable_policies:
            return {"allowed": False, "reason": "NO_POLICY"}

        policy = applicable_policies[0]

        # Check access level
        access_hierarchy = [AccessLevel.NONE, AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN]
        if access_hierarchy.index(requested_access) > access_hierarchy.index(policy.access_level):
            return {"allowed": False, "reason": "INSUFFICIENT_PRIVILEGE"}

        # Log access
        self.access_logs.append({
            "principal_id": principal_id,
            "resource_id": resource_id,
            "access_level": requested_access.value,
            "allowed": True,
            "timestamp": time.time()
        })

        return {"allowed": True, "reason": "APPROVED"}

    def update_risk_score(self, principal_id: str, risk_factor: float) -> Optional[float]:
        """Update risk score for principal"""
        if principal_id not in self.principals:
            return None

        current_score = self.trust_scores.get(principal_id, 0)
        new_score = min(1.0, max(0, current_score + risk_factor))

        self.trust_scores[principal_id] = new_score

        principal = self.principals[principal_id]
        if new_score > 0.7:
            principal.risk_score = new_score
            principal.trust_status = TrustStatus.SUSPICIOUS

        return new_score

    def get_security_stats(self) -> Dict:
        """Get zero trust security statistics"""
        total_principals = len(self.principals)
        verified = sum(1 for p in self.principals.values()
                      if p.trust_status == TrustStatus.VERIFIED)
        unverified = sum(1 for p in self.principals.values()
                        if p.trust_status == TrustStatus.UNVERIFIED)
        suspicious = sum(1 for p in self.principals.values()
                        if p.trust_status == TrustStatus.SUSPICIOUS)

        return {
            "total_principals": total_principals,
            "verified": verified,
            "unverified": unverified,
            "suspicious": suspicious,
            "access_policies": len(self.access_policies),
            "verification_challenges": len(self.verification_challenges),
            "access_logs": len(self.access_logs),
            "high_risk_principals": sum(1 for s in self.trust_scores.values() if s > 0.7),
        }

    def generate_security_report(self) -> str:
        """Generate zero trust security report"""
        stats = self.get_security_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              ZERO TRUST SECURITY MANAGER REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

🔐 SECURITY STATISTICS:
├─ Total Principals: {stats['total_principals']}
├─ Verified: {stats['verified']}
├─ Unverified: {stats['unverified']}
├─ Suspicious: {stats['suspicious']}
├─ High Risk: {stats['high_risk_principals']}
├─ Access Policies: {stats['access_policies']}
└─ Access Logs: {stats['access_logs']}

👥 PRINCIPALS:
"""

        for principal in list(self.principals.values())[:10]:
            report += f"  {principal.principal_name} ({principal.principal_type})\n"
            report += f"    Status: {principal.trust_status.value}\n"
            report += f"    Risk Score: {principal.risk_score:.2f}\n"

        return report

    def export_security_config(self) -> str:
        """Export security configuration"""
        stats = self.get_security_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "principals": [
                {
                    "id": p.principal_id,
                    "name": p.principal_name,
                    "type": p.principal_type,
                    "trust_status": p.trust_status.value,
                    "risk_score": p.risk_score,
                }
                for p in self.principals.values()
            ],
            "access_policies": [
                {
                    "resource_id": ap.resource_id,
                    "access_level": ap.access_level.value,
                }
                for ap in self.access_policies[:20]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔐 Zero Trust Security Manager - Continuous Verification")
    print("=" * 70)

    manager = ZeroTrustSecurityManager()

    # Register principals
    print("\n👥 Registering principals...")
    user1 = manager.register_principal("alice@company.com", "USER")
    user2 = manager.register_principal("bob@company.com", "USER")
    service1 = manager.register_principal("api-service", "SERVICE")
    print(f"✅ Registered {len(manager.principals)} principals")

    # Create access policies
    print("\n📋 Creating access policies...")
    manager.create_access_policy("database_prod", user1.principal_id, AccessLevel.READ)
    manager.create_access_policy("database_prod", service1.principal_id, AccessLevel.WRITE)
    manager.create_access_policy("admin_panel", user2.principal_id, AccessLevel.ADMIN)
    print(f"✅ Created {len(manager.access_policies)} policies")

    # Issue verification challenges
    print("\n🔐 Issuing verification challenges...")
    challenge1 = manager.issue_verification_challenge(
        user1.principal_id,
        [VerificationType.MFA, VerificationType.DEVICE_POSTURE]
    )
    challenge2 = manager.issue_verification_challenge(
        service1.principal_id,
        [VerificationType.NETWORK]
    )
    print(f"✅ Issued {len(manager.verification_challenges)} challenges")

    # Complete verifications
    print("\n✅ Completing verifications...")
    if challenge1:
        manager.complete_verification(challenge1.challenge_id, {"MFA": True, "DEVICE_POSTURE": True})
    if challenge2:
        manager.complete_verification(challenge2.challenge_id, {"NETWORK": True})
    print("✅ Verifications completed")

    # Evaluate access requests
    print("\n📊 Evaluating access requests...")
    result1 = manager.evaluate_access_request(user1.principal_id, "database_prod", AccessLevel.READ)
    result2 = manager.evaluate_access_request(user2.principal_id, "database_prod", AccessLevel.WRITE)
    print(f"✅ Access evaluations: Allowed={sum(1 for r in [result1, result2] if r['allowed'])}")

    # Update risk scores
    print("\n⚠️  Updating risk scores...")
    manager.update_risk_score(user2.principal_id, 0.3)
    print("✅ Risk scores updated")

    # Generate report
    print(manager.generate_security_report())

    # Export
    print("\n📄 Exporting security config...")
    export = manager.export_security_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Zero trust security manager ready")


if __name__ == "__main__":
    main()
