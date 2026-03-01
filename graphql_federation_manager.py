#!/usr/bin/env python3
"""
GraphQL Federation Manager - Federated GraphQL schema management
Manages multiple GraphQL services with Apollo Federation pattern
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import random


class FederationRole(Enum):
    """Federation service roles"""
    GATEWAY = "GATEWAY"
    SUBGRAPH = "SUBGRAPH"
    MANAGED = "MANAGED"


@dataclass
class FederatedType:
    """Type in federated schema"""
    type_name: str
    service_name: str
    is_entity: bool
    fields: Dict[str, str] = field(default_factory=dict)
    reference_fields: List[str] = field(default_factory=list)


@dataclass
class Subgraph:
    """GraphQL Subgraph service"""
    subgraph_id: str
    name: str
    url: str
    types: Dict[str, FederatedType] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)
    query_depth: int = 5
    rate_limit: int = 1000  # requests per minute
    registered_at: float = field(default_factory=time.time)
    healthy: bool = True
    last_check: float = field(default_factory=time.time)


@dataclass
class FederatedSchema:
    """Complete federated schema"""
    schema_id: str
    name: str
    version: str
    timestamp: float
    subgraphs: Dict[str, Subgraph] = field(default_factory=dict)
    entity_mappings: Dict[str, List[str]] = field(default_factory=dict)  # entity -> services
    composition_errors: List[str] = field(default_factory=list)
    is_valid: bool = True


@dataclass
class EntityReference:
    """Reference to an entity"""
    entity_type: str
    entity_id: str
    source_service: str
    referenced_by: Set[str] = field(default_factory=set)


@dataclass
class CompositionResult:
    """Result of schema composition"""
    composition_id: str
    timestamp: float
    composed_schema: Optional[FederatedSchema] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = False
    composition_time_ms: float = 0.0


class GraphQLFederationManager:
    """
    GraphQL Federation management system

    Provides:
    - Federated schema composition
    - Subgraph management
    - Entity reference resolution
    - Schema validation
    - Service orchestration
    - Performance monitoring
    """

    def __init__(self, gateway_url: str = "http://localhost:4000"):
        self.gateway_url = gateway_url
        self.subgraphs: Dict[str, Subgraph] = {}
        self.federated_schemas: Dict[str, FederatedSchema] = {}
        self.entity_mappings: Dict[str, EntityReference] = {}
        self.composition_history: List[CompositionResult] = []

    def register_subgraph(self,
                         name: str,
                         url: str,
                         types: Dict[str, Dict],
                         entities: List[str] = None) -> Subgraph:
        """
        Register GraphQL subgraph

        Args:
            name: Subgraph name
            url: GraphQL endpoint URL
            types: Type definitions
            entities: Entity types

        Returns:
            Registered Subgraph
        """
        subgraph_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        subgraph = Subgraph(
            subgraph_id=subgraph_id,
            name=name,
            url=url,
            entities=entities or []
        )

        # Parse types
        for type_name, type_def in types.items():
            fed_type = FederatedType(
                type_name=type_name,
                service_name=name,
                is_entity=type_name in (entities or []),
                fields=type_def.get("fields", {}),
                reference_fields=type_def.get("reference_fields", [])
            )
            subgraph.types[type_name] = fed_type

        self.subgraphs[subgraph_id] = subgraph

        return subgraph

    def compose_schema(self) -> CompositionResult:
        """Compose federated schema from subgraphs"""
        composition_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]

        result = CompositionResult(
            composition_id=composition_id,
            timestamp=time.time()
        )

        start_time = time.time()

        # Check subgraph health
        unhealthy = [sg for sg in self.subgraphs.values() if not sg.healthy]
        if unhealthy:
            result.errors.append(f"{len(unhealthy)} unhealthy subgraphs")

        # Collect all types
        all_types = {}
        for subgraph in self.subgraphs.values():
            for type_name, fed_type in subgraph.types.items():
                if type_name not in all_types:
                    all_types[type_name] = []
                all_types[type_name].append(fed_type)

        # Check for conflicts
        conflicts = []
        for type_name, type_list in all_types.items():
            if len(type_list) > 1:
                # Check if multiple services define same entity
                entity_providers = [t.service_name for t in type_list if t.is_entity]
                if len(entity_providers) > 1:
                    conflicts.append(f"Entity {type_name} defined in multiple services: {entity_providers}")

        if conflicts:
            result.errors.extend(conflicts)

        # Create federated schema
        schema_id = hashlib.md5(f"{composition_id}".encode()).hexdigest()[:8]
        schema = FederatedSchema(
            schema_id=schema_id,
            name="federated-schema",
            version="1.0.0",
            timestamp=time.time(),
            subgraphs={sg.subgraph_id: sg for sg in self.subgraphs.values()},
            is_valid=len(result.errors) == 0
        )

        # Build entity mappings
        for type_name, type_list in all_types.items():
            if any(t.is_entity for t in type_list):
                providers = [t.service_name for t in type_list if t.is_entity]
                schema.entity_mappings[type_name] = providers

        result.composed_schema = schema
        result.success = len(result.errors) == 0
        result.composition_time_ms = (time.time() - start_time) * 1000

        self.federated_schemas[schema_id] = schema
        self.composition_history.append(result)

        return result

    def check_subgraph_health(self, subgraph_id: str) -> bool:
        """Check subgraph health"""
        subgraph = self.subgraphs.get(subgraph_id)
        if not subgraph:
            return False

        # Simulate health check
        is_healthy = random.random() > 0.05  # 95% health rate
        subgraph.healthy = is_healthy
        subgraph.last_check = time.time()

        return is_healthy

    def resolve_entity_reference(self,
                                entity_type: str,
                                entity_id: str) -> Optional[str]:
        """Resolve which service provides entity"""
        # Find in composed schema
        for schema in self.federated_schemas.values():
            if entity_type in schema.entity_mappings:
                providers = schema.entity_mappings[entity_type]
                if providers:
                    return providers[0]  # Return first provider

        return None

    def get_federation_stats(self) -> Dict:
        """Get federation statistics"""
        total_types = set()
        total_entities = set()

        for subgraph in self.subgraphs.values():
            total_types.update(subgraph.types.keys())
            total_entities.update(subgraph.entities)

        latest_schema = self.federated_schemas.get(
            max(self.federated_schemas.keys(), default=None)
        ) if self.federated_schemas else None

        return {
            "subgraphs": len(self.subgraphs),
            "healthy_subgraphs": sum(1 for sg in self.subgraphs.values() if sg.healthy),
            "total_types": len(total_types),
            "total_entities": len(total_entities),
            "schemas_composed": len(self.federated_schemas),
            "composition_errors": sum(len(r.errors) for r in self.composition_history),
            "latest_schema_valid": latest_schema.is_valid if latest_schema else None,
        }

    def generate_federation_report(self) -> str:
        """Generate federation report"""
        stats = self.get_federation_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   GRAPHQL FEDERATION REPORT                                ║
║                   Gateway: {self.gateway_url}                          ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 FEDERATION STATISTICS:
├─ Subgraphs: {stats['subgraphs']}
├─ 🟢 Healthy: {stats['healthy_subgraphs']}/{stats['subgraphs']}
├─ Total Types: {stats['total_types']}
├─ Total Entities: {stats['total_entities']}
├─ Composed Schemas: {stats['schemas_composed']}
└─ Composition Errors: {stats['composition_errors']}

🔗 SUBGRAPH STATUS:
"""

        for subgraph in self.subgraphs.values():
            status_emoji = "🟢" if subgraph.healthy else "🔴"
            report += f"\n{status_emoji} {subgraph.name}\n"
            report += f"  URL: {subgraph.url}\n"
            report += f"  Types: {len(subgraph.types)}\n"
            report += f"  Entities: {len(subgraph.entities)}\n"
            report += f"  Rate Limit: {subgraph.rate_limit} req/min\n"

        report += f"\n📦 ENTITY MAPPINGS:\n"
        if self.federated_schemas:
            latest = list(self.federated_schemas.values())[-1]
            for entity, providers in latest.entity_mappings.items():
                report += f"  • {entity}: {', '.join(providers)}\n"

        report += f"\n⚠️  RECENT COMPOSITION RESULTS:\n"
        for result in self.composition_history[-3:]:
            status = "✅" if result.success else "❌"
            report += f"{status} Composition {result.composition_id[:8]}\n"
            report += f"  Time: {result.composition_time_ms:.1f}ms\n"
            if result.errors:
                report += f"  Errors: {len(result.errors)}\n"

        return report

    def export_federation_config(self) -> str:
        """Export federation configuration"""
        export_data = {
            "gateway_url": self.gateway_url,
            "timestamp": time.time(),
            "subgraphs": [
                {
                    "name": sg.name,
                    "url": sg.url,
                    "healthy": sg.healthy,
                    "types": len(sg.types),
                    "entities": sg.entities,
                }
                for sg in self.subgraphs.values()
            ],
            "composition_stats": {
                "total_compositions": len(self.composition_history),
                "successful": sum(1 for r in self.composition_history if r.success),
                "failed": sum(1 for r in self.composition_history if not r.success),
            }
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔗 GraphQL Federation Manager - Federated Schema Orchestration")
    print("=" * 70)

    manager = GraphQLFederationManager()

    # Register subgraphs
    print("\n📝 Registering subgraphs...")

    users_subgraph = manager.register_subgraph(
        "users-service",
        "http://users-service:4001/graphql",
        {
            "User": {
                "fields": {"id": "ID!", "name": "String!", "email": "String!"},
                "reference_fields": ["id"],
            },
            "Query": {
                "fields": {"user": "User", "users": "[User]"},
            }
        },
        entities=["User"]
    )

    products_subgraph = manager.register_subgraph(
        "products-service",
        "http://products-service:4002/graphql",
        {
            "Product": {
                "fields": {"id": "ID!", "name": "String!", "price": "Float!"},
                "reference_fields": ["id"],
            },
            "Query": {
                "fields": {"product": "Product", "products": "[Product]"},
            }
        },
        entities=["Product"]
    )

    orders_subgraph = manager.register_subgraph(
        "orders-service",
        "http://orders-service:4003/graphql",
        {
            "Order": {
                "fields": {"id": "ID!", "userId": "ID!", "productId": "ID!"},
                "reference_fields": ["id"],
            },
            "Query": {
                "fields": {"order": "Order", "orders": "[Order]"},
            }
        },
        entities=["Order"]
    )

    print(f"✅ Registered {len(manager.subgraphs)} subgraphs")

    # Check health
    print("\n🏥 Checking subgraph health...")
    for subgraph_id in manager.subgraphs.keys():
        manager.check_subgraph_health(subgraph_id)
    print(f"✅ Health check completed")

    # Compose schema
    print("\n🔗 Composing federated schema...")
    result = manager.compose_schema()
    print(f"Composition Status: {'Success' if result.success else 'Failed'}")
    print(f"Composition Time: {result.composition_time_ms:.2f}ms")

    if result.errors:
        print(f"Errors: {result.errors}")

    # Generate report
    print(manager.generate_federation_report())

    # Export
    print("\n📄 Exporting federation config...")
    export = manager.export_federation_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ GraphQL federation ready")


if __name__ == "__main__":
    main()
