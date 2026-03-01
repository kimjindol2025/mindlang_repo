#!/usr/bin/env python3
"""
MindLang 인시던트 관리 시스템
자동 인시던트 탐지, 추적, 분석 및 근본 원인 조사

기능:
- 자동 인시던트 탐지
- 인시던트 분류 및 우선순위
- 자동 복구 시도 및 추적
- 타임라인 분석
- 근본 원인 분석 (RCA)
- 교훈 학습 (Post-Mortem)
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


class IncidentSeverity(Enum):
    """인시던트 심각도"""
    SEV1 = "sev1"  # Critical (down)
    SEV2 = "sev2"  # High (degraded)
    SEV3 = "sev3"  # Medium (slow)
    SEV4 = "sev4"  # Low (informational)


class IncidentStatus(Enum):
    """인시던트 상태"""
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    IN_PROGRESS = "in_progress"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentCause(Enum):
    """인시던트 원인"""
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    EXTERNAL = "external"
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class TimelineEvent:
    """타임라인 이벤트"""
    timestamp: float
    event_type: str  # detected, acknowledged, action_taken, resolved, etc.
    description: str
    actor: str = "system"
    severity_change: Optional[str] = None


@dataclass
class Incident:
    """인시던트"""
    id: str
    timestamp: float
    severity: str
    title: str
    description: str
    status: str
    affected_services: List[str]
    affected_users: int = 0
    impact_scope: str = ""  # regional, global, single_service
    metrics_snapshot: Dict = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    timeline: List[TimelineEvent] = None
    estimated_mttr_minutes: int = 0
    actual_duration_minutes: int = 0
    remediation_actions: List[str] = None
    post_mortem_notes: str = ""
    follow_up_items: List[str] = None

    def __post_init__(self):
        if self.metrics_snapshot is None:
            self.metrics_snapshot = {}
        if self.timeline is None:
            self.timeline = []
        if self.remediation_actions is None:
            self.remediation_actions = []
        if self.follow_up_items is None:
            self.follow_up_items = []


@dataclass
class IncidentStats:
    """인시던트 통계"""
    total_incidents: int
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    by_cause: Dict[str, int]
    average_mttr_minutes: float
    average_duration_minutes: float
    resolution_rate: float


class IncidentManager:
    """인시던트 관리자"""

    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.detection_rules: List[Dict] = []
        self.incident_history: List[Incident] = []
        self._register_detection_rules()

    def _register_detection_rules(self):
        """인시던트 탐지 규칙 등록"""
        self.detection_rules = [
            {
                'name': '서비스 다운',
                'condition': lambda m: m.get('service_status') == 'down',
                'severity': IncidentSeverity.SEV1,
                'title': '서비스 다운 감지'
            },
            {
                'name': '에러율 급증',
                'condition': lambda m: m.get('error_rate', 0) > 0.1,
                'severity': IncidentSeverity.SEV2,
                'title': '에러율 급증'
            },
            {
                'name': '응답시간 급증',
                'condition': lambda m: m.get('latency_ms', 0) > 1000,
                'severity': IncidentSeverity.SEV2,
                'title': '응답시간 급증'
            },
            {
                'name': 'CPU 위험',
                'condition': lambda m: m.get('cpu_usage', 0) > 95,
                'severity': IncidentSeverity.SEV2,
                'title': 'CPU 사용률 위험'
            },
            {
                'name': '메모리 위험',
                'condition': lambda m: m.get('memory_usage', 0) > 95,
                'severity': IncidentSeverity.SEV2,
                'title': '메모리 사용률 위험'
            },
            {
                'name': 'DB 연결 실패',
                'condition': lambda m: m.get('db_connections_failed', 0) > 10,
                'severity': IncidentSeverity.SEV3,
                'title': '데이터베이스 연결 오류'
            }
        ]

    def detect_incidents(self, metrics: Dict) -> List[Incident]:
        """메트릭 기반 인시던트 자동 탐지"""
        detected_incidents = []

        for rule in self.detection_rules:
            if rule['condition'](metrics):
                incident = self._create_incident(
                    severity=rule['severity'],
                    title=rule['title'],
                    metrics=metrics
                )

                self.incidents[incident.id] = incident
                detected_incidents.append(incident)

                print(f"🚨 인시던트 탐지: {incident.severity} - {incident.title}")

        return detected_incidents

    def _create_incident(self, severity: IncidentSeverity, title: str, metrics: Dict) -> Incident:
        """인시던트 생성"""
        incident_id = f"inc_{int(time.time())}"

        incident = Incident(
            id=incident_id,
            timestamp=time.time(),
            severity=severity.value,
            title=title,
            description=f"자동으로 탐지됨: {title}",
            status=IncidentStatus.DETECTED.value,
            affected_services=['api-gateway', 'database'],
            affected_users=100,
            impact_scope='regional',
            metrics_snapshot=metrics,
            estimated_mttr_minutes=self._estimate_mttr(severity)
        )

        # 타임라인 추가
        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='detected',
            description='인시던트 자동 탐지',
            actor='detection_system'
        ))

        return incident

    def _estimate_mttr(self, severity: IncidentSeverity) -> int:
        """MTTR 추정"""
        if severity == IncidentSeverity.SEV1:
            return 15
        elif severity == IncidentSeverity.SEV2:
            return 30
        elif severity == IncidentSeverity.SEV3:
            return 60
        else:
            return 120

    def acknowledge_incident(self, incident_id: str, responder: str = "on_call_engineer") -> bool:
        """인시던트 승인"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        incident.status = IncidentStatus.ACKNOWLEDGED.value

        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='acknowledged',
            description=f'엔지니어 {responder}가 인시던트를 확인',
            actor=responder
        ))

        print(f"✅ 인시던트 승인: {incident_id}")
        return True

    def start_investigation(self, incident_id: str) -> bool:
        """조사 시작"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        incident.status = IncidentStatus.INVESTIGATING.value

        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='investigation_started',
            description='근본 원인 조사 시작',
            actor='on_call_engineer'
        ))

        print(f"🔍 조사 시작: {incident_id}")
        return True

    def diagnose_incident(self, incident_id: str) -> Optional[str]:
        """인시던트 진단"""
        if incident_id not in self.incidents:
            return None

        incident = self.incidents[incident_id]

        # 간단한 진단 로직
        if 'error_rate' in incident.metrics_snapshot:
            if incident.metrics_snapshot['error_rate'] > 0.1:
                root_cause = IncidentCause.APPLICATION.value
                diagnosis = "애플리케이션 코드 오류로 인한 높은 에러율"

        elif 'cpu_usage' in incident.metrics_snapshot:
            if incident.metrics_snapshot['cpu_usage'] > 95:
                root_cause = IncidentCause.INFRASTRUCTURE.value
                diagnosis = "리소스 부족 - CPU 병목 현상"

        elif 'service_status' in incident.metrics_snapshot:
            root_cause = IncidentCause.INFRASTRUCTURE.value
            diagnosis = "서비스 프로세스 다운 - 즉시 재시작 필요"

        else:
            root_cause = IncidentCause.UNKNOWN.value
            diagnosis = "근본 원인 파악 중"

        incident.root_cause = diagnosis
        print(f"📋 진단: {diagnosis}")

        return diagnosis

    def execute_remediation(self, incident_id: str, action: str) -> bool:
        """복구 액션 실행"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        incident.status = IncidentStatus.IN_PROGRESS.value
        incident.remediation_actions.append(action)

        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='remediation_started',
            description=f'복구 액션 실행: {action}',
            actor='auto_system'
        ))

        print(f"⚙️  복구 액션 실행: {action}")
        return True

    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        """인시던트 해결"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]

        # 지속 시간 계산
        duration_seconds = time.time() - incident.timestamp
        incident.actual_duration_minutes = int(duration_seconds / 60)
        incident.status = IncidentStatus.RESOLVED.value
        incident.resolution = resolution

        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='resolved',
            description=f'인시던트 해결: {resolution}',
            actor='on_call_engineer'
        ))

        print(f"✅ 인시던트 해결: {incident_id}")
        print(f"   지속 시간: {incident.actual_duration_minutes}분")
        print(f"   예상 MTTR: {incident.estimated_mttr_minutes}분")
        print(f"   실제 MTTR: {incident.actual_duration_minutes}분")

        return True

    def conduct_postmortem(self, incident_id: str) -> bool:
        """사후 분석 (Post-Mortem)"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]

        # 자동 Post-Mortem 생성
        postmortem = f"""
## 인시던트 Post-Mortem: {incident.title}

### 타임라인
"""
        for event in incident.timeline:
            event_time = datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')
            postmortem += f"- {event_time}: {event.description}\n"

        postmortem += f"""
### 영향
- 영향받은 서비스: {', '.join(incident.affected_services)}
- 영향받은 사용자: {incident.affected_users}명
- 영향 범위: {incident.impact_scope}

### 근본 원인
{incident.root_cause or '조사 중'}

### 해결 방법
{incident.resolution or '미정'}

### 복구 액션
"""
        for i, action in enumerate(incident.remediation_actions, 1):
            postmortem += f"{i}. {action}\n"

        postmortem += """
### 교훈
1. 조기 감지 능력 강화
2. 자동 복구 프로세스 개선
3. 모니터링 임계값 조정

### Follow-up Items
"""
        follow_up_items = [
            "코드 리뷰 및 테스트 강화",
            "배포 프로세스 개선",
            "모니터링 및 알림 규칙 업데이트"
        ]

        for i, item in enumerate(follow_up_items, 1):
            postmortem += f"- [ ] {item}\n"
            incident.follow_up_items.append(item)

        incident.post_mortem_notes = postmortem
        incident.status = IncidentStatus.CLOSED.value

        incident.timeline.append(TimelineEvent(
            timestamp=time.time(),
            event_type='closed',
            description='Post-Mortem 완료, 인시던트 종료',
            actor='on_call_engineer'
        ))

        self.incident_history.append(incident)

        print(f"📝 Post-Mortem 작성 완료:")
        print(postmortem)

        return True

    def get_incident_timeline(self, incident_id: str) -> List[Dict]:
        """인시던트 타임라인 조회"""
        if incident_id not in self.incidents:
            return []

        incident = self.incidents[incident_id]
        timeline_data = []

        for event in incident.timeline:
            timeline_data.append({
                'timestamp': datetime.fromtimestamp(event.timestamp).isoformat(),
                'event_type': event.event_type,
                'description': event.description,
                'actor': event.actor
            })

        return timeline_data

    def get_incident_stats(self) -> IncidentStats:
        """인시던트 통계"""
        all_incidents = list(self.incidents.values()) + self.incident_history

        by_severity = {}
        by_status = {}
        by_cause = {}

        for incident in all_incidents:
            by_severity[incident.severity] = by_severity.get(incident.severity, 0) + 1
            by_status[incident.status] = by_status.get(incident.status, 0) + 1
            if incident.root_cause:
                by_cause[incident.root_cause] = by_cause.get(incident.root_cause, 0) + 1

        resolved_incidents = [i for i in all_incidents if i.status == IncidentStatus.CLOSED.value]

        if resolved_incidents:
            average_mttr = sum(i.actual_duration_minutes for i in resolved_incidents) / len(resolved_incidents)
            average_duration = sum(i.actual_duration_minutes for i in resolved_incidents) / len(resolved_incidents)
            resolution_rate = len(resolved_incidents) / len(all_incidents) * 100
        else:
            average_mttr = 0
            average_duration = 0
            resolution_rate = 0

        return IncidentStats(
            total_incidents=len(all_incidents),
            by_severity=by_severity,
            by_status=by_status,
            by_cause=by_cause,
            average_mttr_minutes=average_mttr,
            average_duration_minutes=average_duration,
            resolution_rate=resolution_rate
        )

    def print_incident_dashboard(self):
        """인시던트 대시보드 출력"""
        print("\n" + "=" * 80)
        print("📊 인시던트 관리 대시보드")
        print("=" * 80 + "\n")

        print("🚨 현재 활성 인시던트:")
        active = [i for i in self.incidents.values() if i.status not in ['resolved', 'closed']]

        if not active:
            print("   활성 인시던트 없음 ✅\n")
        else:
            print(f"{'ID':<15} {'심각도':<10} {'제목':<35} {'상태':<15}")
            print("-" * 75)

            for incident in active:
                print(f"{incident.id:<15} {incident.severity:<10} {incident.title:<35} {incident.status:<15}")

        print("\n📋 최근 인시던트:")
        recent = sorted(self.incident_history, key=lambda x: x.timestamp, reverse=True)[:5]

        if not recent:
            print("   기록 없음\n")
        else:
            print(f"{'ID':<15} {'제목':<35} {'지속시간':<12} {'심각도':<10}")
            print("-" * 75)

            for incident in recent:
                duration = f"{incident.actual_duration_minutes}분"
                print(f"{incident.id:<15} {incident.title:<35} {duration:<12} {incident.severity:<10}")

        # 통계
        stats = self.get_incident_stats()

        print("\n📈 통계:")
        print(f"   총 인시던트: {stats.total_incidents}개")
        print(f"   평균 MTTR: {stats.average_mttr_minutes:.1f}분")
        print(f"   해결율: {stats.resolution_rate:.1f}%\n")

        print("=" * 80 + "\n")

    def export_incident(self, incident_id: str, filename: str = None) -> Optional[str]:
        """인시던트 내보내기"""
        if incident_id not in self.incidents:
            return None

        incident = self.incidents[incident_id]

        if filename is None:
            filename = f"incident_{incident_id}.json"

        incident_data = {
            'id': incident.id,
            'timestamp': datetime.fromtimestamp(incident.timestamp).isoformat(),
            'severity': incident.severity,
            'title': incident.title,
            'description': incident.description,
            'status': incident.status,
            'affected_services': incident.affected_services,
            'affected_users': incident.affected_users,
            'impact_scope': incident.impact_scope,
            'root_cause': incident.root_cause,
            'resolution': incident.resolution,
            'actual_duration_minutes': incident.actual_duration_minutes,
            'estimated_mttr_minutes': incident.estimated_mttr_minutes,
            'remediation_actions': incident.remediation_actions,
            'timeline': self.get_incident_timeline(incident_id),
            'post_mortem': incident.post_mortem_notes,
            'follow_up_items': incident.follow_up_items
        }

        try:
            with open(filename, 'w') as f:
                json.dump(incident_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 인시던트 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = IncidentManager()

    if len(sys.argv) < 2:
        print("사용법: python incident_manager.py [command] [args]")
        print("  dashboard         - 인시던트 대시보드")
        print("  detect            - 인시던트 탐지")
        print("  workflow <id>     - 완전 인시던트 워크플로우")
        return

    command = sys.argv[1]

    if command == "dashboard":
        manager.print_incident_dashboard()

    elif command == "detect":
        metrics = {
            'error_rate': 0.15,
            'latency_ms': 850,
            'cpu_usage': 92,
            'memory_usage': 88,
            'service_status': 'up'
        }
        incidents = manager.detect_incidents(metrics)
        print(f"\n✅ {len(incidents)}개 인시던트 탐지됨")

    elif command == "workflow":
        incident_id = sys.argv[2] if len(sys.argv) > 2 else None

        if not incident_id:
            # 새로운 인시던트 생성
            metrics = {
                'error_rate': 0.12,
                'cpu_usage': 93,
                'latency_ms': 900
            }

            incidents = manager.detect_incidents(metrics)
            if incidents:
                incident_id = incidents[0].id

        if incident_id:
            manager.acknowledge_incident(incident_id)
            manager.start_investigation(incident_id)
            manager.diagnose_incident(incident_id)
            manager.execute_remediation(incident_id, "스케일 업 실행")
            time.sleep(1)
            manager.resolve_incident(incident_id, "자동 복구 성공")
            manager.conduct_postmortem(incident_id)
            manager.export_incident(incident_id)
