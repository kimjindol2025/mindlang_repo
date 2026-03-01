#!/usr/bin/env python3
"""
Observability Stack Manager - Comprehensive monitoring, logging, and tracing management
Manages Prometheus, Grafana, ELK, Jaeger infrastructure for enterprise observability
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import hashlib
import json
import time
import random


class ObservabilityComponent(Enum):
    """Components of observability stack"""
    PROMETHEUS = "PROMETHEUS"
    GRAFANA = "GRAFANA"
    ELASTICSEARCH = "ELASTICSEARCH"
    KIBANA = "KIBANA"
    JAEGER = "JAEGER"
    LOKI = "LOKI"
    ALERTMANAGER = "ALERTMANAGER"
    INFLUXDB = "INFLUXDB"


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    SUMMARY = "SUMMARY"
    RATE = "RATE"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Single log entry"""
    log_id: str
    timestamp: float
    service: str
    level: LogLevel
    message: str
    source_file: str
    line_number: int
    trace_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class Metric:
    """Metric data point"""
    metric_id: str
    metric_name: str
    metric_type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    service: str = ""


@dataclass
class Trace:
    """Distributed trace (from Jaeger)"""
    trace_id: str
    service: str
    operation: str
    spans: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "SUCCESS"  # SUCCESS, ERROR


@dataclass
class Dashboard:
    """Grafana dashboard"""
    dashboard_id: str
    title: str
    description: str
    created_at: float
    updated_at: float
    panels: List[Dict] = field(default_factory=list)
    variables: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    rule_name: str
    description: str
    condition: str  # PromQL condition
    severity: AlertSeverity
    for_duration: str  # e.g., "5m"
    annotations: Dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class ObservabilityStack:
    """Complete observability stack"""
    stack_id: str
    name: str
    created_at: float
    components: Dict[ObservabilityComponent, Dict] = field(default_factory=dict)
    logs: List[LogEntry] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    traces: List[Trace] = field(default_factory=list)
    dashboards: Dict[str, Dashboard] = field(default_factory=dict)
    alert_rules: Dict[str, AlertRule] = field(default_factory=dict)
    retention_days: int = 30


class ObservabilityStackManager:
    """
    Enterprise observability stack management system

    Provides:
    - Metrics collection (Prometheus)
    - Log aggregation (ELK, Loki)
    - Distributed tracing (Jaeger)
    - Dashboard management (Grafana)
    - Alert management
    - Health monitoring
    - Performance analysis
    """

    def __init__(self):
        self.stacks: Dict[str, ObservabilityStack] = {}
        self.logs: Dict[str, LogEntry] = {}
        self.metrics: Dict[str, Metric] = {}
        self.traces: Dict[str, Trace] = {}

    def create_observability_stack(self,
                                  name: str,
                                  components: List[ObservabilityComponent],
                                  retention_days: int = 30) -> ObservabilityStack:
        """
        Create observability stack

        Args:
            name: Stack name
            components: Components to include
            retention_days: Data retention period

        Returns:
            Created ObservabilityStack
        """
        stack_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        stack = ObservabilityStack(
            stack_id=stack_id,
            name=name,
            created_at=time.time(),
            retention_days=retention_days
        )

        # Initialize components
        for component in components:
            stack.components[component] = {
                "status": "HEALTHY",
                "version": "latest",
                "last_check": time.time(),
            }

        self.stacks[stack_id] = stack
        return stack

    def ingest_logs(self,
                   stack_id: str,
                   logs_batch: List[Dict]) -> int:
        """
        Ingest logs into stack

        Args:
            stack_id: Target stack
            logs_batch: Batch of log entries

        Returns:
            Number of logs ingested
        """
        stack = self.stacks.get(stack_id)
        if not stack:
            return 0

        ingested = 0
        for log_data in logs_batch:
            log_id = hashlib.md5(
                f"{log_data.get('service')}:{time.time()}:{random.random()}".encode()
            ).hexdigest()[:8]

            log_entry = LogEntry(
                log_id=log_id,
                timestamp=log_data.get("timestamp", time.time()),
                service=log_data.get("service", "unknown"),
                level=LogLevel[log_data.get("level", "INFO")],
                message=log_data.get("message", ""),
                source_file=log_data.get("source_file", ""),
                line_number=log_data.get("line_number", 0),
                trace_id=log_data.get("trace_id"),
                metadata=log_data.get("metadata", {})
            )

            stack.logs.append(log_entry)
            self.logs[log_id] = log_entry
            ingested += 1

        return ingested

    def record_metrics(self,
                      stack_id: str,
                      metrics_batch: List[Dict]) -> int:
        """
        Record metrics

        Args:
            stack_id: Target stack
            metrics_batch: Batch of metrics

        Returns:
            Number of metrics recorded
        """
        stack = self.stacks.get(stack_id)
        if not stack:
            return 0

        recorded = 0
        for metric_data in metrics_batch:
            metric_id = hashlib.md5(
                f"{metric_data.get('name')}:{time.time()}".encode()
            ).hexdigest()[:8]

            metric = Metric(
                metric_id=metric_id,
                metric_name=metric_data.get("name", ""),
                metric_type=MetricType[metric_data.get("type", "GAUGE")],
                value=metric_data.get("value", 0.0),
                timestamp=metric_data.get("timestamp", time.time()),
                labels=metric_data.get("labels", {}),
                service=metric_data.get("service", "")
            )

            stack.metrics.append(metric)
            self.metrics[metric_id] = metric
            recorded += 1

        return recorded

    def trace_operation(self,
                       stack_id: str,
                       service: str,
                       operation: str,
                       duration_ms: float,
                       status: str = "SUCCESS") -> Trace:
        """
        Record distributed trace

        Args:
            stack_id: Target stack
            service: Service name
            operation: Operation name
            duration_ms: Operation duration
            status: Operation status

        Returns:
            Recorded Trace
        """
        stack = self.stacks.get(stack_id)
        if not stack:
            return None

        trace_id = hashlib.md5(
            f"{service}:{operation}:{time.time()}".encode()
        ).hexdigest()[:8]

        trace = Trace(
            trace_id=trace_id,
            service=service,
            operation=operation,
            start_time=time.time(),
            duration_ms=duration_ms,
            status=status
        )

        trace.end_time = trace.start_time + (duration_ms / 1000)

        # Create spans
        span_count = random.randint(1, 5)
        current_time = trace.start_time
        for i in range(span_count):
            span_duration = duration_ms / span_count
            span = {
                "span_id": hashlib.md5(f"{trace_id}:{i}".encode()).hexdigest()[:8],
                "parent_span_id": None if i == 0 else hashlib.md5(f"{trace_id}:{i-1}".encode()).hexdigest()[:8],
                "operation": f"{operation}.{i}",
                "start_time": current_time,
                "duration_ms": span_duration,
                "tags": {"component": f"step_{i}"}
            }
            trace.spans.append(span)
            current_time += (span_duration / 1000)

        stack.traces.append(trace)
        self.traces[trace_id] = trace

        return trace

    def create_dashboard(self,
                        stack_id: str,
                        title: str,
                        description: str,
                        panels: List[Dict]) -> Optional[Dashboard]:
        """
        Create Grafana dashboard

        Args:
            stack_id: Target stack
            title: Dashboard title
            description: Dashboard description
            panels: Dashboard panels

        Returns:
            Created Dashboard
        """
        stack = self.stacks.get(stack_id)
        if not stack:
            return None

        dashboard_id = hashlib.md5(f"{stack_id}:{title}".encode()).hexdigest()[:8]

        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            title=title,
            description=description,
            created_at=time.time(),
            updated_at=time.time(),
            panels=panels
        )

        stack.dashboards[dashboard_id] = dashboard
        return dashboard

    def add_alert_rule(self,
                      stack_id: str,
                      rule_name: str,
                      description: str,
                      condition: str,
                      severity: AlertSeverity) -> Optional[AlertRule]:
        """
        Add alert rule

        Args:
            stack_id: Target stack
            rule_name: Alert rule name
            description: Rule description
            condition: PromQL condition
            severity: Alert severity

        Returns:
            Created AlertRule
        """
        stack = self.stacks.get(stack_id)
        if not stack:
            return None

        rule_id = hashlib.md5(f"{stack_id}:{rule_name}".encode()).hexdigest()[:8]

        rule = AlertRule(
            rule_id=rule_id,
            rule_name=rule_name,
            description=description,
            condition=condition,
            severity=severity,
            for_duration="5m"
        )

        stack.alert_rules[rule_id] = rule
        return rule

    def get_stack_health(self, stack_id: str) -> Dict:
        """Get stack health status"""
        stack = self.stacks.get(stack_id)
        if not stack:
            return {}

        health = {
            "stack_id": stack_id,
            "name": stack.name,
            "components": {},
            "overall_health": "HEALTHY"
        }

        unhealthy_count = 0
        for component, config in stack.components.items():
            status = "HEALTHY" if random.random() > 0.05 else "DEGRADED"
            if status == "DEGRADED":
                unhealthy_count += 1
            health["components"][component.value] = status

        if unhealthy_count > 0:
            health["overall_health"] = "DEGRADED" if unhealthy_count < len(stack.components) else "UNHEALTHY"

        return health

    def generate_observability_report(self, stack_id: str) -> str:
        """Generate observability stack report"""
        stack = self.stacks.get(stack_id)
        if not stack:
            return f"❌ Stack {stack_id} not found"

        health = self.get_stack_health(stack_id)

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    OBSERVABILITY STACK REPORT                              ║
║                    {stack.name}                                             ║
╚════════════════════════════════════════════════════════════════════════════╝

🏥 STACK HEALTH: {health['overall_health']}

📊 COMPONENT STATUS:
"""

        for component, status in health["components"].items():
            emoji = "✅" if status == "HEALTHY" else "⚠️"
            report += f"{emoji} {component}: {status}\n"

        report += f"\n📈 DATA INGESTION:\n"
        report += f"├─ Logs Ingested: {len(stack.logs):,}\n"
        report += f"├─ Metrics Recorded: {len(stack.metrics):,}\n"
        report += f"└─ Traces Collected: {len(stack.traces)}\n"

        report += f"\n📋 DASHBOARDS: {len(stack.dashboards)}\n"
        for dash_id, dashboard in list(stack.dashboards.items())[:3]:
            report += f"  • {dashboard.title} ({len(dashboard.panels)} panels)\n"

        report += f"\n🚨 ALERT RULES: {len(stack.alert_rules)}\n"
        for rule_id, rule in list(stack.alert_rules.items())[:3]:
            report += f"  • {rule.rule_name} ({rule.severity.value})\n"

        # Recent logs
        report += f"\n📝 RECENT LOGS:\n"
        for log in reversed(stack.logs[-5:]):
            emoji = "🔴" if log.level == LogLevel.ERROR else "🟡" if log.level == LogLevel.WARNING else "🔵"
            report += f"{emoji} [{log.service}] {log.message[:60]}\n"

        return report

    def export_stack_config(self, stack_id: str) -> str:
        """Export stack configuration as JSON"""
        stack = self.stacks.get(stack_id)
        if not stack:
            return "{}"

        export_data = {
            "stack_id": stack.stack_id,
            "name": stack.name,
            "created_at": stack.created_at,
            "retention_days": stack.retention_days,
            "components": [c.value for c in stack.components.keys()],
            "statistics": {
                "logs": len(stack.logs),
                "metrics": len(stack.metrics),
                "traces": len(stack.traces),
                "dashboards": len(stack.dashboards),
                "alert_rules": len(stack.alert_rules),
            }
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 Observability Stack Manager - Comprehensive Monitoring")
    print("=" * 70)

    manager = ObservabilityStackManager()

    # Create observability stack
    print("\n🔨 Creating observability stack...")
    stack = manager.create_observability_stack(
        "Production Observability",
        [
            ObservabilityComponent.PROMETHEUS,
            ObservabilityComponent.GRAFANA,
            ObservabilityComponent.ELASTICSEARCH,
            ObservabilityComponent.KIBANA,
            ObservabilityComponent.JAEGER,
        ],
        retention_days=30
    )
    print(f"✅ Created stack with {len(stack.components)} components")

    # Ingest logs
    print("\n📝 Ingesting logs...")
    logs = [
        {
            "timestamp": time.time() - random.randint(0, 3600),
            "service": "api-server",
            "level": "INFO",
            "message": f"Request processed {i}",
            "source_file": "server.py",
            "line_number": 125,
        }
        for i in range(100)
    ]
    ingested = manager.ingest_logs(stack.stack_id, logs)
    print(f"✅ Ingested {ingested} log entries")

    # Record metrics
    print("\n📈 Recording metrics...")
    metrics = [
        {
            "name": "http_requests_total",
            "type": "COUNTER",
            "value": random.randint(100, 10000),
            "service": "api-server",
            "labels": {"method": "GET", "status": "200"}
        }
        for _ in range(50)
    ]
    recorded = manager.record_metrics(stack.stack_id, metrics)
    print(f"✅ Recorded {recorded} metrics")

    # Trace operations
    print("\n🔗 Recording distributed traces...")
    for _ in range(20):
        manager.trace_operation(
            stack.stack_id,
            random.choice(["api-server", "database", "cache"]),
            random.choice(["process_request", "query_db", "get_cache"]),
            random.uniform(10, 500),
            "SUCCESS" if random.random() > 0.05 else "ERROR"
        )
    print(f"✅ Recorded {len(stack.traces)} traces")

    # Create dashboard
    print("\n📊 Creating dashboards...")
    dashboard = manager.create_dashboard(
        stack.stack_id,
        "System Overview",
        "Overall system health and performance",
        [
            {"title": "CPU Usage", "type": "graph"},
            {"title": "Memory Usage", "type": "graph"},
            {"title": "Request Rate", "type": "graph"},
            {"title": "Error Rate", "type": "graph"},
        ]
    )
    print(f"✅ Created dashboard")

    # Add alert rules
    print("\n🚨 Setting up alert rules...")
    manager.add_alert_rule(
        stack.stack_id,
        "HighErrorRate",
        "Alert when error rate exceeds 5%",
        "rate(errors_total[5m]) > 0.05",
        AlertSeverity.CRITICAL
    )

    manager.add_alert_rule(
        stack.stack_id,
        "HighLatency",
        "Alert when P95 latency exceeds 1s",
        "histogram_quantile(0.95, request_duration) > 1",
        AlertSeverity.WARNING
    )
    print(f"✅ Created {len(stack.alert_rules)} alert rules")

    # Generate report
    print(manager.generate_observability_report(stack.stack_id))

    # Export
    print("\n📄 Exporting stack configuration...")
    export = manager.export_stack_config(stack.stack_id)
    print(f"✅ Exported {len(export)} characters of config")

    print("\n" + "=" * 70)
    print("✨ Observability stack setup complete")


if __name__ == "__main__":
    main()
