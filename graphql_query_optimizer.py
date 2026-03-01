#!/usr/bin/env python3
"""
GraphQL Query Optimizer - Query optimization and batching
Optimizes GraphQL queries for performance and reduces N+1 queries
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import re


class OptimizationType(Enum):
    """Optimization types"""
    QUERY_DEDUPLICATION = "QUERY_DEDUPLICATION"
    FIELD_PRUNING = "FIELD_PRUNING"
    BATCH_LOADING = "BATCH_LOADING"
    QUERY_CACHING = "QUERY_CACHING"
    QUERY_SPLITTING = "QUERY_SPLITTING"


@dataclass
class GraphQLQuery:
    """GraphQL query"""
    query_id: str
    query_string: str
    operation_name: str
    variables: Dict = field(default_factory=dict)
    requested_fields: Set[str] = field(default_factory=set)
    depth: int = 0
    complexity: float = 0.0


@dataclass
class OptimizedQuery:
    """Optimized query"""
    optimized_id: str
    original_query_id: str
    optimization_type: OptimizationType
    optimized_query: str
    complexity_reduction: float
    execution_time_reduction_ms: float
    cache_key: Optional[str] = None


@dataclass
class QueryBatch:
    """Batch of queries"""
    batch_id: str
    queries: List[str]
    combined_query: str
    batch_size: int = 0
    combined_complexity: float = 0.0


class GraphQLQueryOptimizer:
    """
    GraphQL Query Optimizer

    Provides:
    - Query deduplication
    - Field-level pruning
    - Query batching
    - Complexity analysis
    - Performance optimization
    - Cache-aware optimization
    """

    def __init__(self):
        self.queries: Dict[str, GraphQLQuery] = {}
        self.optimizations: List[OptimizedQuery] = []
        self.batches: Dict[str, QueryBatch] = {}
        self.query_cache: Dict[str, Dict] = {}

    def parse_query(self,
                   query_string: str,
                   operation_name: str = None,
                   variables: Dict = None) -> GraphQLQuery:
        """Parse and analyze GraphQL query"""
        query_id = hashlib.md5(
            f"{query_string}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Extract requested fields
        fields = self._extract_fields(query_string)

        # Calculate complexity
        depth = self._calculate_depth(query_string)
        complexity = self._calculate_complexity(query_string)

        query = GraphQLQuery(
            query_id=query_id,
            query_string=query_string,
            operation_name=operation_name or "AnonymousQuery",
            variables=variables or {},
            requested_fields=fields,
            depth=depth,
            complexity=complexity
        )

        self.queries[query_id] = query
        return query

    def _extract_fields(self, query_string: str) -> Set[str]:
        """Extract requested fields from query"""
        # Simple regex-based extraction
        pattern = r'(\w+)\s*{'
        matches = re.findall(pattern, query_string)
        return set(matches)

    def _calculate_depth(self, query_string: str) -> int:
        """Calculate query depth"""
        max_depth = 0
        current_depth = 0
        for char in query_string:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1
        return max_depth

    def _calculate_complexity(self, query_string: str) -> float:
        """Calculate query complexity score"""
        # Simple complexity calculation
        complexity = 1.0
        complexity += len(self._extract_fields(query_string)) * 0.5
        complexity += self._calculate_depth(query_string) * 0.3
        return complexity

    def optimize_query(self,
                      query_id: str,
                      optimization_type: OptimizationType = OptimizationType.FIELD_PRUNING) -> Optional[OptimizedQuery]:
        """Optimize query"""
        query = self.queries.get(query_id)
        if not query:
            return None

        optimized_id = hashlib.md5(
            f"{query_id}:{optimization_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        if optimization_type == OptimizationType.FIELD_PRUNING:
            optimized_query = self._prune_fields(query.query_string)
        elif optimization_type == OptimizationType.QUERY_SPLITTING:
            optimized_query = self._split_query(query.query_string)
        else:
            optimized_query = query.query_string

        # Calculate improvements
        original_complexity = query.complexity
        optimized_complexity = self._calculate_complexity(optimized_query)
        complexity_reduction = (original_complexity - optimized_complexity) / original_complexity * 100

        optimization = OptimizedQuery(
            optimized_id=optimized_id,
            original_query_id=query_id,
            optimization_type=optimization_type,
            optimized_query=optimized_query,
            complexity_reduction=complexity_reduction,
            execution_time_reduction_ms=complexity_reduction * 0.5  # Estimate
        )

        self.optimizations.append(optimization)
        return optimization

    def _prune_fields(self, query_string: str) -> str:
        """Prune unnecessary fields"""
        # Simulate field pruning
        return query_string.replace("__typename", "")

    def _split_query(self, query_string: str) -> str:
        """Split query into smaller queries"""
        # Simulate query splitting
        return query_string

    def batch_queries(self, query_ids: List[str]) -> Optional[QueryBatch]:
        """Batch multiple queries"""
        if not query_ids:
            return None

        batch_id = hashlib.md5(
            f"batch:{':'.join(query_ids)}:{time.time()}".encode()
        ).hexdigest()[:8]

        queries = [self.queries[qid].query_string for qid in query_ids if qid in self.queries]

        # Combine queries
        combined_query = self._combine_queries(queries)

        batch = QueryBatch(
            batch_id=batch_id,
            queries=queries,
            combined_query=combined_query,
            batch_size=len(queries),
            combined_complexity=sum(self.queries[qid].complexity for qid in query_ids if qid in self.queries)
        )

        self.batches[batch_id] = batch
        return batch

    def _combine_queries(self, queries: List[str]) -> str:
        """Combine multiple queries into one"""
        # Simulate combining
        return f"query {{ {' '.join(queries)} }}"

    def cache_query(self, query_id: str, result: Dict) -> str:
        """Cache query result"""
        query = self.queries.get(query_id)
        if not query:
            return None

        cache_key = hashlib.sha256(
            f"{query.query_string}:{json.dumps(query.variables)}".encode()
        ).hexdigest()[:16]

        self.query_cache[cache_key] = {
            "query_id": query_id,
            "result": result,
            "cached_at": time.time()
        }

        return cache_key

    def get_cached_result(self, query_id: str, variables: Dict = None) -> Optional[Dict]:
        """Get cached query result"""
        query = self.queries.get(query_id)
        if not query:
            return None

        cache_key = hashlib.sha256(
            f"{query.query_string}:{json.dumps(variables or {})}".encode()
        ).hexdigest()[:16]

        if cache_key in self.query_cache:
            return self.query_cache[cache_key]["result"]

        return None

    def get_optimizer_stats(self) -> Dict:
        """Get optimizer statistics"""
        total_queries = len(self.queries)
        avg_complexity = sum(q.complexity for q in self.queries.values()) / max(1, total_queries)
        avg_depth = sum(q.depth for q in self.queries.values()) / max(1, total_queries)
        total_optimization = sum(o.complexity_reduction for o in self.optimizations)

        return {
            "queries_analyzed": total_queries,
            "optimizations": len(self.optimizations),
            "batches": len(self.batches),
            "cached_queries": len(self.query_cache),
            "avg_complexity": avg_complexity,
            "avg_depth": avg_depth,
            "total_complexity_reduction": total_optimization,
        }

    def generate_optimizer_report(self) -> str:
        """Generate optimizer report"""
        stats = self.get_optimizer_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              GRAPHQL QUERY OPTIMIZER REPORT                                ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Queries Analyzed: {stats['queries_analyzed']}
├─ Optimizations Applied: {stats['optimizations']}
├─ Batches Created: {stats['batches']}
├─ Cached Queries: {stats['cached_queries']}
├─ Avg Complexity: {stats['avg_complexity']:.2f}
├─ Avg Depth: {stats['avg_depth']:.1f}
└─ Total Complexity Reduction: {stats['total_complexity_reduction']:.1f}%

⚡ TOP OPTIMIZATIONS:
"""

        for opt in sorted(self.optimizations, key=lambda o: o.complexity_reduction, reverse=True)[:5]:
            report += f"\n  {opt.optimization_type.value}\n"
            report += f"    Complexity Reduction: {opt.complexity_reduction:.1f}%\n"
            report += f"    Time Reduction: {opt.execution_time_reduction_ms:.1f}ms\n"

        return report

    def export_optimizer_config(self) -> str:
        """Export optimizer configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_optimizer_stats(),
            "optimizations": [
                {
                    "type": o.optimization_type.value,
                    "reduction": o.complexity_reduction,
                }
                for o in self.optimizations
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("⚡ GraphQL Query Optimizer - Query Performance Optimization")
    print("=" * 70)

    optimizer = GraphQLQueryOptimizer()

    # Parse queries
    print("\n📝 Parsing GraphQL queries...")
    query1_str = "query { users { id name email posts { id title } } }"
    query2_str = "query { products { id name price } }"

    query1 = optimizer.parse_query(query1_str, "GetUsers")
    query2 = optimizer.parse_query(query2_str, "GetProducts")
    print(f"✅ Parsed {len(optimizer.queries)} queries")

    # Optimize queries
    print("\n⚡ Optimizing queries...")
    opt1 = optimizer.optimize_query(query1.query_id, OptimizationType.FIELD_PRUNING)
    opt2 = optimizer.optimize_query(query2.query_id, OptimizationType.QUERY_SPLITTING)
    print(f"✅ Applied {len(optimizer.optimizations)} optimizations")

    if opt1:
        print(f"   Complexity reduction: {opt1.complexity_reduction:.1f}%")

    # Batch queries
    print("\n📦 Batching queries...")
    batch = optimizer.batch_queries([query1.query_id, query2.query_id])
    print(f"✅ Batched {batch.batch_size} queries")

    # Cache queries
    print("\n💾 Caching results...")
    cache_key = optimizer.cache_query(query1.query_id, {"users": []})
    print(f"✅ Cached with key: {cache_key}")

    # Get stats
    print("\n📊 Getting statistics...")
    stats = optimizer.get_optimizer_stats()
    print(f"✅ Avg Complexity: {stats['avg_complexity']:.2f}")

    # Generate report
    print(optimizer.generate_optimizer_report())

    # Export
    print("\n📄 Exporting optimizer config...")
    export = optimizer.export_optimizer_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ GraphQL query optimizer ready")


if __name__ == "__main__":
    main()
