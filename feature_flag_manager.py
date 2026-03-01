#!/usr/bin/env python3
"""
MindLang 기능 플래그 관리 시스템
A/B 테스트, 기능 토글, 카나리 배포를 위한 통합 플래그 관리

기능:
- 기능 플래그 정의 및 관리
- 대상 기반 활성화 (사용자, 그룹, 지역)
- A/B 테스트 지원
- 카나리 배포 관리
- 실시간 토글
- 분석 및 보고
"""

import json
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class FlagType(Enum):
    """플래그 타입"""
    FEATURE = "feature"  # 새로운 기능
    EXPERIMENT = "experiment"  # A/B 테스트
    CANARY = "canary"  # 카나리 배포
    KILL_SWITCH = "kill_switch"  # 긴급 중지
    CONFIG = "config"  # 설정 플래그


class RolloutStrategy(Enum):
    """롤아웃 전략"""
    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    GROUP = "group"
    GEOGRAPHIC = "geographic"
    TIME_BASED = "time_based"


@dataclass
class TargetingRule:
    """대상 규칙"""
    rule_id: str
    rule_type: str  # user_id, group, country, region
    values: List[str]  # 규칙에 해당하는 값들
    enabled: bool = True


@dataclass
class FeatureFlag:
    """기능 플래그"""
    flag_id: str
    name: str
    description: str
    flag_type: str
    enabled: bool = False
    rollout_percentage: float = 0.0  # 0-100
    rollout_strategy: str = RolloutStrategy.ALL_USERS.value
    targeting_rules: List[TargetingRule] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class FlagEvaluation:
    """플래그 평가 결과"""
    flag_id: str
    user_id: str
    enabled: bool
    evaluated_at: float
    matched_rule: Optional[str] = None
    reason: str = ""


@dataclass
class ExperimentVariant:
    """A/B 테스트 변형"""
    variant_id: str
    name: str
    description: str
    traffic_allocation: float  # 0-100
    metrics: Dict = field(default_factory=dict)


class FeatureFlagManager:
    """기능 플래그 관리자"""

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self.evaluations: List[FlagEvaluation] = []
        self.experiments: Dict[str, List[ExperimentVariant]] = {}
        self.user_cache: Dict[str, Dict] = {}
        self._initialize_default_flags()

    def _initialize_default_flags(self):
        """기본 플래그 초기화"""
        print("🚩 기능 플래그 시스템 초기화\n")

        flags = [
            FeatureFlag(
                flag_id="new_dashboard",
                name="새로운 대시보드",
                description="개선된 UI의 새로운 대시보드",
                flag_type=FlagType.FEATURE.value,
                enabled=True,
                rollout_percentage=50.0,
                rollout_strategy=RolloutStrategy.PERCENTAGE.value,
                created_at=time.time(),
                updated_at=time.time(),
                owner="ui_team",
                tags=["ui", "v2", "beta"]
            ),
            FeatureFlag(
                flag_id="ai_recommendations",
                name="AI 추천 기능",
                description="머신러닝 기반 추천",
                flag_type=FlagType.EXPERIMENT.value,
                enabled=True,
                rollout_percentage=25.0,
                rollout_strategy=RolloutStrategy.PERCENTAGE.value,
                created_at=time.time(),
                updated_at=time.time(),
                owner="ml_team",
                tags=["ai", "ml", "experiment"]
            ),
            FeatureFlag(
                flag_id="v3_api",
                name="API v3",
                description="v3 API 베타 버전",
                flag_type=FlagType.CANARY.value,
                enabled=True,
                rollout_percentage=5.0,
                rollout_strategy=RolloutStrategy.CANARY.value,
                created_at=time.time(),
                updated_at=time.time(),
                owner="api_team",
                tags=["api", "canary"]
            ),
            FeatureFlag(
                flag_id="legacy_api_shutdown",
                name="레거시 API 종료",
                description="구형 API 비활성화",
                flag_type=FlagType.KILL_SWITCH.value,
                enabled=False,
                created_at=time.time(),
                updated_at=time.time(),
                owner="backend_team",
                tags=["deprecation", "migration"]
            )
        ]

        for flag in flags:
            self.flags[flag.flag_id] = flag

        print("✅ 4개의 기능 플래그 초기화 완료")
        for flag in flags:
            status = "✅" if flag.enabled else "⭕"
            print(f"   {status} {flag.name} ({flag.rollout_percentage}% 롤아웃)")

        print()

    def create_flag(
        self,
        flag_id: str,
        name: str,
        description: str,
        flag_type: str,
        owner: str = "platform_team"
    ) -> FeatureFlag:
        """플래그 생성"""
        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description=description,
            flag_type=flag_type,
            created_at=time.time(),
            updated_at=time.time(),
            owner=owner
        )

        self.flags[flag_id] = flag
        print(f"✅ 플래그 생성: {flag_id}")

        return flag

    def enable_flag(self, flag_id: str, percentage: float = 100.0):
        """플래그 활성화"""
        if flag_id not in self.flags:
            print(f"❌ 플래그를 찾을 수 없음: {flag_id}")
            return

        flag = self.flags[flag_id]
        flag.enabled = True
        flag.rollout_percentage = percentage
        flag.updated_at = time.time()

        print(f"✅ 플래그 활성화: {flag_id} ({percentage}% 롤아웃)")

    def disable_flag(self, flag_id: str):
        """플래그 비활성화"""
        if flag_id not in self.flags:
            return

        flag = self.flags[flag_id]
        flag.enabled = False
        flag.updated_at = time.time()

        print(f"⭕ 플래그 비활성화: {flag_id}")

    def add_targeting_rule(self, flag_id: str, rule_type: str, values: List[str]):
        """대상 규칙 추가"""
        if flag_id not in self.flags:
            return

        flag = self.flags[flag_id]
        rule = TargetingRule(
            rule_id=f"rule_{int(time.time())}",
            rule_type=rule_type,
            values=values,
            enabled=True
        )

        flag.targeting_rules.append(rule)
        print(f"✅ 대상 규칙 추가: {flag_id} - {rule_type}")

    def evaluate_flag(self, flag_id: str, user_id: str, context: Dict = None) -> FlagEvaluation:
        """플래그 평가"""
        if flag_id not in self.flags:
            return FlagEvaluation(
                flag_id=flag_id,
                user_id=user_id,
                enabled=False,
                evaluated_at=time.time(),
                reason="플래그를 찾을 수 없음"
            )

        flag = self.flags[flag_id]
        context = context or {}

        # 플래그가 비활성화되어 있으면 false
        if not flag.enabled:
            return FlagEvaluation(
                flag_id=flag_id,
                user_id=user_id,
                enabled=False,
                evaluated_at=time.time(),
                reason="플래그가 비활성화됨"
            )

        # 대상 규칙 확인
        for rule in flag.targeting_rules:
            if not rule.enabled:
                continue

            if rule.rule_type == "user_id" and user_id in rule.values:
                return FlagEvaluation(
                    flag_id=flag_id,
                    user_id=user_id,
                    enabled=True,
                    evaluated_at=time.time(),
                    matched_rule=rule.rule_id,
                    reason="사용자 규칙 매칭"
                )

            if rule.rule_type == "group" and context.get("group") in rule.values:
                return FlagEvaluation(
                    flag_id=flag_id,
                    user_id=user_id,
                    enabled=True,
                    evaluated_at=time.time(),
                    matched_rule=rule.rule_id,
                    reason="그룹 규칙 매칭"
                )

            if rule.rule_type == "country" and context.get("country") in rule.values:
                return FlagEvaluation(
                    flag_id=flag_id,
                    user_id=user_id,
                    enabled=True,
                    evaluated_at=time.time(),
                    matched_rule=rule.rule_id,
                    reason="지역 규칙 매칭"
                )

        # 롤아웃 비율 확인
        if flag.rollout_percentage > 0:
            # 사용자 ID 해시 기반 결정 (일관성 유지)
            user_hash = hash(f"{flag_id}:{user_id}") % 100
            if user_hash < flag.rollout_percentage:
                return FlagEvaluation(
                    flag_id=flag_id,
                    user_id=user_id,
                    enabled=True,
                    evaluated_at=time.time(),
                    reason=f"롤아웃 비율 {flag.rollout_percentage}%"
                )

        return FlagEvaluation(
            flag_id=flag_id,
            user_id=user_id,
            enabled=False,
            evaluated_at=time.time(),
            reason="어떤 조건도 매칭되지 않음"
        )

    def setup_experiment(
        self,
        flag_id: str,
        variant_a: str,
        variant_b: str,
        traffic_split: float = 50.0
    ):
        """A/B 테스트 설정"""
        if flag_id not in self.flags:
            print(f"❌ 플래그를 찾을 수 없음: {flag_id}")
            return

        flag = self.flags[flag_id]
        flag.flag_type = FlagType.EXPERIMENT.value

        variants = [
            ExperimentVariant(
                variant_id=f"var_a_{flag_id}",
                name=variant_a,
                description=f"{variant_a} 변형",
                traffic_allocation=traffic_split
            ),
            ExperimentVariant(
                variant_id=f"var_b_{flag_id}",
                name=variant_b,
                description=f"{variant_b} 변형",
                traffic_allocation=100 - traffic_split
            )
        ]

        self.experiments[flag_id] = variants

        print(f"✅ 실험 설정: {flag_id}")
        print(f"   변형 A: {variant_a} ({traffic_split}%)")
        print(f"   변형 B: {variant_b} ({100 - traffic_split}%)")

    def get_variant(self, flag_id: str, user_id: str) -> Optional[str]:
        """사용자의 실험 변형 반환"""
        if flag_id not in self.experiments:
            return None

        variants = self.experiments[flag_id]
        user_hash = hash(f"{flag_id}:{user_id}") % 100

        cumulative = 0
        for variant in variants:
            cumulative += variant.traffic_allocation
            if user_hash < cumulative:
                return variant.name

        return variants[-1].name

    def track_event(self, flag_id: str, event_type: str, user_id: str = None, value: float = 1.0):
        """이벤트 추적"""
        if flag_id not in self.experiments:
            return

        variants = self.experiments[flag_id]
        for variant in variants:
            if event_type not in variant.metrics:
                variant.metrics[event_type] = {
                    'count': 0,
                    'sum': 0,
                    'avg': 0
                }

            variant.metrics[event_type]['count'] += 1
            variant.metrics[event_type]['sum'] += value
            variant.metrics[event_type]['avg'] = variant.metrics[event_type]['sum'] / variant.metrics[event_type]['count']

    def get_experiment_results(self, flag_id: str) -> Dict:
        """실험 결과 조회"""
        if flag_id not in self.experiments:
            return {}

        variants = self.experiments[flag_id]
        results = {
            'flag_id': flag_id,
            'variants': []
        }

        for variant in variants:
            variant_result = {
                'name': variant.name,
                'traffic_allocation': variant.traffic_allocation,
                'metrics': variant.metrics
            }
            results['variants'].append(variant_result)

        return results

    def gradual_rollout(self, flag_id: str, target_percentage: float, step_size: float = 10.0):
        """단계적 롤아웃"""
        if flag_id not in self.flags:
            print(f"❌ 플래그를 찾을 수 없음: {flag_id}")
            return

        flag = self.flags[flag_id]

        print(f"\n📈 단계적 롤아웃: {flag_id}")
        print(f"   목표: {target_percentage}% (단계: {step_size}%)\n")

        current = flag.rollout_percentage

        while current < target_percentage:
            next_step = min(current + step_size, target_percentage)
            flag.rollout_percentage = next_step
            flag.updated_at = time.time()

            print(f"   {current:.0f}% → {next_step:.0f}% ✅")
            time.sleep(0.1)
            current = next_step

        print(f"\n✅ 롤아웃 완료: {target_percentage}%\n")

    def print_flags_dashboard(self):
        """플래그 대시보드 출력"""
        print("\n" + "=" * 80)
        print("🚩 기능 플래그 대시보드")
        print("=" * 80 + "\n")

        print(f"{'플래그':<25} {'타입':<15} {'상태':<10} {'롤아웃':<10} {'규칙':<5}")
        print("-" * 70)

        for flag_id, flag in self.flags.items():
            status = "✅ ON" if flag.enabled else "⭕ OFF"
            rollout = f"{flag.rollout_percentage:.0f}%" if flag.enabled else "N/A"
            rules = len(flag.targeting_rules)

            print(f"{flag.name:<25} {flag.flag_type:<15} {status:<10} {rollout:<10} {rules:<5}")

        print("\n" + "=" * 80 + "\n")

    def get_flag_stats(self) -> Dict:
        """플래그 통계"""
        total_flags = len(self.flags)
        enabled_flags = sum(1 for f in self.flags.values() if f.enabled)
        experiments = len(self.experiments)
        evaluations = len(self.evaluations)

        return {
            'total_flags': total_flags,
            'enabled_flags': enabled_flags,
            'disabled_flags': total_flags - enabled_flags,
            'active_experiments': experiments,
            'total_evaluations': evaluations
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_flag_stats()

        print("\n" + "=" * 70)
        print("📊 기능 플래그 시스템 통계")
        print("=" * 70 + "\n")

        print(f"총 플래그: {stats['total_flags']}개")
        print(f"활성: {stats['enabled_flags']}개")
        print(f"비활성: {stats['disabled_flags']}개")
        print(f"활성 실험: {stats['active_experiments']}개")
        print(f"총 평가: {stats['total_evaluations']}회\n")

        print("=" * 70 + "\n")

    def export_flags(self, filename: str = None) -> Optional[str]:
        """플래그 설정 내보내기"""
        if filename is None:
            filename = f"feature_flags_{int(time.time())}.json"

        flags_data = {
            'timestamp': datetime.now().isoformat(),
            'flags': [
                {
                    'id': flag.flag_id,
                    'name': flag.name,
                    'type': flag.flag_type,
                    'enabled': flag.enabled,
                    'rollout_percentage': flag.rollout_percentage,
                    'rules': len(flag.targeting_rules)
                }
                for flag in self.flags.values()
            ],
            'experiments': len(self.experiments)
        }

        try:
            with open(filename, 'w') as f:
                json.dump(flags_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 플래그 설정 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = FeatureFlagManager()

    if len(sys.argv) < 2:
        print("사용법: python feature_flag_manager.py [command] [args]")
        print("  dashboard           - 플래그 대시보드")
        print("  enable <flag_id>    - 플래그 활성화")
        print("  disable <flag_id>   - 플래그 비활성화")
        print("  evaluate <flag_id> <user_id> - 플래그 평가")
        print("  experiment          - A/B 테스트 설정")
        print("  stats               - 통계")
        return

    command = sys.argv[1]

    if command == "dashboard":
        manager.print_flags_dashboard()

    elif command == "enable":
        flag_id = sys.argv[2] if len(sys.argv) > 2 else "new_dashboard"
        percentage = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
        manager.enable_flag(flag_id, percentage)

    elif command == "disable":
        flag_id = sys.argv[2] if len(sys.argv) > 2 else "new_dashboard"
        manager.disable_flag(flag_id)

    elif command == "evaluate":
        flag_id = sys.argv[2] if len(sys.argv) > 2 else "new_dashboard"
        user_id = sys.argv[3] if len(sys.argv) > 3 else "user123"

        result = manager.evaluate_flag(flag_id, user_id)
        print(f"\n🎯 플래그 평가: {flag_id}")
        print(f"   사용자: {user_id}")
        print(f"   활성: {result.enabled}")
        print(f"   이유: {result.reason}\n")

    elif command == "experiment":
        manager.setup_experiment("ai_recommendations", "A/B 테스트 V1", "A/B 테스트 V2", 50.0)

    elif command == "stats":
        manager.print_stats()
