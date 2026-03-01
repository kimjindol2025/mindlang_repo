#!/usr/bin/env python3
"""
Configuration Management System - Centralized configuration for distributed systems
Manages application configuration with versioning, rollback, and environment support
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class ConfigSource(Enum):
    """Configuration sources"""
    FILE = "FILE"
    ENVIRONMENT = "ENVIRONMENT"
    DATABASE = "DATABASE"
    REMOTE_API = "REMOTE_API"
    GIT = "GIT"


class ConfigEnvironment(Enum):
    """Environments"""
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    CANARY = "CANARY"


class ConfigStatus(Enum):
    """Configuration status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


@dataclass
class ConfigKey:
    """Configuration key-value entry"""
    key_id: str
    key: str
    value: Any
    value_type: str  # string, number, boolean, json, secret
    description: str
    default_value: Optional[Any] = None
    encrypted: bool = False
    immutable: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class ConfigVersion:
    """Configuration version"""
    version_id: str
    version: int
    environment: ConfigEnvironment
    config: Dict[str, ConfigKey]
    status: ConfigStatus
    created_by: str
    created_at: float
    description: str
    parent_version: Optional[str] = None
    change_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigProfile:
    """Configuration profile for specific context"""
    profile_id: str
    profile_name: str
    environment: ConfigEnvironment
    config: Dict[str, ConfigKey]
    active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class ConfigAudit:
    """Audit trail for configuration changes"""
    audit_id: str
    timestamp: float
    action: str  # CREATE, UPDATE, DELETE, PUBLISH, ROLLBACK
    key: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    changed_by: str
    reason: str


class ConfigurationManager:
    """
    Configuration Management System

    Provides:
    - Multi-environment configuration
    - Version control with rollback
    - Secret management
    - Configuration hot-reload
    - Feature flags
    - Audit trail
    - Template support
    """

    def __init__(self, default_env: ConfigEnvironment = ConfigEnvironment.DEVELOPMENT):
        self.default_env = default_env
        self.versions: Dict[str, ConfigVersion] = {}  # version_id -> ConfigVersion
        self.profiles: Dict[str, ConfigProfile] = {}
        self.current_version: Dict[ConfigEnvironment, str] = {}  # env -> version_id
        self.audit_log: List[ConfigAudit] = []
        self.watches: Dict[str, List] = {}  # key -> callbacks

    def create_version(self,
                      environment: ConfigEnvironment,
                      config: Dict[str, ConfigKey],
                      created_by: str,
                      description: str,
                      parent_version: Optional[str] = None) -> ConfigVersion:
        """Create configuration version"""
        version_id = hashlib.md5(
            f"{environment.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Determine version number
        existing = [v for v in self.versions.values() if v.environment == environment]
        version_num = max([v.version for v in existing], default=0) + 1

        version = ConfigVersion(
            version_id=version_id,
            version=version_num,
            environment=environment,
            config=config,
            status=ConfigStatus.DRAFT,
            created_by=created_by,
            created_at=time.time(),
            description=description,
            parent_version=parent_version
        )

        self.versions[version_id] = version
        return version

    def set_key(self,
               version_id: str,
               key: str,
               value: Any,
               value_type: str = "string",
               description: str = "",
               encrypted: bool = False) -> Optional[ConfigKey]:
        """Set configuration key"""
        version = self.versions.get(version_id)
        if not version or version.status != ConfigStatus.DRAFT:
            return None

        key_id = hashlib.md5(f"{key}:{version_id}".encode()).hexdigest()[:8]

        config_key = ConfigKey(
            key_id=key_id,
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            encrypted=encrypted
        )

        version.config[key] = config_key
        return config_key

    def publish_version(self,
                       version_id: str,
                       published_by: str) -> bool:
        """Publish configuration version"""
        version = self.versions.get(version_id)
        if not version:
            return False

        # Save previous version if exists
        old_version_id = self.current_version.get(version.environment)

        version.status = ConfigStatus.PUBLISHED
        self.current_version[version.environment] = version_id

        # Trigger watchers
        self._trigger_watchers(version.environment)

        # Audit
        self._audit("PUBLISH", f"version_{version_id}", None, version_id, published_by, "Version published")

        return True

    def rollback_version(self,
                        environment: ConfigEnvironment,
                        rollback_by: str) -> bool:
        """Rollback to previous version"""
        current_id = self.current_version.get(environment)
        if not current_id:
            return False

        current = self.versions.get(current_id)
        if not current or not current.parent_version:
            return False

        parent = self.versions.get(current.parent_version)
        if not parent:
            return False

        self.current_version[environment] = current.parent_version
        current.status = ConfigStatus.DEPRECATED

        self._trigger_watchers(environment)
        self._audit("ROLLBACK", f"version_{current_id}", current_id, current.parent_version, rollback_by, "Rolled back to previous version")

        return True

    def get_active_config(self, environment: ConfigEnvironment = None) -> Dict[str, Any]:
        """Get active configuration"""
        env = environment or self.default_env
        version_id = self.current_version.get(env)

        if not version_id:
            return {}

        version = self.versions.get(version_id)
        if not version:
            return {}

        return {k: v.value for k, v in version.config.items()}

    def get_key(self,
               key: str,
               environment: ConfigEnvironment = None) -> Optional[Any]:
        """Get configuration key value"""
        config = self.get_active_config(environment)
        return config.get(key)

    def watch_key(self,
                 key: str,
                 callback) -> str:
        """Watch for key changes"""
        watch_id = hashlib.md5(f"{key}:{time.time()}".encode()).hexdigest()[:8]

        if key not in self.watches:
            self.watches[key] = []

        self.watches[key].append(callback)
        return watch_id

    def _trigger_watchers(self, environment: ConfigEnvironment):
        """Trigger watchers for environment changes"""
        config = self.get_active_config(environment)
        for key, callbacks in self.watches.items():
            if key in config:
                for callback in callbacks:
                    try:
                        callback(key, config[key])
                    except Exception as e:
                        print(f"Error in watcher: {e}")

    def create_profile(self,
                      profile_name: str,
                      environment: ConfigEnvironment,
                      config: Dict[str, ConfigKey]) -> ConfigProfile:
        """Create configuration profile"""
        profile_id = hashlib.md5(
            f"{profile_name}:{environment.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        profile = ConfigProfile(
            profile_id=profile_id,
            profile_name=profile_name,
            environment=environment,
            config=config
        )

        self.profiles[profile_id] = profile
        return profile

    def activate_profile(self, profile_id: str) -> bool:
        """Activate configuration profile"""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        # Deactivate others in same environment
        for p in self.profiles.values():
            if p.environment == profile.environment and p.profile_id != profile_id:
                p.active = False

        profile.active = True
        self._trigger_watchers(profile.environment)
        return True

    def validate_config(self, version_id: str) -> List[str]:
        """Validate configuration"""
        version = self.versions.get(version_id)
        if not version:
            return ["Version not found"]

        errors = []

        # Check required keys
        required_keys = {"database_url", "api_key"}
        config_keys = set(version.config.keys())
        missing = required_keys - config_keys
        if missing:
            errors.append(f"Missing required keys: {missing}")

        # Validate types
        for key, config_key in version.config.items():
            if config_key.value_type == "number":
                try:
                    float(config_key.value)
                except:
                    errors.append(f"Key '{key}' is not a valid number")

        return errors

    def export_config(self, version_id: str) -> str:
        """Export configuration as JSON"""
        version = self.versions.get(version_id)
        if not version:
            return "{}"

        export_data = {
            "version": version.version,
            "environment": version.environment.value,
            "status": version.status.value,
            "created_at": version.created_at,
            "config": {k: v.value for k, v in version.config.items()}
        }
        return json.dumps(export_data, indent=2)

    def _audit(self,
              action: str,
              key: str,
              old_value: Optional[Any],
              new_value: Optional[Any],
              changed_by: str,
              reason: str):
        """Record audit entry"""
        audit_id = hashlib.md5(f"{time.time()}:{key}".encode()).hexdigest()[:8]
        audit = ConfigAudit(
            audit_id=audit_id,
            timestamp=time.time(),
            action=action,
            key=key,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason
        )
        self.audit_log.append(audit)

    def get_config_stats(self) -> Dict:
        """Get configuration statistics"""
        return {
            "total_versions": len(self.versions),
            "environments": list(set(v.environment.value for v in self.versions.values())),
            "profiles": len(self.profiles),
            "audit_entries": len(self.audit_log),
            "active_versions": len(self.current_version),
        }

    def generate_config_report(self) -> str:
        """Generate configuration report"""
        stats = self.get_config_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              CONFIGURATION MANAGEMENT REPORT                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Versions: {stats['total_versions']}
├─ Environments: {', '.join(stats['environments'])}
├─ Profiles: {stats['profiles']}
├─ Active Versions: {stats['active_versions']}
└─ Audit Entries: {stats['audit_entries']}

📌 ACTIVE VERSIONS:
"""

        for env, version_id in self.current_version.items():
            version = self.versions.get(version_id)
            if version:
                report += f"\n  {env.value} (v{version.version})\n"
                report += f"    Status: {version.status.value}\n"
                report += f"    Keys: {len(version.config)}\n"

        report += f"\n📋 RECENT CHANGES:\n"
        for audit in self.audit_log[-5:]:
            report += f"  {audit.action}: {audit.key} (by {audit.changed_by})\n"

        return report


def main():
    """CLI interface"""
    print("⚙️  Configuration Management System - Centralized Config Management")
    print("=" * 70)

    manager = ConfigurationManager()

    # Create configurations
    print("\n📝 Creating configurations...")

    dev_config = {}
    dev_config["database_url"] = ConfigKey(
        key_id="db1", key="database_url",
        value="postgres://localhost:5432/dev", value_type="string",
        description="Development database"
    )
    dev_config["api_key"] = ConfigKey(
        key_id="api1", key="api_key",
        value="dev_key_12345", value_type="string",
        description="API key for services", encrypted=True
    )

    dev_version = manager.create_version(
        ConfigEnvironment.DEVELOPMENT,
        dev_config,
        "admin",
        "Initial development config"
    )
    print(f"✅ Created development config v{dev_version.version}")

    prod_config = {}
    prod_config["database_url"] = ConfigKey(
        key_id="db2", key="database_url",
        value="postgres://prod-db:5432/main", value_type="string",
        description="Production database"
    )
    prod_config["api_key"] = ConfigKey(
        key_id="api2", key="api_key",
        value="prod_key_99999", value_type="string",
        description="Production API key", encrypted=True
    )

    prod_version = manager.create_version(
        ConfigEnvironment.PRODUCTION,
        prod_config,
        "admin",
        "Initial production config"
    )
    print(f"✅ Created production config v{prod_version.version}")

    # Publish versions
    print("\n🔄 Publishing configurations...")
    manager.publish_version(dev_version.version_id, "admin")
    manager.publish_version(prod_version.version_id, "admin")
    print("✅ Configurations published")

    # Get active config
    print("\n📖 Retrieving active config...")
    dev_active = manager.get_active_config(ConfigEnvironment.DEVELOPMENT)
    print(f"✅ Dev config keys: {list(dev_active.keys())}")

    # Validate
    print("\n✅ Validating configurations...")
    errors = manager.validate_config(dev_version.version_id)
    print(f"✅ Validation: {'PASSED' if not errors else errors}")

    # Export
    print("\n📄 Exporting configurations...")
    export = manager.export_config(dev_version.version_id)
    print(f"✅ Exported {len(export)} characters")

    # Generate report
    print(manager.generate_config_report())

    print("\n" + "=" * 70)
    print("✨ Configuration management ready")


if __name__ == "__main__":
    main()
