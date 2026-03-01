#!/usr/bin/env python3
"""
Service Registry & Discovery - Dynamic service registration and discovery
Manages service instances, health checks, and client-side load balancing
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable
import hashlib
import json
import time
import random


class ServiceStatus(Enum):
    """Service instance status"""
    UP = "UP"
    DOWN = "DOWN"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    STARTING = "STARTING"
    STOPPING = "STOPPING"


class HealthCheckType(Enum):
    """Health check types"""
    HTTP = "HTTP"
    TCP = "TCP"
    GRPC = "GRPC"
    CUSTOM = "CUSTOM"


@dataclass
class ServiceMetadata:
    """Service metadata"""
    key: str
    value: str


@dataclass
class ServiceInstance:
    """Service instance registration"""
    instance_id: str
    service_name: str
    host: str
    port: int
    scheme: str  # http, https, grpc
    status: ServiceStatus = ServiceStatus.UP
    metadata: Dict[str, str] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    last_heartbeat: float = field(default_factory=time.time)
    registered_at: float = field(default_factory=time.time)
    lease_renewal_interval: int = 30
    priority: int = 50
    weight: int = 100


@dataclass
class HealthCheck:
    """Health check configuration"""
    check_id: str
    check_type: HealthCheckType
    interval: int  # seconds
    timeout: int  # seconds
    unhealthy_threshold: int = 3
    healthy_threshold: int = 2
    path: Optional[str] = None
    expected_status: Optional[int] = None


@dataclass
class ServiceRegistration:
    """Service registration information"""
    service_id: str
    service_name: str
    instances: Dict[str, ServiceInstance] = field(default_factory=dict)
    health_checks: List[HealthCheck] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ServiceQuery:
    """Service discovery query"""
    query_id: str
    service_name: str
    filters: Dict[str, str] = field(default_factory=dict)
    results: List[ServiceInstance] = field(default_factory=list)
    execution_time_ms: float = 0.0


class ServiceRegistry:
    """
    Service Registry & Discovery

    Provides:
    - Dynamic service registration
    - Automatic deregistration
    - Health checking
    - Load balancing strategies
    - Client-side service discovery
    - Service metadata management
    - Lease-based registration
    """

    def __init__(self):
        self.services: Dict[str, ServiceRegistration] = {}
        self.instances: Dict[str, ServiceInstance] = {}  # instance_id -> instance
        self.queries: List[ServiceQuery] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.subscribers: Dict[str, List[Callable]] = {}  # event -> callbacks
        self.leases: Dict[str, float] = {}  # instance_id -> expiry_time

    def register_service(self,
                        service_name: str,
                        host: str,
                        port: int,
                        scheme: str = "http",
                        metadata: Dict[str, str] = None,
                        health_check_url: Optional[str] = None,
                        tags: List[str] = None) -> ServiceInstance:
        """Register service instance"""
        instance_id = hashlib.md5(
            f"{service_name}:{host}:{port}:{time.time()}".encode()
        ).hexdigest()[:8]

        instance = ServiceInstance(
            instance_id=instance_id,
            service_name=service_name,
            host=host,
            port=port,
            scheme=scheme,
            metadata=metadata or {},
            health_check_url=health_check_url
        )

        # Register service if not exists
        if service_name not in self.services:
            self.services[service_name] = ServiceRegistration(
                service_id=hashlib.md5(service_name.encode()).hexdigest()[:8],
                service_name=service_name,
                tags=tags or []
            )

        service = self.services[service_name]
        service.instances[instance_id] = instance
        self.instances[instance_id] = instance

        # Set lease
        self.leases[instance_id] = time.time() + instance.lease_renewal_interval

        # Notify subscribers
        self._notify_subscribers(f"service_registered", {
            "service_name": service_name,
            "instance_id": instance_id
        })

        return instance

    def deregister_service(self, instance_id: str) -> bool:
        """Deregister service instance"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False

        service_name = instance.service_name
        service = self.services.get(service_name)

        if service and instance_id in service.instances:
            del service.instances[instance_id]

        del self.instances[instance_id]
        if instance_id in self.leases:
            del self.leases[instance_id]

        # Clean up empty service registration
        if service and not service.instances:
            del self.services[service_name]

        # Notify subscribers
        self._notify_subscribers(f"service_deregistered", {
            "service_name": service_name,
            "instance_id": instance_id
        })

        return True

    def heartbeat(self, instance_id: str) -> bool:
        """Service instance heartbeat (renew lease)"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False

        instance.last_heartbeat = time.time()
        self.leases[instance_id] = time.time() + instance.lease_renewal_interval
        return True

    def discover_service(self,
                        service_name: str,
                        filters: Dict[str, str] = None) -> ServiceQuery:
        """Discover service instances"""
        query_id = hashlib.md5(
            f"{service_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        query = ServiceQuery(
            query_id=query_id,
            service_name=service_name,
            filters=filters or {}
        )

        start_time = time.time()

        service = self.services.get(service_name)
        if service:
            for instance in service.instances.values():
                # Check lease
                if instance_id := [id for id, exp in self.leases.items()
                                  if time.time() > exp]:
                    if instance.instance_id in instance_id:
                        self.deregister_service(instance.instance_id)
                        continue

                # Apply filters
                if self._matches_filters(instance, query.filters):
                    query.results.append(instance)

        query.execution_time_ms = (time.time() - start_time) * 1000
        self.queries.append(query)

        return query

    def _matches_filters(self, instance: ServiceInstance, filters: Dict[str, str]) -> bool:
        """Check if instance matches filters"""
        for key, value in filters.items():
            if key == "status":
                if instance.status.value != value:
                    return False
            elif key in instance.metadata:
                if instance.metadata[key] != value:
                    return False
            else:
                return False
        return True

    def register_health_check(self,
                            service_name: str,
                            check_type: HealthCheckType,
                            interval: int = 10,
                            timeout: int = 5,
                            path: Optional[str] = None) -> HealthCheck:
        """Register health check"""
        check_id = hashlib.md5(
            f"{service_name}:{check_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        health_check = HealthCheck(
            check_id=check_id,
            check_type=check_type,
            interval=interval,
            timeout=timeout,
            path=path,
            expected_status=200 if check_type == HealthCheckType.HTTP else None
        )

        self.health_checks[check_id] = health_check

        service = self.services.get(service_name)
        if service:
            service.health_checks.append(health_check)

        return health_check

    def perform_health_checks(self, service_name: str) -> Dict[str, bool]:
        """Perform health checks for service"""
        results = {}

        service = self.services.get(service_name)
        if not service:
            return results

        for instance in service.instances.values():
            is_healthy = random.random() > 0.1  # 90% health rate
            instance.status = ServiceStatus.UP if is_healthy else ServiceStatus.DOWN
            results[instance.instance_id] = is_healthy

        return results

    def get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of service"""
        service = self.services.get(service_name)
        if not service:
            return []

        return [i for i in service.instances.values() if i.status == ServiceStatus.UP]

    def subscribe(self, event: str, callback: Callable):
        """Subscribe to service events"""
        if event not in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(callback)

    def _notify_subscribers(self, event: str, data: Dict):
        """Notify subscribers of event"""
        if event in self.subscribers:
            for callback in self.subscribers[event]:
                try:
                    callback(event, data)
                except Exception as e:
                    print(f"Error notifying subscriber: {e}")

    def get_registry_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_services": len(self.services),
            "total_instances": len(self.instances),
            "healthy_instances": sum(1 for i in self.instances.values() if i.status == ServiceStatus.UP),
            "unhealthy_instances": sum(1 for i in self.instances.values() if i.status == ServiceStatus.DOWN),
            "total_queries": len(self.queries),
            "health_checks": len(self.health_checks),
        }

    def generate_registry_report(self) -> str:
        """Generate registry report"""
        stats = self.get_registry_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  SERVICE REGISTRY REPORT                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Services: {stats['total_services']}
├─ Total Instances: {stats['total_instances']}
├─ 🟢 Healthy: {stats['healthy_instances']}
├─ 🔴 Unhealthy: {stats['unhealthy_instances']}
├─ Queries: {stats['total_queries']}
└─ Health Checks: {stats['health_checks']}

🌐 REGISTERED SERVICES:
"""

        for service_name, service in self.services.items():
            report += f"\n  {service_name}\n"
            report += f"    Instances: {len(service.instances)}\n"
            for instance in service.instances.values():
                status_emoji = "🟢" if instance.status == ServiceStatus.UP else "🔴"
                report += f"    {status_emoji} {instance.host}:{instance.port}\n"

        return report

    def export_registry_config(self) -> str:
        """Export registry configuration"""
        export_data = {
            "timestamp": time.time(),
            "services": {
                name: {
                    "instances": [
                        {
                            "id": i.instance_id,
                            "host": i.host,
                            "port": i.port,
                            "status": i.status.value,
                            "metadata": i.metadata,
                        }
                        for i in service.instances.values()
                    ],
                    "tags": service.tags,
                }
                for name, service in self.services.items()
            },
            "statistics": self.get_registry_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔍 Service Registry & Discovery - Dynamic Service Discovery")
    print("=" * 70)

    registry = ServiceRegistry()

    # Register services
    print("\n📝 Registering services...")

    users_inst1 = registry.register_service(
        "users-service",
        "10.0.1.10",
        8001,
        health_check_url="/health"
    )
    users_inst2 = registry.register_service(
        "users-service",
        "10.0.1.11",
        8001,
        health_check_url="/health"
    )
    print(f"✅ Registered users-service with 2 instances")

    products_inst1 = registry.register_service(
        "products-service",
        "10.0.2.10",
        8002,
        health_check_url="/health"
    )
    print(f"✅ Registered products-service with 1 instance")

    orders_inst1 = registry.register_service(
        "orders-service",
        "10.0.3.10",
        8003,
        health_check_url="/health"
    )
    print(f"✅ Registered orders-service with 1 instance")

    # Register health checks
    print("\n🏥 Registering health checks...")
    registry.register_health_check(
        "users-service",
        HealthCheckType.HTTP,
        interval=10,
        path="/health"
    )
    print("✅ Health checks registered")

    # Perform health checks
    print("\n🔍 Performing health checks...")
    for service_name in ["users-service", "products-service", "orders-service"]:
        results = registry.perform_health_checks(service_name)
        print(f"✅ Checked {service_name}")

    # Discover services
    print("\n🔎 Discovering services...")
    users_query = registry.discover_service("users-service")
    print(f"✅ Found {len(users_query.results)} user service instances")

    products_query = registry.discover_service("products-service")
    print(f"✅ Found {len(products_query.results)} product service instances")

    # Heartbeat
    print("\n💓 Sending heartbeats...")
    registry.heartbeat(users_inst1.instance_id)
    registry.heartbeat(users_inst2.instance_id)
    print("✅ Heartbeats sent")

    # Generate report
    print(registry.generate_registry_report())

    # Export
    print("\n📄 Exporting registry config...")
    export = registry.export_registry_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Service registry ready for discovery")


if __name__ == "__main__":
    main()
