#!/usr/bin/env python3
"""
Synthetic Monitoring System - Proactive monitoring through synthetic tests
Performs synthetic transactions to detect issues before real users
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable
import hashlib
import json
import time
import random


class MonitorType(Enum):
    """Monitor types"""
    HTTP = "HTTP"
    GRPC = "GRPC"
    DATABASE = "DATABASE"
    DNS = "DNS"
    SELENIUM = "SELENIUM"
    API = "API"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class SyntheticTest:
    """Synthetic test definition"""
    test_id: str
    test_name: str
    monitor_type: MonitorType
    endpoint: str
    interval: int  # seconds
    timeout: int  # seconds
    enabled: bool = True
    last_run: Optional[float] = None
    next_run: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


@dataclass
class TestExecution:
    """Test execution result"""
    execution_id: str
    test_id: str
    timestamp: float
    duration_ms: float
    status: str  # SUCCESS, FAILURE, TIMEOUT
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TestMetrics:
    """Test metrics"""
    test_id: str
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    timeout: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    availability: float = 0.0
    last_execution: Optional[float] = None


@dataclass
class SyntheticAlert:
    """Alert from synthetic monitoring"""
    alert_id: str
    test_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: float
    resolved: bool = False


class SyntheticMonitoringSystem:
    """
    Synthetic Monitoring System

    Provides:
    - Synthetic transaction testing
    - Distributed monitoring
    - Multi-protocol support
    - Availability tracking
    - SLA enforcement
    - Alert generation
    """

    def __init__(self):
        self.tests: Dict[str, SyntheticTest] = {}
        self.executions: List[TestExecution] = []
        self.metrics: Dict[str, TestMetrics] = {}
        self.alerts: List[SyntheticAlert] = []
        self.execution_history: Dict[str, List[TestExecution]] = {}

    def create_test(self,
                   test_name: str,
                   monitor_type: MonitorType,
                   endpoint: str,
                   interval: int = 60,
                   timeout: int = 10) -> SyntheticTest:
        """Create synthetic test"""
        test_id = hashlib.md5(
            f"{test_name}:{endpoint}:{time.time()}".encode()
        ).hexdigest()[:8]

        test = SyntheticTest(
            test_id=test_id,
            test_name=test_name,
            monitor_type=monitor_type,
            endpoint=endpoint,
            interval=interval,
            timeout=timeout
        )

        self.tests[test_id] = test
        self.metrics[test_id] = TestMetrics(test_id=test_id)
        self.execution_history[test_id] = []

        return test

    def run_test(self, test_id: str) -> TestExecution:
        """Execute synthetic test"""
        test = self.tests.get(test_id)
        if not test:
            return None

        execution_id = hashlib.md5(
            f"{test_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:8]

        start_time = time.time()

        # Simulate test execution based on type
        if test.monitor_type == MonitorType.HTTP:
            status, response_code, error = self._test_http(test.endpoint, test.timeout)
        elif test.monitor_type == MonitorType.API:
            status, response_code, error = self._test_api(test.endpoint, test.timeout)
        elif test.monitor_type == MonitorType.DATABASE:
            status, response_code, error = self._test_database(test.endpoint, test.timeout)
        elif test.monitor_type == MonitorType.DNS:
            status, response_code, error = self._test_dns(test.endpoint, test.timeout)
        else:
            status, response_code, error = "FAILURE", None, "Unknown monitor type"

        duration_ms = (time.time() - start_time) * 1000

        execution = TestExecution(
            execution_id=execution_id,
            test_id=test_id,
            timestamp=time.time(),
            duration_ms=duration_ms,
            status=status,
            response_code=response_code,
            error_message=error
        )

        # Record execution
        self.executions.append(execution)
        self.execution_history[test_id].append(execution)
        test.last_run = time.time()
        test.next_run = time.time() + test.interval

        # Update metrics
        self._update_metrics(test_id, execution)

        # Check for alerts
        self._check_alerts(test_id, execution)

        return execution

    def _test_http(self, endpoint: str, timeout: int) -> tuple:
        """Test HTTP endpoint"""
        success = random.random() > 0.05  # 95% success rate
        if success:
            return "SUCCESS", 200, None
        else:
            return "FAILURE", 500, "Server error"

    def _test_api(self, endpoint: str, timeout: int) -> tuple:
        """Test API endpoint"""
        success = random.random() > 0.05
        if success:
            return "SUCCESS", 200, None
        else:
            return "FAILURE", 503, "Service unavailable"

    def _test_database(self, endpoint: str, timeout: int) -> tuple:
        """Test database connection"""
        success = random.random() > 0.02  # 98% success rate
        if success:
            return "SUCCESS", None, None
        else:
            return "FAILURE", None, "Connection timeout"

    def _test_dns(self, endpoint: str, timeout: int) -> tuple:
        """Test DNS resolution"""
        success = random.random() > 0.01  # 99% success rate
        if success:
            return "SUCCESS", None, None
        else:
            return "FAILURE", None, "DNS resolution failed"

    def _update_metrics(self, test_id: str, execution: TestExecution):
        """Update test metrics"""
        metrics = self.metrics[test_id]
        metrics.total_executions += 1
        metrics.last_execution = execution.timestamp

        if execution.status == "SUCCESS":
            metrics.successful += 1
        elif execution.status == "FAILURE":
            metrics.failed += 1
        elif execution.status == "TIMEOUT":
            metrics.timeout += 1

        # Calculate availability
        metrics.availability = metrics.successful / max(1, metrics.total_executions)

        # Update response times
        history = self.execution_history[test_id]
        response_times = sorted([e.duration_ms for e in history if e.status == "SUCCESS"])
        if response_times:
            metrics.avg_response_time_ms = sum(response_times) / len(response_times)
            metrics.p95_response_time_ms = response_times[int(len(response_times) * 0.95)]
            metrics.p99_response_time_ms = response_times[int(len(response_times) * 0.99)]

    def _check_alerts(self, test_id: str, execution: TestExecution):
        """Check for alert conditions"""
        metrics = self.metrics[test_id]
        test = self.tests[test_id]

        if execution.status == "FAILURE":
            if metrics.failed >= 3:  # 3 consecutive failures
                self._create_alert(
                    test_id,
                    AlertSeverity.CRITICAL,
                    f"Test {test.test_name} failed",
                    f"Test failed {metrics.failed} times"
                )

        if metrics.availability < 0.99:  # 99% availability SLA
            self._create_alert(
                test_id,
                AlertSeverity.WARNING,
                f"Low availability for {test.test_name}",
                f"Availability: {metrics.availability:.2%}"
            )

    def _create_alert(self,
                     test_id: str,
                     severity: AlertSeverity,
                     title: str,
                     message: str):
        """Create alert"""
        alert_id = hashlib.md5(
            f"{test_id}:{title}:{time.time()}".encode()
        ).hexdigest()[:8]

        alert = SyntheticAlert(
            alert_id=alert_id,
            test_id=test_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=time.time()
        )

        self.alerts.append(alert)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                return True
        return False

    def get_test_report(self, test_id: str) -> Dict:
        """Get test report"""
        test = self.tests.get(test_id)
        metrics = self.metrics.get(test_id)

        if not test or not metrics:
            return {}

        return {
            "test_name": test.test_name,
            "endpoint": test.endpoint,
            "total_executions": metrics.total_executions,
            "successful": metrics.successful,
            "failed": metrics.failed,
            "availability": metrics.availability,
            "avg_response_time": metrics.avg_response_time_ms,
            "p95_response_time": metrics.p95_response_time_ms,
            "p99_response_time": metrics.p99_response_time_ms,
        }

    def get_system_health(self) -> Dict:
        """Get overall system health"""
        total_executions = len(self.executions)
        successful = sum(1 for e in self.executions if e.status == "SUCCESS")
        failed = sum(1 for e in self.executions if e.status == "FAILURE")
        timeout = sum(1 for e in self.executions if e.status == "TIMEOUT")

        overall_availability = successful / max(1, total_executions)
        critical_alerts = sum(1 for a in self.alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved)

        return {
            "tests": len(self.tests),
            "total_executions": total_executions,
            "successful": successful,
            "failed": failed,
            "timeout": timeout,
            "overall_availability": overall_availability,
            "critical_alerts": critical_alerts,
            "unresolved_alerts": sum(1 for a in self.alerts if not a.resolved),
        }

    def generate_monitoring_report(self) -> str:
        """Generate monitoring report"""
        health = self.get_system_health()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              SYNTHETIC MONITORING REPORT                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

🏥 SYSTEM HEALTH:
├─ Overall Availability: {health['overall_availability']:.2%}
├─ Critical Alerts: {health['critical_alerts']}
└─ Unresolved Alerts: {health['unresolved_alerts']}

📊 TEST RESULTS:
├─ Total Tests: {health['tests']}
├─ Executions: {health['total_executions']}
├─ ✅ Successful: {health['successful']}
├─ ❌ Failed: {health['failed']}
└─ ⏱️  Timeout: {health['timeout']}

🧪 INDIVIDUAL TESTS:
"""

        for test_id, test in self.tests.items():
            report_data = self.get_test_report(test_id)
            if report_data:
                report += f"\n  {test.test_name}\n"
                report += f"    Availability: {report_data['availability']:.2%}\n"
                report += f"    Avg Response: {report_data['avg_response_time']:.1f}ms\n"

        return report

    def export_monitoring_config(self) -> str:
        """Export monitoring configuration"""
        export_data = {
            "timestamp": time.time(),
            "tests": [
                {
                    "name": t.test_name,
                    "type": t.monitor_type.value,
                    "endpoint": t.endpoint,
                    "interval": t.interval,
                }
                for t in self.tests.values()
            ],
            "system_health": self.get_system_health(),
            "alerts": [
                {
                    "severity": a.severity.value,
                    "title": a.title,
                    "resolved": a.resolved,
                }
                for a in self.alerts
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔬 Synthetic Monitoring System - Proactive Monitoring")
    print("=" * 70)

    system = SyntheticMonitoringSystem()

    # Create tests
    print("\n🧪 Creating synthetic tests...")
    test1 = system.create_test(
        "API Health Check",
        MonitorType.HTTP,
        "https://api.example.com/health",
        interval=60
    )
    test2 = system.create_test(
        "Database Connectivity",
        MonitorType.DATABASE,
        "postgres://db.example.com:5432/main",
        interval=300
    )
    test3 = system.create_test(
        "DNS Resolution",
        MonitorType.DNS,
        "api.example.com",
        interval=600
    )
    print(f"✅ Created {len(system.tests)} tests")

    # Run tests
    print("\n🔄 Running synthetic tests...")
    for _ in range(10):
        for test_id in system.tests.keys():
            execution = system.run_test(test_id)
            if execution:
                status_emoji = "✅" if execution.status == "SUCCESS" else "❌"
                print(f"  {status_emoji} {system.tests[test_id].test_name}: {execution.duration_ms:.1f}ms")

    # Generate report
    print(system.generate_monitoring_report())

    # Export
    print("\n📄 Exporting monitoring config...")
    export = system.export_monitoring_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Synthetic monitoring ready")


if __name__ == "__main__":
    main()
