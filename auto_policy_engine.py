#!/usr/bin/env python3
"""
MindLang 자동 정책 엔진
학습 결과를 정책으로 자동 변환 및 적용

기능:
- 패턴 기반 정책 생성
- 신뢰도 기반 정책 우선순위
- 정책 충돌 해결
- 정책 효과 검증
- 자동 롤백
"""

import json
import time
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import statistics


class PolicyType(str, Enum):
    """정책 유형"""
    THRESHOLD = "threshold"          # 임계값 기반
    PATTERN = "pattern"              # 패턴 기반
    TIME_BASED = "time_based"        # 시간 기반
    CORRELATION = "correlation"      # 상관관계 기반
    LEARNED = "learned"              # 학습 기반


class PolicyStatus(str, Enum):
    """정책 상태"""
    DRAFT = "draft"                  # 작성 중
    ACTIVE = "active"                # 활성
    TESTING = "testing"              # 테스트 중
    DEPRECATED = "deprecated"        # 사용 중단
    ROLLBACK = "rollback"            # 롤백됨


@dataclass
class PolicyRule:
    """정책 규칙"""
    name: str
    condition: Dict                   # 조건 (예: {"cpu": ">85", "memory": ">78"})
    action: str                       # 실행 동작
    confidence: float                 # 신뢰도
    evidence_count: int              # 증거 수
    created_at: float = field(default_factory=time.time)


@dataclass
class Policy:
    """정책"""
    id: str
    name: str
    description: str
    policy_type: PolicyType
    rules: List[PolicyRule]
    status: PolicyStatus = PolicyStatus.DRAFT
    confidence: float = 0.0          # 전체 신뢰도
    priority: int = 5                 # 우선순위 (1-10)
    success_rate: float = 0.0        # 성공률
    application_count: int = 0        # 적용 횟수
    success_count: int = 0            # 성공 횟수
    created_at: float = field(default_factory=time.time)
    activated_at: Optional[float] = None
    last_applied_at: Optional[float] = None
    rollback_reason: Optional[str] = None


@dataclass
class PolicyApplication:
    """정책 적용 기록"""
    policy_id: str
    timestamp: float
    metrics: Dict
    result: str                       # SCALE_UP, CONTINUE, ROLLBACK 등
    success: bool
    feedback: Optional[str] = None


class AutoPolicyEngine:
    """자동 정책 엔진"""

    def __init__(self, policy_file: str = 'policies.json'):
        self.policy_file = policy_file
        self.policies: Dict[str, Policy] = {}
        self.applications: List[PolicyApplication] = []
        self.max_applications = 5000
        self.load_policies()

    def load_policies(self):
        """정책 로드"""
        try:
            with open(self.policy_file, 'r') as f:
                data = json.load(f)
                for policy_data in data.get('policies', []):
                    policy = Policy(
                        id=policy_data['id'],
                        name=policy_data['name'],
                        description=policy_data['description'],
                        policy_type=PolicyType(policy_data['policy_type']),
                        rules=[
                            PolicyRule(**rule) for rule in policy_data.get('rules', [])
                        ],
                        status=PolicyStatus(policy_data.get('status', 'draft')),
                        confidence=policy_data.get('confidence', 0.0),
                        priority=policy_data.get('priority', 5),
                        success_rate=policy_data.get('success_rate', 0.0),
                        application_count=policy_data.get('application_count', 0),
                        success_count=policy_data.get('success_count', 0)
                    )
                    self.policies[policy.id] = policy
        except FileNotFoundError:
            self.policies = {}

    def save_policies(self):
        """정책 저장"""
        data = {
            'timestamp': time.time(),
            'policies': [
                {
                    **asdict(policy),
                    'policy_type': policy.policy_type.value,
                    'status': policy.status.value,
                    'rules': [asdict(rule) for rule in policy.rules]
                }
                for policy in self.policies.values()
            ]
        }
        with open(self.policy_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_policy_from_pattern(
        self,
        pattern_name: str,
        pattern_description: str,
        condition: Dict,
        recommended_action: str,
        confidence: float,
        evidence_count: int
    ) -> Policy:
        """패턴으로부터 정책 생성"""
        policy_id = f"policy_{int(time.time())}_{hash(pattern_name) % 10000}"

        rule = PolicyRule(
            name=pattern_name,
            condition=condition,
            action=recommended_action,
            confidence=confidence,
            evidence_count=evidence_count
        )

        policy = Policy(
            id=policy_id,
            name=pattern_name,
            description=pattern_description,
            policy_type=PolicyType.PATTERN,
            rules=[rule],
            confidence=confidence,
            priority=self._calculate_priority(confidence),
            status=PolicyStatus.DRAFT
        )

        self.policies[policy_id] = policy
        self.save_policies()

        return policy

    def create_policy_from_threshold(
        self,
        metric_name: str,
        threshold_value: float,
        comparison: str,  # >, <, >=, <=, ==
        recommended_action: str,
        confidence: float,
        evidence_count: int
    ) -> Policy:
        """임계값 기반 정책 생성"""
        policy_id = f"policy_{int(time.time())}_{metric_name}"

        condition = {
            metric_name: f"{comparison}{threshold_value}"
        }

        rule = PolicyRule(
            name=f"{metric_name} {comparison} {threshold_value}",
            condition=condition,
            action=recommended_action,
            confidence=confidence,
            evidence_count=evidence_count
        )

        policy = Policy(
            id=policy_id,
            name=f"{metric_name} Threshold Policy",
            description=f"자동 생성: {metric_name}이 {comparison}{threshold_value}일 때 {recommended_action}",
            policy_type=PolicyType.THRESHOLD,
            rules=[rule],
            confidence=confidence,
            priority=self._calculate_priority(confidence),
            status=PolicyStatus.DRAFT
        )

        self.policies[policy_id] = policy
        self.save_policies()

        return policy

    def _calculate_priority(self, confidence: float) -> int:
        """신뢰도로부터 우선순위 계산"""
        if confidence >= 0.9:
            return 9
        elif confidence >= 0.8:
            return 8
        elif confidence >= 0.7:
            return 7
        elif confidence >= 0.6:
            return 6
        else:
            return 5

    def activate_policy(self, policy_id: str) -> bool:
        """정책 활성화"""
        if policy_id not in self.policies:
            return False

        policy = self.policies[policy_id]
        policy.status = PolicyStatus.ACTIVE
        policy.activated_at = time.time()
        self.save_policies()

        return True

    def deactivate_policy(self, policy_id: str) -> bool:
        """정책 비활성화"""
        if policy_id not in self.policies:
            return False

        policy = self.policies[policy_id]
        policy.status = PolicyStatus.DEPRECATED
        self.save_policies()

        return True

    def evaluate_policies(self, metrics: Dict) -> Tuple[Optional[str], Optional[str], float]:
        """메트릭에 대해 정책 평가"""
        active_policies = [
            p for p in self.policies.values()
            if p.status == PolicyStatus.ACTIVE
        ]

        # 우선순위로 정렬
        active_policies.sort(key=lambda p: p.priority, reverse=True)

        matches = []
        for policy in active_policies:
            for rule in policy.rules:
                if self._condition_matches(metrics, rule.condition):
                    matches.append((policy, rule))

        if matches:
            # 가장 높은 신뢰도 매칭 선택
            best_policy, best_rule = max(
                matches,
                key=lambda x: x[0].priority + x[1].confidence
            )
            return (best_rule.action, best_policy.id, best_rule.confidence)

        return (None, None, 0.0)

    def _condition_matches(self, metrics: Dict, condition: Dict) -> bool:
        """조건이 메트릭과 일치하는지 확인"""
        for metric_name, condition_str in condition.items():
            if metric_name not in metrics:
                return False

            metric_value = metrics[metric_name]

            # 조건 파싱 (예: ">85", ">=75", "<50")
            if condition_str.startswith(">="):
                threshold = float(condition_str[2:])
                if not (metric_value >= threshold):
                    return False
            elif condition_str.startswith(">"):
                threshold = float(condition_str[1:])
                if not (metric_value > threshold):
                    return False
            elif condition_str.startswith("<="):
                threshold = float(condition_str[2:])
                if not (metric_value <= threshold):
                    return False
            elif condition_str.startswith("<"):
                threshold = float(condition_str[1:])
                if not (metric_value < threshold):
                    return False
            elif condition_str.startswith("=="):
                threshold = float(condition_str[2:])
                if not (metric_value == threshold):
                    return False

        return True

    def record_application(
        self,
        policy_id: str,
        metrics: Dict,
        result: str,
        success: bool,
        feedback: Optional[str] = None
    ):
        """정책 적용 기록"""
        application = PolicyApplication(
            policy_id=policy_id,
            timestamp=time.time(),
            metrics=metrics,
            result=result,
            success=success,
            feedback=feedback
        )

        self.applications.append(application)
        if len(self.applications) > self.max_applications:
            self.applications.pop(0)

        # 정책 통계 업데이트
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            policy.application_count += 1
            if success:
                policy.success_count += 1
            policy.success_rate = (
                policy.success_count / policy.application_count
                if policy.application_count > 0 else 0
            )
            policy.last_applied_at = time.time()

            # 성공률이 50% 이하면 롤백
            if policy.application_count >= 10 and policy.success_rate < 0.5:
                policy.status = PolicyStatus.ROLLBACK
                policy.rollback_reason = f"낮은 성공률: {policy.success_rate:.1%}"

            self.save_policies()

    def get_policy_recommendations(self) -> Dict:
        """정책 권고사항"""
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'total_policies': len(self.policies),
            'active_policies': sum(
                1 for p in self.policies.values()
                if p.status == PolicyStatus.ACTIVE
            ),
            'policy_status': {},
            'recommendations': []
        }

        # 정책 상태 분석
        for policy in self.policies.values():
            status_key = policy.status.value
            if status_key not in recommendations['policy_status']:
                recommendations['policy_status'][status_key] = []

            recommendations['policy_status'][status_key].append({
                'id': policy.id,
                'name': policy.name,
                'success_rate': policy.success_rate,
                'priority': policy.priority,
                'confidence': policy.confidence
            })

        # 권고사항 생성
        high_success_policies = [
            p for p in self.policies.values()
            if p.status == PolicyStatus.TESTING and p.success_rate >= 0.8 and p.application_count >= 10
        ]
        if high_success_policies:
            for policy in high_success_policies:
                recommendations['recommendations'].append({
                    'type': '승격 권고',
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'reason': f'높은 성공률 ({policy.success_rate:.1%})'
                })

        low_success_policies = [
            p for p in self.policies.values()
            if p.status == PolicyStatus.ACTIVE and p.success_rate < 0.5 and p.application_count >= 10
        ]
        if low_success_policies:
            for policy in low_success_policies:
                recommendations['recommendations'].append({
                    'type': '롤백 권고',
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'reason': f'낮은 성공률 ({policy.success_rate:.1%})'
                })

        inactive_policies = [
            p for p in self.policies.values()
            if p.status == PolicyStatus.DRAFT and p.confidence >= 0.7
        ]
        if inactive_policies:
            for policy in inactive_policies:
                recommendations['recommendations'].append({
                    'type': '활성화 권고',
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'reason': f'높은 신뢰도 ({policy.confidence:.1%})'
                })

        return recommendations

    def get_conflicting_policies(self) -> List[Tuple[Policy, Policy]]:
        """충돌하는 정책 찾기"""
        conflicts = []

        active_policies = [
            p for p in self.policies.values()
            if p.status == PolicyStatus.ACTIVE
        ]

        for i, policy1 in enumerate(active_policies):
            for policy2 in active_policies[i+1:]:
                # 같은 조건에 다른 액션이 있는지 확인
                for rule1 in policy1.rules:
                    for rule2 in policy2.rules:
                        if rule1.condition == rule2.condition and rule1.action != rule2.action:
                            conflicts.append((policy1, policy2))

        return conflicts

    def get_policy_statistics(self) -> Dict:
        """정책 통계"""
        stats = {
            'total_policies': len(self.policies),
            'by_type': {},
            'by_status': {},
            'avg_confidence': 0.0,
            'avg_success_rate': 0.0,
            'total_applications': len(self.applications),
            'success_rate_overall': 0.0
        }

        # 유형별 통계
        for policy in self.policies.values():
            type_key = policy.policy_type.value
            if type_key not in stats['by_type']:
                stats['by_type'][type_key] = 0
            stats['by_type'][type_key] += 1

            status_key = policy.status.value
            if status_key not in stats['by_status']:
                stats['by_status'][status_key] = 0
            stats['by_status'][status_key] += 1

        # 평균 신뢰도
        confidences = [p.confidence for p in self.policies.values()]
        if confidences:
            stats['avg_confidence'] = statistics.mean(confidences)

        # 평균 성공률
        success_rates = [p.success_rate for p in self.policies.values() if p.application_count > 0]
        if success_rates:
            stats['avg_success_rate'] = statistics.mean(success_rates)

        # 전체 성공률
        if self.applications:
            successful = sum(1 for app in self.applications if app.success)
            stats['success_rate_overall'] = successful / len(self.applications)

        return stats


# 사용 예시
if __name__ == "__main__":
    engine = AutoPolicyEngine()

    # 패턴 기반 정책 생성
    policy1 = engine.create_policy_from_pattern(
        pattern_name="High CPU → Scale Up",
        pattern_description="CPU 사용률이 85% 이상일 때는 SCALE_UP이 최적",
        condition={"cpu_usage": ">85"},
        recommended_action="SCALE_UP",
        confidence=0.87,
        evidence_count=42
    )

    # 임계값 기반 정책 생성
    policy2 = engine.create_policy_from_threshold(
        metric_name="error_rate",
        threshold_value=0.05,
        comparison=">",
        recommended_action="ROLLBACK",
        confidence=0.92,
        evidence_count=35
    )

    # 정책 활성화
    engine.activate_policy(policy1.id)
    engine.activate_policy(policy2.id)

    # 메트릭으로 정책 평가
    metrics = {
        'cpu_usage': 88,
        'memory_usage': 70,
        'error_rate': 0.02
    }

    action, policy_id, confidence = engine.evaluate_policies(metrics)
    print(f"\n평가 결과:")
    print(f"추천 동작: {action}")
    print(f"정책 ID: {policy_id}")
    print(f"신뢰도: {confidence:.1%}")

    # 적용 기록
    if policy_id:
        engine.record_application(
            policy_id=policy_id,
            metrics=metrics,
            result=action,
            success=True,
            feedback="CPU 빠르게 정상화됨"
        )

    # 권고사항
    print("\n정책 권고사항:")
    recommendations = engine.get_policy_recommendations()
    for rec in recommendations.get('recommendations', []):
        print(f"  {rec['type']}: {rec['policy_name']} - {rec['reason']}")

    # 통계
    print("\n정책 통계:")
    stats = engine.get_policy_statistics()
    print(f"  총 정책: {stats['total_policies']}")
    print(f"  평균 신뢰도: {stats['avg_confidence']:.1%}")
    print(f"  전체 성공률: {stats['success_rate_overall']:.1%}")
