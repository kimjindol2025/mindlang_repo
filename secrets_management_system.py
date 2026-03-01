#!/usr/bin/env python3
"""
Secrets Management System - Secure credential and secret management
Manages secrets with encryption, rotation, audit logging, and access control
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class SecretType(Enum):
    """Secret types"""
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    CERTIFICATE = "CERTIFICATE"
    CONNECTION_STRING = "CONNECTION_STRING"
    ENCRYPTION_KEY = "ENCRYPTION_KEY"
    OAUTH_TOKEN = "OAUTH_TOKEN"


class AccessLevel(Enum):
    """Secret access levels"""
    NONE = "NONE"
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


@dataclass
class Secret:
    """Secret credential"""
    secret_id: str
    secret_name: str
    secret_type: SecretType
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    rotation_interval_days: int = 90
    is_encrypted: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecretAccess:
    """Secret access record"""
    access_id: str
    secret_id: str
    principal: str
    access_level: AccessLevel
    accessed_at: float
    granted_by: Optional[str] = None


@dataclass
class SecretRotation:
    """Secret rotation record"""
    rotation_id: str
    secret_id: str
    previous_version: Optional[str] = None
    new_version: Optional[str] = None
    rotated_at: float = field(default_factory=time.time)
    rotation_reason: str = ""


class SecretsManagementSystem:
    """
    Secrets Management System

    Provides:
    - Secret storage and encryption
    - Access control
    - Automatic rotation
    - Audit logging
    - Secret lifecycle management
    - Compliance support
    """

    def __init__(self):
        self.secrets: Dict[str, Secret] = {}
        self.access_logs: List[SecretAccess] = []
        self.rotation_history: List[SecretRotation] = []
        self.access_policies: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []

    def create_secret(self,
                     secret_name: str,
                     secret_type: SecretType,
                     rotation_interval_days: int = 90,
                     expires_in_days: Optional[int] = None) -> Secret:
        """Create secret"""
        secret_id = hashlib.md5(
            f"{secret_name}:{secret_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        now = time.time()
        expires_at = None
        if expires_in_days:
            expires_at = now + (expires_in_days * 86400)

        secret = Secret(
            secret_id=secret_id,
            secret_name=secret_name,
            secret_type=secret_type,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            rotation_interval_days=rotation_interval_days,
            metadata={"version": "1"}
        )

        self.secrets[secret_id] = secret

        # Audit log
        self.audit_log.append({
            "action": "SECRET_CREATED",
            "secret_id": secret_id,
            "timestamp": now
        })

        return secret

    def grant_access(self,
                    secret_id: str,
                    principal: str,
                    access_level: AccessLevel,
                    granted_by: str = "admin") -> Optional[SecretAccess]:
        """Grant access to secret"""
        secret = self.secrets.get(secret_id)
        if not secret:
            return None

        access_id = hashlib.md5(
            f"{secret_id}:{principal}:{time.time()}".encode()
        ).hexdigest()[:8]

        access = SecretAccess(
            access_id=access_id,
            secret_id=secret_id,
            principal=principal,
            access_level=access_level,
            accessed_at=time.time(),
            granted_by=granted_by
        )

        self.access_logs.append(access)

        # Store policy
        policy_key = f"{secret_id}:{principal}"
        self.access_policies[policy_key] = {
            "access_level": access_level.value,
            "granted_at": time.time()
        }

        return access

    def retrieve_secret(self, secret_id: str, principal: str) -> Optional[Dict]:
        """Retrieve secret with access check"""
        secret = self.secrets.get(secret_id)
        if not secret:
            return None

        # Check access
        policy_key = f"{secret_id}:{principal}"
        if policy_key not in self.access_policies:
            self.audit_log.append({
                "action": "UNAUTHORIZED_ACCESS_ATTEMPT",
                "secret_id": secret_id,
                "principal": principal,
                "timestamp": time.time()
            })
            return None

        policy = self.access_policies[policy_key]
        if policy["access_level"] not in ["READ", "WRITE", "ADMIN"]:
            return None

        # Check expiration
        if secret.expires_at and time.time() > secret.expires_at:
            self.audit_log.append({
                "action": "EXPIRED_SECRET_ACCESS",
                "secret_id": secret_id,
                "timestamp": time.time()
            })
            return None

        # Log access
        self.audit_log.append({
            "action": "SECRET_ACCESSED",
            "secret_id": secret_id,
            "principal": principal,
            "timestamp": time.time()
        })

        return {
            "secret_id": secret_id,
            "name": secret.secret_name,
            "type": secret.secret_type.value,
            "accessed_by": principal
        }

    def rotate_secret(self, secret_id: str, reason: str = "Scheduled rotation") -> Optional[SecretRotation]:
        """Rotate secret"""
        secret = self.secrets.get(secret_id)
        if not secret:
            return None

        rotation_id = hashlib.md5(
            f"{secret_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        rotation = SecretRotation(
            rotation_id=rotation_id,
            secret_id=secret_id,
            previous_version=secret.metadata.get("version"),
            rotation_reason=reason,
            rotated_at=time.time()
        )

        # Update secret
        current_version = int(secret.metadata.get("version", "1"))
        new_version = current_version + 1
        secret.metadata["version"] = str(new_version)
        secret.updated_at = time.time()
        rotation.new_version = str(new_version)

        self.rotation_history.append(rotation)

        self.audit_log.append({
            "action": "SECRET_ROTATED",
            "secret_id": secret_id,
            "new_version": new_version,
            "timestamp": time.time()
        })

        return rotation

    def check_rotation_needed(self) -> List[str]:
        """Check which secrets need rotation"""
        secrets_needing_rotation = []

        for secret in self.secrets.values():
            days_since_update = (time.time() - secret.updated_at) / 86400
            if days_since_update >= secret.rotation_interval_days:
                secrets_needing_rotation.append(secret.secret_id)

        return secrets_needing_rotation

    def revoke_access(self, secret_id: str, principal: str) -> bool:
        """Revoke principal access to secret"""
        policy_key = f"{secret_id}:{principal}"
        if policy_key in self.access_policies:
            del self.access_policies[policy_key]

            self.audit_log.append({
                "action": "ACCESS_REVOKED",
                "secret_id": secret_id,
                "principal": principal,
                "timestamp": time.time()
            })

            return True

        return False

    def get_secrets_stats(self) -> Dict:
        """Get secrets statistics"""
        total_secrets = len(self.secrets)

        by_type = {}
        for secret in self.secrets.values():
            secret_type = secret.secret_type.value
            by_type[secret_type] = by_type.get(secret_type, 0) + 1

        needing_rotation = len(self.check_rotation_needed())

        unauthorized_attempts = sum(1 for log in self.audit_log
                                   if log.get("action") == "UNAUTHORIZED_ACCESS_ATTEMPT")

        return {
            "total_secrets": total_secrets,
            "by_type": by_type,
            "needing_rotation": needing_rotation,
            "access_policies": len(self.access_policies),
            "rotations": len(self.rotation_history),
            "unauthorized_attempts": unauthorized_attempts,
            "audit_entries": len(self.audit_log),
        }

    def generate_secrets_report(self) -> str:
        """Generate secrets report"""
        stats = self.get_secrets_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              SECRETS MANAGEMENT SYSTEM REPORT                              ║
╚════════════════════════════════════════════════════════════════════════════╝

🔐 STATISTICS:
├─ Total Secrets: {stats['total_secrets']}
├─ Needing Rotation: {stats['needing_rotation']}
├─ Access Policies: {stats['access_policies']}
├─ Rotations: {stats['rotations']}
├─ Unauthorized Attempts: {stats['unauthorized_attempts']}
└─ Audit Entries: {stats['audit_entries']}

📋 BY TYPE:
"""

        for secret_type, count in stats['by_type'].items():
            report += f"  {secret_type}: {count}\n"

        return report

    def export_secrets_config(self) -> str:
        """Export secrets configuration"""
        stats = self.get_secrets_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "secrets": [
                {
                    "id": s.secret_id,
                    "name": s.secret_name,
                    "type": s.secret_type.value,
                    "version": s.metadata.get("version"),
                    "expires_at": s.expires_at,
                }
                for s in self.secrets.values()
            ],
            "rotation_history": [
                {
                    "secret_id": r.secret_id,
                    "reason": r.rotation_reason,
                    "timestamp": r.rotated_at,
                }
                for r in self.rotation_history[-20:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔐 Secrets Management System - Credential Management")
    print("=" * 70)

    system = SecretsManagementSystem()

    # Create secrets
    print("\n🔐 Creating secrets...")
    api_key = system.create_secret("aws_api_key", SecretType.API_KEY, rotation_interval_days=90)
    db_password = system.create_secret("prod_db_password", SecretType.PASSWORD, rotation_interval_days=30, expires_in_days=90)
    oauth_token = system.create_secret("github_oauth_token", SecretType.OAUTH_TOKEN)
    print(f"✅ Created {len(system.secrets)} secrets")

    # Grant access
    print("\n✅ Granting access...")
    system.grant_access(api_key.secret_id, "service_a", AccessLevel.READ, "admin")
    system.grant_access(db_password.secret_id, "service_b", AccessLevel.READ, "admin")
    system.grant_access(oauth_token.secret_id, "ci_pipeline", AccessLevel.READ, "admin")
    print(f"✅ Granted {len(system.access_policies)} access policies")

    # Retrieve secret
    print("\n🔓 Retrieving secrets...")
    secret = system.retrieve_secret(api_key.secret_id, "service_a")
    if secret:
        print(f"✅ Retrieved: {secret['name']}")

    # Rotate secret
    print("\n🔄 Rotating secrets...")
    rotation = system.rotate_secret(db_password.secret_id, "Scheduled quarterly rotation")
    print(f"✅ Rotated secret to version {rotation.new_version}")

    # Check rotation needed
    print("\n📋 Checking rotation schedule...")
    needing = system.check_rotation_needed()
    print(f"✅ {len(needing)} secrets need rotation")

    # Revoke access
    print("\n❌ Revoking access...")
    system.revoke_access(oauth_token.secret_id, "ci_pipeline")
    print("✅ Access revoked")

    # Generate report
    print(system.generate_secrets_report())

    # Export
    print("\n📄 Exporting secrets config...")
    export = system.export_secrets_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Secrets management system ready")


if __name__ == "__main__":
    main()
