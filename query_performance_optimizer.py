#!/usr/bin/env python3
"""
Query Performance Optimizer - Database query analysis and optimization
Analyzes query performance and provides optimization recommendations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class QueryType(Enum):
    """Query types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    JOIN = "JOIN"
    AGGREGATE = "AGGREGATE"


class OptimizationLevel(Enum):
    """Optimization severity"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Query:
    """Database query"""
    query_id: str
    query_text: str
    query_type: QueryType
    execution_time_ms: float
    rows_returned: int
    rows_scanned: int
    timestamp: float = field(default_factory=time.time)
    database: str = ""
    tables: List[str] = field(default_factory=list)


@dataclass
class QueryAnalysis:
    """Query analysis result"""
    analysis_id: str
    query_id: str
    execution_time_ms: float
    estimated_time_ms: float
    efficiency: float  # 0-100
    optimization_level: OptimizationLevel
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    analyzed_at: float = field(default_factory=time.time)


@dataclass
class IndexRecommendation:
    """Index recommendation"""
    recommendation_id: str
    table: str
    columns: List[str]
    estimated_improvement_percent: float
    estimated_queries_improved: int


class QueryPerformanceOptimizer:
    """
    Query Performance Optimizer

    Provides:
    - Query analysis
    - Performance profiling
    - Optimization recommendations
    - Index suggestions
    - Slow query tracking
    - Plan optimization
    """

    def __init__(self):
        self.queries: Dict[str, Query] = {}
        self.analyses: List[QueryAnalysis] = []
        self.index_recommendations: List[IndexRecommendation] = []
        self.slow_query_log: List[Dict] = []
        self.optimization_history: List[Dict] = []

    def log_query(self,
                 query_text: str,
                 query_type: QueryType,
                 execution_time_ms: float,
                 rows_returned: int = 0,
                 rows_scanned: int = 0,
                 database: str = "") -> Query:
        """Log executed query"""
        query_id = hashlib.md5(
            f"{query_text}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Extract tables
        tables = self._extract_tables(query_text)

        query = Query(
            query_id=query_id,
            query_text=query_text,
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            rows_returned=rows_returned,
            rows_scanned=rows_scanned,
            database=database,
            tables=tables
        )

        self.queries[query_id] = query

        # Log if slow
        if execution_time_ms > 1000:
            self.slow_query_log.append({
                "query_id": query_id,
                "execution_time_ms": execution_time_ms,
                "timestamp": time.time()
            })

        return query

    def _extract_tables(self, query_text: str) -> List[str]:
        """Extract table names from query"""
        # Simplified table extraction
        tables = []
        words = query_text.split()

        for i, word in enumerate(words):
            if word.upper() in ["FROM", "INTO", "UPDATE", "JOIN"]:
                if i + 1 < len(words):
                    tables.append(words[i + 1])

        return tables

    def analyze_query(self, query_id: str) -> Optional[QueryAnalysis]:
        """Analyze query performance"""
        query = self.queries.get(query_id)
        if not query:
            return None

        analysis_id = hashlib.md5(
            f"{query_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Estimate time
        estimated_time = query.execution_time_ms * 0.8  # Assume 20% improvement possible

        # Calculate efficiency
        efficiency = min(100, (estimated_time / query.execution_time_ms) * 100)

        # Identify issues
        issues = []
        recommendations = []

        if query.rows_scanned > query.rows_returned * 10:
            issues.append("High rows scanned to returned ratio")
            recommendations.append("Consider adding index on WHERE clause columns")

        if query.execution_time_ms > 1000:
            issues.append("Slow query execution")
            recommendations.append("Review query plan")

        if query.query_type == QueryType.JOIN:
            recommendations.append("Ensure join columns are indexed")

        # Determine optimization level
        if query.execution_time_ms > 5000:
            opt_level = OptimizationLevel.CRITICAL
        elif query.execution_time_ms > 1000:
            opt_level = OptimizationLevel.HIGH
        elif query.execution_time_ms > 100:
            opt_level = OptimizationLevel.MEDIUM
        else:
            opt_level = OptimizationLevel.LOW

        analysis = QueryAnalysis(
            analysis_id=analysis_id,
            query_id=query_id,
            execution_time_ms=query.execution_time_ms,
            estimated_time_ms=estimated_time,
            efficiency=efficiency,
            optimization_level=opt_level,
            issues=issues,
            recommendations=recommendations
        )

        self.analyses.append(analysis)
        return analysis

    def recommend_index(self,
                       table: str,
                       columns: List[str],
                       estimated_improvement: float) -> IndexRecommendation:
        """Recommend index creation"""
        recommendation_id = hashlib.md5(
            f"{table}:{':'.join(columns)}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Estimate queries improved
        affected_queries = sum(1 for q in self.queries.values()
                              if table in q.tables and
                              any(col in q.query_text for col in columns))

        recommendation = IndexRecommendation(
            recommendation_id=recommendation_id,
            table=table,
            columns=columns,
            estimated_improvement_percent=estimated_improvement,
            estimated_queries_improved=affected_queries
        )

        self.index_recommendations.append(recommendation)
        return recommendation

    def generate_index_recommendations(self) -> List[IndexRecommendation]:
        """Generate index recommendations from slow queries"""
        recommendations = []

        for slow_query in self.slow_query_log[-50:]:
            query = self.queries.get(slow_query["query_id"])
            if not query:
                continue

            analysis = next((a for a in self.analyses
                           if a.query_id == query.query_id), None)

            if analysis and "index" in " ".join(analysis.recommendations).lower():
                # Extract potential index columns
                columns = self._extract_where_columns(query.query_text)

                if columns:
                    for table in query.tables:
                        rec = self.recommend_index(table, columns[:2], 25.0)
                        recommendations.append(rec)

        return recommendations

    def _extract_where_columns(self, query_text: str) -> List[str]:
        """Extract columns from WHERE clause"""
        # Simplified WHERE clause extraction
        if "WHERE" not in query_text.upper():
            return []

        where_part = query_text.upper().split("WHERE")[1]
        # Extract column names (simplified)
        columns = []
        for word in where_part.split():
            if "=" in word or ">" in word or "<" in word:
                col = word.split("=")[0].split(">")[0].split("<")[0].strip()
                if col:
                    columns.append(col)

        return columns

    def get_optimization_stats(self) -> Dict:
        """Get optimization statistics"""
        total_queries = len(self.queries)
        slow_queries = len(self.slow_query_log)

        avg_execution = sum(q.execution_time_ms for q in self.queries.values()) / max(1, total_queries)

        by_type = {}
        for query in self.queries.values():
            qtype = query.query_type.value
            by_type[qtype] = by_type.get(qtype, 0) + 1

        critical_optimizations = sum(1 for a in self.analyses
                                   if a.optimization_level == OptimizationLevel.CRITICAL)

        return {
            "total_queries": total_queries,
            "slow_queries": slow_queries,
            "avg_execution_ms": avg_execution,
            "by_type": by_type,
            "analyses": len(self.analyses),
            "critical_optimizations": critical_optimizations,
            "index_recommendations": len(self.index_recommendations),
        }

    def generate_optimization_report(self) -> str:
        """Generate optimization report"""
        stats = self.get_optimization_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              QUERY PERFORMANCE OPTIMIZER REPORT                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Queries: {stats['total_queries']}
├─ Slow Queries: {stats['slow_queries']}
├─ Avg Execution: {stats['avg_execution_ms']:.1f}ms
├─ Analyses: {stats['analyses']}
├─ Critical Issues: {stats['critical_optimizations']}
└─ Index Recommendations: {stats['index_recommendations']}

📋 BY QUERY TYPE:
"""

        for qtype, count in stats['by_type'].items():
            report += f"  {qtype}: {count}\n"

        return report

    def export_optimization_config(self) -> str:
        """Export optimization configuration"""
        stats = self.get_optimization_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "analyses": [
                {
                    "optimization_level": a.optimization_level.value,
                    "efficiency": a.efficiency,
                    "issues_count": len(a.issues),
                    "recommendations_count": len(a.recommendations),
                }
                for a in self.analyses[-20:]
            ],
            "index_recommendations": [
                {
                    "table": r.table,
                    "columns": r.columns,
                    "estimated_improvement": r.estimated_improvement_percent,
                }
                for r in self.index_recommendations
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("⚡ Query Performance Optimizer - Query Analysis")
    print("=" * 70)

    optimizer = QueryPerformanceOptimizer()

    # Log queries
    print("\n📝 Logging queries...")
    q1 = optimizer.log_query(
        "SELECT * FROM users WHERE id = 123",
        QueryType.SELECT, 45.5, 1, 1, "production"
    )
    q2 = optimizer.log_query(
        "SELECT u.*, p.* FROM users u JOIN posts p ON u.id = p.user_id",
        QueryType.JOIN, 1200.0, 500, 5000, "production"
    )
    q3 = optimizer.log_query(
        "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
        QueryType.AGGREGATE, 2500.0, 1, 50000, "production"
    )
    print(f"✅ Logged {len(optimizer.queries)} queries")

    # Analyze queries
    print("\n🔍 Analyzing queries...")
    analysis1 = optimizer.analyze_query(q1.query_id)
    analysis2 = optimizer.analyze_query(q2.query_id)
    analysis3 = optimizer.analyze_query(q3.query_id)
    print(f"✅ Analyzed {len(optimizer.analyses)} queries")

    # Generate index recommendations
    print("\n💡 Generating index recommendations...")
    recommendations = optimizer.generate_index_recommendations()
    print(f"✅ Generated {len(recommendations)} recommendations")

    # Generate report
    print(optimizer.generate_optimization_report())

    # Export
    print("\n📄 Exporting optimization config...")
    export = optimizer.export_optimization_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Query performance optimizer ready")


if __name__ == "__main__":
    main()
