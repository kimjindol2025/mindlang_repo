#!/usr/bin/env python3
"""
MindLang 시뮬레이션 엔진
"What-If" 시나리오 분석을 통한 의사결정 검증 및 최적화

기능:
- 시나리오 기반 시뮬레이션
- 의사결정 시뮬레이션 및 검증
- 정책 효과 예측
- 위험 평가 및 영향 분석
- 대안 비교 분석
"""

import json
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import statistics
from enum import Enum


class SimulationType(Enum):
    """시뮬레이션 타입"""
    SCENARIO = "scenario"
    DECISION = "decision"
    POLICY = "policy"
    RISK = "risk"
    OPTIMIZATION = "optimization"


@dataclass
class SimulationMetrics:
    """시뮬레이션 메트릭"""
    cpu_usage: float
    memory_usage: float
    error_rate: float
    latency_ms: float
    throughput: float
    cost_per_hour: float


@dataclass
class SimulationResult:
    """시뮬레이션 결과"""
    id: str
    timestamp: float
    simulation_type: str
    scenario_name: str
    initial_metrics: Dict
    final_metrics: Dict
    decision: str
    confidence: float
    estimated_outcome: str
    risk_level: str  # low, medium, high
    impact_analysis: Dict
    recommendations: List[str]


class Scenario:
    """시나리오 정의"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.conditions: Dict = {}
        self.duration_minutes = 60

    def add_condition(self, metric: str, operator: str, value: float):
        """조건 추가"""
        self.conditions[metric] = {
            'operator': operator,
            'value': value
        }

    def set_duration(self, minutes: int):
        """시뮬레이션 지속 시간 설정"""
        self.duration_minutes = minutes


class SimulationEngine:
    """시뮬레이션 엔진"""

    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.results: Dict[str, SimulationResult] = {}
        self._register_default_scenarios()

    def _register_default_scenarios(self):
        """기본 시나리오 등록"""
        # 시나리오 1: 트래픽 급증
        scenario1 = Scenario(
            "트래픽 급증",
            "갑자기 트래픽이 3배 증가하는 상황"
        )
        scenario1.add_condition("cpu_usage", ">", 85)
        scenario1.add_condition("latency_ms", ">", 300)
        scenario1.set_duration(30)
        self.scenarios["traffic_spike"] = scenario1

        # 시나리오 2: 메모리 누수
        scenario2 = Scenario(
            "메모리 누수",
            "지속적인 메모리 사용률 증가"
        )
        scenario2.add_condition("memory_usage", ">", 90)
        scenario2.add_condition("error_rate", ">", 0.05)
        scenario2.set_duration(120)
        self.scenarios["memory_leak"] = scenario2

        # 시나리오 3: 데이터베이스 장애
        scenario3 = Scenario(
            "데이터베이스 장애",
            "데이터베이스 응답 시간 증가"
        )
        scenario3.add_condition("latency_ms", ">", 500)
        scenario3.add_condition("error_rate", ">", 0.10)
        scenario3.set_duration(45)
        self.scenarios["db_failure"] = scenario3

        # 시나리오 4: 특정 모듈 실패
        scenario4 = Scenario(
            "모듈 실패",
            "특정 마이크로서비스 장애"
        )
        scenario4.add_condition("cpu_usage", "<", 20)
        scenario4.add_condition("error_rate", ">", 0.50)
        scenario4.set_duration(60)
        self.scenarios["service_failure"] = scenario4

        # 시나리오 5: 비용 최적화 시도
        scenario5 = Scenario(
            "비용 최적화",
            "리소스 절감을 위한 스케일 다운"
        )
        scenario5.add_condition("cpu_usage", "<", 30)
        scenario5.add_condition("memory_usage", "<", 40)
        scenario5.set_duration(90)
        self.scenarios["cost_optimization"] = scenario5

    def create_custom_scenario(self, name: str, description: str) -> Scenario:
        """커스텀 시나리오 생성"""
        scenario = Scenario(name, description)
        self.scenarios[name.lower().replace(" ", "_")] = scenario
        return scenario

    def simulate_scenario(self, scenario_id: str, current_metrics: Dict) -> Optional[SimulationResult]:
        """시나리오 시뮬레이션"""
        if scenario_id not in self.scenarios:
            print(f"❌ 시나리오 {scenario_id}을(를) 찾을 수 없습니다")
            return None

        scenario = self.scenarios[scenario_id]
        print(f"\n🎯 시뮬레이션 시작: {scenario.name}")
        print(f"   설명: {scenario.description}")
        print(f"   지속시간: {scenario.duration_minutes}분\n")

        result_id = f"sim_{int(datetime.now().timestamp())}"

        try:
            # 초기 메트릭 저장
            initial_metrics = current_metrics.copy()

            # 시나리오 조건 적용
            simulated_metrics = self._apply_scenario_conditions(
                current_metrics,
                scenario.conditions
            )

            # 의사결정 생성
            decision, confidence = self._generate_decision(
                scenario,
                simulated_metrics
            )

            # 영향 분석
            impact_analysis = self._analyze_impact(
                initial_metrics,
                simulated_metrics
            )

            # 의사결정 실행 후 메트릭 시뮬레이션
            final_metrics = self._simulate_decision_outcome(
                simulated_metrics,
                decision
            )

            # 리스크 평가
            risk_level = self._assess_risk(final_metrics)

            # 권장사항 생성
            recommendations = self._generate_recommendations(
                scenario,
                final_metrics,
                decision
            )

            # 결과 저장
            result = SimulationResult(
                id=result_id,
                timestamp=datetime.now().timestamp(),
                simulation_type=SimulationType.SCENARIO.value,
                scenario_name=scenario.name,
                initial_metrics=initial_metrics,
                final_metrics=final_metrics,
                decision=decision,
                confidence=confidence,
                estimated_outcome=self._evaluate_outcome(final_metrics),
                risk_level=risk_level,
                impact_analysis=impact_analysis,
                recommendations=recommendations
            )

            self.results[result_id] = result

            # 결과 출력
            self._print_simulation_result(result)

            return result

        except Exception as e:
            print(f"❌ 시뮬레이션 실패: {e}")
            return None

    def simulate_decision(self, decision: str, current_metrics: Dict) -> Optional[SimulationResult]:
        """의사결정 시뮬레이션"""
        print(f"\n🎯 의사결정 시뮬레이션: {decision}")

        result_id = f"sim_{int(datetime.now().timestamp())}"

        try:
            initial_metrics = current_metrics.copy()

            # 의사결정 실행 시뮬레이션
            final_metrics = self._simulate_decision_outcome(
                current_metrics,
                decision
            )

            # 영향 분석
            impact_analysis = self._analyze_impact(
                initial_metrics,
                final_metrics
            )

            # 리스크 평가
            risk_level = self._assess_risk(final_metrics)

            # 권장사항
            recommendations = [
                f"{decision} 의사결정 실행 후 메트릭 모니터링 필요",
                "2-3분 후 효과 측정 및 검증",
                "리스크가 높으면 즉시 롤백 준비"
            ]

            result = SimulationResult(
                id=result_id,
                timestamp=datetime.now().timestamp(),
                simulation_type=SimulationType.DECISION.value,
                scenario_name=f"{decision} 의사결정",
                initial_metrics=initial_metrics,
                final_metrics=final_metrics,
                decision=decision,
                confidence=0.85,
                estimated_outcome=self._evaluate_outcome(final_metrics),
                risk_level=risk_level,
                impact_analysis=impact_analysis,
                recommendations=recommendations
            )

            self.results[result_id] = result

            self._print_simulation_result(result)

            return result

        except Exception as e:
            print(f"❌ 의사결정 시뮬레이션 실패: {e}")
            return None

    def compare_alternatives(self, decisions: List[str], current_metrics: Dict) -> Dict:
        """대안 비교 분석"""
        print(f"\n🎯 대안 비교 분석: {len(decisions)}개 옵션\n")

        comparison = {}
        results = []

        for decision in decisions:
            print(f"   - {decision} 시뮬레이션 중...")
            final_metrics = self._simulate_decision_outcome(
                current_metrics.copy(),
                decision
            )

            impact = self._analyze_impact(current_metrics, final_metrics)
            risk = self._assess_risk(final_metrics)

            comparison[decision] = {
                'final_metrics': final_metrics,
                'impact': impact,
                'risk_level': risk,
                'overall_score': self._calculate_decision_score(final_metrics, risk)
            }
            results.append(decision)

        # 최적 의사결정 추천
        best_decision = max(
            comparison.items(),
            key=lambda x: x[1]['overall_score']
        )

        print(f"\n✅ 최적 의사결정: {best_decision[0]} (점수: {best_decision[1]['overall_score']:.2f})")
        print("\n비교 결과:")
        print(f"{'의사결정':<20} {'리스크':<12} {'점수':<10}")
        print("-" * 45)

        for decision, data in sorted(
            comparison.items(),
            key=lambda x: x[1]['overall_score'],
            reverse=True
        ):
            print(f"{decision:<20} {data['risk_level']:<12} {data['overall_score']:<10.2f}")

        return comparison

    def _apply_scenario_conditions(self, metrics: Dict, conditions: Dict) -> Dict:
        """시나리오 조건 적용"""
        simulated = metrics.copy()

        for metric, condition in conditions.items():
            operator = condition['operator']
            value = condition['value']

            if metric in simulated:
                if operator == '>':
                    # 조건을 만족하는 방향으로 악화
                    simulated[metric] = value + random.uniform(0, 10)
                elif operator == '<':
                    # 조건을 만족하는 방향으로 개선
                    simulated[metric] = value - random.uniform(0, 5)
                elif operator == '=':
                    simulated[metric] = value

        return simulated

    def _generate_decision(self, scenario: Scenario, metrics: Dict) -> Tuple[str, float]:
        """의사결정 생성"""
        cpu = metrics.get('cpu_usage', 50)
        memory = metrics.get('memory_usage', 50)
        error_rate = metrics.get('error_rate', 0.01)
        latency = metrics.get('latency_ms', 100)

        confidence = 0.8

        # 스케일 업 필요
        if cpu > 80 or memory > 80 or latency > 300:
            return "SCALE_UP", confidence

        # 스케일 다운 가능
        if cpu < 30 and memory < 40:
            return "SCALE_DOWN", confidence

        # 롤백 필요
        if error_rate > 0.1:
            return "ROLLBACK", confidence + 0.1

        # 계속 모니터링
        return "CONTINUE", 0.9

    def _simulate_decision_outcome(self, metrics: Dict, decision: str) -> Dict:
        """의사결정 실행 결과 시뮬레이션"""
        result = metrics.copy()

        if decision == "SCALE_UP":
            result['cpu_usage'] = max(0, result.get('cpu_usage', 50) - 25)
            result['memory_usage'] = max(0, result.get('memory_usage', 50) - 20)
            result['latency_ms'] = max(10, result.get('latency_ms', 100) - 50)
            result['error_rate'] = max(0, result.get('error_rate', 0.01) - 0.02)
            result['cost_per_hour'] = result.get('cost_per_hour', 100) + 30

        elif decision == "SCALE_DOWN":
            result['cpu_usage'] = min(100, result.get('cpu_usage', 50) + 15)
            result['memory_usage'] = min(100, result.get('memory_usage', 50) + 10)
            result['latency_ms'] = result.get('latency_ms', 100) + 20
            result['cost_per_hour'] = max(50, result.get('cost_per_hour', 100) - 25)

        elif decision == "ROLLBACK":
            result['error_rate'] = max(0, result.get('error_rate', 0.01) - 0.05)
            result['latency_ms'] = result.get('latency_ms', 100) + 10
            result['cpu_usage'] = result.get('cpu_usage', 50) - 5

        elif decision == "CONTINUE":
            # 약간의 자연스러운 변화
            result['cpu_usage'] = result.get('cpu_usage', 50) + random.uniform(-2, 2)
            result['memory_usage'] = result.get('memory_usage', 50) + random.uniform(-1, 1)

        return result

    def _analyze_impact(self, before: Dict, after: Dict) -> Dict:
        """영향 분석"""
        impact = {}

        for metric in before.keys():
            if metric in after:
                change = after[metric] - before[metric]
                change_pct = (change / before[metric] * 100) if before[metric] != 0 else 0
                impact[metric] = {
                    'before': before[metric],
                    'after': after[metric],
                    'change': round(change, 2),
                    'change_percent': round(change_pct, 2)
                }

        return impact

    def _assess_risk(self, metrics: Dict) -> str:
        """리스크 평가"""
        cpu = metrics.get('cpu_usage', 50)
        memory = metrics.get('memory_usage', 50)
        error_rate = metrics.get('error_rate', 0.01)

        risk_score = 0

        if cpu > 85:
            risk_score += 3
        elif cpu > 70:
            risk_score += 1

        if memory > 85:
            risk_score += 3
        elif memory > 70:
            risk_score += 1

        if error_rate > 0.1:
            risk_score += 3
        elif error_rate > 0.05:
            risk_score += 1

        if risk_score >= 5:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def _evaluate_outcome(self, metrics: Dict) -> str:
        """결과 평가"""
        cpu = metrics.get('cpu_usage', 50)
        memory = metrics.get('memory_usage', 50)
        error_rate = metrics.get('error_rate', 0.01)

        if cpu < 70 and memory < 70 and error_rate < 0.05:
            return "성공: 모든 메트릭이 정상 범위"
        elif cpu < 85 and memory < 85 and error_rate < 0.10:
            return "부분 성공: 대부분의 메트릭 개선"
        else:
            return "미흡: 추가 조치 필요"

    def _calculate_decision_score(self, metrics: Dict, risk: str) -> float:
        """의사결정 점수 계산"""
        # 0-100 점수
        cpu = max(0, 100 - metrics.get('cpu_usage', 50) * 0.8)
        memory = max(0, 100 - metrics.get('memory_usage', 50) * 0.8)
        error = max(0, 100 - metrics.get('error_rate', 0) * 1000)

        score = (cpu + memory + error) / 3

        # 리스크에 따른 감점
        if risk == "high":
            score *= 0.7
        elif risk == "medium":
            score *= 0.85

        return score

    def _generate_recommendations(self, scenario: Scenario, metrics: Dict, decision: str) -> List[str]:
        """권장사항 생성"""
        recommendations = [
            f"의사결정 '{decision}' 실행 권장",
            "2-3분 후 메트릭 변화 모니터링",
            "변화가 예상과 다르면 대체 의사결정 준비"
        ]

        if metrics.get('cpu_usage', 0) > 80:
            recommendations.append("⚠️ CPU 사용률 높음 - 추가 스케일업 준비")

        if metrics.get('error_rate', 0) > 0.05:
            recommendations.append("⚠️ 에러율 높음 - 로그 분석 필요")

        if metrics.get('latency_ms', 0) > 300:
            recommendations.append("⚠️ 응답시간 길어짐 - 데이터베이스 최적화 검토")

        return recommendations

    def _print_simulation_result(self, result: SimulationResult):
        """시뮬레이션 결과 출력"""
        print(f"\n{'='*70}")
        print(f"🎯 시뮬레이션 결과: {result.scenario_name}")
        print(f"{'='*70}\n")

        print(f"시뮬레이션 ID: {result.id}")
        print(f"의사결정: {result.decision} (신뢰도: {result.confidence:.1%})")
        print(f"예상 결과: {result.estimated_outcome}")
        print(f"리스크 수준: {result.risk_level.upper()}\n")

        print("📊 메트릭 변화:")
        print(f"{'메트릭':<20} {'초기값':<15} {'최종값':<15} {'변화':<15}")
        print("-" * 65)

        for metric, impact in result.impact_analysis.items():
            change = impact['change']
            change_pct = impact['change_percent']
            before = impact['before']
            after = impact['after']

            change_str = f"{change:+.2f} ({change_pct:+.1f}%)"
            print(f"{metric:<20} {before:<15.2f} {after:<15.2f} {change_str:<15}")

        print("\n💡 권장사항:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")

        print(f"\n{'='*70}\n")

    def list_scenarios(self) -> None:
        """시나리오 목록 표시"""
        print("\n📋 등록된 시나리오\n")
        print(f"{'시나리오 ID':<25} {'이름':<25} {'지속시간':<12}")
        print("-" * 65)

        for scenario_id, scenario in self.scenarios.items():
            print(f"{scenario_id:<25} {scenario.name:<25} {scenario.duration_minutes}분")

    def get_simulation_stats(self) -> Dict:
        """시뮬레이션 통계"""
        if not self.results:
            return {}

        total = len(self.results)
        by_type = {}
        by_risk = {'low': 0, 'medium': 0, 'high': 0}

        for result in self.results.values():
            sim_type = result.simulation_type
            by_type[sim_type] = by_type.get(sim_type, 0) + 1
            by_risk[result.risk_level] = by_risk.get(result.risk_level, 0) + 1

        return {
            'total_simulations': total,
            'by_type': by_type,
            'by_risk': by_risk
        }


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    engine = SimulationEngine()

    if len(sys.argv) < 2:
        print("사용법: python simulation_engine.py [command] [args]")
        print("  scenarios           - 등록된 시나리오 목록")
        print("  simulate <id>       - 시나리오 시뮬레이션")
        print("  decision <action>   - 의사결정 시뮬레이션")
        print("  compare <a> <b> <c> - 대안 비교 (최소 2개)")
        print("  stats               - 시뮬레이션 통계")
        return

    command = sys.argv[1]

    if command == "scenarios":
        engine.list_scenarios()

    elif command == "simulate":
        scenario_id = sys.argv[2] if len(sys.argv) > 2 else None
        if scenario_id:
            current_metrics = {
                'cpu_usage': 75,
                'memory_usage': 68,
                'error_rate': 0.03,
                'latency_ms': 250,
                'throughput': 5000,
                'cost_per_hour': 120
            }
            engine.simulate_scenario(scenario_id, current_metrics)
        else:
            print("시나리오 ID를 지정하세요")

    elif command == "decision":
        decision = sys.argv[2] if len(sys.argv) > 2 else None
        if decision:
            current_metrics = {
                'cpu_usage': 75,
                'memory_usage': 68,
                'error_rate': 0.03,
                'latency_ms': 250,
                'throughput': 5000,
                'cost_per_hour': 120
            }
            engine.simulate_decision(decision, current_metrics)
        else:
            print("의사결정 작업을 지정하세요 (예: SCALE_UP)")

    elif command == "compare":
        if len(sys.argv) >= 4:
            decisions = sys.argv[2:]
            current_metrics = {
                'cpu_usage': 75,
                'memory_usage': 68,
                'error_rate': 0.03,
                'latency_ms': 250,
                'throughput': 5000,
                'cost_per_hour': 120
            }
            engine.compare_alternatives(decisions, current_metrics)
        else:
            print("최소 2개 이상의 의사결정을 지정하세요")

    elif command == "stats":
        stats = engine.get_simulation_stats()
        print("\n📊 시뮬레이션 통계\n")
        print(f"총 시뮬레이션: {stats.get('total_simulations', 0)}개")
        if stats.get('by_type'):
            print("\n시뮬레이션 타입:")
            for sim_type, count in stats.get('by_type', {}).items():
                print(f"  - {sim_type}: {count}개")
        if stats.get('by_risk'):
            print("\n리스크 수준별:")
            for risk, count in stats.get('by_risk', {}).items():
                print(f"  - {risk}: {count}개")
