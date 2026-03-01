#!/usr/bin/env python3
"""
Service Mesh Manager - Service mesh orchestration and observability
Manages Istio/Linkerd configurations, traffic policies, and mesh observability
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import random


class MeshType(Enum):
    """Service mesh types"""
    ISTIO = "ISTIO"
    LINKERD = "LINKERD"
    CONSUL = "CONSUL"
    APP_MESH = "APP_MESH"


class TrafficPolicyType(Enum):
    """Types of traffic policies"""
    LOAD_BALANCING = "LOAD_BALANCING"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    RETRY = "RETRY"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITING = "RATE_LIMITING"
    CANARY = "CANARY"
    A_B_TESTING = "A_B_TESTING"
    FAULT_INJECTION = "FAULT_INJECTION"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_REQUEST = "LEAST_REQUEST"
    RANDOM = "RANDOM"
    CONSISTENT_HASH = "CONSISTENT_HASH"
    MAGLEV = "MAGLEV"


class MtlsMode(Enum):
    """mTLS modes"""
    DISABLE = "DISABLE"
    PERMISSIVE = "PERMISSIVE"
    STRICT = "STRICT"


@dataclass
class ServiceInfo:
    """Information about a service in the mesh"""
    service_name: str
    namespace: str
    port: int
    protocol: str  # "HTTP", "gRPC", "TCP"
    endpoints: List[str] = field(default_factory=list)  # Pod IPs
    healthy_endpoints: int = 0
    total_endpoints: int = 0
    mtls_enabled: bool = False
    traffic_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrafficPolicy:
    """Traffic management policy"""
    policy_id: str
    policy_type: TrafficPolicyType
    source_service: str
    destination_service: str
    created_at: float = field(default_factory=time.time)
    config: Dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class VirtualService:
    """Istio VirtualService configuration"""
    vs_id: str
    name: str
    namespace: str
    hosts: List[str] = field(default_factory=list)
    http_routes: List[Dict] = field(default_factory=list)
    tcp_routes: List[Dict] = field(default_factory=list)
    tls_routes: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class DestinationRule:
    """Istio DestinationRule configuration"""
    dr_id: str
    name: str
    namespace: str
    host: str
    traffic_policy: Optional[Dict] = None
    subsets: List[Dict] = field(default_factory=list)
    export_to: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class MeshMetrics:
    """Metrics for mesh health and performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    error_rate: float = 0.0
    throughput_rps: float = 0.0
    active_connections: int = 0


@dataclass
class MeshStatus:
    """Overall mesh status"""
    mesh_type: MeshType
    timestamp: float
    control_plane_healthy: bool = True
    services_count: int = 0
    policies_count: int = 0
    mtls_coverage: float = 0.0  # Percentage
    mesh_metrics: MeshMetrics = field(default_factory=MeshMetrics)
    issues: List[str] = field(default_factory=list)


class ServiceMeshManager:
    """
    Enterprise service mesh management system

    Manages:
    - Service mesh deployment and configuration
    - Virtual services and destination rules
    - Traffic policies and routing
    - mTLS and security policies
    - Service discovery and endpoints
    - Mesh observability and metrics
    - Policy validation and testing
    """

    def __init__(self, mesh_type: MeshType = MeshType.ISTIO):
        self.mesh_type = mesh_type
        self.services: Dict[str, ServiceInfo] = {}
        self.traffic_policies: Dict[str, TrafficPolicy] = {}
        self.virtual_services: Dict[str, VirtualService] = {}
        self.destination_rules: Dict[str, DestinationRule] = {}
        self.mesh_status = MeshStatus(mesh_type=mesh_type, timestamp=time.time())

    def register_service(self,
                        service_name: str,
                        namespace: str,
                        port: int,
                        protocol: str = "HTTP") -> ServiceInfo:
        """
        Register service in mesh

        Args:
            service_name: Name of service
            namespace: Kubernetes namespace
            port: Service port
            protocol: Protocol (HTTP, gRPC, TCP)

        Returns:
            ServiceInfo for registered service
        """
        service = ServiceInfo(
            service_name=service_name,
            namespace=namespace,
            port=port,
            protocol=protocol,
            endpoints=self._discover_endpoints(service_name, namespace),
        )

        # Simulate endpoint discovery
        service.total_endpoints = random.randint(1, 10)
        service.healthy_endpoints = random.randint(int(service.total_endpoints * 0.8), service.total_endpoints)

        self.services[f"{namespace}/{service_name}"] = service
        self.mesh_status.services_count = len(self.services)

        return service

    def _discover_endpoints(self, service_name: str, namespace: str) -> List[str]:
        """Discover service endpoints"""
        return [f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}" for _ in range(random.randint(2, 5))]

    def create_traffic_policy(self,
                            source_service: str,
                            destination_service: str,
                            policy_type: TrafficPolicyType,
                            config: Dict) -> TrafficPolicy:
        """
        Create traffic management policy

        Args:
            source_service: Source service
            destination_service: Destination service
            policy_type: Type of policy
            config: Policy configuration

        Returns:
            Created TrafficPolicy
        """
        policy_id = hashlib.md5(
            f"{source_service}:{destination_service}:{policy_type.value}".encode()
        ).hexdigest()[:8]

        policy = TrafficPolicy(
            policy_id=policy_id,
            policy_type=policy_type,
            source_service=source_service,
            destination_service=destination_service,
            config=config
        )

        self.traffic_policies[policy_id] = policy
        self.mesh_status.policies_count = len(self.traffic_policies)

        return policy

    def enable_mtls(self, namespace: str = None, mode: MtlsMode = MtlsMode.STRICT) -> bool:
        """
        Enable mTLS for services

        Args:
            namespace: Namespace to enable mTLS in (None = all)
            mode: mTLS mode (STRICT, PERMISSIVE)

        Returns:
            Success status
        """
        target_services = [
            s for name, s in self.services.items()
            if namespace is None or name.startswith(namespace)
        ]

        for service in target_services:
            service.mtls_enabled = True

        # Calculate mTLS coverage
        if self.services:
            mtls_services = sum(1 for s in self.services.values() if s.mtls_enabled)
            self.mesh_status.mtls_coverage = (mtls_services / len(self.services)) * 100

        return True

    def create_virtual_service(self,
                             name: str,
                             namespace: str,
                             hosts: List[str],
                             routes: List[Dict]) -> VirtualService:
        """
        Create Istio VirtualService

        Args:
            name: VirtualService name
            namespace: Namespace
            hosts: Service hosts
            routes: HTTP routes

        Returns:
            Created VirtualService
        """
        vs_id = hashlib.md5(f"{namespace}:{name}".encode()).hexdigest()[:8]

        vs = VirtualService(
            vs_id=vs_id,
            name=name,
            namespace=namespace,
            hosts=hosts,
            http_routes=routes
        )

        self.virtual_services[vs_id] = vs
        return vs

    def create_destination_rule(self,
                               name: str,
                               namespace: str,
                               host: str,
                               traffic_policy: Dict = None,
                               subsets: List[Dict] = None) -> DestinationRule:
        """
        Create Istio DestinationRule

        Args:
            name: DestinationRule name
            namespace: Namespace
            host: Destination host
            traffic_policy: Traffic policy config
            subsets: Service subsets

        Returns:
            Created DestinationRule
        """
        dr_id = hashlib.md5(f"{namespace}:{name}".encode()).hexdigest()[:8]

        dr = DestinationRule(
            dr_id=dr_id,
            name=name,
            namespace=namespace,
            host=host,
            traffic_policy=traffic_policy or self._default_traffic_policy(),
            subsets=subsets or []
        )

        self.destination_rules[dr_id] = dr
        return dr

    def _default_traffic_policy(self) -> Dict:
        """Generate default traffic policy"""
        return {
            "connectionPool": {
                "tcp": {"maxConnections": 100},
                "http": {"http1MaxPendingRequests": 100, "http2MaxRequests": 1000},
            },
            "outlierDetection": {
                "consecutive5xxErrors": 5,
                "interval": "30s",
                "baseEjectionTime": "30s",
            },
            "loadBalancer": {
                "simple": "ROUND_ROBIN",
            },
        }

    def simulate_canary_deployment(self,
                                   service: str,
                                   canary_percentage: int = 10) -> VirtualService:
        """
        Simulate canary deployment

        Args:
            service: Service name
            canary_percentage: Percentage of traffic to canary (0-100)

        Returns:
            VirtualService configured for canary
        """
        routes = [
            {
                "name": "canary",
                "destination": {"host": service, "subset": "canary"},
                "weight": canary_percentage,
            },
            {
                "name": "stable",
                "destination": {"host": service, "subset": "stable"},
                "weight": 100 - canary_percentage,
            },
        ]

        return self.create_virtual_service(
            name=f"{service}-canary",
            namespace="default",
            hosts=[service],
            routes=routes
        )

    def setup_circuit_breaker(self,
                            service: str,
                            consecutive_errors: int = 5,
                            interval: str = "30s") -> Dict:
        """
        Setup circuit breaker for service

        Args:
            service: Service name
            consecutive_errors: Error threshold
            interval: Check interval

        Returns:
            Circuit breaker configuration
        """
        config = {
            "outlierDetection": {
                "consecutive5xxErrors": consecutive_errors,
                "interval": interval,
                "baseEjectionTime": "30s",
                "maxEjectionPercent": 50,
                "minRequestVolume": 5,
                "splitExternalLocalOriginErrors": True,
            }
        }

        self.create_traffic_policy(
            source_service="*",
            destination_service=service,
            policy_type=TrafficPolicyType.CIRCUIT_BREAKER,
            config=config
        )

        return config

    def get_mesh_status(self) -> MeshStatus:
        """Get overall mesh status"""
        # Simulate metrics
        total_req = random.randint(10000, 100000)
        success_rate = random.uniform(0.95, 0.99)
        error_rate = 1 - success_rate

        self.mesh_status.mesh_metrics = MeshMetrics(
            total_requests=total_req,
            successful_requests=int(total_req * success_rate),
            failed_requests=int(total_req * error_rate),
            p50_latency=random.uniform(10, 50),
            p95_latency=random.uniform(50, 200),
            p99_latency=random.uniform(200, 500),
            error_rate=error_rate * 100,
            throughput_rps=random.uniform(100, 500),
            active_connections=random.randint(100, 1000)
        )

        # Check for issues
        self.mesh_status.issues = []
        if self.mesh_status.mesh_metrics.error_rate > 1:
            self.mesh_status.issues.append(f"High error rate: {self.mesh_status.mesh_metrics.error_rate:.2f}%")
        if self.mesh_status.mesh_metrics.p99_latency > 300:
            self.mesh_status.issues.append(f"High P99 latency: {self.mesh_status.mesh_metrics.p99_latency:.0f}ms")
        if self.mesh_status.mtls_coverage < 100:
            self.mesh_status.issues.append(f"Incomplete mTLS coverage: {self.mesh_status.mtls_coverage:.1f}%")

        self.mesh_status.timestamp = time.time()
        return self.mesh_status

    def generate_mesh_config_yaml(self, service: str) -> str:
        """Generate Istio YAML configuration"""
        yaml = f"""---
# VirtualService
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {service}
  namespace: default
spec:
  hosts:
  - {service}
  http:
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: {service}
        port:
          number: 8080
    timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 2s
---
# DestinationRule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {service}
  namespace: default
spec:
  host: {service}
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
---
# PeerAuthentication
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: {service}
  namespace: default
spec:
  mtls:
    mode: STRICT
---
# AuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: {service}
  namespace: default
spec:
  rules:
  - from:
    - source:
        principals:
        - cluster.local/ns/default/sa/app
    to:
    - operation:
        methods:
        - GET
        - POST
        paths:
        - /api/*
"""
        return yaml

    def generate_mesh_report(self) -> str:
        """Generate comprehensive mesh status report"""
        status = self.get_mesh_status()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         SERVICE MESH STATUS REPORT                         ║
║                         Mesh Type: {status.mesh_type.value}                       ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 MESH HEALTH:
├─ Control Plane: {'✅ Healthy' if status.control_plane_healthy else '❌ Degraded'}
├─ Services: {status.services_count}
├─ Traffic Policies: {status.policies_count}
└─ mTLS Coverage: {status.mtls_coverage:.1f}%

📈 TRAFFIC METRICS (Last 1 hour):
├─ Total Requests: {status.mesh_metrics.total_requests:,}
├─ Success Rate: {(status.mesh_metrics.successful_requests/status.mesh_metrics.total_requests*100):.2f}%
├─ Error Rate: {status.mesh_metrics.error_rate:.2f}%
├─ Throughput: {status.mesh_metrics.throughput_rps:.0f} RPS
├─ P50 Latency: {status.mesh_metrics.p50_latency:.1f}ms
├─ P95 Latency: {status.mesh_metrics.p95_latency:.1f}ms
├─ P99 Latency: {status.mesh_metrics.p99_latency:.1f}ms
└─ Active Connections: {status.mesh_metrics.active_connections}

📋 REGISTERED SERVICES:
"""

        for service_key, service in list(self.services.items())[:5]:
            mtls_icon = "🔒" if service.mtls_enabled else "🔓"
            health_pct = (service.healthy_endpoints / service.total_endpoints * 100) if service.total_endpoints > 0 else 0
            report += f"\n{mtls_icon} {service.service_name} ({service.namespace})\n"
            report += f"  Port: {service.port} ({service.protocol})\n"
            report += f"  Endpoints: {service.healthy_endpoints}/{service.total_endpoints} healthy ({health_pct:.0f}%)\n"

        if status.issues:
            report += f"\n⚠️  ISSUES:\n"
            for issue in status.issues:
                report += f"  • {issue}\n"

        return report

    def export_mesh_config(self) -> str:
        """Export mesh configuration as JSON"""
        export_data = {
            "mesh_type": self.mesh_type.value,
            "services": {
                key: {
                    "name": svc.service_name,
                    "namespace": svc.namespace,
                    "port": svc.port,
                    "protocol": svc.protocol,
                    "endpoints": svc.total_endpoints,
                    "healthy": svc.healthy_endpoints,
                    "mtls_enabled": svc.mtls_enabled,
                }
                for key, svc in self.services.items()
            },
            "policies": {
                key: {
                    "type": policy.policy_type.value,
                    "source": policy.source_service,
                    "destination": policy.destination_service,
                }
                for key, policy in self.traffic_policies.items()
            },
            "virtual_services": len(self.virtual_services),
            "destination_rules": len(self.destination_rules),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🕸️  Service Mesh Manager - Service Mesh Orchestration")
    print("=" * 70)

    manager = ServiceMeshManager(mesh_type=MeshType.ISTIO)

    # Register services
    print("\n📝 Registering services in mesh...")
    manager.register_service("auth-service", "default", 8080, "HTTP")
    manager.register_service("user-service", "default", 8081, "gRPC")
    manager.register_service("payment-service", "default", 8082, "HTTP")
    manager.register_service("notification-service", "production", 8083, "HTTP")

    # Enable mTLS
    print("\n🔒 Enabling mTLS...")
    manager.enable_mtls(mode=MtlsMode.STRICT)

    # Create traffic policies
    print("\n🚦 Setting up traffic policies...")
    manager.setup_circuit_breaker("payment-service", consecutive_errors=5)
    manager.create_traffic_policy(
        source_service="auth-service",
        destination_service="user-service",
        policy_type=TrafficPolicyType.RETRY,
        config={"attempts": 3, "perTryTimeout": "2s"}
    )

    # Setup canary deployment
    print("\n🐤 Setting up canary deployment...")
    manager.simulate_canary_deployment("user-service", canary_percentage=10)

    # Generate report
    print(manager.generate_mesh_report())

    # Export config
    print("\n📄 Exporting mesh configuration...")
    export = manager.export_mesh_config()
    print(f"✅ Exported {len(export)} characters of mesh config")

    print("\n" + "=" * 70)
    print("✨ Service mesh management complete")


if __name__ == "__main__":
    main()
