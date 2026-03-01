#!/usr/bin/env python3
"""
API Gateway Manager - Unified service entry point with routing and mediation
Manages cross-cutting concerns: routing, rate limiting, authentication, transformation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
import hashlib
import json
import time
import random


class RouteType(Enum):
    """Route types"""
    HTTP = "HTTP"
    GRPC = "GRPC"
    WEBSOCKET = "WEBSOCKET"
    GRAPHQL = "GRAPHQL"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_CONNECTIONS = "LEAST_CONNECTIONS"
    WEIGHTED = "WEIGHTED"
    IP_HASH = "IP_HASH"
    RANDOM = "RANDOM"


class AuthType(Enum):
    """Authentication types"""
    NONE = "NONE"
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH2 = "OAUTH2"
    MTLS = "MTLS"


class GatewayMetric(Enum):
    """Gateway metrics"""
    REQUESTS = "REQUESTS"
    RESPONSE_TIME = "RESPONSE_TIME"
    ERROR_RATE = "ERROR_RATE"
    THROUGHPUT = "THROUGHPUT"
    ACTIVE_CONNECTIONS = "ACTIVE_CONNECTIONS"


@dataclass
class Upstream:
    """Upstream service"""
    upstream_id: str
    name: str
    url: str
    port: int
    weight: int = 1
    healthy: bool = True
    active_connections: int = 0
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    last_check: float = field(default_factory=time.time)


@dataclass
class Route:
    """API route definition"""
    route_id: str
    path_pattern: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    route_type: RouteType
    upstreams: List[Upstream] = field(default_factory=list)
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    auth_type: AuthType = AuthType.BEARER_TOKEN
    rate_limit: int = 1000  # requests per minute
    timeout_ms: int = 30000
    retry_count: int = 3
    cache_ttl: int = 300  # seconds
    middleware: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class GatewayRequest:
    """Incoming request to gateway"""
    request_id: str
    path: str
    method: str
    headers: Dict[str, str]
    body: Optional[str] = None
    source_ip: str = "0.0.0.0"
    timestamp: float = field(default_factory=time.time)


@dataclass
class GatewayResponse:
    """Response from gateway"""
    response_id: str
    request_id: str
    status_code: int
    body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    upstream_id: Optional[str] = None
    processing_time_ms: float = 0.0
    cached: bool = False


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    bucket_id: str
    client_id: str
    tokens: int
    max_tokens: int
    refill_rate: int  # tokens per second
    last_refill: float = field(default_factory=time.time)


@dataclass
class GatewayMetrics:
    """Gateway metrics"""
    total_requests: int = 0
    total_errors: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    active_connections: int = 0
    request_history: List[float] = field(default_factory=list)


class APIGatewayManager:
    """
    API Gateway management system

    Provides:
    - Request routing and load balancing
    - Rate limiting and quota management
    - Authentication and authorization
    - Response caching
    - Circuit breaking
    - Request/response transformation
    - Metrics collection
    """

    def __init__(self, gateway_url: str = "http://localhost:8000"):
        self.gateway_url = gateway_url
        self.routes: Dict[str, Route] = {}
        self.upstreams: Dict[str, Upstream] = {}
        self.rate_limits: Dict[str, RateLimitBucket] = {}
        self.request_log: List[Tuple[GatewayRequest, GatewayResponse]] = []
        self.cache: Dict[str, Tuple[GatewayResponse, float]] = {}  # response, expiry
        self.metrics = GatewayMetrics()
        self.middleware_registry: Dict[str, Callable] = {}
        self.round_robin_index: int = 0

    def register_upstream(self,
                        name: str,
                        url: str,
                        port: int,
                        weight: int = 1) -> Upstream:
        """Register upstream service"""
        upstream_id = hashlib.md5(f"{name}:{url}:{port}".encode()).hexdigest()[:8]

        upstream = Upstream(
            upstream_id=upstream_id,
            name=name,
            url=url,
            port=port,
            weight=weight
        )

        self.upstreams[upstream_id] = upstream
        return upstream

    def register_route(self,
                      path_pattern: str,
                      method: str,
                      route_type: RouteType = RouteType.HTTP,
                      upstream_ids: List[str] = None,
                      auth_type: AuthType = AuthType.BEARER_TOKEN,
                      rate_limit: int = 1000) -> Route:
        """Register API route"""
        route_id = hashlib.md5(
            f"{path_pattern}:{method}:{time.time()}".encode()
        ).hexdigest()[:8]

        upstreams = [self.upstreams[uid] for uid in (upstream_ids or [])
                     if uid in self.upstreams]

        route = Route(
            route_id=route_id,
            path_pattern=path_pattern,
            method=method,
            route_type=route_type,
            upstreams=upstreams,
            auth_type=auth_type,
            rate_limit=rate_limit
        )

        self.routes[route_id] = route
        return route

    def process_request(self,
                       path: str,
                       method: str,
                       headers: Dict[str, str],
                       body: Optional[str] = None,
                       source_ip: str = "0.0.0.0") -> GatewayResponse:
        """Process incoming request"""
        request_id = hashlib.md5(
            f"{path}:{method}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:8]

        request = GatewayRequest(
            request_id=request_id,
            path=path,
            method=method,
            headers=headers,
            body=body,
            source_ip=source_ip
        )

        start_time = time.time()

        # Find matching route
        route = self._match_route(path, method)
        if not route:
            response = GatewayResponse(
                response_id=hashlib.md5(f"{request_id}".encode()).hexdigest()[:8],
                request_id=request_id,
                status_code=404,
                body="Route not found"
            )
            self.metrics.total_errors += 1
            return response

        # Check authentication
        if route.auth_type != AuthType.NONE:
            if not self._authenticate(headers, route.auth_type):
                response = GatewayResponse(
                    response_id=hashlib.md5(f"{request_id}".encode()).hexdigest()[:8],
                    request_id=request_id,
                    status_code=401,
                    body="Unauthorized"
                )
                self.metrics.total_errors += 1
                return response

        # Check rate limit
        client_id = self._extract_client_id(headers, source_ip)
        if not self._check_rate_limit(client_id, route.rate_limit):
            response = GatewayResponse(
                response_id=hashlib.md5(f"{request_id}".encode()).hexdigest()[:8],
                request_id=request_id,
                status_code=429,
                body="Rate limit exceeded"
            )
            self.metrics.total_errors += 1
            return response

        # Check cache
        cache_key = f"{method}:{path}"
        if method == "GET" and cache_key in self.cache:
            cached_response, expiry = self.cache[cache_key]
            if time.time() < expiry:
                self.metrics.cache_hits += 1
                cached_response.cached = True
                return cached_response
            else:
                del self.cache[cache_key]

        self.metrics.cache_misses += 1

        # Select upstream
        upstream = self._select_upstream(route)
        if not upstream:
            response = GatewayResponse(
                response_id=hashlib.md5(f"{request_id}".encode()).hexdigest()[:8],
                request_id=request_id,
                status_code=503,
                body="No healthy upstreams available"
            )
            self.metrics.total_errors += 1
            return response

        # Apply middleware
        modified_body = body
        for middleware_name in route.middleware:
            if middleware_name in self.middleware_registry:
                modified_body = self.middleware_registry[middleware_name](modified_body)

        # Simulate upstream call with retries
        response = None
        for attempt in range(route.retry_count):
            response = self._call_upstream(upstream, request, modified_body)
            if response.status_code < 500:
                break

        # Cache successful responses
        if response.status_code == 200 and method == "GET" and route.cache_ttl > 0:
            self.cache[cache_key] = (response, time.time() + route.cache_ttl)

        # Update metrics
        processing_time = (time.time() - start_time) * 1000
        response.processing_time_ms = processing_time
        self.metrics.total_requests += 1
        self.metrics.request_history.append(processing_time)
        if response.status_code >= 400:
            self.metrics.total_errors += 1

        self._update_response_time_metrics()
        self.request_log.append((request, response))

        return response

    def _match_route(self, path: str, method: str) -> Optional[Route]:
        """Match path and method to route"""
        for route in self.routes.values():
            if route.method == method and self._path_matches(path, route.path_pattern):
                return route
        return None

    def _path_matches(self, path: str, pattern: str) -> bool:
        """Simple path matching (supports /users/{id})"""
        pattern_parts = pattern.split('/')
        path_parts = path.split('/')

        if len(pattern_parts) != len(path_parts):
            return False

        for p_part, path_part in zip(pattern_parts, path_parts):
            if p_part.startswith('{') and p_part.endswith('}'):
                continue
            if p_part != path_part:
                return False

        return True

    def _authenticate(self, headers: Dict[str, str], auth_type: AuthType) -> bool:
        """Authenticate request"""
        if auth_type == AuthType.NONE:
            return True
        elif auth_type == AuthType.API_KEY:
            return "X-API-Key" in headers
        elif auth_type == AuthType.BEARER_TOKEN:
            return "Authorization" in headers and headers["Authorization"].startswith("Bearer ")
        elif auth_type == AuthType.OAUTH2:
            return "Authorization" in headers and headers["Authorization"].startswith("Bearer ")
        elif auth_type == AuthType.MTLS:
            return "X-Client-Cert" in headers
        return False

    def _extract_client_id(self, headers: Dict[str, str], source_ip: str) -> str:
        """Extract client ID from headers or IP"""
        if "X-API-Key" in headers:
            return headers["X-API-Key"]
        elif "Authorization" in headers:
            return headers["Authorization"][:20]  # Partial token
        else:
            return source_ip

    def _check_rate_limit(self, client_id: str, limit: int) -> bool:
        """Check token bucket rate limit"""
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = RateLimitBucket(
                bucket_id=hashlib.md5(client_id.encode()).hexdigest()[:8],
                client_id=client_id,
                tokens=limit,
                max_tokens=limit,
                refill_rate=limit // 60  # Refill per second
            )

        bucket = self.rate_limits[client_id]

        # Refill tokens
        now = time.time()
        elapsed = now - bucket.last_refill
        refilled = int(elapsed * bucket.refill_rate)
        bucket.tokens = min(bucket.max_tokens, bucket.tokens + refilled)
        bucket.last_refill = now

        # Check limit
        if bucket.tokens > 0:
            bucket.tokens -= 1
            return True
        return False

    def _select_upstream(self, route: Route) -> Optional[Upstream]:
        """Select upstream based on load balancing strategy"""
        healthy_upstreams = [u for u in route.upstreams if u.healthy]

        if not healthy_upstreams:
            return None

        if route.load_balancing == LoadBalancingStrategy.ROUND_ROBIN:
            upstream = healthy_upstreams[self.round_robin_index % len(healthy_upstreams)]
            self.round_robin_index += 1
            return upstream
        elif route.load_balancing == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_upstreams, key=lambda u: u.active_connections)
        elif route.load_balancing == LoadBalancingStrategy.WEIGHTED:
            total_weight = sum(u.weight for u in healthy_upstreams)
            choice = random.uniform(0, total_weight)
            current = 0
            for upstream in healthy_upstreams:
                current += upstream.weight
                if choice <= current:
                    return upstream
        elif route.load_balancing == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_upstreams)

        return healthy_upstreams[0]

    def _call_upstream(self,
                      upstream: Upstream,
                      request: GatewayRequest,
                      body: Optional[str]) -> GatewayResponse:
        """Call upstream service"""
        upstream.active_connections += 1

        start_time = time.time()

        # Simulate upstream call
        success = random.random() > 0.05  # 95% success rate
        status_code = 200 if success else 500
        response_body = json.dumps({"result": "success"}) if success else None

        response_time = (time.time() - start_time) * 1000
        upstream.response_time_ms = response_time
        upstream.error_rate = 0.05

        upstream.active_connections -= 1

        return GatewayResponse(
            response_id=hashlib.md5(
                f"{request.request_id}:{upstream.upstream_id}".encode()
            ).hexdigest()[:8],
            request_id=request.request_id,
            status_code=status_code,
            body=response_body,
            upstream_id=upstream.upstream_id,
            processing_time_ms=response_time
        )

    def _update_response_time_metrics(self):
        """Update response time metrics"""
        if self.metrics.request_history:
            sorted_times = sorted(self.metrics.request_history)
            self.metrics.avg_response_time_ms = sum(sorted_times) / len(sorted_times)
            self.metrics.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]

    def check_upstream_health(self, upstream_id: str) -> bool:
        """Health check upstream"""
        upstream = self.upstreams.get(upstream_id)
        if not upstream:
            return False

        # Simulate health check
        is_healthy = random.random() > 0.1  # 90% health rate
        upstream.healthy = is_healthy
        upstream.last_check = time.time()

        return is_healthy

    def register_middleware(self, name: str, handler: Callable):
        """Register middleware handler"""
        self.middleware_registry[name] = handler

    def get_gateway_stats(self) -> Dict:
        """Get gateway statistics"""
        return {
            "total_requests": self.metrics.total_requests,
            "total_errors": self.metrics.total_errors,
            "error_rate": (self.metrics.total_errors / max(1, self.metrics.total_requests)),
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_rate": (self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses)),
            "avg_response_time_ms": self.metrics.avg_response_time_ms,
            "p99_response_time_ms": self.metrics.p99_response_time_ms,
            "routes": len(self.routes),
            "upstreams": len(self.upstreams),
            "healthy_upstreams": sum(1 for u in self.upstreams.values() if u.healthy),
        }

    def generate_gateway_report(self) -> str:
        """Generate gateway report"""
        stats = self.get_gateway_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      API GATEWAY REPORT                                    ║
║                      Gateway: {self.gateway_url}                          ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 REQUEST STATISTICS:
├─ Total Requests: {stats['total_requests']}
├─ Errors: {stats['total_errors']}
├─ Error Rate: {stats['error_rate']:.2%}
├─ Avg Response Time: {stats['avg_response_time_ms']:.2f}ms
└─ P99 Response Time: {stats['p99_response_time_ms']:.2f}ms

💾 CACHING:
├─ Cache Hits: {stats['cache_hits']}
├─ Cache Misses: {stats['cache_misses']}
└─ Hit Rate: {stats['cache_hit_rate']:.2%}

🌐 UPSTREAMS:
├─ Total: {stats['upstreams']}
└─ 🟢 Healthy: {stats['healthy_upstreams']}/{stats['upstreams']}

📍 ROUTES:
"""

        for route in self.routes.values():
            report += f"\n  {route.method} {route.path_pattern}\n"
            report += f"    Type: {route.route_type.value}\n"
            report += f"    Auth: {route.auth_type.value}\n"
            report += f"    Rate Limit: {route.rate_limit} req/min\n"

        return report

    def export_gateway_config(self) -> str:
        """Export gateway configuration"""
        export_data = {
            "gateway_url": self.gateway_url,
            "timestamp": time.time(),
            "routes": [
                {
                    "path": r.path_pattern,
                    "method": r.method,
                    "type": r.route_type.value,
                    "auth": r.auth_type.value,
                    "upstreams": len(r.upstreams),
                    "rate_limit": r.rate_limit,
                }
                for r in self.routes.values()
            ],
            "upstreams": [
                {
                    "name": u.name,
                    "url": u.url,
                    "healthy": u.healthy,
                    "response_time": u.response_time_ms,
                }
                for u in self.upstreams.values()
            ],
            "statistics": self.get_gateway_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🚪 API Gateway Manager - Unified Service Entry Point")
    print("=" * 70)

    gateway = APIGatewayManager("http://localhost:8000")

    # Register upstreams
    print("\n📝 Registering upstreams...")
    users_upstream = gateway.register_upstream(
        "users-service",
        "http://users-service",
        4001,
        weight=2
    )
    products_upstream = gateway.register_upstream(
        "products-service",
        "http://products-service",
        4002,
        weight=1
    )
    orders_upstream = gateway.register_upstream(
        "orders-service",
        "http://orders-service",
        4003,
        weight=2
    )
    print(f"✅ Registered {len(gateway.upstreams)} upstreams")

    # Register routes
    print("\n📍 Registering routes...")
    gateway.register_route(
        "/api/v1/users",
        "GET",
        route_type=RouteType.HTTP,
        upstream_ids=[users_upstream.upstream_id],
        rate_limit=1000
    )
    gateway.register_route(
        "/api/v1/users/{id}",
        "GET",
        route_type=RouteType.HTTP,
        upstream_ids=[users_upstream.upstream_id],
        rate_limit=1000
    )
    gateway.register_route(
        "/api/v1/products",
        "GET",
        route_type=RouteType.HTTP,
        upstream_ids=[products_upstream.upstream_id],
        rate_limit=1000
    )
    gateway.register_route(
        "/api/v1/orders",
        "POST",
        route_type=RouteType.HTTP,
        upstream_ids=[orders_upstream.upstream_id],
        rate_limit=500
    )
    print(f"✅ Registered {len(gateway.routes)} routes")

    # Register middleware
    print("\n⚙️  Registering middleware...")
    def compress_middleware(body):
        return body  # Simulate compression

    gateway.register_middleware("compress", compress_middleware)
    print("✅ Middleware registered")

    # Process requests
    print("\n📨 Processing requests...")
    response1 = gateway.process_request(
        "/api/v1/users",
        "GET",
        {"Authorization": "Bearer token123"},
        source_ip="192.168.1.100"
    )
    print(f"✅ Request 1: {response1.status_code}")

    response2 = gateway.process_request(
        "/api/v1/products",
        "GET",
        {"Authorization": "Bearer token456"},
        source_ip="192.168.1.101"
    )
    print(f"✅ Request 2: {response2.status_code}")

    response3 = gateway.process_request(
        "/api/v1/orders",
        "POST",
        {"Authorization": "Bearer token789"},
        body='{"items": []}',
        source_ip="192.168.1.102"
    )
    print(f"✅ Request 3: {response3.status_code}")

    # Check health
    print("\n🏥 Checking upstream health...")
    for upstream_id in gateway.upstreams.keys():
        gateway.check_upstream_health(upstream_id)
    print("✅ Health checks completed")

    # Generate report
    print(gateway.generate_gateway_report())

    # Export
    print("\n📄 Exporting gateway config...")
    export = gateway.export_gateway_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ API Gateway ready for traffic")


if __name__ == "__main__":
    main()
