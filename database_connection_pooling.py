#!/usr/bin/env python3
"""
Database Connection Pooling - Connection pool management
Manages database connection pools with monitoring, health checking, and optimization
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time


class PoolStrategy(Enum):
    """Pool management strategies"""
    FIXED = "FIXED"
    DYNAMIC = "DYNAMIC"
    ADAPTIVE = "ADAPTIVE"


class ConnectionStatus(Enum):
    """Connection status"""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    CLOSED = "CLOSED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class Connection:
    """Database connection"""
    connection_id: str
    pool_id: str
    status: ConnectionStatus = ConnectionStatus.IDLE
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    query_count: int = 0
    error_count: int = 0
    response_time_ms: float = 0.0


@dataclass
class ConnectionPool:
    """Connection pool configuration"""
    pool_id: str
    name: str
    database_url: str
    min_connections: int
    max_connections: int
    idle_timeout_seconds: int
    max_lifetime_seconds: int
    strategy: PoolStrategy = PoolStrategy.FIXED
    created_at: float = field(default_factory=time.time)


@dataclass
class PoolMetrics:
    """Pool metrics"""
    pool_id: str
    total_connections: int
    idle_connections: int
    active_connections: int
    waiting_requests: int
    total_queries: int
    failed_queries: int
    avg_response_time: float
    peak_connections: int


class DatabaseConnectionPooling:
    """
    Database Connection Pooling

    Provides:
    - Connection pool management
    - Health checking
    - Dynamic sizing
    - Connection reuse
    - Timeout management
    - Performance monitoring
    """

    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.connections: Dict[str, Connection] = {}
        self.pool_connections: Dict[str, List[str]] = {}  # pool_id -> connection_ids
        self.wait_queue: Dict[str, List[Dict]] = {}  # pool_id -> waiting requests
        self.metrics_history: List[Dict] = []

    def create_pool(self,
                   pool_name: str,
                   database_url: str,
                   min_connections: int = 5,
                   max_connections: int = 20,
                   idle_timeout: int = 300,
                   max_lifetime: int = 3600,
                   strategy: PoolStrategy = PoolStrategy.FIXED) -> ConnectionPool:
        """Create connection pool"""
        pool_id = hashlib.md5(
            f"{pool_name}:{database_url}:{time.time()}".encode()
        ).hexdigest()[:8]

        pool = ConnectionPool(
            pool_id=pool_id,
            name=pool_name,
            database_url=database_url,
            min_connections=min_connections,
            max_connections=max_connections,
            idle_timeout_seconds=idle_timeout,
            max_lifetime_seconds=max_lifetime,
            strategy=strategy
        )

        self.pools[pool_id] = pool
        self.pool_connections[pool_id] = []
        self.wait_queue[pool_id] = []

        # Initialize minimum connections
        for _ in range(min_connections):
            self._create_connection(pool_id)

        return pool

    def _create_connection(self, pool_id: str) -> Optional[Connection]:
        """Create new connection in pool"""
        pool = self.pools.get(pool_id)
        if not pool:
            return None

        # Check max connections
        if len(self.pool_connections[pool_id]) >= pool.max_connections:
            return None

        connection_id = hashlib.md5(
            f"{pool_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        connection = Connection(
            connection_id=connection_id,
            pool_id=pool_id,
            status=ConnectionStatus.IDLE
        )

        self.connections[connection_id] = connection
        self.pool_connections[pool_id].append(connection_id)

        return connection

    def acquire_connection(self, pool_id: str, timeout_ms: int = 5000) -> Optional[Connection]:
        """Acquire connection from pool"""
        pool = self.pools.get(pool_id)
        if not pool:
            return None

        # Find idle connection
        for conn_id in self.pool_connections[pool_id]:
            conn = self.connections[conn_id]
            if conn.status == ConnectionStatus.IDLE:
                conn.status = ConnectionStatus.ACTIVE
                conn.last_used = time.time()
                return conn

        # Try to create new connection
        if len(self.pool_connections[pool_id]) < pool.max_connections:
            new_conn = self._create_connection(pool_id)
            if new_conn:
                new_conn.status = ConnectionStatus.ACTIVE
                return new_conn

        # Add to wait queue
        wait_request = {
            "requested_at": time.time(),
            "timeout_ms": timeout_ms,
            "request_id": hashlib.md5(f"{pool_id}:{time.time()}".encode()).hexdigest()[:8]
        }
        self.wait_queue[pool_id].append(wait_request)

        return None

    def release_connection(self, connection_id: str) -> bool:
        """Release connection back to pool"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        connection.status = ConnectionStatus.IDLE
        pool_id = connection.pool_id

        # Try to serve waiting request
        if self.wait_queue[pool_id]:
            wait_request = self.wait_queue[pool_id].pop(0)
            connection.status = ConnectionStatus.ACTIVE
            return True

        return True

    def execute_query(self,
                     connection_id: str,
                     query: str,
                     response_time_ms: float = 0.0) -> bool:
        """Execute query on connection"""
        connection = self.connections.get(connection_id)
        if not connection or connection.status != ConnectionStatus.ACTIVE:
            return False

        connection.query_count += 1
        connection.response_time_ms = response_time_ms

        return True

    def mark_connection_error(self, connection_id: str) -> bool:
        """Mark connection with error"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        connection.error_count += 1

        if connection.error_count > 3:
            connection.status = ConnectionStatus.UNHEALTHY
            return False

        return True

    def health_check_pool(self, pool_id: str) -> int:
        """Perform health check on pool connections"""
        healthy_count = 0
        now = time.time()

        for conn_id in self.pool_connections[pool_id]:
            conn = self.connections[conn_id]

            # Check idle timeout
            if (conn.status == ConnectionStatus.IDLE and
                now - conn.last_used > self.pools[pool_id].idle_timeout_seconds):
                conn.status = ConnectionStatus.CLOSED

            # Check max lifetime
            elif now - conn.created_at > self.pools[pool_id].max_lifetime_seconds:
                conn.status = ConnectionStatus.CLOSED

            # Check health
            elif conn.error_count > 5:
                conn.status = ConnectionStatus.UNHEALTHY

            else:
                healthy_count += 1

        return healthy_count

    def get_pool_metrics(self, pool_id: str) -> Optional[PoolMetrics]:
        """Get pool metrics"""
        pool = self.pools.get(pool_id)
        if not pool:
            return None

        connections = [self.connections[cid] for cid in self.pool_connections[pool_id]]

        idle = sum(1 for c in connections if c.status == ConnectionStatus.IDLE)
        active = sum(1 for c in connections if c.status == ConnectionStatus.ACTIVE)
        total_queries = sum(c.query_count for c in connections)
        failed = sum(c.error_count for c in connections)

        if connections:
            avg_response = sum(c.response_time_ms for c in connections) / len(connections)
        else:
            avg_response = 0

        metrics = PoolMetrics(
            pool_id=pool_id,
            total_connections=len(connections),
            idle_connections=idle,
            active_connections=active,
            waiting_requests=len(self.wait_queue[pool_id]),
            total_queries=total_queries,
            failed_queries=failed,
            avg_response_time=avg_response,
            peak_connections=pool.max_connections
        )

        return metrics

    def get_pooling_stats(self) -> Dict:
        """Get pooling statistics"""
        total_pools = len(self.pools)
        total_connections = len(self.connections)
        active_connections = sum(1 for c in self.connections.values()
                                if c.status == ConnectionStatus.ACTIVE)
        idle_connections = sum(1 for c in self.connections.values()
                              if c.status == ConnectionStatus.IDLE)

        return {
            "total_pools": total_pools,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "idle_connections": idle_connections,
            "waiting_requests": sum(len(v) for v in self.wait_queue.values()),
            "total_queries": sum(c.query_count for c in self.connections.values()),
            "failed_queries": sum(c.error_count for c in self.connections.values()),
        }

    def generate_pooling_report(self) -> str:
        """Generate pooling report"""
        stats = self.get_pooling_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DATABASE CONNECTION POOLING REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Pools: {stats['total_pools']}
├─ Total Connections: {stats['total_connections']}
├─ Active Connections: {stats['active_connections']}
├─ Idle Connections: {stats['idle_connections']}
├─ Waiting Requests: {stats['waiting_requests']}
├─ Total Queries: {stats['total_queries']}
└─ Failed Queries: {stats['failed_queries']}

📈 POOL METRICS:
"""

        for pool_id, pool in self.pools.items():
            metrics = self.get_pool_metrics(pool_id)
            if metrics:
                report += f"\n  {pool.name}\n"
                report += f"    Connections: {metrics.total_connections}/{pool.max_connections}\n"
                report += f"    Active: {metrics.active_connections}, Idle: {metrics.idle_connections}\n"
                report += f"    Avg Response: {metrics.avg_response_time:.2f}ms\n"

        return report

    def export_pooling_config(self) -> str:
        """Export pooling configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_pooling_stats(),
            "pools": [
                {
                    "id": p.pool_id,
                    "name": p.name,
                    "min_connections": p.min_connections,
                    "max_connections": p.max_connections,
                    "strategy": p.strategy.value,
                }
                for p in self.pools.values()
            ],
            "pool_metrics": [
                {
                    "pool_id": pid,
                    "total": m.total_connections,
                    "active": m.active_connections,
                }
                for pid, m in [(pid, self.get_pool_metrics(pid)) for pid in self.pools.keys()]
                if m
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🗄️  Database Connection Pooling - Connection Management")
    print("=" * 70)

    pooling = DatabaseConnectionPooling()

    # Create pools
    print("\n🏗️  Creating connection pools...")
    pool1 = pooling.create_pool(
        "Primary DB", "postgresql://primary.db:5432",
        min_connections=5, max_connections=20
    )
    pool2 = pooling.create_pool(
        "Analytics DB", "postgresql://analytics.db:5432",
        min_connections=3, max_connections=10,
        strategy=PoolStrategy.DYNAMIC
    )
    print(f"✅ Created {len(pooling.pools)} pools")

    # Acquire connections
    print("\n📡 Acquiring connections...")
    conn1 = pooling.acquire_connection(pool1.pool_id)
    conn2 = pooling.acquire_connection(pool1.pool_id)
    conn3 = pooling.acquire_connection(pool2.pool_id)
    print(f"✅ Acquired connections")

    # Execute queries
    print("\n⚡ Executing queries...")
    if conn1:
        pooling.execute_query(conn1.connection_id, "SELECT * FROM users", 45.5)
    if conn2:
        pooling.execute_query(conn2.connection_id, "SELECT * FROM products", 52.3)
    print("✅ Queries executed")

    # Release connections
    print("\n🔄 Releasing connections...")
    if conn1:
        pooling.release_connection(conn1.connection_id)
    if conn2:
        pooling.release_connection(conn2.connection_id)
    print("✅ Connections released")

    # Health check
    print("\n🏥 Performing health checks...")
    healthy1 = pooling.health_check_pool(pool1.pool_id)
    healthy2 = pooling.health_check_pool(pool2.pool_id)
    print(f"✅ Pool 1: {healthy1} healthy, Pool 2: {healthy2} healthy")

    # Generate report
    print(pooling.generate_pooling_report())

    # Export
    print("\n📄 Exporting pooling config...")
    export = pooling.export_pooling_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Database connection pooling ready")


if __name__ == "__main__":
    main()
