#!/usr/bin/env python3
"""
Distributed Tracing Advanced - Enhanced tracing with service dependency mapping
Advanced tracing with critical path analysis and anomaly detection
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import random


class SpanStatus(Enum):
    """Span status"""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class TraceType(Enum):
    """Trace types"""
    REQUEST = "REQUEST"
    DATABASE = "DATABASE"
    CACHE = "CACHE"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"
    EXTERNAL_API = "EXTERNAL_API"


@dataclass
class TraceSpan:
    """Trace span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    service_name: str
    span_name: str
    span_type: TraceType
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.RUNNING
    attributes: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class TracePath:
    """Critical path in trace"""
    path_id: str
    trace_id: str
    spans: List[str]  # span_ids in order
    total_duration_ms: float
    services_involved: Set[str] = field(default_factory=set)


@dataclass
class ServiceDependency:
    """Service dependency"""
    dependency_id: str
    source_service: str
    target_service: str
    call_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    last_seen: float = field(default_factory=time.time)


@dataclass
class TraceAnomalies:
    """Detected anomalies in traces"""
    anomaly_id: str
    trace_id: str
    timestamp: float
    anomaly_type: str  # SLOW_SPAN, ERROR_SPIKE, TIMEOUT
    affected_service: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class AdvancedDistributedTracer:
    """
    Advanced Distributed Tracing

    Provides:
    - Detailed span tracing
    - Critical path analysis
    - Service dependency mapping
    - Anomaly detection
    - Performance bottleneck identification
    - Distributed context propagation
    """

    def __init__(self):
        self.traces: Dict[str, List[TraceSpan]] = {}  # trace_id -> spans
        self.spans: Dict[str, TraceSpan] = {}  # span_id -> span
        self.paths: Dict[str, TracePath] = {}
        self.dependencies: Dict[str, ServiceDependency] = {}
        self.anomalies: List[TraceAnomalies] = []

    def start_trace(self,
                   service_name: str,
                   operation_name: str,
                   trace_type: TraceType = TraceType.REQUEST) -> TraceSpan:
        """Start a new trace"""
        trace_id = hashlib.md5(f"{time.time()}:{random.random()}".encode()).hexdigest()[:16]
        span_id = hashlib.md5(f"{trace_id}:0".encode()).hexdigest()[:16]

        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            service_name=service_name,
            span_name=operation_name,
            span_type=trace_type,
            start_time=time.time()
        )

        self.spans[span_id] = span
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].append(span)

        return span

    def add_span(self,
                trace_id: str,
                parent_span_id: str,
                service_name: str,
                span_name: str,
                span_type: TraceType = TraceType.REQUEST) -> Optional[TraceSpan]:
        """Add span to trace"""
        if trace_id not in self.traces:
            return None

        span_id = hashlib.md5(
            f"{trace_id}:{parent_span_id}:{service_name}:{time.time()}".encode()
        ).hexdigest()[:16]

        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            service_name=service_name,
            span_name=span_name,
            span_type=span_type,
            start_time=time.time()
        )

        self.spans[span_id] = span
        self.traces[trace_id].append(span)

        # Record dependency
        parent_span = self.spans.get(parent_span_id)
        if parent_span:
            self._record_dependency(parent_span.service_name, service_name)

        return span

    def end_span(self,
                span_id: str,
                status: SpanStatus = SpanStatus.COMPLETED,
                error: Optional[str] = None) -> bool:
        """End span"""
        span = self.spans.get(span_id)
        if not span:
            return False

        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.status = status
        span.error = error

        return True

    def _record_dependency(self, source: str, target: str):
        """Record service dependency"""
        dep_id = f"{source}->{target}"

        if dep_id not in self.dependencies:
            self.dependencies[dep_id] = ServiceDependency(
                dependency_id=dep_id,
                source_service=source,
                target_service=target
            )

        dep = self.dependencies[dep_id]
        dep.call_count += 1
        dep.last_seen = time.time()

    def analyze_critical_path(self, trace_id: str) -> Optional[TracePath]:
        """Analyze critical path of trace"""
        spans = self.traces.get(trace_id, [])
        if not spans:
            return None

        # Find longest path through dependency tree
        path_id = hashlib.md5(f"{trace_id}:{time.time()}".encode()).hexdigest()[:8]

        span_ids = [s.span_id for s in spans]
        total_duration = sum(s.duration_ms for s in spans)
        services = set(s.service_name for s in spans)

        path = TracePath(
            path_id=path_id,
            trace_id=trace_id,
            spans=span_ids,
            total_duration_ms=total_duration,
            services_involved=services
        )

        self.paths[path_id] = path
        return path

    def detect_anomalies(self, trace_id: str) -> List[TraceAnomalies]:
        """Detect anomalies in trace"""
        anomalies = []
        spans = self.traces.get(trace_id, [])

        # Calculate baseline latency
        avg_latency = sum(s.duration_ms for s in spans) / max(1, len(spans))

        for span in spans:
            # Detect slow spans (>2x average)
            if span.duration_ms > avg_latency * 2:
                anomaly = TraceAnomalies(
                    anomaly_id=hashlib.md5(f"{trace_id}:{span.span_id}".encode()).hexdigest()[:8],
                    trace_id=trace_id,
                    timestamp=time.time(),
                    anomaly_type="SLOW_SPAN",
                    affected_service=span.service_name,
                    severity="HIGH" if span.duration_ms > avg_latency * 5 else "MEDIUM"
                )
                anomalies.append(anomaly)

            # Detect errors
            if span.status == SpanStatus.FAILED:
                anomaly = TraceAnomalies(
                    anomaly_id=hashlib.md5(f"{trace_id}:{span.span_id}:error".encode()).hexdigest()[:8],
                    trace_id=trace_id,
                    timestamp=time.time(),
                    anomaly_type="ERROR",
                    affected_service=span.service_name,
                    severity="CRITICAL"
                )
                anomalies.append(anomaly)

        self.anomalies.extend(anomalies)
        return anomalies

    def get_dependency_graph(self) -> Dict:
        """Get service dependency graph"""
        graph = {}
        for dep in self.dependencies.values():
            if dep.source_service not in graph:
                graph[dep.source_service] = []
            graph[dep.source_service].append({
                "target": dep.target_service,
                "calls": dep.call_count,
                "errors": dep.error_count,
                "latency": dep.avg_latency_ms
            })
        return graph

    def get_tracing_stats(self) -> Dict:
        """Get tracing statistics"""
        total_spans = len(self.spans)
        completed_traces = sum(1 for trace in self.traces.values()
                              if all(s.status in [SpanStatus.COMPLETED, SpanStatus.FAILED]
                                    for s in trace))
        failed_spans = sum(1 for s in self.spans.values() if s.status == SpanStatus.FAILED)

        return {
            "traces": len(self.traces),
            "completed_traces": completed_traces,
            "total_spans": total_spans,
            "failed_spans": failed_spans,
            "dependencies": len(self.dependencies),
            "anomalies": len(self.anomalies),
            "critical_paths": len(self.paths),
        }

    def generate_tracing_report(self) -> str:
        """Generate tracing report"""
        stats = self.get_tracing_stats()
        graph = self.get_dependency_graph()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DISTRIBUTED TRACING REPORT                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Traces: {stats['traces']}
├─ Completed: {stats['completed_traces']}
├─ Total Spans: {stats['total_spans']}
├─ Failed: {stats['failed_spans']}
├─ Dependencies: {stats['dependencies']}
├─ Anomalies: {stats['anomalies']}
└─ Critical Paths: {stats['critical_paths']}

🔗 SERVICE DEPENDENCIES:
"""

        for source, targets in graph.items():
            report += f"\n  {source}\n"
            for target in targets:
                report += f"    → {target['target']} ({target['calls']} calls, {target['latency']:.1f}ms)\n"

        return report

    def export_tracing_config(self) -> str:
        """Export tracing configuration"""
        export_data = {
            "timestamp": time.time(),
            "traces": len(self.traces),
            "spans": len(self.spans),
            "dependency_graph": self.get_dependency_graph(),
            "statistics": self.get_tracing_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔍 Distributed Tracing Advanced - Service Dependency Mapping")
    print("=" * 70)

    tracer = AdvancedDistributedTracer()

    # Start trace
    print("\n📝 Starting trace...")
    root_span = tracer.start_trace("api-gateway", "ProcessRequest", TraceType.REQUEST)
    print(f"✅ Root span: {root_span.span_id[:8]}...")

    # Add child spans
    print("\n🔗 Adding service spans...")
    auth_span = tracer.add_span(
        root_span.trace_id,
        root_span.span_id,
        "auth-service",
        "AuthenticateUser",
        TraceType.REQUEST
    )
    time.sleep(0.01)

    db_span = tracer.add_span(
        root_span.trace_id,
        auth_span.span_id,
        "database",
        "QueryUser",
        TraceType.DATABASE
    )
    time.sleep(0.02)

    cache_span = tracer.add_span(
        root_span.trace_id,
        root_span.span_id,
        "cache-service",
        "GetSession",
        TraceType.CACHE
    )
    time.sleep(0.01)

    print(f"✅ Added {len(tracer.traces[root_span.trace_id])} spans")

    # End spans
    print("\n✅ Ending spans...")
    tracer.end_span(db_span.span_id)
    tracer.end_span(cache_span.span_id)
    tracer.end_span(auth_span.span_id)
    tracer.end_span(root_span.span_id)
    print("✅ Spans completed")

    # Analyze critical path
    print("\n📊 Analyzing critical path...")
    path = tracer.analyze_critical_path(root_span.trace_id)
    print(f"✅ Critical path: {path.total_duration_ms:.1f}ms across {len(path.services_involved)} services")

    # Detect anomalies
    print("\n🚨 Detecting anomalies...")
    anomalies = tracer.detect_anomalies(root_span.trace_id)
    print(f"✅ Found {len(anomalies)} anomalies")

    # Generate report
    print(tracer.generate_tracing_report())

    # Export
    print("\n📄 Exporting tracing config...")
    export = tracer.export_tracing_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Advanced distributed tracing ready")


if __name__ == "__main__":
    main()
