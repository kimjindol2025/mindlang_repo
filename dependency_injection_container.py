#!/usr/bin/env python3
"""
Dependency Injection Container - IoC container implementation
Implements inversion of control with dependency injection and service resolution
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import hashlib
import json
import time


class LifetimeScope(Enum):
    """Dependency lifetime scopes"""
    SINGLETON = "SINGLETON"
    TRANSIENT = "TRANSIENT"
    SCOPED = "SCOPED"


class RegistrationType(Enum):
    """Service registration types"""
    INTERFACE = "INTERFACE"
    FACTORY = "FACTORY"
    INSTANCE = "INSTANCE"


@dataclass
class ServiceDescriptor:
    """Service descriptor"""
    descriptor_id: str
    service_type: str
    implementation_type: Optional[str] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ResolvedService:
    """Resolved service instance"""
    instance_id: str
    service_type: str
    instance: Any
    resolved_at: float
    resolution_time_ms: float


@dataclass
class ServiceScope:
    """Service scope"""
    scope_id: str
    parent_scope: Optional[str] = None
    instances: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class DependencyInjectionContainer:
    """
    Dependency Injection Container

    Provides:
    - Service registration
    - Dependency resolution
    - Lifetime management
    - Circular dependency detection
    - Service scoping
    - Factory support
    """

    def __init__(self):
        self.service_descriptors: Dict[str, ServiceDescriptor] = {}
        self.resolved_services: List[ResolvedService] = []
        self.service_scopes: Dict[str, ServiceScope] = {}
        self.singletons: Dict[str, Any] = {}
        self.resolution_history: List[Dict] = []

    def register_singleton(self,
                         service_type: str,
                         implementation_type: str = None,
                         instance: Any = None) -> ServiceDescriptor:
        """Register singleton service"""
        descriptor_id = hashlib.md5(
            f"{service_type}:{LifetimeScope.SINGLETON.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        descriptor = ServiceDescriptor(
            descriptor_id=descriptor_id,
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            instance=instance,
            lifetime=LifetimeScope.SINGLETON
        )

        self.service_descriptors[descriptor_id] = descriptor
        return descriptor

    def register_transient(self,
                         service_type: str,
                         implementation_type: str = None) -> ServiceDescriptor:
        """Register transient service"""
        descriptor_id = hashlib.md5(
            f"{service_type}:{LifetimeScope.TRANSIENT.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        descriptor = ServiceDescriptor(
            descriptor_id=descriptor_id,
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            lifetime=LifetimeScope.TRANSIENT
        )

        self.service_descriptors[descriptor_id] = descriptor
        return descriptor

    def register_scoped(self,
                      service_type: str,
                      implementation_type: str = None) -> ServiceDescriptor:
        """Register scoped service"""
        descriptor_id = hashlib.md5(
            f"{service_type}:{LifetimeScope.SCOPED.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        descriptor = ServiceDescriptor(
            descriptor_id=descriptor_id,
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            lifetime=LifetimeScope.SCOPED
        )

        self.service_descriptors[descriptor_id] = descriptor
        return descriptor

    def register_factory(self,
                        service_type: str,
                        factory: Callable) -> ServiceDescriptor:
        """Register service with factory"""
        descriptor_id = hashlib.md5(
            f"{service_type}:factory:{time.time()}".encode()
        ).hexdigest()[:8]

        descriptor = ServiceDescriptor(
            descriptor_id=descriptor_id,
            service_type=service_type,
            factory=factory,
            lifetime=LifetimeScope.TRANSIENT
        )

        self.service_descriptors[descriptor_id] = descriptor
        return descriptor

    def add_dependency(self, descriptor_id: str, dependency_type: str) -> Optional[ServiceDescriptor]:
        """Add dependency to service"""
        descriptor = self.service_descriptors.get(descriptor_id)
        if not descriptor:
            return None

        if dependency_type not in descriptor.dependencies:
            descriptor.dependencies.append(dependency_type)

        return descriptor

    def resolve(self, service_type: str, scope_id: Optional[str] = None) -> Optional[Any]:
        """Resolve service instance"""
        start_time = time.time()

        # Find descriptor
        descriptor = next((d for d in self.service_descriptors.values()
                         if d.service_type == service_type), None)

        if not descriptor:
            return None

        # Check for singleton
        if descriptor.lifetime == LifetimeScope.SINGLETON:
            if service_type in self.singletons:
                return self.singletons[service_type]

        # Create instance
        instance = self._create_instance(descriptor)

        # Store singleton
        if descriptor.lifetime == LifetimeScope.SINGLETON:
            self.singletons[service_type] = instance

        # Store in scope
        if scope_id and descriptor.lifetime == LifetimeScope.SCOPED:
            scope = self.service_scopes.get(scope_id)
            if scope:
                scope.instances[service_type] = instance

        # Record resolution
        resolution_time = (time.time() - start_time) * 1000
        resolved = ResolvedService(
            instance_id=hashlib.md5(f"{service_type}:{time.time()}".encode()).hexdigest()[:8],
            service_type=service_type,
            instance=instance,
            resolved_at=time.time(),
            resolution_time_ms=resolution_time
        )

        self.resolved_services.append(resolved)

        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create service instance"""
        if descriptor.factory:
            return descriptor.factory()

        if descriptor.instance is not None:
            return descriptor.instance

        # Simulate instance creation
        return {"type": descriptor.implementation_type, "created_at": time.time()}

    def create_scope(self, parent_scope_id: Optional[str] = None) -> ServiceScope:
        """Create new service scope"""
        scope_id = hashlib.md5(
            f"scope:{time.time()}".encode()
        ).hexdigest()[:8]

        scope = ServiceScope(
            scope_id=scope_id,
            parent_scope=parent_scope_id
        )

        self.service_scopes[scope_id] = scope
        return scope

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies"""
        cycles = []

        for descriptor_id, descriptor in self.service_descriptors.items():
            path = []
            if self._find_cycle(descriptor.service_type, path):
                cycles.append(path)

        return cycles

    def _find_cycle(self, service_type: str, path: List[str]) -> bool:
        """Find cycle in dependency graph"""
        if service_type in path:
            return True

        descriptor = next((d for d in self.service_descriptors.values()
                         if d.service_type == service_type), None)

        if not descriptor or not descriptor.dependencies:
            return False

        path.append(service_type)

        for dep in descriptor.dependencies:
            if self._find_cycle(dep, path.copy()):
                return True

        return False

    def get_container_stats(self) -> Dict:
        """Get container statistics"""
        total_descriptors = len(self.service_descriptors)
        total_singletons = len(self.singletons)

        by_lifetime = {}
        for descriptor in self.service_descriptors.values():
            lifetime = descriptor.lifetime.value
            by_lifetime[lifetime] = by_lifetime.get(lifetime, 0) + 1

        return {
            "total_services": total_descriptors,
            "singletons": total_singletons,
            "by_lifetime": by_lifetime,
            "scopes": len(self.service_scopes),
            "resolutions": len(self.resolved_services),
            "circular_dependencies": len(self.detect_circular_dependencies()),
        }

    def generate_container_report(self) -> str:
        """Generate container report"""
        stats = self.get_container_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DEPENDENCY INJECTION CONTAINER REPORT                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Services: {stats['total_services']}
├─ Singletons: {stats['singletons']}
├─ Scopes: {stats['scopes']}
├─ Resolutions: {stats['resolutions']}
└─ Circular Dependencies: {stats['circular_dependencies']}

📋 BY LIFETIME:
"""

        for lifetime, count in stats['by_lifetime'].items():
            report += f"  {lifetime}: {count}\n"

        return report

    def export_container_config(self) -> str:
        """Export container configuration"""
        stats = self.get_container_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "services": [
                {
                    "type": d.service_type,
                    "implementation": d.implementation_type,
                    "lifetime": d.lifetime.value,
                    "dependencies": d.dependencies,
                }
                for d in self.service_descriptors.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔧 Dependency Injection Container - IoC Container")
    print("=" * 70)

    container = DependencyInjectionContainer()

    # Register services
    print("\n📋 Registering services...")
    container.register_singleton("IDatabase", "PostgresDatabase")
    container.register_scoped("IUserService", "UserService")
    container.register_transient("IEmailService", "EmailService")
    container.register_singleton("ICache", "RedisCache")
    print(f"✅ Registered {len(container.service_descriptors)} services")

    # Add dependencies
    print("\n🔗 Adding dependencies...")
    user_service = next((d for d in container.service_descriptors.values()
                        if d.service_type == "IUserService"), None)
    if user_service:
        container.add_dependency(user_service.descriptor_id, "IDatabase")
        container.add_dependency(user_service.descriptor_id, "ICache")
    print("✅ Dependencies added")

    # Resolve services
    print("\n⚙️  Resolving services...")
    db = container.resolve("IDatabase")
    cache = container.resolve("ICache")
    email = container.resolve("IEmailService")
    print(f"✅ Resolved services")

    # Create scope
    print("\n🔎 Creating service scope...")
    scope = container.create_scope()
    user_service_scoped = container.resolve("IUserService", scope.scope_id)
    print(f"✅ Created scope with {len(scope.instances)} instances")

    # Detect circular dependencies
    print("\n🔄 Detecting circular dependencies...")
    cycles = container.detect_circular_dependencies()
    print(f"✅ Found {len(cycles)} circular dependencies")

    # Generate report
    print(container.generate_container_report())

    # Export
    print("\n📄 Exporting container config...")
    export = container.export_container_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Dependency injection container ready")


if __name__ == "__main__":
    main()
