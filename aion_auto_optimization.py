#!/usr/bin/env python3
"""
AION: Autonomous Infrastructure Optimization Network
자동 인프라 최적화 네트워크 (3단계)

Phase 1: 의사결정 (MindLang 4경로)
Phase 2: 원인분석 (Before/After 속성)
Phase 3: 정책조정 (학습 및 피드백)

철학: "한 번의 배포로 끝나지 않는다. 계속 배운다."
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class AIONPhase(Enum):
    """AION 단계"""
    PHASE1_DECISION = "phase1_decision"
    PHASE2_ANALYSIS = "phase2_analysis"
    PHASE3_ADJUSTMENT = "phase3_adjustment"


class MetricType(Enum):
    """메트릭 타입"""
    CPU = "cpu"
    MEMORY = "memory"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    COST = "cost"


@dataclass
class Metrics:
    """시스템 메트릭"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    latency_p95: float
    error_rate: float
    throughput: int
    cost_per_hour: float

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'latency_p95': self.latency_p95,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'cost_per_hour': self.cost_per_hour
        }


@dataclass
class Action:
    """실행한 액션"""
    action_type: str  # SCALE_UP, SCALE_DOWN, ROLLBACK, etc
    timestamp: float
    parameters: Dict = field(default_factory=dict)
    reason: str = ""


@dataclass
class Phase2Analysis:
    """Phase 2: 원인분석"""
    before_metrics: Metrics
    after_metrics: Metrics
    action_taken: Action
    attribution: Dict[str, float]  # 각 메트릭별 개선도
    confidence: float
    analysis_time: float = 0.0

    def __str__(self) -> str:
        return (
            f"📊 Phase 2 원인분석\n"
            f"  액션: {self.action_taken.action_type}\n"
            f"  CPU: {self.before_metrics.cpu_usage:.1f}% → "
            f"{self.after_metrics.cpu_usage:.1f}% "
            f"({self.attribution.get('cpu', 0)*100:.1f}% 개선)\n"
            f"  메모리: {self.before_metrics.memory_usage:.1f}% → "
            f"{self.after_metrics.memory_usage:.1f}% "
            f"({self.attribution.get('memory', 0)*100:.1f}% 개선)\n"
            f"  지연: {self.before_metrics.latency_p95:.0f}ms → "
            f"{self.after_metrics.latency_p95:.0f}ms "
            f"({self.attribution.get('latency', 0)*100:.1f}% 개선)\n"
            f"  신뢰도: {self.confidence*100:.0f}%"
        )


@dataclass
class AIONPolicy:
    """최적화 정책"""
    policy_id: str
    name: str
    description: str
    conditions: List[str]
    action: Action
    success_rate: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    last_applied: Optional[float] = None

    def update_success(self):
        """성공 기록"""
        self.success_count += 1
        self.success_rate = self.success_count / (self.success_count + self.failure_count)
        self.last_applied = time.time()

    def update_failure(self):
        """실패 기록"""
        self.failure_count += 1
        self.success_rate = self.success_count / (self.success_count + self.failure_count)


class AION:
    """자동 인프라 최적화 네트워크"""

    def __init__(self, mindlang_analyzer):
        """
        Args:
            mindlang_analyzer: MindLang 4경로 추론 객체
        """
        self.mindlang = mindlang_analyzer
        self.policies: Dict[str, AIONPolicy] = {}
        self.analysis_history: List[Phase2Analysis] = []
        self.decision_history: List[Dict] = []
        self.current_phase = AIONPhase.PHASE1_DECISION

    def execute_cycle(self,
                     current_metrics: Metrics,
                     previous_metrics: Optional[Metrics] = None) -> Dict:
        """
        AION 전체 사이클 실행

        Returns:
            {
                'phase1_decision': {...},
                'phase2_analysis': {...},
                'phase3_adjustment': {...}
            }
        """
        print(f"\n🔄 AION 사이클 시작 ({datetime.now().isoformat()})")
        print("=" * 70)

        # Phase 1: 의사결정
        phase1_result = self._phase1_decision(current_metrics)

        # Phase 2: 원인분석 (이전 메트릭이 있을 경우)
        phase2_result = None
        if previous_metrics:
            phase2_result = self._phase2_analysis(
                previous_metrics,
                current_metrics,
                phase1_result.get('action')
            )

        # Phase 3: 정책조정
        phase3_result = self._phase3_adjustment(phase2_result)

        result = {
            'phase1_decision': phase1_result,
            'phase2_analysis': phase2_result,
            'phase3_adjustment': phase3_result,
            'timestamp': time.time()
        }

        self.decision_history.append(result)
        return result

    def _phase1_decision(self, metrics: Metrics) -> Dict:
        """Phase 1: MindLang을 통한 의사결정"""
        print("\n📍 Phase 1: 의사결정 (4경로 추론)")
        print("-" * 70)

        # MindLang 4경로 분석
        metrics_dict = {
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage,
            'latency_p95': metrics.latency_p95,
            'error_rate': metrics.error_rate,
            'throughput': metrics.throughput
        }

        decision = self.mindlang.analyze(metrics_dict)

        action_obj = Action(
            action_type=decision['primary_decision'],
            timestamp=metrics.timestamp,
            reason=decision.get('reasoning', '')
        )

        print(f"  🎯 최종 의사결정: {decision['primary_decision']}")
        print(f"  📊 신뢰도: {decision['confidence']*100:.1f}%")
        print(f"  🤖 Red Team 의견: {decision['red_team_analysis']['counter_recommendation']}")

        return {
            'decision': decision['primary_decision'],
            'confidence': decision['confidence'],
            'reasoning': decision.get('reasoning', ''),
            'red_team_analysis': decision['red_team_analysis'],
            'action': action_obj
        }

    def _phase2_analysis(self,
                        before_metrics: Metrics,
                        after_metrics: Metrics,
                        action: Action) -> Phase2Analysis:
        """Phase 2: 원인분석"""
        print("\n📍 Phase 2: 원인분석")
        print("-" * 70)

        # Before/After 비교
        attribution = self._calculate_attribution(before_metrics, after_metrics)

        # 신뢰도 계산
        confidence = self._calculate_analysis_confidence(attribution)

        analysis = Phase2Analysis(
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            action_taken=action,
            attribution=attribution,
            confidence=confidence,
            analysis_time=time.time()
        )

        print(analysis)

        self.analysis_history.append(analysis)
        return analysis

    def _phase3_adjustment(self, phase2_analysis: Optional[Phase2Analysis]) -> Dict:
        """Phase 3: 정책조정"""
        print("\n📍 Phase 3: 정책조정")
        print("-" * 70)

        if not phase2_analysis:
            print("  (이전 데이터 없음 - 정책 조정 스킵)")
            return {'status': 'skipped', 'reason': 'no_previous_data'}

        action_type = phase2_analysis.action_taken.action_type

        # 기존 정책 업데이트
        if action_type in self.policies:
            policy = self.policies[action_type]
            if phase2_analysis.confidence > 0.7:
                policy.update_success()
                print(f"  ✅ '{policy.name}' 정책 성공 (신뢰도: {phase2_analysis.confidence*100:.0f}%)")
            else:
                policy.update_failure()
                print(f"  ❌ '{policy.name}' 정책 실패 (신뢰도: {phase2_analysis.confidence*100:.0f}%)")
        else:
            # 새 정책 생성
            self._create_new_policy(action_type, phase2_analysis)

        # 정책 최적화
        self._optimize_policies()

        return {
            'status': 'completed',
            'policies_updated': len(self.policies),
            'total_success_rate': self._calculate_overall_success_rate()
        }

    def _calculate_attribution(self,
                              before: Metrics,
                              after: Metrics) -> Dict[str, float]:
        """Before/After로부터 개선도 계산"""
        attribution = {}

        # CPU 개선도
        if before.cpu_usage > 0:
            cpu_improvement = (before.cpu_usage - after.cpu_usage) / before.cpu_usage
            attribution['cpu'] = max(0, cpu_improvement)

        # 메모리 개선도
        if before.memory_usage > 0:
            mem_improvement = (before.memory_usage - after.memory_usage) / before.memory_usage
            attribution['memory'] = max(0, mem_improvement)

        # 지연 개선도
        if before.latency_p95 > 0:
            latency_improvement = (before.latency_p95 - after.latency_p95) / before.latency_p95
            attribution['latency'] = max(0, latency_improvement)

        # 에러율 개선도
        if before.error_rate > 0:
            error_improvement = (before.error_rate - after.error_rate) / before.error_rate
            attribution['error_rate'] = max(0, error_improvement)

        return attribution

    def _calculate_analysis_confidence(self, attribution: Dict[str, float]) -> float:
        """분석 신뢰도 계산"""
        if not attribution:
            return 0.0

        # 개선된 메트릭이 많을수록 신뢰도 증가
        improved_count = sum(1 for v in attribution.values() if v > 0)
        avg_improvement = sum(attribution.values()) / len(attribution)

        confidence = (improved_count / len(attribution)) * 0.5 + avg_improvement * 0.5
        return min(0.99, max(0.0, confidence))

    def _create_new_policy(self, action_type: str, analysis: Phase2Analysis):
        """새 정책 생성"""
        policy = AIONPolicy(
            policy_id=f"policy_{len(self.policies)}",
            name=f"{action_type} 정책",
            description=f"{action_type} 자동화 정책",
            conditions=[f"confidence > {analysis.confidence*100:.0f}%"],
            action=analysis.action_taken,
            success_count=1 if analysis.confidence > 0.7 else 0,
            failure_count=0 if analysis.confidence > 0.7 else 1
        )
        self.policies[action_type] = policy
        print(f"  🆕 새 정책 생성: {policy.name}")

    def _optimize_policies(self):
        """정책 최적화"""
        for policy_id, policy in self.policies.items():
            # 성공률이 낮은 정책은 주의
            if policy.success_rate < 0.5 and policy.success_count + policy.failure_count > 5:
                print(f"  ⚠️  '{policy.name}' 성공률 낮음 ({policy.success_rate*100:.0f}%) - 재검토 권장")

    def _calculate_overall_success_rate(self) -> float:
        """전체 성공률"""
        if not self.policies:
            return 0.0

        total_success = sum(p.success_count for p in self.policies.values())
        total_attempts = sum(p.success_count + p.failure_count for p in self.policies.values())

        if total_attempts == 0:
            return 0.0

        return total_success / total_attempts

    def get_report(self) -> Dict:
        """AION 리포트"""
        return {
            'total_cycles': len(self.decision_history),
            'policies': {
                policy_id: {
                    'name': policy.name,
                    'success_rate': f"{policy.success_rate*100:.1f}%",
                    'successes': policy.success_count,
                    'failures': policy.failure_count,
                    'last_applied': datetime.fromtimestamp(policy.last_applied).isoformat()
                    if policy.last_applied else 'never'
                }
                for policy_id, policy in self.policies.items()
            },
            'overall_success_rate': f"{self._calculate_overall_success_rate()*100:.1f}%",
            'analyses': len(self.analysis_history)
        }


# 사용 예시
if __name__ == "__main__":
    from mindlang_with_red_team import MindLangRedTeam

    # MindLang 초기화
    mindlang = MindLangRedTeam()

    # AION 초기화
    aion = AION(mindlang)

    # 테스트 메트릭
    before = Metrics(
        timestamp=time.time(),
        cpu_usage=85.0,
        memory_usage=78.0,
        latency_p95=450.0,
        error_rate=0.025,
        throughput=10000,
        cost_per_hour=50.0
    )

    after = Metrics(
        timestamp=time.time() + 3600,
        cpu_usage=45.0,
        memory_usage=50.0,
        latency_p95=250.0,
        error_rate=0.005,
        throughput=15000,
        cost_per_hour=75.0  # 성능 향상으로 인한 비용 증가
    )

    # 사이클 실행
    result = aion.execute_cycle(before)
    print("\n" + "=" * 70)

    # 2번째 사이클 (이전 데이터 포함)
    result = aion.execute_cycle(after, before)
    print("\n" + "=" * 70)

    # 리포트
    print("\n📋 AION 리포트")
    import json
    print(json.dumps(aion.get_report(), indent=2, ensure_ascii=False))
