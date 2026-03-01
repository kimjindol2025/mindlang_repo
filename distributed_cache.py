#!/usr/bin/env python3
"""
Distributed Cache Coordinator - Cache coherence and synchronization
Manages multi-node cache coordination with consistency guarantees
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time
import random


class CacheConsistency(Enum):
    """Cache consistency models"""
    STRONG = "STRONG"
    EVENTUAL = "EVENTUAL"
    CAUSAL = "CAUSAL"


class CacheEvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "LRU"
    LFU = "LFU"
    FIFO = "FIFO"
    TTL = "TTL"


class InvalidationStrategy(Enum):
    """Cache invalidation strategies"""
    WRITE_THROUGH = "WRITE_THROUGH"
    WRITE_BACK = "WRITE_BACK"
    WRITE_AROUND = "WRITE_AROUND"
    BROADCAST = "BROADCAST"
    GOSSIP = "GOSSIP"


@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    value: Any
    version: int
    created_at: float
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[int] = None  # seconds
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheNode:
    """Cache node in distributed system"""
    node_id: str
    node_name: str
    host: str
    port: int
    cache: Dict[str, CacheEntry] = field(default_factory=dict)
    max_size: int = 1000
    eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    is_active: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    hits: int = 0
    misses: int = 0


@dataclass
class CacheInvalidation:
    """Cache invalidation event"""
    invalidation_id: str
    key: str
    affected_nodes: List[str]
    timestamp: float
    reason: str
    source_node: str


@dataclass
class CacheReplication:
    """Replication configuration"""
    replication_id: str
    key: str
    primary_node: str
    replica_nodes: List[str]
    consistency: CacheConsistency
    version: int = 0


class DistributedCacheCoordinator:
    """
    Distributed Cache Coordinator

    Provides:
    - Multi-node cache coordination
    - Cache consistency guarantees
    - Invalidation strategies
    - Replication management
    - Coherence protocols
    - Cache statistics
    """

    def __init__(self, consistency: CacheConsistency = CacheConsistency.EVENTUAL):
        self.consistency = consistency
        self.nodes: Dict[str, CacheNode] = {}
        self.replications: Dict[str, CacheReplication] = {}
        self.invalidations: List[CacheInvalidation] = []
        self.node_graph: Dict[str, List[str]] = {}  # node -> neighbors

    def register_node(self,
                     node_name: str,
                     host: str,
                     port: int,
                     max_size: int = 1000) -> CacheNode:
        """Register cache node"""
        node_id = hashlib.md5(f"{node_name}:{host}:{port}".encode()).hexdigest()[:8]

        node = CacheNode(
            node_id=node_id,
            node_name=node_name,
            host=host,
            port=port,
            max_size=max_size
        )

        self.nodes[node_id] = node
        self.node_graph[node_id] = []

        return node

    def set(self,
           key: str,
           value: Any,
           primary_node: str,
           replicas: List[str] = None,
           ttl: int = 3600) -> CacheReplication:
        """Set value in cache with replication"""
        replicas = replicas or []

        # Store in primary
        primary = self.nodes.get(primary_node)
        if primary:
            entry = CacheEntry(
                key=key,
                value=value,
                version=1,
                created_at=time.time(),
                ttl=ttl
            )
            primary.cache[key] = entry

        # Replicate
        replication_id = hashlib.md5(f"{key}:{primary_node}:{time.time()}".encode()).hexdigest()[:8]
        replication = CacheReplication(
            replication_id=replication_id,
            key=key,
            primary_node=primary_node,
            replica_nodes=replicas,
            consistency=self.consistency
        )

        # Store replicas
        for replica_node_id in replicas:
            replica = self.nodes.get(replica_node_id)
            if replica:
                replica.cache[key] = CacheEntry(
                    key=key,
                    value=value,
                    version=1,
                    created_at=time.time(),
                    ttl=ttl
                )

        self.replications[replication_id] = replication
        return replication

    def get(self, key: str, node_id: str) -> Optional[Any]:
        """Get value from cache"""
        node = self.nodes.get(node_id)
        if not node:
            return None

        entry = node.cache.get(key)
        if entry:
            # Check expiration
            if entry.ttl and time.time() - entry.created_at > entry.ttl:
                del node.cache[key]
                node.misses += 1
                return None

            entry.last_accessed = time.time()
            entry.access_count += 1
            node.hits += 1
            return entry.value

        node.misses += 1
        return None

    def invalidate(self,
                  key: str,
                  source_node: str,
                  strategy: InvalidationStrategy = InvalidationStrategy.BROADCAST) -> CacheInvalidation:
        """Invalidate cache entry"""
        invalidation_id = hashlib.md5(
            f"{key}:{source_node}:{time.time()}".encode()
        ).hexdigest()[:8]

        affected_nodes = []

        if strategy == InvalidationStrategy.BROADCAST:
            # Invalidate on all nodes
            for node_id, node in self.nodes.items():
                if key in node.cache:
                    del node.cache[key]
                    affected_nodes.append(node_id)

        elif strategy == InvalidationStrategy.GOSSIP:
            # Gossip invalidation to neighbors
            visited = set()
            to_visit = [source_node]

            while to_visit:
                current = to_visit.pop(0)
                if current in visited:
                    continue
                visited.add(current)

                node = self.nodes.get(current)
                if node and key in node.cache:
                    del node.cache[key]
                    affected_nodes.append(current)

                to_visit.extend(self.node_graph.get(current, []))

        invalidation = CacheInvalidation(
            invalidation_id=invalidation_id,
            key=key,
            affected_nodes=affected_nodes,
            timestamp=time.time(),
            reason="User invalidation",
            source_node=source_node
        )

        self.invalidations.append(invalidation)
        return invalidation

    def connect_nodes(self, node1_id: str, node2_id: str):
        """Connect two cache nodes (for gossip protocol)"""
        if node1_id in self.node_graph:
            self.node_graph[node1_id].append(node2_id)
        if node2_id in self.node_graph:
            self.node_graph[node2_id].append(node1_id)

    def synchronize_nodes(self):
        """Synchronize cache across nodes"""
        # Collect all keys from all nodes
        all_keys = set()
        for node in self.nodes.values():
            all_keys.update(node.cache.keys())

        # Synchronize
        for key in all_keys:
            # Find primary node
            replication = None
            for rep in self.replications.values():
                if rep.key == key:
                    replication = rep
                    break

            if replication:
                primary = self.nodes.get(replication.primary_node)
                if primary and key in primary.cache:
                    value = primary.cache[key].value
                    version = primary.cache[key].version

                    # Update replicas
                    for replica_id in replication.replica_nodes:
                        replica = self.nodes.get(replica_id)
                        if replica:
                            replica.cache[key] = CacheEntry(
                                key=key,
                                value=value,
                                version=version,
                                created_at=primary.cache[key].created_at,
                                ttl=primary.cache[key].ttl
                            )

    def evict_lru(self, node_id: str):
        """Evict least recently used entry"""
        node = self.nodes.get(node_id)
        if not node or not node.cache:
            return

        lru_key = min(
            node.cache.keys(),
            key=lambda k: node.cache[k].last_accessed
        )
        del node.cache[lru_key]

    def evict_lfu(self, node_id: str):
        """Evict least frequently used entry"""
        node = self.nodes.get(node_id)
        if not node or not node.cache:
            return

        lfu_key = min(
            node.cache.keys(),
            key=lambda k: node.cache[k].access_count
        )
        del node.cache[lfu_key]

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_keys = sum(len(node.cache) for node in self.nodes.values())
        total_hits = sum(node.hits for node in self.nodes.values())
        total_misses = sum(node.misses for node in self.nodes.values())
        hit_rate = total_hits / max(1, total_hits + total_misses)

        return {
            "nodes": len(self.nodes),
            "active_nodes": sum(1 for n in self.nodes.values() if n.is_active),
            "total_keys": total_keys,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": hit_rate,
            "replications": len(self.replications),
            "invalidations": len(self.invalidations),
        }

    def generate_cache_report(self) -> str:
        """Generate cache report"""
        stats = self.get_cache_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DISTRIBUTED CACHE REPORT                                      ║
║              Consistency: {self.consistency.value}                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Nodes: {stats['active_nodes']}/{stats['nodes']}
├─ Total Keys: {stats['total_keys']}
├─ Hits: {stats['total_hits']}
├─ Misses: {stats['total_misses']}
├─ Hit Rate: {stats['hit_rate']:.2%}
├─ Replications: {stats['replications']}
└─ Invalidations: {stats['invalidations']}

🖥️  CACHE NODES:
"""

        for node in self.nodes.values():
            status = "🟢" if node.is_active else "🔴"
            report += f"\n  {status} {node.node_name}\n"
            report += f"    Keys: {len(node.cache)}\n"
            report += f"    Hit Rate: {node.hits / max(1, node.hits + node.misses):.2%}\n"

        return report

    def export_cache_config(self) -> str:
        """Export cache configuration"""
        export_data = {
            "timestamp": time.time(),
            "consistency": self.consistency.value,
            "nodes": [
                {
                    "name": n.node_name,
                    "host": n.host,
                    "keys": len(n.cache),
                    "active": n.is_active,
                }
                for n in self.nodes.values()
            ],
            "statistics": self.get_cache_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Distributed Cache Coordinator - Cache Coherence Management")
    print("=" * 70)

    coordinator = DistributedCacheCoordinator(CacheConsistency.EVENTUAL)

    # Register nodes
    print("\n📝 Registering cache nodes...")
    node1 = coordinator.register_node("cache-1", "10.0.1.10", 6379)
    node2 = coordinator.register_node("cache-2", "10.0.1.11", 6379)
    node3 = coordinator.register_node("cache-3", "10.0.1.12", 6379)
    print(f"✅ Registered {len(coordinator.nodes)} cache nodes")

    # Connect nodes
    print("\n🔗 Connecting nodes...")
    coordinator.connect_nodes(node1.node_id, node2.node_id)
    coordinator.connect_nodes(node2.node_id, node3.node_id)
    print("✅ Nodes connected")

    # Set values with replication
    print("\n📝 Setting cache entries...")
    rep1 = coordinator.set(
        "user:123",
        {"id": 123, "name": "John Doe"},
        primary_node=node1.node_id,
        replicas=[node2.node_id, node3.node_id]
    )
    print(f"✅ Set user:123 with replication")

    rep2 = coordinator.set(
        "product:456",
        {"id": 456, "name": "Product", "price": 99.99},
        primary_node=node2.node_id,
        replicas=[node1.node_id, node3.node_id]
    )
    print(f"✅ Set product:456 with replication")

    # Get values
    print("\n🔍 Getting cache entries...")
    user = coordinator.get("user:123", node1.node_id)
    print(f"✅ Retrieved user:123: {user}")

    product = coordinator.get("product:456", node2.node_id)
    print(f"✅ Retrieved product:456: {product}")

    # Synchronize
    print("\n🔄 Synchronizing nodes...")
    coordinator.synchronize_nodes()
    print("✅ Nodes synchronized")

    # Invalidate
    print("\n❌ Invalidating entries...")
    invalidation = coordinator.invalidate(
        "user:123",
        source_node=node1.node_id,
        strategy=InvalidationStrategy.BROADCAST
    )
    print(f"✅ Invalidated {len(invalidation.affected_nodes)} nodes")

    # Generate report
    print(coordinator.generate_cache_report())

    # Export
    print("\n📄 Exporting cache config...")
    export = coordinator.export_cache_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Distributed cache coordinator ready")


if __name__ == "__main__":
    main()
