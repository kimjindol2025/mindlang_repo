#!/usr/bin/env python3
"""
MindLang 카오스 엔지니어링 시스템
의도적으로 장애를 주입하여 시스템의 복원력 검증

기능:
- 다양한 장애 시뮬레이션
- 카오스 시나리오 오케스트레이션
- 시스템 복원력 평가
- 실패점 식별
- 자동 복구 검증
- 카오스 보고서 생성
"""

import json
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ChaosExperimentType(Enum):
    """카오스 실험 타입"""
    LATENCY_INJECTION = "latency_injection"  # 네트워크 지연
    SERVICE_FAILURE = "service_failure"  # 서비스 다운
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 리소스 부족
    NETWORK_PARTITION = "network_partition"  # 네트워크 분할
    DATA_CORRUPTION = "data_corruption"  # 데이터 손상
    CASCADING_FAILURE = "cascading_failure"  # 연쇄 실패
    HIGH_ERROR_RATE = "high_error_rate"  # 높은 에러율
    DEPENDENCY_TIMEOUT = "dependency_timeout"  # 의존성 타임아웃


@dataclass
class ChaosExperiment:
    """카오스 실험"""
    experiment_id: str
    name: str
    description: str
    chaos_type: str
    target_service: str
    target_percentage: float  # 0-100, 영향받을 트래픽 비율
    duration_seconds: int
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: str = "pending"  # pending, running, completed, failed
    expected_impact: str = ""
    actual_impact: Dict = field(default_factory=dict)
    system_recovery_time_seconds: Optional[float] = None
    success: bool = False


@dataclass
class ChaosObservation:
    """카오스 관찰 데이터"""
    timestamp: float
    metric_name: str
    baseline_value: float
    chaos_value: float
    deviation_percentage: float
    is_anomaly: bool


@dataclass
class ResilienceTest:
    """복원력 테스트 결과"""
    test_id: str
    name: str
    experiments: List[ChaosExperiment]
    total_duration_seconds: float
    failures_detected: int
    vulnerabilities: List[str]
    recovery_quality_score: float  # 0-100
    recommendations: List[str]


class ChaosEngineer:
    """카오스 엔지니어링 엔진"""

    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.observations: List[ChaosObservation] = []
        self.resilience_tests: List[ResilienceTest] = []
        self.baseline_metrics: Dict[str, float] = {}
        self._initialize_baselines()

    def _initialize_baselines(self):
        """기본 메트릭 초기화"""
        self.baseline_metrics = {
            'response_time_ms': 150,
            'error_rate': 0.01,
            'throughput': 5000,
            'cpu_usage': 45,
            'memory_usage': 55,
            'availability': 99.95
        }

    def create_experiment(
        self,
        name: str,
        description: str,
        chaos_type: str,
        target_service: str,
        target_percentage: float = 10.0,
        duration_seconds: int = 60
    ) -> ChaosExperiment:
        """카오스 실험 생성"""
        experiment_id = f"chaos_{int(time.time())}"

        experiment = ChaosExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            chaos_type=chaos_type,
            target_service=target_service,
            target_percentage=target_percentage,
            duration_seconds=duration_seconds,
            expected_impact=self._predict_impact(chaos_type)
        )

        self.experiments[experiment_id] = experiment
        print(f"✅ 카오스 실험 생성: {experiment_id}")
        print(f"   타입: {chaos_type}")
        print(f"   대상: {target_service}")
        print(f"   영향: {target_percentage}%")

        return experiment

    def _predict_impact(self, chaos_type: str) -> str:
        """예상 영향 예측"""
        impacts = {
            ChaosExperimentType.LATENCY_INJECTION.value: "응답시간 증가, 사용자 경험 저하",
            ChaosExperimentType.SERVICE_FAILURE.value: "서비스 다운, 의존성 실패",
            ChaosExperimentType.RESOURCE_EXHAUSTION.value: "성능 저하, 타임아웃 증가",
            ChaosExperimentType.NETWORK_PARTITION.value: "통신 두절, 분산 트랜잭션 실패",
            ChaosExperimentType.DATA_CORRUPTION.value: "데이터 무결성 문제, 에러 증가",
            ChaosExperimentType.CASCADING_FAILURE.value: "연쇄 실패, 광범위 장애",
            ChaosExperimentType.HIGH_ERROR_RATE.value: "에러율 급증, 서비스 품질 저하",
            ChaosExperimentType.DEPENDENCY_TIMEOUT.value: "의존성 타임아웃, 요청 실패"
        }
        return impacts.get(chaos_type, "알 수 없음")

    def run_experiment(self, experiment_id: str) -> bool:
        """카오스 실험 실행"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        experiment.start_time = time.time()
        experiment.status = "running"

        print(f"\n🔥 카오스 실험 시작: {experiment.name}")
        print(f"   대상: {experiment.target_service}")
        print(f"   지속시간: {experiment.duration_seconds}초")
        print(f"   영향: {experiment.target_percentage}%\n")

        # 시뮬레이션: 장애 주입
        chaos_metrics = self._inject_chaos(experiment.chaos_type, experiment.target_percentage)

        # 메트릭 관찰
        start_time = time.time()
        chaos_start_time = start_time + 5  # 5초 후 카오스 시작
        chaos_end_time = chaos_start_time + experiment.duration_seconds

        # 시뮬레이션 타임라인
        for i in range(experiment.duration_seconds + 15):
            current_time = start_time + i

            if current_time >= chaos_start_time and current_time <= chaos_end_time:
                # 카오스 기간
                for metric_name, baseline in self.baseline_metrics.items():
                    chaos_value = chaos_metrics.get(metric_name, baseline)
                    deviation = ((chaos_value - baseline) / baseline) * 100

                    observation = ChaosObservation(
                        timestamp=current_time,
                        metric_name=metric_name,
                        baseline_value=baseline,
                        chaos_value=chaos_value,
                        deviation_percentage=deviation,
                        is_anomaly=abs(deviation) > 20
                    )

                    self.observations.append(observation)

                    if i % 10 == 0 and metric_name == 'error_rate':
                        print(f"   [{i}s] {metric_name}: {baseline} → {chaos_value:.2f} ({deviation:+.1f}%)")

            else:
                # 복구 기간
                for metric_name, baseline in self.baseline_metrics.items():
                    if current_time > chaos_end_time:
                        # 복구 중
                        recovery_progress = (current_time - chaos_end_time) / 10
                        recovery_value = baseline + (chaos_metrics.get(metric_name, baseline) - baseline) * (1 - recovery_progress)
                        recovery_value = max(baseline, recovery_value) if recovery_value >= baseline else min(baseline, recovery_value)
                    else:
                        recovery_value = baseline

                    observation = ChaosObservation(
                        timestamp=current_time,
                        metric_name=metric_name,
                        baseline_value=baseline,
                        chaos_value=recovery_value,
                        deviation_percentage=((recovery_value - baseline) / baseline) * 100,
                        is_anomaly=False
                    )

                    self.observations.append(observation)

        experiment.end_time = time.time()
        experiment.status = "completed"

        # 복구 시간 계산
        recovery_time = self._calculate_recovery_time(experiment)
        experiment.system_recovery_time_seconds = recovery_time

        # 성공 판정
        experiment.success = recovery_time < (experiment.duration_seconds * 2)

        print(f"\n✅ 카오스 실험 완료")
        print(f"   상태: {'성공' if experiment.success else '실패'}")
        print(f"   복구 시간: {recovery_time:.1f}초")
        print(f"   예상 영향: {experiment.expected_impact}\n")

        return True

    def _inject_chaos(self, chaos_type: str, percentage: float) -> Dict:
        """장애 주입"""
        chaos_metrics = self.baseline_metrics.copy()

        if chaos_type == ChaosExperimentType.LATENCY_INJECTION.value:
            chaos_metrics['response_time_ms'] *= (1 + percentage / 100 * 3)
            chaos_metrics['error_rate'] += (percentage / 100) * 0.02

        elif chaos_type == ChaosExperimentType.SERVICE_FAILURE.value:
            chaos_metrics['availability'] -= percentage
            chaos_metrics['error_rate'] += (percentage / 100) * 0.5
            chaos_metrics['throughput'] *= (1 - percentage / 100)

        elif chaos_type == ChaosExperimentType.RESOURCE_EXHAUSTION.value:
            chaos_metrics['cpu_usage'] = 95
            chaos_metrics['memory_usage'] = 98
            chaos_metrics['response_time_ms'] *= 2
            chaos_metrics['error_rate'] += 0.05

        elif chaos_type == ChaosExperimentType.NETWORK_PARTITION.value:
            chaos_metrics['error_rate'] = 0.30
            chaos_metrics['availability'] -= 50
            chaos_metrics['throughput'] *= 0.1

        elif chaos_type == ChaosExperimentType.DATA_CORRUPTION.value:
            chaos_metrics['error_rate'] += 0.10
            chaos_metrics['response_time_ms'] *= 1.5

        elif chaos_type == ChaosExperimentType.CASCADING_FAILURE.value:
            chaos_metrics['availability'] = 50
            chaos_metrics['error_rate'] = 0.50
            chaos_metrics['throughput'] = 100

        elif chaos_type == ChaosExperimentType.HIGH_ERROR_RATE.value:
            chaos_metrics['error_rate'] = 0.20
            chaos_metrics['response_time_ms'] *= 1.2

        elif chaos_type == ChaosExperimentType.DEPENDENCY_TIMEOUT.value:
            chaos_metrics['error_rate'] = 0.15
            chaos_metrics['response_time_ms'] = 30000  # 30초 타임아웃

        return chaos_metrics

    def _calculate_recovery_time(self, experiment: ChaosExperiment) -> float:
        """복구 시간 계산"""
        if not experiment.start_time or not experiment.end_time:
            return 0

        # 메트릭이 기준선으로 돌아오는 시간
        recovery_threshold = 0.95  # 95% 복구

        last_anomaly_time = None
        for obs in sorted(self.observations, key=lambda x: x.timestamp, reverse=True):
            if obs.is_anomaly and obs.timestamp >= experiment.start_time:
                last_anomaly_time = obs.timestamp
                break

        if last_anomaly_time:
            recovery_time = last_anomaly_time - experiment.start_time
            return max(0, recovery_time)

        return 0

    def identify_vulnerabilities(self, experiment: ChaosExperiment) -> List[str]:
        """취약점 식별"""
        vulnerabilities = []

        # 복구 시간 분석
        if experiment.system_recovery_time_seconds and experiment.system_recovery_time_seconds > 120:
            vulnerabilities.append("⚠️ 복구 시간이 너무 김 (120초 이상)")

        # 에러율 분석
        error_observations = [o for o in self.observations if o.metric_name == 'error_rate' and o.is_anomaly]
        if len(error_observations) > 10:
            vulnerabilities.append("⚠️ 높은 에러율 지속")

        # 연쇄 실패 감지
        if experiment.chaos_type == ChaosExperimentType.SERVICE_FAILURE.value:
            if experiment.system_recovery_time_seconds and experiment.system_recovery_time_seconds > 60:
                vulnerabilities.append("⚠️ 서비스 장애 시 의존성 연쇄 실패 가능성")

        # 리소스 한계
        cpu_observations = [o for o in self.observations if o.metric_name == 'cpu_usage' and o.chaos_value > 90]
        if cpu_observations:
            vulnerabilities.append("⚠️ CPU 병목 현상 감지")

        if not vulnerabilities:
            vulnerabilities.append("✅ 주요 취약점 없음")

        return vulnerabilities

    def run_resilience_test(self, test_name: str) -> ResilienceTest:
        """복원력 테스트 실행"""
        print(f"\n{'='*70}")
        print(f"🧪 복원력 테스트: {test_name}")
        print(f"{'='*70}\n")

        test_id = f"resilience_{int(time.time())}"

        # 다양한 카오스 실험 실행
        test_experiments = [
            self.create_experiment(
                "API 레이턴시 주입",
                "API 게이트웨이 응답 시간 증가",
                ChaosExperimentType.LATENCY_INJECTION.value,
                "api-gateway",
                10.0,
                30
            ),
            self.create_experiment(
                "데이터베이스 장애",
                "데이터베이스 서비스 다운",
                ChaosExperimentType.SERVICE_FAILURE.value,
                "database",
                20.0,
                45
            ),
            self.create_experiment(
                "리소스 고갈",
                "CPU 및 메모리 고갈",
                ChaosExperimentType.RESOURCE_EXHAUSTION.value,
                "business-service",
                15.0,
                60
            )
        ]

        # 각 실험 실행
        for exp in test_experiments:
            self.run_experiment(exp.experiment_id)

        # 복원력 점수 계산
        recovery_quality_score = self._calculate_resilience_score(test_experiments)

        # 취약점 식별
        all_vulnerabilities = []
        for exp in test_experiments:
            vulns = self.identify_vulnerabilities(exp)
            all_vulnerabilities.extend(vulns)

        # 권장사항 생성
        recommendations = self._generate_recommendations(test_experiments, all_vulnerabilities)

        # 테스트 결과 생성
        test_result = ResilienceTest(
            test_id=test_id,
            name=test_name,
            experiments=test_experiments,
            total_duration_seconds=sum(e.duration_seconds for e in test_experiments),
            failures_detected=len([e for e in test_experiments if not e.success]),
            vulnerabilities=all_vulnerabilities,
            recovery_quality_score=recovery_quality_score,
            recommendations=recommendations
        )

        self.resilience_tests.append(test_result)

        self._print_test_report(test_result)

        return test_result

    def _calculate_resilience_score(self, experiments: List[ChaosExperiment]) -> float:
        """복원력 점수 계산"""
        if not experiments:
            return 0

        success_count = sum(1 for e in experiments if e.success)
        success_rate = (success_count / len(experiments)) * 50  # 50점 만점

        # 복구 시간 점수
        avg_recovery_time = sum(e.system_recovery_time_seconds or 0 for e in experiments) / len(experiments)
        recovery_score = max(0, 50 - (avg_recovery_time / 2))  # 50점 만점

        total_score = success_rate + recovery_score

        return min(100, max(0, total_score))

    def _generate_recommendations(self, experiments: List[ChaosExperiment], vulnerabilities: List[str]) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        for exp in experiments:
            if not exp.success:
                recommendations.append(f"🔧 {exp.target_service} 서비스의 {exp.chaos_type} 복원력 개선 필요")

            if exp.system_recovery_time_seconds and exp.system_recovery_time_seconds > 60:
                recommendations.append(f"⚡ {exp.target_service}의 자동 복구 메커니즘 강화")

        if not recommendations:
            recommendations.append("✅ 시스템이 모든 카오스 실험을 성공적으로 통과")

        return recommendations

    def _print_test_report(self, test_result: ResilienceTest):
        """테스트 보고서 출력"""
        print(f"\n{'='*70}")
        print(f"📊 복원력 테스트 결과: {test_result.name}")
        print(f"{'='*70}\n")

        print(f"복원력 점수: {test_result.recovery_quality_score:.1f}/100")
        print(f"총 지속시간: {test_result.total_duration_seconds}초")
        print(f"실패한 실험: {test_result.failures_detected}개\n")

        print("🧪 실험 결과:")
        print(f"{'실험':<30} {'결과':<10} {'복구시간':<12}")
        print("-" * 55)

        for exp in test_result.experiments:
            result = "✅ 성공" if exp.success else "❌ 실패"
            recovery = f"{exp.system_recovery_time_seconds:.1f}s" if exp.system_recovery_time_seconds else "N/A"
            print(f"{exp.name:<30} {result:<10} {recovery:<12}")

        print(f"\n🔍 발견된 취약점:")
        for vuln in test_result.vulnerabilities:
            print(f"   {vuln}")

        print(f"\n💡 권장사항:")
        for rec in test_result.recommendations:
            print(f"   {rec}")

        print(f"\n{'='*70}\n")

    def get_chaos_stats(self) -> Dict:
        """카오스 통계"""
        total_experiments = len(self.experiments)
        completed_experiments = len([e for e in self.experiments.values() if e.status == "completed"])
        successful_experiments = len([e for e in self.experiments.values() if e.success])

        return {
            'total_experiments': total_experiments,
            'completed_experiments': completed_experiments,
            'successful_experiments': successful_experiments,
            'success_rate': (successful_experiments / completed_experiments * 100) if completed_experiments > 0 else 0,
            'tests_conducted': len(self.resilience_tests)
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_chaos_stats()

        print("\n" + "=" * 70)
        print("📊 카오스 엔지니어링 통계")
        print("=" * 70 + "\n")

        print(f"총 실험: {stats['total_experiments']}개")
        print(f"완료된 실험: {stats['completed_experiments']}개")
        print(f"성공한 실험: {stats['successful_experiments']}개")
        print(f"성공률: {stats['success_rate']:.1f}%")
        print(f"복원력 테스트: {stats['tests_conducted']}회\n")

        print("=" * 70 + "\n")

    def export_test_report(self, test_id: str, filename: str = None) -> Optional[str]:
        """테스트 보고서 내보내기"""
        test = next((t for t in self.resilience_tests if t.test_id == test_id), None)

        if not test:
            return None

        if filename is None:
            filename = f"resilience_test_{test_id}.json"

        report_data = {
            'test_id': test.test_id,
            'name': test.name,
            'timestamp': datetime.now().isoformat(),
            'resilience_score': test.recovery_quality_score,
            'total_duration_seconds': test.total_duration_seconds,
            'failures_detected': test.failures_detected,
            'experiments': [
                {
                    'name': exp.name,
                    'chaos_type': exp.chaos_type,
                    'success': exp.success,
                    'recovery_time': exp.system_recovery_time_seconds
                }
                for exp in test.experiments
            ],
            'vulnerabilities': test.vulnerabilities,
            'recommendations': test.recommendations
        }

        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 테스트 보고서 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    chaos = ChaosEngineer()

    if len(sys.argv) < 2:
        print("사용법: python chaos_engineering.py [command] [args]")
        print("  experiment <name> <type> <service> - 실험 생성 및 실행")
        print("  resilience_test                     - 복원력 테스트")
        print("  stats                               - 통계")
        return

    command = sys.argv[1]

    if command == "experiment":
        name = sys.argv[2] if len(sys.argv) > 2 else "API 레이턴시 주입"
        exp_type = sys.argv[3] if len(sys.argv) > 3 else "latency_injection"
        service = sys.argv[4] if len(sys.argv) > 4 else "api-gateway"

        exp = chaos.create_experiment(
            name,
            f"{name} 테스트",
            exp_type,
            service,
            15.0,
            30
        )
        chaos.run_experiment(exp.experiment_id)

    elif command == "resilience_test":
        chaos.run_resilience_test("MindLang 시스템 복원력 테스트")

    elif command == "stats":
        chaos.print_stats()
