#!/usr/bin/env python3
"""
GraphQL Schema Manager - Schema versioning, evolution, and compatibility management
Validates schema changes, detects breaking changes, and manages schema versions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any
import hashlib
import json
import time
import random


class FieldType(Enum):
    """GraphQL field types"""
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    LIST = "LIST"
    NON_NULL = "NON_NULL"


class SchemaChangeType(Enum):
    """Types of schema changes"""
    FIELD_ADDED = "FIELD_ADDED"
    FIELD_REMOVED = "FIELD_REMOVED"
    FIELD_TYPE_CHANGED = "FIELD_TYPE_CHANGED"
    FIELD_MADE_NULLABLE = "FIELD_MADE_NULLABLE"
    FIELD_MADE_NON_NULLABLE = "FIELD_MADE_NON_NULL"
    ENUM_VALUE_ADDED = "ENUM_VALUE_ADDED"
    ENUM_VALUE_REMOVED = "ENUM_VALUE_REMOVED"
    ARGUMENT_ADDED = "ARGUMENT_ADDED"
    ARGUMENT_REMOVED = "ARGUMENT_REMOVED"
    ARGUMENT_TYPE_CHANGED = "ARGUMENT_TYPE_CHANGED"
    TYPE_CREATED = "TYPE_CREATED"
    TYPE_REMOVED = "TYPE_REMOVED"
    INTERFACE_ADDED = "INTERFACE_ADDED"
    INTERFACE_REMOVED = "INTERFACE_REMOVED"


class SchemaChangeImpact(Enum):
    """Impact of schema changes"""
    NON_BREAKING = "NON_BREAKING"
    POTENTIALLY_BREAKING = "POTENTIALLY_BREAKING"
    BREAKING = "BREAKING"
    CRITICAL = "CRITICAL"


@dataclass
class GraphQLField:
    """GraphQL field definition"""
    name: str
    field_type: str  # "String", "Int", "User", "[User]", "String!", etc.
    description: str = ""
    deprecated: bool = False
    deprecation_reason: str = ""
    arguments: Dict[str, str] = field(default_factory=dict)  # arg_name -> type
    directives: List[str] = field(default_factory=list)


@dataclass
class GraphQLType:
    """GraphQL type definition"""
    name: str
    type_kind: FieldType
    description: str = ""
    fields: Dict[str, GraphQLField] = field(default_factory=dict)
    interfaces: List[str] = field(default_factory=list)
    enum_values: List[str] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)


@dataclass
class GraphQLSchema:
    """Complete GraphQL schema"""
    schema_id: str
    version: str
    timestamp: float
    description: str = ""
    query_type: str = "Query"
    mutation_type: Optional[str] = None
    subscription_type: Optional[str] = None
    types: Dict[str, GraphQLType] = field(default_factory=dict)
    directives: List[str] = field(default_factory=list)
    schema_hash: str = ""


@dataclass
class SchemaChange:
    """Detected schema change"""
    change_id: str
    change_type: SchemaChangeType
    impact: SchemaChangeImpact
    affected_type: str
    affected_field: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    description: str = ""
    affected_queries: List[str] = field(default_factory=list)
    remediation: str = ""


@dataclass
class SchemaDiff:
    """Difference between two schema versions"""
    diff_id: str
    old_version: str
    new_version: str
    changes: List[SchemaChange] = field(default_factory=list)
    breaking_changes: int = 0
    potentially_breaking: int = 0
    non_breaking_changes: int = 0
    is_backward_compatible: bool = True


@dataclass
class ClientQuery:
    """Client GraphQL query for impact analysis"""
    query_id: str
    query_text: str
    client_name: str
    used_fields: List[str] = field(default_factory=list)
    used_types: List[str] = field(default_factory=list)
    is_affected_by_changes: bool = False
    affected_by: List[str] = field(default_factory=list)


class GraphQLSchemaManager:
    """
    GraphQL schema management and evolution system

    Provides:
    - Schema versioning and history
    - Breaking change detection
    - Backward compatibility checking
    - Client impact analysis
    - Schema validation
    - Schema composition for federated schemas
    - Deprecation management
    """

    def __init__(self):
        self.schemas: Dict[str, GraphQLSchema] = {}
        self.schema_diffs: Dict[str, SchemaDiff] = {}
        self.client_queries: Dict[str, ClientQuery] = {}
        self.schema_history: List[Tuple[str, str]] = []  # (version, timestamp)

    def create_schema(self,
                     version: str,
                     description: str,
                     type_definitions: Dict[str, Dict]) -> GraphQLSchema:
        """
        Create new GraphQL schema

        Args:
            version: Schema version
            description: Schema description
            type_definitions: Dict of type name to type definition

        Returns:
            Created GraphQLSchema
        """
        schema_id = hashlib.md5(f"{version}:{time.time()}".encode()).hexdigest()[:8]

        types = {}
        for type_name, type_def in type_definitions.items():
            fields = {}
            for field_name, field_info in type_def.get("fields", {}).items():
                field = GraphQLField(
                    name=field_name,
                    field_type=field_info.get("type", "String"),
                    description=field_info.get("description", ""),
                    deprecated=field_info.get("deprecated", False),
                    arguments=field_info.get("arguments", {})
                )
                fields[field_name] = field

            gql_type = GraphQLType(
                name=type_name,
                type_kind=FieldType[type_def.get("kind", "OBJECT")],
                description=type_def.get("description", ""),
                fields=fields,
                enum_values=type_def.get("enum_values", []),
                interfaces=type_def.get("interfaces", [])
            )
            types[type_name] = gql_type

        schema = GraphQLSchema(
            schema_id=schema_id,
            version=version,
            timestamp=time.time(),
            description=description,
            types=types
        )

        # Calculate schema hash
        schema.schema_hash = self._calculate_schema_hash(schema)

        self.schemas[schema_id] = schema
        self.schema_history.append((version, str(schema.timestamp)))

        return schema

    def _calculate_schema_hash(self, schema: GraphQLSchema) -> str:
        """Calculate hash of schema for comparison"""
        schema_dict = {
            name: {
                "kind": type_obj.type_kind.value,
                "fields": {
                    field_name: {
                        "type": field.field_type,
                        "deprecated": field.deprecated,
                    }
                    for field_name, field in type_obj.fields.items()
                },
                "enum_values": type_obj.enum_values,
            }
            for name, type_obj in schema.types.items()
        }
        return hashlib.md5(json.dumps(schema_dict, sort_keys=True).encode()).hexdigest()

    def detect_schema_changes(self,
                             old_schema_id: str,
                             new_schema_id: str) -> SchemaDiff:
        """
        Detect changes between two schema versions

        Args:
            old_schema_id: ID of old schema
            new_schema_id: ID of new schema

        Returns:
            SchemaDiff with detected changes
        """
        old_schema = self.schemas.get(old_schema_id)
        new_schema = self.schemas.get(new_schema_id)

        if not old_schema or not new_schema:
            return SchemaDiff(
                diff_id="",
                old_version="",
                new_version="",
                is_backward_compatible=False
            )

        diff_id = hashlib.md5(f"{old_schema_id}:{new_schema_id}".encode()).hexdigest()[:8]
        diff = SchemaDiff(
            diff_id=diff_id,
            old_version=old_schema.version,
            new_version=new_schema.version
        )

        # Compare types
        old_types = set(old_schema.types.keys())
        new_types = set(new_schema.types.keys())

        # Detect removed types
        for type_name in old_types - new_types:
            change = SchemaChange(
                change_id=f"{diff_id}-type-removed-{type_name}",
                change_type=SchemaChangeType.TYPE_REMOVED,
                impact=SchemaChangeImpact.BREAKING,
                affected_type=type_name,
                description=f"Type '{type_name}' removed",
                remediation="Clients must remove usage of this type"
            )
            diff.changes.append(change)
            diff.breaking_changes += 1

        # Detect added types
        for type_name in new_types - old_types:
            change = SchemaChange(
                change_id=f"{diff_id}-type-added-{type_name}",
                change_type=SchemaChangeType.TYPE_CREATED,
                impact=SchemaChangeImpact.NON_BREAKING,
                affected_type=type_name,
                description=f"Type '{type_name}' added"
            )
            diff.changes.append(change)
            diff.non_breaking_changes += 1

        # Compare fields in common types
        for type_name in old_types & new_types:
            old_type = old_schema.types[type_name]
            new_type = new_schema.types[type_name]

            old_fields = set(old_type.fields.keys())
            new_fields = set(new_type.fields.keys())

            # Detect removed fields
            for field_name in old_fields - new_fields:
                change = SchemaChange(
                    change_id=f"{diff_id}-field-removed-{type_name}-{field_name}",
                    change_type=SchemaChangeType.FIELD_REMOVED,
                    impact=SchemaChangeImpact.BREAKING,
                    affected_type=type_name,
                    affected_field=field_name,
                    description=f"Field '{field_name}' removed from type '{type_name}'",
                    remediation="Clients must remove usage of this field"
                )
                diff.changes.append(change)
                diff.breaking_changes += 1

            # Detect added fields
            for field_name in new_fields - old_fields:
                new_field = new_type.fields[field_name]
                is_required = "!" in new_field.field_type

                impact = SchemaChangeImpact.POTENTIALLY_BREAKING if is_required else SchemaChangeImpact.NON_BREAKING

                change = SchemaChange(
                    change_id=f"{diff_id}-field-added-{type_name}-{field_name}",
                    change_type=SchemaChangeType.FIELD_ADDED,
                    impact=impact,
                    affected_type=type_name,
                    affected_field=field_name,
                    new_value=new_field.field_type,
                    description=f"Field '{field_name}' added to type '{type_name}'",
                    remediation="Update clients to use the new field"
                )
                diff.changes.append(change)

                if impact == SchemaChangeImpact.POTENTIALLY_BREAKING:
                    diff.potentially_breaking += 1
                else:
                    diff.non_breaking_changes += 1

            # Detect field type changes
            for field_name in old_fields & new_fields:
                old_field = old_type.fields[field_name]
                new_field = new_type.fields[field_name]

                if old_field.field_type != new_field.field_type:
                    impact = self._assess_type_change_impact(old_field.field_type, new_field.field_type)
                    change = SchemaChange(
                        change_id=f"{diff_id}-field-type-{type_name}-{field_name}",
                        change_type=SchemaChangeType.FIELD_TYPE_CHANGED,
                        impact=impact,
                        affected_type=type_name,
                        affected_field=field_name,
                        old_value=old_field.field_type,
                        new_value=new_field.field_type,
                        description=f"Field '{field_name}' type changed from {old_field.field_type} to {new_field.field_type}",
                        remediation="Verify client compatibility with new type"
                    )
                    diff.changes.append(change)

                    if impact == SchemaChangeImpact.BREAKING:
                        diff.breaking_changes += 1
                    elif impact == SchemaChangeImpact.POTENTIALLY_BREAKING:
                        diff.potentially_breaking += 1
                    else:
                        diff.non_breaking_changes += 1

        # Determine backward compatibility
        diff.is_backward_compatible = diff.breaking_changes == 0

        self.schema_diffs[diff_id] = diff
        return diff

    def _assess_type_change_impact(self, old_type: str, new_type: str) -> SchemaChangeImpact:
        """Assess impact of field type change"""
        # Making field non-nullable is breaking
        if old_type.endswith("!") and not new_type.endswith("!"):
            return SchemaChangeImpact.NON_BREAKING  # More permissive
        elif not old_type.endswith("!") and new_type.endswith("!"):
            return SchemaChangeImpact.BREAKING  # More restrictive
        # Type name changes are breaking
        elif old_type.rstrip("![]") != new_type.rstrip("![]"):
            return SchemaChangeImpact.BREAKING
        else:
            return SchemaChangeImpact.NON_BREAKING

    def register_client_query(self,
                             client_name: str,
                             query_text: str) -> ClientQuery:
        """
        Register client query for impact analysis

        Args:
            client_name: Name of client using query
            query_text: GraphQL query text

        Returns:
            Registered ClientQuery
        """
        query_id = hashlib.md5(f"{client_name}:{query_text}".encode()).hexdigest()[:8]

        # Parse query to extract used fields/types
        used_fields = self._extract_fields_from_query(query_text)
        used_types = self._extract_types_from_query(query_text)

        query = ClientQuery(
            query_id=query_id,
            query_text=query_text,
            client_name=client_name,
            used_fields=used_fields,
            used_types=used_types
        )

        self.client_queries[query_id] = query
        return query

    def _extract_fields_from_query(self, query_text: str) -> List[str]:
        """Extract field names from query (simplified)"""
        # Simple extraction
        import re
        fields = re.findall(r'\b([a-zA-Z]\w*)\s*(?:{|:|\(|,|$)', query_text)
        return list(set(fields))

    def _extract_types_from_query(self, query_text: str) -> List[str]:
        """Extract type references from query (simplified)"""
        # This would normally parse the GraphQL more thoroughly
        import re
        # Look for type definitions in the query
        types = []
        if "User" in query_text:
            types.append("User")
        if "Post" in query_text:
            types.append("Post")
        return types

    def analyze_client_impact(self,
                             diff_id: str) -> Dict[str, List[str]]:
        """
        Analyze impact of schema changes on clients

        Args:
            diff_id: ID of schema diff to analyze

        Returns:
            Dict mapping client name to list of affected queries
        """
        diff = self.schema_diffs.get(diff_id)
        if not diff:
            return {}

        impact_analysis = {}

        # Get all affected fields and types
        affected_fields = set()
        affected_types = set()

        for change in diff.changes:
            if change.affected_field:
                affected_fields.add(change.affected_field)
            affected_types.add(change.affected_type)

        # Check each client query
        for query_id, client_query in self.client_queries.items():
            affected_queries = []

            # Check if query uses affected fields or types
            for field in affected_fields:
                if field in client_query.used_fields:
                    affected_queries.append(client_query.query_text[:50] + "...")

            for type_name in affected_types:
                if type_name in client_query.used_types:
                    affected_queries.append(client_query.query_text[:50] + "...")

            if affected_queries:
                if client_query.client_name not in impact_analysis:
                    impact_analysis[client_query.client_name] = []
                impact_analysis[client_query.client_name].extend(affected_queries)

        return impact_analysis

    def validate_schema(self, schema_id: str) -> Dict:
        """
        Validate GraphQL schema

        Args:
            schema_id: ID of schema to validate

        Returns:
            Dict with validation results
        """
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"valid": False, "errors": ["Schema not found"]}

        errors = []
        warnings = []

        # Check for Query type
        if "Query" not in schema.types:
            errors.append("Schema must define Query type")

        # Check for circular references
        for type_name, type_obj in schema.types.items():
            for field_name, field in type_obj.fields.items():
                # Simple circular check
                base_type = field.field_type.rstrip("![]")
                if base_type == type_name:
                    warnings.append(f"Type '{type_name}' has self-referencing field '{field_name}'")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "schema_id": schema_id,
            "version": schema.version,
        }

    def generate_schema_diff_report(self, diff_id: str) -> str:
        """Generate schema diff report"""
        diff = self.schema_diffs.get(diff_id)
        if not diff:
            return f"❌ Diff {diff_id} not found"

        compatibility_icon = "✅" if diff.is_backward_compatible else "❌"
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         GRAPHQL SCHEMA DIFF REPORT                         ║
║                         {diff.old_version} → {diff.new_version}                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

{compatibility_icon} BACKWARD COMPATIBLE: {'Yes' if diff.is_backward_compatible else 'No'}

📊 CHANGE SUMMARY:
├─ Breaking Changes: {diff.breaking_changes}
├─ Potentially Breaking: {diff.potentially_breaking}
└─ Non-Breaking Changes: {diff.non_breaking_changes}

🔄 CHANGES:
"""

        for change in diff.changes:
            emoji = "🔴" if change.impact == SchemaChangeImpact.BREAKING else \
                    "🟠" if change.impact == SchemaChangeImpact.POTENTIALLY_BREAKING else "🟢"
            report += f"\n{emoji} {change.change_type.value}\n"
            report += f"  Type: {change.affected_type}\n"
            if change.affected_field:
                report += f"  Field: {change.affected_field}\n"
            report += f"  Impact: {change.impact.value}\n"
            if change.remediation:
                report += f"  ✅ {change.remediation}\n"

        return report

    def export_schema(self, schema_id: str) -> str:
        """Export schema as JSON"""
        schema = self.schemas.get(schema_id)
        if not schema:
            return "{}"

        export_data = {
            "schema_id": schema.schema_id,
            "version": schema.version,
            "timestamp": schema.timestamp,
            "description": schema.description,
            "types": {
                name: {
                    "kind": type_obj.type_kind.value,
                    "description": type_obj.description,
                    "fields": {
                        field_name: {
                            "type": field.field_type,
                            "deprecated": field.deprecated,
                        }
                        for field_name, field in type_obj.fields.items()
                    },
                }
                for name, type_obj in schema.types.items()
            },
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 GraphQL Schema Manager - Schema Evolution Management")
    print("=" * 70)

    manager = GraphQLSchemaManager()

    # Create first schema version
    print("\n📝 Creating GraphQL schema v1.0...")
    schema_v1 = manager.create_schema(
        version="1.0.0",
        description="Initial GraphQL schema",
        type_definitions={
            "Query": {
                "kind": "OBJECT",
                "fields": {
                    "user": {
                        "type": "User",
                        "arguments": {"id": "ID!"},
                        "description": "Get user by ID"
                    },
                    "users": {
                        "type": "[User!]!",
                        "description": "Get all users"
                    }
                }
            },
            "User": {
                "kind": "OBJECT",
                "fields": {
                    "id": {"type": "ID!", "description": "User ID"},
                    "name": {"type": "String!", "description": "User name"},
                    "email": {"type": "String!", "description": "User email"},
                }
            },
        }
    )
    print(f"✅ Created schema {schema_v1.version}")

    # Create second schema version with changes
    print("\n📝 Creating GraphQL schema v1.1 with changes...")
    schema_v2 = manager.create_schema(
        version="1.1.0",
        description="Add profile field to User",
        type_definitions={
            "Query": {
                "kind": "OBJECT",
                "fields": {
                    "user": {
                        "type": "User",
                        "arguments": {"id": "ID!"},
                        "description": "Get user by ID"
                    },
                    "users": {
                        "type": "[User!]!",
                        "description": "Get all users"
                    }
                }
            },
            "User": {
                "kind": "OBJECT",
                "fields": {
                    "id": {"type": "ID!", "description": "User ID"},
                    "name": {"type": "String!", "description": "User name"},
                    "email": {"type": "String!", "description": "User email"},
                    "profile": {"type": "Profile", "description": "User profile"},  # NEW
                }
            },
            "Profile": {  # NEW TYPE
                "kind": "OBJECT",
                "fields": {
                    "bio": {"type": "String", "description": "User bio"},
                    "avatar": {"type": "String", "description": "Avatar URL"},
                }
            },
        }
    )
    print(f"✅ Created schema {schema_v2.version}")

    # Detect changes
    print("\n🔍 Detecting schema changes...")
    diff = manager.detect_schema_changes(schema_v1.schema_id, schema_v2.schema_id)
    print(f"Breaking: {diff.breaking_changes}, Potentially Breaking: {diff.potentially_breaking}, Non-Breaking: {diff.non_breaking_changes}")

    # Register client query
    print("\n📱 Registering client query...")
    client_query = manager.register_client_query(
        client_name="web-frontend",
        query_text="""
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    name
                    email
                }
            }
        """
    )
    print(f"✅ Registered client query")

    # Analyze impact
    print("\n📊 Analyzing schema change impact...")
    impact = manager.analyze_client_impact(diff.schema_id)
    print(f"Affected clients: {len(impact)}")

    # Generate report
    print(manager.generate_schema_diff_report(diff.diff_id))

    # Export schema
    print("\n📄 Exporting schema...")
    export = manager.export_schema(schema_v2.schema_id)
    print(f"✅ Exported {len(export)} characters of schema data")

    print("\n" + "=" * 70)
    print("✨ GraphQL schema management complete")


if __name__ == "__main__":
    main()
