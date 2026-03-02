#!/usr/bin/env python3
"""
MindLang A/B 테스팅 프레임워크
Day 9: 통계 기반 성능 비교

구조:
├─ ExperimentRunner (실험 실행)
├─ MetricsCollector (메트릭 수집)
├─ StatisticalTest (통계 검정)
└─ ResultAnalyzer (결과 분석)

목표:
├─ A/B 테스트: p-value < 0.05
├─ 샘플 크기: 1000+ 요청
├─ 신뢰도: 95%
└─ 테스트: 통계적으로 유의미한 결과
"""

import time
import math
import random
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroupType(Enum):
    """그룹 타입"""
    CONTROL = "Control"  # 기존 방식
    TREATMENT = "Treatment"  # 새로운 방식


@dataclass
class MetricValue:
    """메트릭 데이터"""
    group: GroupType
    metric_name: str
    value: float
    timestamp: float


class MetricsCollector:
    """메트릭 수집"""

    def __init__(self):
        """메트릭 수집 초기화"""
        self.metrics: Dict[GroupType, List[Dict[str, float]]] = {
            GroupType.CONTROL: [],
            GroupType.TREATMENT: []
        }
        self.group_stats = {
            GroupType.CONTROL: defaultdict(list),
            GroupType.TREATMENT: defaultdict(list)
        }

    def record_metric(self, group: GroupType, metrics: Dict[str, float]) -> None:
        """메트릭 기록"""
        self.metrics[group].append(metrics)

        # 메트릭별 통계 추적
        for metric_name, value in metrics.items():
            self.group_stats[group][metric_name].append(value)

    def get_group_statistics(self, group: GroupType, metric_name: str) -> Dict[str, float]:
        """그룹 통계 계산"""
        values = self.group_stats[group].get(metric_name, [])

        if not values:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'count': 0}

        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n if n > 0 else 0
        std = math.sqrt(variance)

        return {
            'mean': mean,
            'std': std,
            'min': min(values),
            'max': max(values),
            'count': n,
            'sum': sum(values)
        }

    def get_all_metrics(self) -> Dict[GroupType, Dict[str, Any]]:
        """모든 메트릭 반환"""
        result = {}
        for group in [GroupType.CONTROL, GroupType.TREATMENT]:
            result[group] = {}
            for metric_name in self.group_stats[group]:
                result[group][metric_name] = self.get_group_statistics(group, metric_name)
        return result


class StatisticalTest:
    """통계 검정"""

    @staticmethod
    def independent_t_test(group1_values: List[float], group2_values: List[float]) -> Tuple[float, float]:
        """독립 표본 t-검정 (Independent Samples T-Test)

        반환: (t-statistic, p-value)
        """
        n1, n2 = len(group1_values), len(group2_values)

        if n1 < 2 or n2 < 2:
            return 0.0, 1.0

        mean1 = sum(group1_values) / n1
        mean2 = sum(group2_values) / n2

        var1 = sum((x - mean1) ** 2 for x in group1_values) / (n1 - 1) if n1 > 1 else 0
        var2 = sum((x - mean2) ** 2 for x in group2_values) / (n2 - 1) if n2 > 1 else 0

        # 합동 표준오차 (Pooled Standard Error)
        if n1 + n2 - 2 > 0:
            pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
            se = math.sqrt(pooled_var * (1 / n1 + 1 / n2)) if pooled_var > 0 else 0
        else:
            se = 0

        # t-통계량
        if se > 0:
            t_stat = (mean1 - mean2) / se
        else:
            t_stat = 0

        # p-값 근사 (양측 검정)
        # 간단한 근사: |t| > 1.96 → p < 0.05
        if abs(t_stat) > 2.576:  # p < 0.01
            p_value = 0.01
        elif abs(t_stat) > 1.96:  # p < 0.05
            p_value = 0.05
        elif abs(t_stat) > 1.645:  # p < 0.10
            p_value = 0.10
        else:
            p_value = 0.5

        return t_stat, p_value

    @staticmethod
    def chi_square_test(control_success: int, control_total: int,
                       treatment_success: int, treatment_total: int) -> Tuple[float, float]:
        """카이제곱 검정 (Chi-Square Test)

        반환: (chi2-statistic, p-value)
        """
        # 분할표 (Contingency Table)
        # [[control_success, control_failure],
        #  [treatment_success, treatment_failure]]

        control_failure = control_total - control_success
        treatment_failure = treatment_total - treatment_success

        # 카이제곱 통계량
        n = control_total + treatment_total
        if n == 0:
            return 0.0, 1.0

        expected_control_success = (control_total * (control_success + treatment_success)) / n
        expected_treatment_success = (treatment_total * (control_success + treatment_success)) / n

        if expected_control_success == 0 or expected_treatment_success == 0:
            return 0.0, 1.0

        chi2_stat = (
            (control_success - expected_control_success) ** 2 / expected_control_success +
            (treatment_success - expected_treatment_success) ** 2 / expected_treatment_success
        )

        # p-값 근사
        if chi2_stat > 6.635:  # p < 0.01
            p_value = 0.01
        elif chi2_stat > 3.841:  # p < 0.05
            p_value = 0.05
        elif chi2_stat > 2.706:  # p < 0.10
            p_value = 0.10
        else:
            p_value = 0.5

        return chi2_stat, p_value

    @staticmethod
    def effect_size_cohens_d(group1_values: List[float], group2_values: List[float]) -> float:
        """코헨의 d (Effect Size)"""
        if not group1_values or not group2_values:
            return 0.0

        n1, n2 = len(group1_values), len(group2_values)
        mean1 = sum(group1_values) / n1
        mean2 = sum(group2_values) / n2

        var1 = sum((x - mean1) ** 2 for x in group1_values) / (n1 - 1) if n1 > 1 else 0
        var2 = sum((x - mean2) ** 2 for x in group2_values) / (n2 - 1) if n2 > 1 else 0

        pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 0

        if pooled_std == 0:
            return 0.0

        cohens_d = (mean1 - mean2) / pooled_std
        return cohens_d


class ResultAnalyzer:
    """결과 분석"""

    def __init__(self, confidence_level: float = 0.95):
        """결과 분석 초기화

        Args:
            confidence_level: 신뢰도 (기본: 95%)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level  # p-value 임계값

    def analyze_continuous_metric(self, collector: MetricsCollector, metric_name: str) -> Dict[str, Any]:
        """연속형 메트릭 분석"""
        control_stats = collector.get_group_statistics(GroupType.CONTROL, metric_name)
        treatment_stats = collector.get_group_statistics(GroupType.TREATMENT, metric_name)

        control_values = collector.group_stats[GroupType.CONTROL].get(metric_name, [])
        treatment_values = collector.group_stats[GroupType.TREATMENT].get(metric_name, [])

        # t-검정
        t_stat, p_value = StatisticalTest.independent_t_test(control_values, treatment_values)

        # 효과 크기
        cohens_d = StatisticalTest.effect_size_cohens_d(control_values, treatment_values)

        # 통계적 유의성
        is_significant = p_value < self.alpha

        # 승자 결정
        if is_significant:
            winner = GroupType.TREATMENT if treatment_stats['mean'] > control_stats['mean'] else GroupType.CONTROL
        else:
            winner = None

        return {
            'metric': metric_name,
            'type': 'continuous',
            'control': control_stats,
            'treatment': treatment_stats,
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'is_significant': is_significant,
            'winner': winner.value if winner else 'No winner',
            'confidence_level': self.confidence_level,
            'improvement': (
                (treatment_stats['mean'] - control_stats['mean']) / control_stats['mean'] * 100
                if control_stats['mean'] > 0 else 0
            )
        }

    def analyze_categorical_metric(self, collector: MetricsCollector,
                                   metric_name: str, success_threshold: float) -> Dict[str, Any]:
        """범주형 메트릭 분석 (예: 성공률)"""
        control_values = collector.group_stats[GroupType.CONTROL].get(metric_name, [])
        treatment_values = collector.group_stats[GroupType.TREATMENT].get(metric_name, [])

        if not control_values or not treatment_values:
            return {'error': 'Insufficient data'}

        # 성공 개수 계산
        control_success = sum(1 for v in control_values if v >= success_threshold)
        treatment_success = sum(1 for v in treatment_values if v >= success_threshold)

        # 카이제곱 검정
        chi2_stat, p_value = StatisticalTest.chi_square_test(
            control_success, len(control_values),
            treatment_success, len(treatment_values)
        )

        # 성공률
        control_rate = control_success / len(control_values) if control_values else 0
        treatment_rate = treatment_success / len(treatment_values) if treatment_values else 0

        is_significant = p_value < self.alpha

        winner = GroupType.TREATMENT if treatment_rate > control_rate else GroupType.CONTROL

        return {
            'metric': metric_name,
            'type': 'categorical',
            'control_success': control_success,
            'control_total': len(control_values),
            'control_rate': control_rate,
            'treatment_success': treatment_success,
            'treatment_total': len(treatment_values),
            'treatment_rate': treatment_rate,
            'chi2_statistic': chi2_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'winner': winner.value if is_significant else 'No winner',
            'improvement': (treatment_rate - control_rate) * 100
        }


class ExperimentRunner:
    """실험 실행"""

    def __init__(self, duration_seconds: int = 60):
        """실험 실행 초기화

        Args:
            duration_seconds: 실험 지속 시간
        """
        self.duration = duration_seconds
        self.collector = MetricsCollector()
        self.analyzer = ResultAnalyzer(confidence_level=0.95)
        self.start_time = None
        self.end_time = None

    def simulate_control_group(self, num_requests: int = 500) -> None:
        """Control 그룹 시뮬레이션 (기존 방식)"""
        logger.info(f"▶️  Control 그룹 시뮬레이션 ({num_requests} 요청)...")

        for _ in range(num_requests):
            # 기존 방식: 평균 50ms, 표준편차 15ms
            response_time = max(10, random.gauss(50, 15))
            # 정확도: 85%
            accuracy = 0.85 + random.gauss(0, 0.1)
            accuracy = max(0, min(1, accuracy))
            # 사용자 만족도: 3.5/5
            satisfaction = 3.5 + random.gauss(0, 0.5)
            satisfaction = max(1, min(5, satisfaction))

            metrics = {
                'response_time': response_time,
                'accuracy': accuracy,
                'satisfaction': satisfaction
            }
            self.collector.record_metric(GroupType.CONTROL, metrics)

    def simulate_treatment_group(self, num_requests: int = 500) -> None:
        """Treatment 그룹 시뮬레이션 (새로운 방식 - 개선됨)"""
        logger.info(f"▶️  Treatment 그룹 시뮬레이션 ({num_requests} 요청)...")

        for _ in range(num_requests):
            # 새로운 방식: 평균 35ms (30% 개선), 표준편차 12ms
            response_time = max(10, random.gauss(35, 12))
            # 정확도: 92% (8% 개선)
            accuracy = 0.92 + random.gauss(0, 0.08)
            accuracy = max(0, min(1, accuracy))
            # 사용자 만족도: 4.2/5 (20% 개선)
            satisfaction = 4.2 + random.gauss(0, 0.4)
            satisfaction = max(1, min(5, satisfaction))

            metrics = {
                'response_time': response_time,
                'accuracy': accuracy,
                'satisfaction': satisfaction
            }
            self.collector.record_metric(GroupType.TREATMENT, metrics)

    def run_experiment(self) -> Dict[str, Any]:
        """실험 실행"""
        logger.info("\n" + "=" * 70)
        logger.info("🧪 A/B 테스트 실험 시작")
        logger.info("=" * 70)

        self.start_time = time.time()

        # 두 그룹 시뮬레이션
        self.simulate_control_group(500)
        self.simulate_treatment_group(500)

        self.end_time = time.time()

        # 결과 분석
        logger.info("\n📊 결과 분석 중...")

        results = {
            'duration': self.end_time - self.start_time,
            'control_sample_size': len(self.collector.metrics[GroupType.CONTROL]),
            'treatment_sample_size': len(self.collector.metrics[GroupType.TREATMENT]),
            'metrics': {}
        }

        # 연속형 메트릭 분석
        for metric_name in ['response_time', 'accuracy', 'satisfaction']:
            results['metrics'][metric_name] = self.analyzer.analyze_continuous_metric(
                self.collector, metric_name
            )

        return results

    def print_results(self, results: Dict[str, Any]) -> None:
        """결과 출력"""
        print("\n" + "=" * 70)
        print("📈 A/B 테스트 결과")
        print("=" * 70)

        print(f"\n📌 샘플 크기:")
        print(f"  Control: {results['control_sample_size']} 요청")
        print(f"  Treatment: {results['treatment_sample_size']} 요청")
        print(f"  총 실험 시간: {results['duration']:.2f}초")

        print(f"\n📊 메트릭 분석:")

        for metric_name, analysis in results['metrics'].items():
            print(f"\n  📍 {metric_name}:")
            print(f"     Control 평균: {analysis['control']['mean']:.2f}")
            print(f"     Treatment 평균: {analysis['treatment']['mean']:.2f}")
            print(f"     개선율: {analysis['improvement']:.1f}%")
            print(f"     p-value: {analysis['p_value']:.4f}")
            print(f"     통계 유의성: {'✅ 유의' if analysis['is_significant'] else '❌ 무의'}")
            print(f"     효과 크기 (Cohen's d): {analysis['cohens_d']:.3f}")
            print(f"     승자: {analysis['winner']}")

        print("\n" + "=" * 70)
        print("🎯 최종 결론")
        print("=" * 70)

        # 최종 결론
        significant_metrics = [
            m for m in results['metrics'].values() if m.get('is_significant')
        ]

        if significant_metrics:
            print(f"\n✅ 통계적으로 유의미한 차이 발견!")
            print(f"   유의미한 메트릭: {len(significant_metrics)}/{len(results['metrics'])}")
            print(f"   신뢰도: 95%")
            print(f"   결론: Treatment 방식 도입 권장")
        else:
            print(f"\n❌ 통계적으로 유의미한 차이 없음")
            print(f"   결론: 추가 테스트 필요 또는 현재 방식 유지")

        print("=" * 70 + "\n")


if __name__ == "__main__":
    # A/B 테스트 실행
    runner = ExperimentRunner()
    results = runner.run_experiment()
    runner.print_results(results)
