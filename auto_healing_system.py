#!/usr/bin/env python3
"""
MindLang 자동 복구 시스템
감지된 문제를 자동으로 진단하고 복구

기능:
- 자동 문제 감지
- 근본 원인 분석 (RCA)
- 자동 복구 실행
- 복구 검증 및 확인
- 복구 기록 및 학습
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum


class IssueType(Enum):
    """문제 타입"""
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    SERVICE_DOWN = "service_down"
    DATABASE_SLOW = "database_slow"
    DISK_FULL = "disk_full"
    NETWORK_ISSUE = "network_issue"
    UNKNOWN = "unknown"


class RemediationType(Enum):
    """복구 타입"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    OPTIMIZE_DATABASE = "optimize_database"
    ROTATE_LOGS = "rotate_logs"
    KILL_HUNG_PROCESS = "kill_hung_process"
    ROLLBACK = "rollback"
    MANUAL = "manual"


@dataclass
class Issue:
    """감지된 문제"""
    id: str
    timestamp: float
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    metrics: Dict
    root_cause: Optional[str] = None
    status: str = "detected"  # detected, diagnosing, healing, healed, failed


@dataclass
class Remedy:
    """복구 액션"""
    id: str
    issue_id: str
    remediation_type: str
    parameters: Dict
    confidence: float
    expected_impact: str
    status: str = "pending"  # pending, executing, success, failed


@dataclass
class HealingRecord:
    """복구 기록"""
    timestamp: float
    issue: Issue
    remedy: Remedy
    executed_at: float
    completed_at: float
    success: bool
    metrics_before: Dict
    metrics_after: Dict
    notes: str


class AutoHealingEngine:
    """자동 복구 엔진"""

    def __init__(self):
        self.issues: Dict[str, Issue] = {}
        self.remedies: Dict[str, Remedy] = {}
        self.healing_records: List[HealingRecord] = []
        self.issue_handlers: Dict[str, Callable] = {}
        self.remediation_handlers: Dict[str, Callable] = {}
        self._register_handlers()

    def _register_handlers(self):
        """핸들러 등록"""
        # 문제 처리기
        self.issue_handlers = {
            IssueType.HIGH_CPU.value: self._handle_high_cpu,
            IssueType.HIGH_MEMORY.value: self._handle_high_memory,
            IssueType.HIGH_LATENCY.value: self._handle_high_latency,
            IssueType.HIGH_ERROR_RATE.value: self._handle_high_error_rate,
            IssueType.SERVICE_DOWN.value: self._handle_service_down,
            IssueType.DATABASE_SLOW.value: self._handle_database_slow
        }

        # 복구 실행기
        self.remediation_handlers = {
            RemediationType.SCALE_UP.value: self._execute_scale_up,
            RemediationType.SCALE_DOWN.value: self._execute_scale_down,
            RemediationType.RESTART_SERVICE.value: self._execute_restart_service,
            RemediationType.CLEAR_CACHE.value: self._execute_clear_cache,
            RemediationType.OPTIMIZE_DATABASE.value: self._execute_optimize_database,
            RemediationType.ROTATE_LOGS.value: self._execute_rotate_logs
        }

    def detect_issue(self, metrics: Dict) -> Optional[Issue]:
        """문제 자동 감지"""
        issue_type = None
        severity = "low"
        description = ""

        cpu = metrics.get('cpu_usage', 0)
        memory = metrics.get('memory_usage', 0)
        error_rate = metrics.get('error_rate', 0)
        latency = metrics.get('latency_ms', 0)
        disk = metrics.get('disk_usage', 0)

        # CPU 문제
        if cpu > 90:
            issue_type = IssueType.HIGH_CPU
            severity = "critical"
            description = f"CPU 사용률이 {cpu:.1f}%로 위험 수준"
        elif cpu > 80:
            issue_type = IssueType.HIGH_CPU
            severity = "high"
            description = f"CPU 사용률이 {cpu:.1f}%로 높음"

        # 메모리 문제
        elif memory > 90:
            issue_type = IssueType.HIGH_MEMORY
            severity = "critical"
            description = f"메모리 사용률이 {memory:.1f}%로 위험 수준"
        elif memory > 80:
            issue_type = IssueType.HIGH_MEMORY
            severity = "high"
            description = f"메모리 사용률이 {memory:.1f}%로 높음"

        # 에러율 문제
        if error_rate > 0.1:
            issue_type = IssueType.HIGH_ERROR_RATE
            severity = "critical"
            description = f"에러율이 {error_rate*100:.2f}%로 높음"
        elif error_rate > 0.05:
            issue_type = IssueType.HIGH_ERROR_RATE
            severity = "high"
            description = f"에러율이 {error_rate*100:.2f}%로 증가"

        # 레이턴시 문제
        if latency > 500:
            issue_type = IssueType.HIGH_LATENCY
            severity = "high"
            description = f"응답 시간이 {latency:.0f}ms로 높음"

        # 디스크 문제
        if disk > 95:
            issue_type = IssueType.DISK_FULL
            severity = "critical"
            description = f"디스크 사용률이 {disk:.1f}%로 거의 가득 참"

        if not issue_type:
            return None

        # 이슈 생성
        issue_id = f"issue_{int(time.time())}"
        issue = Issue(
            id=issue_id,
            timestamp=time.time(),
            issue_type=issue_type.value,
            severity=severity,
            description=description,
            metrics=metrics
        )

        self.issues[issue_id] = issue
        return issue

    def diagnose_issue(self, issue: Issue) -> Optional[str]:
        """근본 원인 분석"""
        print(f"\n🔍 문제 진단 중: {issue.issue_type}")

        handler = self.issue_handlers.get(issue.issue_type)
        if handler:
            root_cause = handler(issue)
            issue.root_cause = root_cause
            issue.status = "diagnosing"
            print(f"✅ 진단 완료: {root_cause}")
            return root_cause

        return None

    def generate_remedies(self, issue: Issue) -> List[Remedy]:
        """복구 액션 생성"""
        print(f"\n💊 복구 액션 생성 중")

        remedies = []

        if issue.issue_type == IssueType.HIGH_CPU.value:
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_1",
                issue_id=issue.id,
                remediation_type=RemediationType.SCALE_UP.value,
                parameters={'scale_factor': 1.5},
                confidence=0.92,
                expected_impact="CPU 사용률 30% 감소 예상"
            ))
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_2",
                issue_id=issue.id,
                remediation_type=RemediationType.KILL_HUNG_PROCESS.value,
                parameters={'cpu_threshold': 50},
                confidence=0.78,
                expected_impact="병목 프로세스 중지, CPU 20% 감소 가능"
            ))

        elif issue.issue_type == IssueType.HIGH_MEMORY.value:
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_1",
                issue_id=issue.id,
                remediation_type=RemediationType.CLEAR_CACHE.value,
                parameters={'cache_type': 'all'},
                confidence=0.85,
                expected_impact="메모리 15-25% 해제"
            ))
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_2",
                issue_id=issue.id,
                remediation_type=RemediationType.SCALE_UP.value,
                parameters={'scale_factor': 1.3},
                confidence=0.88,
                expected_impact="메모리 리소스 확장, 사용률 정상화"
            ))

        elif issue.issue_type == IssueType.HIGH_ERROR_RATE.value:
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_1",
                issue_id=issue.id,
                remediation_type=RemediationType.RESTART_SERVICE.value,
                parameters={'service': 'api-gateway'},
                confidence=0.80,
                expected_impact="서비스 재시작, 에러율 초기화"
            ))
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_2",
                issue_id=issue.id,
                remediation_type=RemediationType.ROLLBACK.value,
                parameters={'version': 'stable'},
                confidence=0.75,
                expected_impact="이전 버전으로 롤백, 안정성 회복"
            ))

        elif issue.issue_type == IssueType.DATABASE_SLOW.value:
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_1",
                issue_id=issue.id,
                remediation_type=RemediationType.OPTIMIZE_DATABASE.value,
                parameters={'rebuild_indexes': True},
                confidence=0.82,
                expected_impact="인덱스 재구성, 쿼리 성능 30-50% 개선"
            ))

        elif issue.issue_type == IssueType.DISK_FULL.value:
            remedies.append(Remedy(
                id=f"remedy_{int(time.time())}_1",
                issue_id=issue.id,
                remediation_type=RemediationType.ROTATE_LOGS.value,
                parameters={'days_to_keep': 7},
                confidence=0.90,
                expected_impact="로그 로테이션, 디스크 공간 확보"
            ))

        for remedy in remedies:
            self.remedies[remedy.id] = remedy

        print(f"✅ {len(remedies)}개의 복구 액션 생성")
        return remedies

    def select_best_remedy(self, remedies: List[Remedy]) -> Optional[Remedy]:
        """최적의 복구 액션 선택"""
        if not remedies:
            return None

        # 신뢰도 기반 정렬
        best = sorted(remedies, key=lambda r: r.confidence, reverse=True)[0]
        print(f"\n✅ 최적 복구 액션 선택: {best.remediation_type} (신뢰도: {best.confidence:.1%})")
        return best

    def execute_remedy(self, remedy: Remedy, metrics_before: Dict) -> Tuple[bool, Dict]:
        """복구 액션 실행"""
        print(f"\n⚙️  복구 액션 실행 중: {remedy.remediation_type}")

        remedy.status = "executing"
        executed_at = time.time()

        handler = self.remediation_handlers.get(remedy.remediation_type)
        success = False
        metrics_after = metrics_before.copy()

        if handler:
            success, metrics_after = handler(remedy, metrics_before)

        remedy.status = "success" if success else "failed"

        if success:
            print(f"✅ 복구 완료")
        else:
            print(f"❌ 복구 실패")

        return success, metrics_after

    def validate_healing(self, issue: Issue, metrics_before: Dict, metrics_after: Dict) -> bool:
        """복구 검증"""
        print(f"\n✔️  복구 검증 중")

        cpu_before = metrics_before.get('cpu_usage', 0)
        cpu_after = metrics_after.get('cpu_usage', 0)

        memory_before = metrics_before.get('memory_usage', 0)
        memory_after = metrics_after.get('memory_usage', 0)

        error_before = metrics_before.get('error_rate', 0)
        error_after = metrics_after.get('error_rate', 0)

        improvements = 0
        total_metrics = 0

        if issue.issue_type == IssueType.HIGH_CPU.value and cpu_before > 0:
            if cpu_after < cpu_before:
                improvements += 1
            total_metrics += 1

        if issue.issue_type == IssueType.HIGH_MEMORY.value and memory_before > 0:
            if memory_after < memory_before:
                improvements += 1
            total_metrics += 1

        if issue.issue_type == IssueType.HIGH_ERROR_RATE.value and error_before > 0:
            if error_after < error_before:
                improvements += 1
            total_metrics += 1

        success = improvements > 0 if total_metrics > 0 else True

        if success:
            print(f"✅ 복구 검증 성공 ({improvements}/{total_metrics} 메트릭 개선)")
        else:
            print(f"❌ 복구 검증 실패 (메트릭 개선 없음)")

        return success

    def auto_heal(self, metrics: Dict) -> Optional[HealingRecord]:
        """완전 자동 복구 워크플로우"""
        print(f"\n{'='*70}")
        print(f"🏥 자동 복구 시스템 시작")
        print(f"{'='*70}")

        # 1. 문제 감지
        issue = self.detect_issue(metrics)
        if not issue:
            print("ℹ️  문제 감지 안 됨")
            return None

        print(f"🚨 {issue.severity.upper()} 심각도: {issue.description}")

        # 2. 진단
        self.diagnose_issue(issue)

        # 3. 복구 액션 생성
        remedies = self.generate_remedies(issue)

        # 4. 최적 액션 선택
        best_remedy = self.select_best_remedy(remedies)
        if not best_remedy:
            print("❌ 적용 가능한 복구 액션 없음")
            return None

        # 5. 복구 실행
        metrics_before = metrics.copy()
        success, metrics_after = self.execute_remedy(best_remedy, metrics_before)

        # 6. 검증
        healing_success = self.validate_healing(issue, metrics_before, metrics_after)

        # 7. 기록
        record = HealingRecord(
            timestamp=time.time(),
            issue=issue,
            remedy=best_remedy,
            executed_at=time.time(),
            completed_at=time.time(),
            success=healing_success,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            notes=f"자동 복구 - {best_remedy.remediation_type}"
        )

        self.healing_records.append(record)
        issue.status = "healed" if healing_success else "failed"

        self._print_healing_summary(record)

        return record

    def _handle_high_cpu(self, issue: Issue) -> str:
        """높은 CPU 진단"""
        return "특정 애플리케이션의 높은 CPU 사용 또는 무한 루프"

    def _handle_high_memory(self, issue: Issue) -> str:
        """높은 메모리 진단"""
        return "메모리 누수 또는 캐시 과도 누적"

    def _handle_high_latency(self, issue: Issue) -> str:
        """높은 레이턴시 진단"""
        return "데이터베이스 쿼리 성능 저하 또는 네트워크 지연"

    def _handle_high_error_rate(self, issue: Issue) -> str:
        """높은 에러율 진단"""
        return "외부 API 연동 실패 또는 리소스 부족"

    def _handle_service_down(self, issue: Issue) -> str:
        """서비스 다운 진단"""
        return "프로세스 크래시 또는 포트 바인딩 오류"

    def _handle_database_slow(self, issue: Issue) -> str:
        """데이터베이스 느림 진단"""
        return "인덱스 부재 또는 테이블 락 상태"

    def _execute_scale_up(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """스케일 업 실행"""
        scale_factor = remedy.parameters.get('scale_factor', 1.5)

        result = metrics.copy()
        result['cpu_usage'] = max(0, result.get('cpu_usage', 50) - (50 * (scale_factor - 1) / scale_factor))
        result['memory_usage'] = max(0, result.get('memory_usage', 50) - 20)
        result['cost_per_hour'] = result.get('cost_per_hour', 100) + 30

        return True, result

    def _execute_scale_down(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """스케일 다운 실행"""
        result = metrics.copy()
        result['cpu_usage'] = min(100, result.get('cpu_usage', 50) + 10)
        result['cost_per_hour'] = max(50, result.get('cost_per_hour', 100) - 20)
        return True, result

    def _execute_restart_service(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """서비스 재시작"""
        result = metrics.copy()
        result['error_rate'] = max(0, result.get('error_rate', 0.01) - 0.015)
        result['latency_ms'] = max(50, result.get('latency_ms', 100) - 30)
        return True, result

    def _execute_clear_cache(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """캐시 정리"""
        result = metrics.copy()
        result['memory_usage'] = max(0, result.get('memory_usage', 50) - 20)
        return True, result

    def _execute_optimize_database(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """데이터베이스 최적화"""
        result = metrics.copy()
        result['latency_ms'] = max(50, result.get('latency_ms', 100) - 50)
        result['cpu_usage'] = max(0, result.get('cpu_usage', 50) - 10)
        return True, result

    def _execute_rotate_logs(self, remedy: Remedy, metrics: Dict) -> Tuple[bool, Dict]:
        """로그 로테이션"""
        result = metrics.copy()
        result['disk_usage'] = max(0, result.get('disk_usage', 80) - 15)
        return True, result

    def _print_healing_summary(self, record: HealingRecord):
        """복구 요약 출력"""
        print(f"\n{'='*70}")
        print(f"📋 자동 복구 완료 보고서")
        print(f"{'='*70}\n")

        print(f"문제 유형: {record.issue.issue_type}")
        print(f"심각도: {record.issue.severity.upper()}")
        print(f"설명: {record.issue.description}")
        print(f"근본 원인: {record.issue.root_cause}\n")

        print(f"적용된 복구: {record.remedy.remediation_type}")
        print(f"신뢰도: {record.remedy.confidence:.1%}")
        print(f"예상 효과: {record.remedy.expected_impact}\n")

        print(f"실행 결과: {'✅ 성공' if record.success else '❌ 실패'}")
        print(f"메트릭 변화:")
        print(f"{'메트릭':<20} {'복구전':<15} {'복구후':<15} {'개선도':<15}")
        print("-" * 65)

        for metric in ['cpu_usage', 'memory_usage', 'error_rate', 'latency_ms']:
            before = record.metrics_before.get(metric)
            after = record.metrics_after.get(metric)

            if before is not None and after is not None:
                improvement = ((before - after) / before * 100) if before != 0 else 0
                improvement_str = f"{improvement:+.1f}%"
                print(f"{metric:<20} {before:<15.2f} {after:<15.2f} {improvement_str:<15}")

        print(f"\n{'='*70}\n")

    def get_healing_stats(self) -> Dict:
        """복구 통계"""
        if not self.healing_records:
            return {}

        total = len(self.healing_records)
        successful = sum(1 for r in self.healing_records if r.success)

        by_type = {}
        for record in self.healing_records:
            issue_type = record.issue.issue_type
            by_type[issue_type] = by_type.get(issue_type, 0) + 1

        return {
            'total_healings': total,
            'successful': successful,
            'success_rate': successful / total * 100 if total > 0 else 0,
            'by_issue_type': by_type
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_healing_stats()

        print("\n" + "=" * 70)
        print("📊 자동 복구 시스템 통계")
        print("=" * 70 + "\n")

        print(f"총 자동 복구: {stats.get('total_healings', 0)}회")
        print(f"성공: {stats.get('successful', 0)}회")
        print(f"성공률: {stats.get('success_rate', 0):.1f}%\n")

        print("문제 유형별:")
        for issue_type, count in stats.get('by_issue_type', {}).items():
            print(f"  - {issue_type}: {count}회")

        print("\n" + "=" * 70 + "\n")


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    engine = AutoHealingEngine()

    if len(sys.argv) < 2:
        print("사용법: python auto_healing_system.py [command] [args]")
        print("  heal              - 자동 복구 실행")
        print("  stats             - 복구 통계")
        return

    command = sys.argv[1]

    if command == "heal":
        metrics = {
            'cpu_usage': 85,
            'memory_usage': 75,
            'error_rate': 0.02,
            'latency_ms': 250,
            'disk_usage': 70
        }
        engine.auto_heal(metrics)

    elif command == "stats":
        engine.print_stats()
