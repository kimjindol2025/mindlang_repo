#!/usr/bin/env python3
"""
Database Migration Tool - Schema versioning and data migration management
Handles database schema changes, rollback strategies, and migration validation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable
import hashlib
import json
import time
import random


class MigrationType(Enum):
    """Types of migrations"""
    SCHEMA = "SCHEMA"
    DATA = "DATA"
    INDEX = "INDEX"
    SECURITY = "SECURITY"
    REFERENCE = "REFERENCE"


class MigrationStatus(Enum):
    """Status of migration execution"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class DatabaseType(Enum):
    """Supported databases"""
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    MONGODB = "MONGODB"
    CASSANDRA = "CASSANDRA"
    DYNAMODB = "DYNAMODB"
    SNOWFLAKE = "SNOWFLAKE"


class RollbackStrategy(Enum):
    """Rollback strategies"""
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    NONE = "NONE"
    SHADOW = "SHADOW"  # Shadow database for testing


@dataclass
class MigrationStep:
    """Individual migration step"""
    step_id: str
    name: str
    description: str
    migration_type: MigrationType
    up_script: str  # Forward migration SQL
    down_script: str  # Rollback SQL
    estimated_duration: int = 0  # seconds
    requires_downtime: bool = False
    safety_checks: List[str] = field(default_factory=list)
    order: int = 0


@dataclass
class Migration:
    """Complete migration"""
    migration_id: str
    version: str
    description: str
    database: DatabaseType
    created_by: str
    created_at: float
    steps: List[MigrationStep] = field(default_factory=list)
    rollback_strategy: RollbackStrategy = RollbackStrategy.AUTOMATIC
    estimated_total_duration: int = 0
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    affected_tables: List[str] = field(default_factory=list)
    data_impact: str = ""


@dataclass
class MigrationExecution:
    """Execution of a migration"""
    execution_id: str
    migration_id: str
    database: DatabaseType
    status: MigrationStatus
    started_at: float
    completed_at: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0
    rows_affected: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rollback_executed: bool = False
    execution_time: float = 0.0


@dataclass
class SchemaSnapshot:
    """Snapshot of database schema"""
    snapshot_id: str
    database: DatabaseType
    timestamp: float
    tables: Dict[str, Dict] = field(default_factory=dict)  # table_name -> schema
    indexes: Dict[str, List] = field(default_factory=dict)
    constraints: Dict[str, List] = field(default_factory=dict)
    procedures: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    hash: str = ""


@dataclass
class MigrationValidationResult:
    """Result of migration validation"""
    migration_id: str
    is_valid: bool
    syntax_errors: List[str] = field(default_factory=list)
    runtime_warnings: List[str] = field(default_factory=list)
    data_validation_issues: List[str] = field(default_factory=list)
    estimated_impact: Dict = field(default_factory=dict)
    rollback_tested: bool = False
    schema_conflicts: List[str] = field(default_factory=list)


class DatabaseMigrationTool:
    """
    Enterprise database migration management system

    Provides:
    - Schema versioning and tracking
    - Safe migration execution with rollback
    - Data migration with validation
    - Schema snapshot and comparison
    - Migration testing and validation
    - Backward compatibility checking
    - Migration rollback capabilities
    """

    def __init__(self, database: DatabaseType = DatabaseType.POSTGRESQL):
        self.database = database
        self.migrations: Dict[str, Migration] = {}
        self.executions: Dict[str, MigrationExecution] = {}
        self.schema_snapshots: Dict[str, SchemaSnapshot] = {}
        self.migration_history: List[Tuple[str, str]] = []  # (version, status)

    def create_migration(self,
                        version: str,
                        description: str,
                        created_by: str,
                        steps: List[Dict]) -> Migration:
        """
        Create new migration

        Args:
            version: Semantic version (e.g., "1.2.3")
            description: Migration description
            created_by: Creator name
            steps: List of migration steps

        Returns:
            Created Migration object
        """
        migration_id = hashlib.md5(f"{version}:{time.time()}".encode()).hexdigest()[:8]

        migration_steps = []
        total_duration = 0

        for i, step_def in enumerate(steps):
            step_id = f"{migration_id}-{i}"
            step = MigrationStep(
                step_id=step_id,
                name=step_def.get("name", f"Step {i+1}"),
                description=step_def.get("description", ""),
                migration_type=MigrationType[step_def.get("type", "SCHEMA")],
                up_script=step_def.get("up_script", ""),
                down_script=step_def.get("down_script", ""),
                estimated_duration=step_def.get("estimated_duration", 0),
                requires_downtime=step_def.get("requires_downtime", False),
                safety_checks=step_def.get("safety_checks", []),
                order=i
            )
            migration_steps.append(step)
            total_duration += step.estimated_duration

        # Determine risk level
        risk_level = self._assess_risk_level(migration_steps)

        migration = Migration(
            migration_id=migration_id,
            version=version,
            description=description,
            database=self.database,
            created_by=created_by,
            created_at=time.time(),
            steps=migration_steps,
            estimated_total_duration=total_duration,
            risk_level=risk_level,
            affected_tables=self._extract_affected_tables(migration_steps)
        )

        self.migrations[migration_id] = migration
        return migration

    def _assess_risk_level(self, steps: List[MigrationStep]) -> str:
        """Assess migration risk"""
        high_risk_count = sum(1 for s in steps if s.requires_downtime)

        if high_risk_count > 2:
            return "CRITICAL"
        elif high_risk_count > 0:
            return "HIGH"
        elif any(len(s.up_script) > 500 for s in steps):
            return "HIGH"
        else:
            return "MEDIUM"

    def _extract_affected_tables(self, steps: List[MigrationStep]) -> List[str]:
        """Extract affected table names from migration steps"""
        tables = set()

        for step in steps:
            # Simple parsing of affected tables
            if "CREATE TABLE" in step.up_script.upper():
                import re
                matches = re.findall(r'CREATE TABLE\s+(\w+)', step.up_script, re.IGNORECASE)
                tables.update(matches)
            if "ALTER TABLE" in step.up_script.upper():
                matches = re.findall(r'ALTER TABLE\s+(\w+)', step.up_script, re.IGNORECASE)
                tables.update(matches)
            if "DROP TABLE" in step.up_script.upper():
                matches = re.findall(r'DROP TABLE\s+(\w+)', step.up_script, re.IGNORECASE)
                tables.update(matches)

        return list(tables)

    def validate_migration(self, migration_id: str) -> MigrationValidationResult:
        """
        Validate migration before execution

        Args:
            migration_id: ID of migration to validate

        Returns:
            MigrationValidationResult with validation details
        """
        migration = self.migrations.get(migration_id)
        if not migration:
            return MigrationValidationResult(
                migration_id=migration_id,
                is_valid=False,
                syntax_errors=["Migration not found"]
            )

        result = MigrationValidationResult(
            migration_id=migration_id,
            is_valid=True
        )

        # Validate SQL syntax
        for step in migration.steps:
            syntax_valid = self._validate_sql_syntax(step.up_script)
            if not syntax_valid:
                result.syntax_errors.append(f"Step {step.order}: Invalid SQL syntax")
                result.is_valid = False

            # Check for dangerous operations
            if self._contains_dangerous_operations(step.up_script):
                result.runtime_warnings.append(f"Step {step.order}: Contains potentially dangerous operations")

        # Check for conflicts with existing migrations
        conflicts = self._check_schema_conflicts(migration)
        if conflicts:
            result.schema_conflicts = conflicts
            result.is_valid = False

        # Check rollback scripts
        for step in migration.steps:
            if not step.down_script.strip():
                result.data_validation_issues.append(f"Step {step.order}: No rollback script defined")

        # Estimate impact
        result.estimated_impact = {
            "estimated_duration": migration.estimated_total_duration,
            "requires_downtime": any(s.requires_downtime for s in migration.steps),
            "affected_tables": len(migration.affected_tables),
            "risk_level": migration.risk_level,
        }

        return result

    def _validate_sql_syntax(self, sql: str) -> bool:
        """Validate SQL syntax (simplified)"""
        # Simple validation
        keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]
        has_keyword = any(kw in sql.upper() for kw in keywords)
        has_syntax_error = "SYNTAX ERROR" in sql.upper()
        return has_keyword and not has_syntax_error

    def _contains_dangerous_operations(self, sql: str) -> bool:
        """Detect dangerous SQL operations"""
        dangerous = [
            "DROP TABLE",
            "DELETE FROM",
            "TRUNCATE",
            "DROP DATABASE",
        ]
        return any(op in sql.upper() for op in dangerous)

    def _check_schema_conflicts(self, migration: Migration) -> List[str]:
        """Check for conflicts with existing schema"""
        conflicts = []

        # Check for duplicate table names in affected tables
        if len(migration.affected_tables) != len(set(migration.affected_tables)):
            conflicts.append("Duplicate table references detected")

        # Check for previous versions
        previous_versions = list(self.migration_history)
        if previous_versions:
            last_version = previous_versions[-1][0]
            if self._version_less_than(last_version, migration.version):
                # This is an upgrade, should be fine
                pass
            else:
                conflicts.append(f"Migration version {migration.version} is not after previous {last_version}")

        return conflicts

    def _version_less_than(self, v1: str, v2: str) -> bool:
        """Compare semantic versions"""
        try:
            v1_parts = [int(x) for x in v1.split(".")]
            v2_parts = [int(x) for x in v2.split(".")]
            return v1_parts < v2_parts
        except:
            return v1 < v2

    def execute_migration(self,
                         migration_id: str,
                         dry_run: bool = False) -> MigrationExecution:
        """
        Execute migration

        Args:
            migration_id: ID of migration to execute
            dry_run: If True, simulate without actual changes

        Returns:
            MigrationExecution with execution details
        """
        migration = self.migrations.get(migration_id)
        if not migration:
            return MigrationExecution(
                execution_id="",
                migration_id=migration_id,
                database=self.database,
                status=MigrationStatus.FAILED,
                started_at=time.time(),
                errors=["Migration not found"]
            )

        execution_id = hashlib.md5(f"{migration_id}:{time.time()}".encode()).hexdigest()[:8]
        execution = MigrationExecution(
            execution_id=execution_id,
            migration_id=migration_id,
            database=self.database,
            status=MigrationStatus.IN_PROGRESS,
            started_at=time.time(),
            total_steps=len(migration.steps)
        )

        # Execute each step
        for step in migration.steps:
            try:
                # Validate before execution
                if not self._validate_sql_syntax(step.up_script):
                    execution.errors.append(f"Step {step.order}: Syntax error")
                    execution.status = MigrationStatus.FAILED
                    break

                # Execute step
                if not dry_run:
                    self._execute_step(step)

                # Simulate rows affected
                rows_affected = random.randint(0, 10000)
                execution.rows_affected += rows_affected
                execution.steps_completed += 1

                # Run safety checks
                for check in step.safety_checks:
                    # Simulate safety check
                    if random.random() > 0.05:  # 95% pass rate
                        execution.warnings.append(f"Step {step.order}: {check} warning")

            except Exception as e:
                execution.errors.append(f"Step {step.order}: {str(e)}")
                execution.status = MigrationStatus.FAILED
                break

        # Determine final status
        if not execution.errors:
            execution.status = MigrationStatus.COMPLETED
            self.migration_history.append((migration.version, "COMPLETED"))
        else:
            execution.status = MigrationStatus.FAILED

        execution.completed_at = time.time()
        execution.execution_time = execution.completed_at - execution.started_at

        self.executions[execution_id] = execution
        return execution

    def _execute_step(self, step: MigrationStep):
        """Execute a migration step (simulated)"""
        # In real implementation, would execute against actual database
        time.sleep(random.uniform(0.1, 1.0))

    def rollback_migration(self, execution_id: str) -> MigrationExecution:
        """
        Rollback a migration execution

        Args:
            execution_id: ID of execution to rollback

        Returns:
            Updated MigrationExecution with rollback status
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return None

        migration = self.migrations.get(execution.migration_id)
        if not migration:
            return execution

        # Execute rollback scripts in reverse order
        for step in reversed(migration.steps):
            if step.down_script:
                self._execute_step(step)  # Execute rollback

        execution.rollback_executed = True
        execution.status = MigrationStatus.ROLLED_BACK
        execution.completed_at = time.time()

        return execution

    def create_schema_snapshot(self, tables: Dict[str, Dict]) -> SchemaSnapshot:
        """
        Create schema snapshot

        Args:
            tables: Dict of table name to schema definition

        Returns:
            Created SchemaSnapshot
        """
        snapshot_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]

        snapshot = SchemaSnapshot(
            snapshot_id=snapshot_id,
            database=self.database,
            timestamp=time.time(),
            tables=tables,
            indexes={},
            constraints={},
        )

        # Calculate hash for comparison
        snapshot.hash = hashlib.md5(json.dumps(tables, sort_keys=True).encode()).hexdigest()

        self.schema_snapshots[snapshot_id] = snapshot
        return snapshot

    def compare_schemas(self, snapshot1_id: str, snapshot2_id: str) -> Dict:
        """
        Compare two schema snapshots

        Args:
            snapshot1_id: ID of first snapshot
            snapshot2_id: ID of second snapshot

        Returns:
            Dict with schema differences
        """
        snap1 = self.schema_snapshots.get(snapshot1_id)
        snap2 = self.schema_snapshots.get(snapshot2_id)

        if not snap1 or not snap2:
            return {}

        differences = {
            "tables_added": list(set(snap2.tables.keys()) - set(snap1.tables.keys())),
            "tables_removed": list(set(snap1.tables.keys()) - set(snap2.tables.keys())),
            "tables_modified": [],
        }

        # Check for modified tables
        for table_name in snap1.tables:
            if table_name in snap2.tables:
                if snap1.tables[table_name] != snap2.tables[table_name]:
                    differences["tables_modified"].append(table_name)

        return differences

    def generate_migration_report(self, migration_id: str) -> str:
        """Generate migration report"""
        migration = self.migrations.get(migration_id)
        if not migration:
            return f"❌ Migration {migration_id} not found"

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        DATABASE MIGRATION REPORT                           ║
║                        Migration: {migration.version}                              ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 MIGRATION DETAILS:
├─ Migration ID: {migration.migration_id}
├─ Version: {migration.version}
├─ Description: {migration.description}
├─ Database: {migration.database.value}
├─ Created By: {migration.created_by}
├─ Risk Level: {migration.risk_level}
└─ Estimated Duration: {migration.estimated_total_duration}s

📊 SCOPE:
├─ Affected Tables: {', '.join(migration.affected_tables) or 'None identified'}
├─ Total Steps: {len(migration.steps)}
└─ Requires Downtime: {'Yes' if any(s.requires_downtime for s in migration.steps) else 'No'}

🔄 MIGRATION STEPS:
"""

        for step in migration.steps:
            downtime_icon = "⏳" if step.requires_downtime else "✅"
            report += f"\n{downtime_icon} Step {step.order + 1}: {step.name}\n"
            report += f"  Type: {step.migration_type.value}\n"
            report += f"  Duration: {step.estimated_duration}s\n"
            if step.safety_checks:
                report += f"  Checks: {', '.join(step.safety_checks)}\n"

        report += f"\n⚙️  ROLLBACK STRATEGY:\n"
        report += f"  Strategy: {migration.rollback_strategy.value}\n"

        return report

    def export_migration(self, migration_id: str) -> str:
        """Export migration as JSON"""
        migration = self.migrations.get(migration_id)
        if not migration:
            return "{}"

        export_data = {
            "migration_id": migration.migration_id,
            "version": migration.version,
            "description": migration.description,
            "database": migration.database.value,
            "created_by": migration.created_by,
            "created_at": migration.created_at,
            "risk_level": migration.risk_level,
            "steps": [
                {
                    "name": step.name,
                    "type": step.migration_type.value,
                    "estimated_duration": step.estimated_duration,
                    "requires_downtime": step.requires_downtime,
                }
                for step in migration.steps
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🗄️  Database Migration Tool - Schema Versioning")
    print("=" * 70)

    tool = DatabaseMigrationTool(DatabaseType.POSTGRESQL)

    # Create migration
    print("\n📝 Creating database migration...")
    migration = tool.create_migration(
        version="2.1.0",
        description="Add user authentication tables and improve performance",
        created_by="alice@example.com",
        steps=[
            {
                "name": "Create users table",
                "type": "SCHEMA",
                "up_script": "CREATE TABLE users (id UUID PRIMARY KEY, email VARCHAR UNIQUE, created_at TIMESTAMP);",
                "down_script": "DROP TABLE users;",
                "estimated_duration": 30,
                "safety_checks": ["Check table structure", "Verify indexes"],
            },
            {
                "name": "Add authentication columns",
                "type": "SCHEMA",
                "up_script": "ALTER TABLE users ADD COLUMN password_hash VARCHAR, ADD COLUMN mfa_enabled BOOLEAN DEFAULT false;",
                "down_script": "ALTER TABLE users DROP COLUMN password_hash, DROP COLUMN mfa_enabled;",
                "estimated_duration": 20,
                "requires_downtime": False,
            },
            {
                "name": "Migrate existing data",
                "type": "DATA",
                "up_script": "UPDATE users SET mfa_enabled = false WHERE mfa_enabled IS NULL;",
                "down_script": "UPDATE users SET mfa_enabled = NULL;",
                "estimated_duration": 60,
                "requires_downtime": True,
            },
        ]
    )

    print(f"✅ Created migration {migration.version}")

    # Validate migration
    print("\n🔍 Validating migration...")
    validation = tool.validate_migration(migration.migration_id)
    if validation.is_valid:
        print(f"✅ Validation passed")
    else:
        print(f"❌ Validation failed: {validation.syntax_errors}")

    # Execute migration
    print("\n▶️  Executing migration...")
    execution = tool.execute_migration(migration.migration_id, dry_run=False)
    print(f"Status: {execution.status.value}")
    print(f"Steps Completed: {execution.steps_completed}/{execution.total_steps}")
    print(f"Rows Affected: {execution.rows_affected}")

    # Generate report
    print(tool.generate_migration_report(migration.migration_id))

    # Export
    print("\n📄 Exporting migration...")
    export = tool.export_migration(migration.migration_id)
    print(f"✅ Exported {len(export)} characters of migration data")

    print("\n" + "=" * 70)
    print("✨ Migration tool ready")


if __name__ == "__main__":
    main()
