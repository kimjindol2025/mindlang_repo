#!/usr/bin/env python3
"""
MindLang SLO/SLA 관리 시스템
서비스 레벨 목표(SLO) 및 계약(SLA) 추적 및 관리

기능:
- SLO/SLA 정의 및 설정
- 실시간 메트릭 모니터링
- 위반 탐지 및 알림
- 에러 예산(Error Budget) 추적
- SLO 달성률 보고
- 위반 기록 및 분석
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class MetricType(Enum):
    """메트릭 타입"""
    AVAILABILITY = "availability"  # %
    LATENCY = "latency"  # ms
    ERROR_RATE = "error_rate"  # %
    THROUGHPUT = "throughput"  # req/s
    SUCCESS_RATE = "success_rate"  # %


class TimeWindow(Enum):
    """시간 윈도우"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class SLOMetric:
    """SLO 메트릭"""
    metric_type: str
    target_value: float
    unit: str  # %, ms, req/s
    comparison: str  # >=, <=, ==
    description: str


@dataclass
class SLO:
    """Service Level Objective"""
    name: str
    service_name: str
    time_window: str
    metrics: List[SLOMetric]
    created_at: float
    description: str = ""
    owner: str = "platform_team"
    status: str = "active"  # active, paused, deprecated


@dataclass
class SLA:
    """Service Level Agreement"""
    name: str
    service_name: str
    slo_ids: List[str]
    penalty_percentage: float  # % refund/credit
    response_time_sla_ms: int
    availability_sla_percentage: float
    incident_response_time_minutes: int
    resolution_time_sla_hours: int


@dataclass
class SLOViolation:
    """SLO 위반"""
    timestamp: float
    slo_name: str
    metric_type: str
    expected_value: float
    actual_value: float
    severity: str  # low, medium, high, critical
    duration_minutes: int
    service_name: str
    description: str


@dataclass
class ErrorBudget:
    """에러 예산"""
    slo_name: str
    time_window: str
    total_budget_minutes: float  # 월간 다운타임 허용치
    remaining_budget_minutes: float
    consumed_minutes: float
    consumption_percentage: float
    status: str  # healthy, warning, critical


class SLOSLAManager:
    """SLO/SLA 관리자"""

    def __init__(self):
        self.slos: Dict[str, SLO] = {}
        self.slas: Dict[str, SLA] = {}
        self.violations: List[SLOViolation] = []
        self.error_budgets: Dict[str, ErrorBudget] = {}
        self.metric_history: Dict[str, List[Tuple[float, float]]] = {}
        self._initialize_default_slos()

    def _initialize_default_slos(self):
        """기본 SLO 초기화"""
        print("📊 SLO/SLA 시스템 초기화\n")

        # API Gateway SLO
        api_gateway_slo = SLO(
            name="api-gateway-availability",
            service_name="api-gateway",
            time_window=TimeWindow.MONTHLY.value,
            metrics=[
                SLOMetric(MetricType.AVAILABILITY.value, 99.95, "%", ">=", "월간 가용성 99.95% 이상"),
                SLOMetric(MetricType.LATENCY.value, 200, "ms", "<=", "P99 레이턴시 200ms 이하"),
                SLOMetric(MetricType.ERROR_RATE.value, 0.1, "%", "<=", "에러율 0.1% 이하")
            ],
            created_at=time.time(),
            description="API Gateway 서비스 레벨 목표"
        )

        # Database SLO
        database_slo = SLO(
            name="database-performance",
            service_name="database",
            time_window=TimeWindow.MONTHLY.value,
            metrics=[
                SLOMetric(MetricType.AVAILABILITY.value, 99.99, "%", ">=", "월간 가용성 99.99% 이상"),
                SLOMetric(MetricType.LATENCY.value, 100, "ms", "<=", "쿼리 응답 시간 100ms 이하"),
                SLOMetric(MetricType.SUCCESS_RATE.value, 99.9, "%", ">=", "쿼리 성공률 99.9% 이상")
            ],
            created_at=time.time(),
            description="데이터베이스 성능 목표"
        )

        # Business Service SLO
        business_slo = SLO(
            name="business-service-uptime",
            service_name="business-service",
            time_window=TimeWindow.MONTHLY.value,
            metrics=[
                SLOMetric(MetricType.AVAILABILITY.value, 99.90, "%", ">=", "월간 가용성 99.90% 이상"),
                SLOMetric(MetricType.ERROR_RATE.value, 0.5, "%", "<=", "에러율 0.5% 이하"),
                SLOMetric(MetricType.THROUGHPUT.value, 1000, "req/s", ">=", "최소 처리량 1000 req/s")
            ],
            created_at=time.time(),
            description="비즈니스 서비스 레벨 목표"
        )

        self.slos = {
            "api-gateway-availability": api_gateway_slo,
            "database-performance": database_slo,
            "business-service-uptime": business_slo
        }

        # 각 SLO에 대한 SLA 정의
        api_gateway_sla = SLA(
            name="api-gateway-sla",
            service_name="api-gateway",
            slo_ids=["api-gateway-availability"],
            penalty_percentage=10,  # 위반 시 10% 크레딧
            response_time_sla_ms=500,
            availability_sla_percentage=99.5,
            incident_response_time_minutes=15,
            resolution_time_sla_hours=4
        )

        database_sla = SLA(
            name="database-sla",
            service_name="database",
            slo_ids=["database-performance"],
            penalty_percentage=25,
            response_time_sla_ms=200,
            availability_sla_percentage=99.95,
            incident_response_time_minutes=10,
            resolution_time_sla_hours=2
        )

        self.slas = {
            "api-gateway-sla": api_gateway_sla,
            "database-sla": database_sla
        }

        # 에러 예산 초기화
        self._initialize_error_budgets()

        print("✅ 3개의 SLO 및 2개의 SLA 설정 완료\n")

    def _initialize_error_budgets(self):
        """에러 예산 초기화"""
        for slo_id, slo in self.slos.items():
            # 월간 기준: 99.95% 가용성 = ~21.6분 다운타임 허용
            availability_metric = next(
                (m for m in slo.metrics if m.metric_type == MetricType.AVAILABILITY.value),
                None
            )

            if availability_metric:
                # 월간 총 분 계산 (30일)
                total_minutes = 30 * 24 * 60
                allowed_downtime = total_minutes * (1 - availability_metric.target_value / 100)

                budget = ErrorBudget(
                    slo_name=slo.name,
                    time_window=slo.time_window,
                    total_budget_minutes=allowed_downtime,
                    remaining_budget_minutes=allowed_downtime,
                    consumed_minutes=0,
                    consumption_percentage=0,
                    status="healthy"
                )

                self.error_budgets[slo_id] = budget

    def check_slo_compliance(self, slo_id: str, current_metrics: Dict) -> Dict:
        """SLO 준수 확인"""
        if slo_id not in self.slos:
            return {}

        slo = self.slos[slo_id]
        compliance_results = {
            'slo_name': slo.name,
            'service_name': slo.service_name,
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'all_met': True
        }

        for metric in slo.metrics:
            current_value = current_metrics.get(metric.metric_type)

            if current_value is None:
                continue

            # 비교 수행
            is_met = self._compare_metric(current_value, metric.target_value, metric.comparison)

            compliance_results['metrics'][metric.metric_type] = {
                'target': metric.target_value,
                'current': current_value,
                'unit': metric.unit,
                'met': is_met,
                'description': metric.description
            }

            if not is_met:
                compliance_results['all_met'] = False

                # 위반 기록
                self._record_violation(slo, metric, current_value)

        return compliance_results

    def _compare_metric(self, current: float, target: float, comparison: str) -> bool:
        """메트릭 비교"""
        if comparison == ">=":
            return current >= target
        elif comparison == "<=":
            return current <= target
        elif comparison == "==":
            return abs(current - target) < 0.01
        else:
            return True

    def _record_violation(self, slo: SLO, metric: SLOMetric, actual_value: float):
        """위반 기록"""
        severity = "low"
        difference = abs(actual_value - metric.target_value)

        if difference > metric.target_value * 0.3:
            severity = "critical"
        elif difference > metric.target_value * 0.2:
            severity = "high"
        elif difference > metric.target_value * 0.1:
            severity = "medium"

        violation = SLOViolation(
            timestamp=time.time(),
            slo_name=slo.name,
            metric_type=metric.metric_type,
            expected_value=metric.target_value,
            actual_value=actual_value,
            severity=severity,
            duration_minutes=1,
            service_name=slo.service_name,
            description=f"{metric.metric_type}: {actual_value} (목표: {metric.target_value})"
        )

        self.violations.append(violation)

        # 에러 예산 소비
        if metric.metric_type == MetricType.AVAILABILITY.value:
            slo_id = next((k for k, v in self.slos.items() if v.name == slo.name), None)
            if slo_id and slo_id in self.error_budgets:
                budget = self.error_budgets[slo_id]
                budget.consumed_minutes += 1
                budget.remaining_budget_minutes -= 1
                budget.consumption_percentage = (budget.consumed_minutes / budget.total_budget_minutes) * 100

                if budget.consumption_percentage > 90:
                    budget.status = "critical"
                elif budget.consumption_percentage > 70:
                    budget.status = "warning"

        print(f"❌ SLO 위반: {slo.name} - {metric.metric_type}")

    def get_error_budget_status(self, slo_id: str) -> Optional[ErrorBudget]:
        """에러 예산 상태"""
        return self.error_budgets.get(slo_id)

    def predict_slo_violation(self, slo_id: str, current_metrics: Dict) -> Optional[str]:
        """SLO 위반 예측"""
        if slo_id not in self.slos:
            return None

        slo = self.slos[slo_id]
        violation_risk = []

        for metric in slo.metrics:
            current_value = current_metrics.get(metric.metric_type)

            if current_value is None:
                continue

            # 위반 위험도 계산
            if metric.comparison == ">=":
                risk = (metric.target_value - current_value) / metric.target_value
            elif metric.comparison == "<=":
                risk = (current_value - metric.target_value) / metric.target_value
            else:
                risk = 0

            if risk > 0.2:  # 20% 이상 위험
                violation_risk.append({
                    'metric': metric.metric_type,
                    'risk_score': min(1.0, risk),
                    'recommendation': f"{metric.metric_type}에 즉시 대응 필요"
                })

        if violation_risk:
            highest_risk = max(violation_risk, key=lambda x: x['risk_score'])
            return highest_risk['recommendation']

        return None

    def generate_slo_report(self, slo_id: str) -> Dict:
        """SLO 보고서 생성"""
        if slo_id not in self.slos:
            return {}

        slo = self.slos[slo_id]
        budget = self.error_budgets.get(slo_id)

        # 최근 위반 통계
        recent_violations = [v for v in self.violations if v.slo_name == slo.name]

        report = {
            'slo_name': slo.name,
            'service_name': slo.service_name,
            'time_window': slo.time_window,
            'reporting_period': {
                'start': (datetime.now() - timedelta(days=30)).isoformat(),
                'end': datetime.now().isoformat()
            },
            'metrics': [
                {
                    'type': m.metric_type,
                    'target': m.target_value,
                    'unit': m.unit,
                    'description': m.description
                }
                for m in slo.metrics
            ],
            'violations': {
                'total_count': len(recent_violations),
                'by_severity': {
                    'critical': len([v for v in recent_violations if v.severity == 'critical']),
                    'high': len([v for v in recent_violations if v.severity == 'high']),
                    'medium': len([v for v in recent_violations if v.severity == 'medium']),
                    'low': len([v for v in recent_violations if v.severity == 'low'])
                },
                'mttr_average_minutes': 15 if recent_violations else None
            },
            'error_budget': {
                'total_minutes': budget.total_budget_minutes if budget else None,
                'consumed_minutes': budget.consumed_minutes if budget else None,
                'remaining_minutes': budget.remaining_budget_minutes if budget else None,
                'consumption_percentage': budget.consumption_percentage if budget else None,
                'status': budget.status if budget else None
            },
            'compliance_status': 'IN_COMPLIANCE' if len(recent_violations) == 0 else 'AT_RISK'
        }

        return report

    def print_slo_dashboard(self):
        """SLO 대시보드 출력"""
        print("\n" + "=" * 90)
        print("📊 SLO/SLA 관리 대시보드")
        print("=" * 90 + "\n")

        print("🎯 등록된 SLO:\n")

        for slo_id, slo in self.slos.items():
            budget = self.error_budgets.get(slo_id)

            print(f"📌 {slo.name} ({slo.service_name})")
            print(f"   시간 윈도우: {slo.time_window}")
            print(f"   상태: {slo.status}")

            for metric in slo.metrics:
                print(f"   • {metric.metric_type}: {metric.target_value}{metric.unit} {metric.comparison}")

            if budget:
                status_icon = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'critical': '🔴'
                }.get(budget.status, '❓')

                print(f"   에러 예산: {budget.remaining_budget_minutes:.1f}/{budget.total_budget_minutes:.1f} 분 {status_icon}")
                print(f"   소비율: {budget.consumption_percentage:.1f}%")

            print()

        # 위반 통계
        if self.violations:
            print("🚨 최근 위반:\n")

            recent = sorted(self.violations, key=lambda x: x.timestamp, reverse=True)[:5]

            for violation in recent:
                time_str = datetime.fromtimestamp(violation.timestamp).strftime('%H:%M:%S')
                print(f"   [{time_str}] {violation.slo_name}: {violation.description} ({violation.severity})")

        print("\n" + "=" * 90 + "\n")

    def export_slo_report(self, slo_id: str, filename: str = None) -> Optional[str]:
        """SLO 보고서 내보내기"""
        report = self.generate_slo_report(slo_id)

        if not report:
            return None

        if filename is None:
            filename = f"slo_report_{slo_id}_{int(time.time())}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"✅ SLO 보고서 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None

    def get_slo_stats(self) -> Dict:
        """SLO 통계"""
        total_slos = len(self.slos)
        total_violations = len(self.violations)

        by_severity = {
            'critical': len([v for v in self.violations if v.severity == 'critical']),
            'high': len([v for v in self.violations if v.severity == 'high']),
            'medium': len([v for v in self.violations if v.severity == 'medium']),
            'low': len([v for v in self.violations if v.severity == 'low'])
        }

        return {
            'total_slos': total_slos,
            'total_violations': total_violations,
            'by_severity': by_severity,
            'slas_defined': len(self.slas)
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_slo_stats()

        print("\n" + "=" * 70)
        print("📊 SLO/SLA 시스템 통계")
        print("=" * 70 + "\n")

        print(f"정의된 SLO: {stats['total_slos']}개")
        print(f"정의된 SLA: {stats['slas_defined']}개")
        print(f"총 위반: {stats['total_violations']}건")
        print(f"  - Critical: {stats['by_severity']['critical']}건")
        print(f"  - High: {stats['by_severity']['high']}건")
        print(f"  - Medium: {stats['by_severity']['medium']}건")
        print(f"  - Low: {stats['by_severity']['low']}건\n")

        print("=" * 70 + "\n")


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = SLOSLAManager()

    if len(sys.argv) < 2:
        print("사용법: python slo_sla_manager.py [command] [args]")
        print("  dashboard       - SLO/SLA 대시보드")
        print("  check <slo_id>  - SLO 준수 확인")
        print("  report <slo_id> - SLO 보고서")
        print("  stats           - 통계")
        return

    command = sys.argv[1]

    if command == "dashboard":
        manager.print_slo_dashboard()

    elif command == "check":
        slo_id = sys.argv[2] if len(sys.argv) > 2 else "api-gateway-availability"

        metrics = {
            'availability': 99.92,
            'latency': 195,
            'error_rate': 0.08,
            'throughput': 1100,
            'success_rate': 99.92
        }

        result = manager.check_slo_compliance(slo_id, metrics)
        print(f"\n✅ SLO 준수 확인: {slo_id}\n")
        for metric, data in result.get('metrics', {}).items():
            status = "✅" if data['met'] else "❌"
            print(f"{status} {metric}: {data['current']}{data['unit']} (목표: {data['target']}{data['unit']})")

    elif command == "report":
        slo_id = sys.argv[2] if len(sys.argv) > 2 else "api-gateway-availability"
        manager.export_slo_report(slo_id)

    elif command == "stats":
        manager.print_stats()
