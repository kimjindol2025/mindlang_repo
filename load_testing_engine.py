#!/usr/bin/env python3
"""
MindLang 부하 테스트 엔진
실시간 부하 테스트, 성능 분석, 병목 식별

기능:
- 다양한 부하 프로파일
- 점진적/일정한/스파이크 부하 생성
- 실시간 메트릭 수집
- 성능 병목 식별
- 용량 예측
- 상세 보고서 생성
"""

import json
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum
import statistics


class LoadProfile(Enum):
    """부하 프로파일"""
    CONSTANT = "constant"  # 일정한 부하
    RAMP_UP = "ramp_up"  # 점진적 증가
    SPIKE = "spike"  # 갑작스러운 스파이크
    WAVE = "wave"  # 파동 형태
    STRESS = "stress"  # 스트레스 테스트 (지속 증가)


@dataclass
class LoadConfig:
    """부하 설정"""
    profile: str
    initial_rps: float  # Requests Per Second
    peak_rps: float
    duration_seconds: int
    ramp_up_seconds: int = 0
    target_service: str = "api-gateway"
    endpoint: str = "/"


@dataclass
class ResponseMetric:
    """응답 메트릭"""
    timestamp: float
    response_time_ms: float
    status_code: int
    error: bool
    request_id: str


@dataclass
class LoadTestResult:
    """부하 테스트 결과"""
    test_id: str
    timestamp: float
    config: LoadConfig
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    throughput_mbps: float
    peak_rps_achieved: float
    bottlenecks: List[str]
    capacity_forecast: Dict


class LoadTestingEngine:
    """부하 테스트 엔진"""

    def __init__(self):
        self.test_results: List[LoadTestResult] = []
        self.active_test: Optional[Tuple[str, LoadConfig]] = None
        self.metrics_history: List[ResponseMetric] = []

    def create_load_config(
        self,
        profile: str,
        initial_rps: float,
        peak_rps: float,
        duration_seconds: int,
        target_service: str = "api-gateway"
    ) -> LoadConfig:
        """부하 설정 생성"""
        config = LoadConfig(
            profile=profile,
            initial_rps=initial_rps,
            peak_rps=peak_rps,
            duration_seconds=duration_seconds,
            target_service=target_service
        )

        print(f"\n✅ 부하 설정 생성")
        print(f"   프로파일: {profile}")
        print(f"   초기 RPS: {initial_rps}")
        print(f"   최고 RPS: {peak_rps}")
        print(f"   지속시간: {duration_seconds}초\n")

        return config

    def run_load_test(self, config: LoadConfig) -> LoadTestResult:
        """부하 테스트 실행"""
        test_id = f"load_test_{int(time.time())}"

        print(f"\n{'='*70}")
        print(f"🔥 부하 테스트 시작: {test_id}")
        print(f"{'='*70}\n")

        print(f"프로파일: {config.profile}")
        print(f"대상: {config.target_service}")
        print(f"지속시간: {config.duration_seconds}초\n")

        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []

        # 시뮬레이션: 부하 생성 및 응답 수집
        for second in range(config.duration_seconds + 5):
            current_rps = self._calculate_rps(config, second)

            # 이 초 동안 생성할 요청 수
            requests_this_second = max(0, int(current_rps))

            if second % 5 == 0 and second > 0:
                print(f"   [{second}s] RPS: {current_rps:.0f}, 총 요청: {total_requests}개")

            for _ in range(requests_this_second):
                total_requests += 1

                # 시뮬레이션: 응답 생성
                response_time, success = self._simulate_response(config, current_rps)

                response_times.append(response_time)

                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1

                metric = ResponseMetric(
                    timestamp=time.time(),
                    response_time_ms=response_time,
                    status_code=200 if success else 500,
                    error=not success,
                    request_id=f"req_{total_requests}"
                )

                self.metrics_history.append(metric)

            time.sleep(0.01)  # 실제 시간 시뮬레이션

        end_time = time.time()
        total_duration = end_time - start_time

        # 통계 계산
        if response_times:
            response_times_sorted = sorted(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            avg_response = statistics.mean(response_times)
            p50_response = response_times_sorted[int(len(response_times) * 0.50)]
            p95_response = response_times_sorted[int(len(response_times) * 0.95)]
            p99_response = response_times_sorted[int(len(response_times) * 0.99)]
        else:
            min_response = max_response = avg_response = p50_response = p95_response = p99_response = 0

        rps = total_requests / total_duration
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # 병목 지점 식별
        bottlenecks = self._identify_bottlenecks(
            avg_response,
            error_rate,
            config.peak_rps,
            rps
        )

        # 용량 예측
        capacity_forecast = self._forecast_capacity(config, response_times, error_rate)

        result = LoadTestResult(
            test_id=test_id,
            timestamp=time.time(),
            config=config,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            min_response_time_ms=min_response,
            max_response_time_ms=max_response,
            avg_response_time_ms=avg_response,
            p50_response_time_ms=p50_response,
            p95_response_time_ms=p95_response,
            p99_response_time_ms=p99_response,
            requests_per_second=rps,
            error_rate=error_rate,
            throughput_mbps=rps * 1.024 / 1024,  # 대략적 계산
            peak_rps_achieved=config.peak_rps,
            bottlenecks=bottlenecks,
            capacity_forecast=capacity_forecast
        )

        self.test_results.append(result)

        self._print_test_report(result)

        return result

    def _calculate_rps(self, config: LoadConfig, second: int) -> float:
        """초 단위 RPS 계산"""
        if config.profile == LoadProfile.CONSTANT.value:
            return config.initial_rps

        elif config.profile == LoadProfile.RAMP_UP.value:
            if second < config.duration_seconds:
                progress = second / config.duration_seconds
                return config.initial_rps + (config.peak_rps - config.initial_rps) * progress
            else:
                return config.initial_rps  # 복구

        elif config.profile == LoadProfile.SPIKE.value:
            if 5 <= second <= 15:  # 10초 스파이크
                return config.peak_rps
            else:
                return config.initial_rps

        elif config.profile == LoadProfile.WAVE.value:
            # 사인 파동
            progress = (second % 20) / 20
            return config.initial_rps + (config.peak_rps - config.initial_rps) * (0.5 + 0.5 * (progress - 0.5) * 2)

        elif config.profile == LoadProfile.STRESS.value:
            # 스트레스: 지속적으로 증가
            return config.initial_rps + (config.peak_rps - config.initial_rps) * (second / config.duration_seconds)

        return config.initial_rps

    def _simulate_response(self, config: LoadConfig, current_rps: float) -> Tuple[float, bool]:
        """응답 시뮬레이션"""
        # 기본 응답 시간
        base_response = random.gauss(150, 30)

        # 부하가 높을수록 응답시간 증가
        load_factor = current_rps / (config.peak_rps if config.peak_rps > 0 else 100)
        response_time = base_response * (1 + load_factor * 2)

        # 에러 가능성
        error_probability = min(0.1, load_factor * 0.1)
        success = random.random() > error_probability

        return max(10, response_time), success

    def _identify_bottlenecks(
        self,
        avg_response: float,
        error_rate: float,
        peak_rps: float,
        achieved_rps: float
    ) -> List[str]:
        """병목 지점 식별"""
        bottlenecks = []

        if avg_response > 200:
            bottlenecks.append("⚠️ 높은 평균 응답시간 (200ms 초과)")

        if error_rate > 1.0:
            bottlenecks.append("⚠️ 높은 에러율 (1% 초과)")

        if achieved_rps < peak_rps * 0.8:
            bottlenecks.append("⚠️ 목표 RPS 미달성 (80% 미만)")

        if error_rate > 5.0:
            bottlenecks.append("🔴 치명적인 에러율 (5% 초과)")

        if not bottlenecks:
            bottlenecks.append("✅ 주요 병목 없음")

        return bottlenecks

    def _forecast_capacity(
        self,
        config: LoadConfig,
        response_times: List[float],
        error_rate: float
    ) -> Dict:
        """용량 예측"""
        if not response_times:
            return {'max_safe_rps': 0, 'recommendation': '테스트 데이터 부족'}

        avg_response = statistics.mean(response_times)

        # 안전한 최대 RPS (에러율 1% 이하 유지)
        if error_rate < 1.0:
            max_safe_rps = config.peak_rps * 1.5
            recommendation = "현재 성능으로 50% 더 많은 부하 처리 가능"
        elif error_rate < 2.0:
            max_safe_rps = config.peak_rps * 1.2
            recommendation = "신중한 증가 필요 (최대 20%)"
        else:
            max_safe_rps = config.peak_rps * 0.8
            recommendation = "용량 스케일링 시급 (현재 80% 수준으로 축소)"

        return {
            'max_safe_rps': max_safe_rps,
            'estimated_scaling_factor': max_safe_rps / config.peak_rps,
            'recommendation': recommendation,
            'avg_response_time_baseline': avg_response
        }

    def _print_test_report(self, result: LoadTestResult):
        """테스트 보고서 출력"""
        print(f"\n{'='*70}")
        print(f"📊 부하 테스트 결과")
        print(f"{'='*70}\n")

        print(f"총 요청: {result.total_requests}개")
        print(f"성공: {result.successful_requests}개 ({(result.successful_requests/result.total_requests*100):.1f}%)")
        print(f"실패: {result.failed_requests}개 ({(result.failed_requests/result.total_requests*100):.1f}%)\n")

        print(f"응답시간:")
        print(f"  최소: {result.min_response_time_ms:.1f}ms")
        print(f"  평균: {result.avg_response_time_ms:.1f}ms")
        print(f"  P50:  {result.p50_response_time_ms:.1f}ms")
        print(f"  P95:  {result.p95_response_time_ms:.1f}ms")
        print(f"  P99:  {result.p99_response_time_ms:.1f}ms")
        print(f"  최대: {result.max_response_time_ms:.1f}ms\n")

        print(f"처리량:")
        print(f"  RPS: {result.requests_per_second:.1f}")
        print(f"  최고 RPS: {result.peak_rps_achieved:.1f}\n")

        print(f"🔍 병목 지점:")
        for bottleneck in result.bottlenecks:
            print(f"  {bottleneck}")

        print(f"\n📈 용량 예측:")
        forecast = result.capacity_forecast
        print(f"  안전한 최대 RPS: {forecast.get('max_safe_rps', 0):.1f}")
        print(f"  스케일 계수: {forecast.get('estimated_scaling_factor', 0):.1f}x")
        print(f"  권장사항: {forecast.get('recommendation', 'N/A')}")

        print(f"\n{'='*70}\n")

    def get_test_stats(self) -> Dict:
        """테스트 통계"""
        if not self.test_results:
            return {}

        avg_error_rate = statistics.mean(t.error_rate for t in self.test_results)
        avg_response = statistics.mean(t.avg_response_time_ms for t in self.test_results)
        max_rps = max(t.peak_rps_achieved for t in self.test_results)

        return {
            'total_tests': len(self.test_results),
            'total_requests': sum(t.total_requests for t in self.test_results),
            'avg_error_rate': avg_error_rate,
            'avg_response_time': avg_response,
            'max_rps_achieved': max_rps
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_test_stats()

        print("\n" + "=" * 70)
        print("📊 부하 테스트 엔진 통계")
        print("=" * 70 + "\n")

        print(f"총 테스트: {stats.get('total_tests', 0)}회")
        print(f"총 요청: {stats.get('total_requests', 0)}개")
        print(f"평균 에러율: {stats.get('avg_error_rate', 0):.2f}%")
        print(f"평균 응답시간: {stats.get('avg_response_time', 0):.1f}ms")
        print(f"최고 RPS: {stats.get('max_rps_achieved', 0):.1f}\n")

        print("=" * 70 + "\n")

    def export_test_report(self, test_id: str, filename: str = None) -> Optional[str]:
        """테스트 보고서 내보내기"""
        result = next((t for t in self.test_results if t.test_id == test_id), None)

        if not result:
            return None

        if filename is None:
            filename = f"load_test_{test_id}.json"

        report_data = {
            'test_id': result.test_id,
            'timestamp': datetime.fromtimestamp(result.timestamp).isoformat(),
            'config': asdict(result.config),
            'total_requests': result.total_requests,
            'error_rate': result.error_rate,
            'response_times': {
                'min': result.min_response_time_ms,
                'avg': result.avg_response_time_ms,
                'p50': result.p50_response_time_ms,
                'p95': result.p95_response_time_ms,
                'p99': result.p99_response_time_ms,
                'max': result.max_response_time_ms
            },
            'bottlenecks': result.bottlenecks,
            'capacity_forecast': result.capacity_forecast
        }

        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)

            print(f"✅ 테스트 보고서 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    engine = LoadTestingEngine()

    if len(sys.argv) < 2:
        print("사용법: python load_testing_engine.py [command] [args]")
        print("  test <profile> <initial_rps> <peak_rps> <duration> - 부하 테스트 실행")
        print("  stats                                                - 통계")
        return

    command = sys.argv[1]

    if command == "test":
        profile = sys.argv[2] if len(sys.argv) > 2 else "ramp_up"
        initial_rps = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
        peak_rps = float(sys.argv[4]) if len(sys.argv) > 4 else 500.0
        duration = int(sys.argv[5]) if len(sys.argv) > 5 else 60

        config = engine.create_load_config(profile, initial_rps, peak_rps, duration)
        result = engine.run_load_test(config)
        engine.export_test_report(result.test_id)

    elif command == "stats":
        engine.print_stats()
