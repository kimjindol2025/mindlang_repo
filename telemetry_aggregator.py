#!/usr/bin/env python3
"""
Telemetry Aggregator - Unified telemetry collection and analysis
Aggregates metrics, logs, and traces from multiple sources
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time
import random


class TelemetryType(Enum):
    """Telemetry types"""
    METRICS = "METRICS"
    LOGS = "LOGS"
    TRACES = "TRACES"
    PROFILES = "PROFILES"


class DataSource(Enum):
    """Telemetry data sources"""
    PROMETHEUS = "PROMETHEUS"
    ELASTICSEARCH = "ELASTICSEARCH"
    JAEGER = "JAEGER"
    DATADOG = "DATADOG"
    NEW_RELIC = "NEW_RELIC"


@dataclass
class TelemetryPoint:
    """Single telemetry data point"""
    point_id: str
    source: DataSource
    telemetry_type: TelemetryType
    timestamp: float
    value: Any
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """Aggregated metrics"""
    aggregation_id: str
    service_name: str
    timestamp: float
    duration_seconds: int
    metrics: Dict[str, float]
    sources: List[DataSource] = field(default_factory=list)


@dataclass
class CorrelationContext:
    """Correlation context for distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]


class TelemetryAggregator:
    """
    Telemetry Aggregator

    Provides:
    - Multi-source telemetry collection
    - Data normalization
    - Correlation analysis
    - Performance profiling
    - Anomaly detection
    - Unified querying
    """

    def __init__(self):
        self.telemetry_points: List[TelemetryPoint] = []
        self.aggregated_metrics: Dict[str, AggregatedMetrics] = {}
        self.correlation_contexts: Dict[str, CorrelationContext] = {}
        self.data_sources: Dict[DataSource, Dict] = {}

    def register_source(self,
                       source: DataSource,
                       config: Dict) -> bool:
        """Register telemetry source"""
        self.data_sources[source] = {
            "config": config,
            "registered_at": time.time(),
            "status": "ACTIVE",
            "points_collected": 0
        }
        return True

    def ingest_telemetry(self,
                        source: DataSource,
                        telemetry_type: TelemetryType,
                        value: Any,
                        tags: Dict[str, str] = None) -> TelemetryPoint:
        """Ingest telemetry data point"""
        point_id = hashlib.md5(
            f"{source.value}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:8]

        point = TelemetryPoint(
            point_id=point_id,
            source=source,
            telemetry_type=telemetry_type,
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )

        self.telemetry_points.append(point)

        # Update source stats
        if source in self.data_sources:
            self.data_sources[source]["points_collected"] += 1

        return point

    def aggregate_metrics(self,
                         service_name: str,
                         duration_seconds: int = 60) -> AggregatedMetrics:
        """Aggregate metrics for service"""
        aggregation_id = hashlib.md5(
            f"{service_name}:{duration_seconds}:{time.time()}".encode()
        ).hexdigest()[:8]

        # Filter recent points
        cutoff_time = time.time() - duration_seconds
        recent_points = [p for p in self.telemetry_points
                        if p.timestamp > cutoff_time and
                        (p.tags.get("service") == service_name or
                         p.tags.get("host", "").startswith(service_name))]

        # Aggregate metrics
        metrics = {}
        metric_sources = set()

        for point in recent_points:
            if point.telemetry_type == TelemetryType.METRICS:
                if isinstance(point.value, dict):
                    for k, v in point.value.items():
                        if k not in metrics:
                            metrics[k] = []
                        metrics[k].append(v)
                metric_sources.add(point.source)

        # Calculate aggregations
        aggregated = {}
        for metric_name, values in metrics.items():
            if values:
                aggregated[f"{metric_name}_avg"] = sum(values) / len(values)
                aggregated[f"{metric_name}_max"] = max(values)
                aggregated[f"{metric_name}_min"] = min(values)
                aggregated[f"{metric_name}_count"] = len(values)

        agg_metrics = AggregatedMetrics(
            aggregation_id=aggregation_id,
            service_name=service_name,
            timestamp=time.time(),
            duration_seconds=duration_seconds,
            metrics=aggregated,
            sources=list(metric_sources)
        )

        self.aggregated_metrics[aggregation_id] = agg_metrics
        return agg_metrics

    def create_correlation(self,
                          trace_id: str,
                          user_id: str = None,
                          session_id: str = None) -> CorrelationContext:
        """Create correlation context"""
        span_id = hashlib.md5(f"{trace_id}:0".encode()).hexdigest()[:16]

        context = CorrelationContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            user_id=user_id,
            session_id=session_id
        )

        self.correlation_contexts[trace_id] = context
        return context

    def correlate_telemetry(self, trace_id: str) -> List[TelemetryPoint]:
        """Get all telemetry for trace ID"""
        correlated = [p for p in self.telemetry_points
                     if p.tags.get("trace_id") == trace_id]
        return correlated

    def detect_anomalies(self,
                        service_name: str,
                        threshold: float = 2.0) -> List[Dict]:
        """Detect anomalies in service telemetry"""
        anomalies = []

        # Get recent aggregation
        recent_aggs = [a for a in self.aggregated_metrics.values()
                      if a.service_name == service_name]

        if not recent_aggs:
            return anomalies

        latest_agg = recent_aggs[-1]

        # Simple baseline comparison
        for metric_name, value in latest_agg.metrics.items():
            if "_avg" in metric_name:
                # Simulate baseline
                baseline = 100.0
                if abs(value - baseline) / baseline > threshold / 100:
                    anomalies.append({
                        "service": service_name,
                        "metric": metric_name,
                        "value": value,
                        "baseline": baseline,
                        "deviation_percent": abs(value - baseline) / baseline * 100
                    })

        return anomalies

    def get_telemetry_stats(self) -> Dict:
        """Get telemetry statistics"""
        total_points = len(self.telemetry_points)

        points_by_type = {}
        for point in self.telemetry_points:
            type_name = point.telemetry_type.value
            points_by_type[type_name] = points_by_type.get(type_name, 0) + 1

        points_by_source = {}
        for point in self.telemetry_points:
            source_name = point.source.value
            points_by_source[source_name] = points_by_source.get(source_name, 0) + 1

        return {
            "total_points": total_points,
            "sources": len(self.data_sources),
            "aggregations": len(self.aggregated_metrics),
            "correlations": len(self.correlation_contexts),
            "by_type": points_by_type,
            "by_source": points_by_source,
        }

    def generate_telemetry_report(self) -> str:
        """Generate telemetry report"""
        stats = self.get_telemetry_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              TELEMETRY AGGREGATOR REPORT                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Data Points: {stats['total_points']}
├─ Sources: {stats['sources']}
├─ Aggregations: {stats['aggregations']}
└─ Correlations: {stats['correlations']}

📈 BY TYPE:
"""

        for ttype, count in stats['by_type'].items():
            report += f"  {ttype}: {count}\n"

        report += f"\n📍 BY SOURCE:\n"
        for source, count in stats['by_source'].items():
            report += f"  {source}: {count}\n"

        return report

    def export_telemetry_config(self) -> str:
        """Export telemetry configuration"""
        export_data = {
            "timestamp": time.time(),
            "sources": [
                {
                    "source": source.value,
                    "config": self.data_sources[source]["config"],
                    "points_collected": self.data_sources[source]["points_collected"],
                }
                for source in self.data_sources
            ],
            "statistics": self.get_telemetry_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 Telemetry Aggregator - Unified Telemetry Collection")
    print("=" * 70)

    aggregator = TelemetryAggregator()

    # Register sources
    print("\n📝 Registering telemetry sources...")
    aggregator.register_source(DataSource.PROMETHEUS, {"url": "http://prometheus:9090"})
    aggregator.register_source(DataSource.ELASTICSEARCH, {"url": "http://elasticsearch:9200"})
    aggregator.register_source(DataSource.JAEGER, {"url": "http://jaeger:16686"})
    print(f"✅ Registered {len(aggregator.data_sources)} sources")

    # Ingest telemetry
    print("\n➕ Ingesting telemetry data...")
    for i in range(100):
        aggregator.ingest_telemetry(
            DataSource.PROMETHEUS,
            TelemetryType.METRICS,
            {"cpu": random.uniform(20, 80), "memory": random.uniform(40, 80)},
            {"service": "api-service", "host": "api-server-1"}
        )

    for i in range(50):
        aggregator.ingest_telemetry(
            DataSource.ELASTICSEARCH,
            TelemetryType.LOGS,
            {"message": "Request processed", "level": "INFO"},
            {"service": "api-service"}
        )

    print(f"✅ Ingested {len(aggregator.telemetry_points)} data points")

    # Aggregate metrics
    print("\n📊 Aggregating metrics...")
    agg = aggregator.aggregate_metrics("api-service", duration_seconds=300)
    print(f"✅ Aggregated {len(agg.metrics)} metrics")

    # Create correlation
    print("\n🔗 Creating correlation...")
    correlation = aggregator.create_correlation("trace_001", user_id="user_123")
    print(f"✅ Created correlation: {correlation.trace_id}")

    # Detect anomalies
    print("\n🚨 Detecting anomalies...")
    anomalies = aggregator.detect_anomalies("api-service")
    print(f"✅ Found {len(anomalies)} anomalies")

    # Generate report
    print(aggregator.generate_telemetry_report())

    # Export
    print("\n📄 Exporting telemetry config...")
    export = aggregator.export_telemetry_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Telemetry aggregation ready")


if __name__ == "__main__":
    main()
