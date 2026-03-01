#!/usr/bin/env python3
"""
AWS Blue-Green Deployment with Auto Fallback
무중단 자동 배포 + 자동 롤백

특징:
- Blue 환경에 새 버전 배포
- 자동 테스트 실행
- 일정 시간 모니터링 후 전환
- 문제 발생 시 자동 롤백
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DeploymentStatus(Enum):
    """배포 상태"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    TESTING = "testing"
    MONITORING = "monitoring"
    SWITCHING = "switching"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class HealthMetric:
    """헬스 체크 메트릭"""
    timestamp: float
    error_rate: float
    latency_p95: float
    cpu_usage: float
    memory_usage: float
    request_count: int

    def is_healthy(self, thresholds=None) -> bool:
        """헬스 체크"""
        if thresholds is None:
            thresholds = {
                'error_rate': 0.01,      # 1%
                'latency_p95': 500,      # 500ms
                'cpu_usage': 80,         # 80%
                'memory_usage': 85       # 85%
            }

        return (
            self.error_rate <= thresholds['error_rate'] and
            self.latency_p95 <= thresholds['latency_p95'] and
            self.cpu_usage <= thresholds['cpu_usage'] and
            self.memory_usage <= thresholds['memory_usage']
        )


class BlueGreenDeployment:
    """Blue-Green 무중단 배포"""

    def __init__(self,
                 initial_version: str = "v1.0.0",
                 monitoring_duration: int = 3600,  # 1시간
                 health_check_interval: int = 60):  # 1분
        self.blue_version = initial_version
        self.green_version = initial_version
        self.active_version = "green"
        self.monitoring_duration = monitoring_duration
        self.health_check_interval = health_check_interval
        self.status = DeploymentStatus.COMPLETED
        self.deployment_history: List[Dict] = []

    def deploy_to_blue(self, new_version: str, deployment_script: str) -> bool:
        """Blue 환경에 새 버전 배포"""
        print(f"📦 Blue 환경에 {new_version} 배포 중...")
        self.status = DeploymentStatus.DEPLOYING

        try:
            # 실제 배포 (여기서는 시뮬레이션)
            self.blue_version = new_version
            print(f"✅ Blue 배포 완료: {new_version}")
            return True
        except Exception as e:
            print(f"❌ Blue 배포 실패: {e}")
            self.status = DeploymentStatus.FAILED
            return False

    def test_blue_environment(self) -> bool:
        """Blue 환경 테스트"""
        print(f"🧪 Blue 환경 테스트 중... ({self.blue_version})")
        self.status = DeploymentStatus.TESTING

        tests = [
            ("헬스 체크", self._health_check()),
            ("API 응답", self._api_response_test()),
            ("DB 연결", self._database_connection_test()),
            ("메모리 누수", self._memory_leak_test())
        ]

        all_passed = True
        for test_name, result in tests:
            if result:
                print(f"  ✅ {test_name}: 통과")
            else:
                print(f"  ❌ {test_name}: 실패")
                all_passed = False

        return all_passed

    def monitor_blue_environment(self) -> bool:
        """Blue 환경 모니터링 (설정된 시간동안)"""
        print(f"🔍 Blue 환경 모니터링 시작... (최대 {self.monitoring_duration}초)")
        self.status = DeploymentStatus.MONITORING

        start_time = time.time()
        health_history: List[HealthMetric] = []

        while time.time() - start_time < self.monitoring_duration:
            metric = self._get_health_metric()
            health_history.append(metric)

            if not metric.is_healthy():
                print(f"❌ {int(time.time() - start_time)}초 후 이상 감지!")
                print(f"   에러율: {metric.error_rate*100:.2f}% | "
                      f"지연: {metric.latency_p95:.0f}ms | "
                      f"CPU: {metric.cpu_usage:.1f}% | "
                      f"MEM: {metric.memory_usage:.1f}%")
                return False

            # 주기적으로 상태 출력
            if len(health_history) % 3 == 0:
                print(f"  ⏱️  {int(time.time() - start_time)}초: 정상 - "
                      f"에러 {metric.error_rate*100:.2f}%, "
                      f"지연 {metric.latency_p95:.0f}ms")

            time.sleep(self.health_check_interval)

        print(f"✅ 모니터링 완료: {len(health_history)}개 체크 포인트, 모두 정상")
        return True

    def switch_to_blue(self) -> bool:
        """Green에서 Blue로 트래픽 전환"""
        print(f"🔄 트래픽을 Blue({self.blue_version})로 전환 중...")
        self.status = DeploymentStatus.SWITCHING

        try:
            # 무중단 전환 (canary/shadow traffic 등)
            old_active = self.active_version
            self.active_version = "blue"
            print(f"✅ 전환 완료: {old_active} → {self.active_version}")
            return True
        except Exception as e:
            print(f"❌ 전환 실패: {e}")
            self.status = DeploymentStatus.FAILED
            return False

    def switch_back_to_green(self) -> bool:
        """Blue에서 Green으로 롤백"""
        print(f"⚠️  Blue에서 Green({self.green_version})로 자동 롤백 중...")
        self.status = DeploymentStatus.ROLLBACK

        try:
            self.active_version = "green"
            print(f"✅ 롤백 완료: Blue → Green ({self.green_version})")
            return True
        except Exception as e:
            print(f"❌ 롤백 실패: {e}")
            self.status = DeploymentStatus.FAILED
            return False

    def cleanup_old_green(self) -> bool:
        """이전 Green 환경 정리 (안전하게)"""
        print(f"🧹 이전 Green 환경 정리... (기록 보존)")

        # 배포 히스토리에 기록
        self.deployment_history.append({
            'timestamp': time.time(),
            'active_version': self.active_version,
            'blue_version': self.blue_version,
            'green_version': self.green_version
        })

        self.green_version = self.blue_version
        print(f"✅ Green 버전 업데이트: {self.green_version}")
        return True

    def execute_deployment(self, new_version: str) -> bool:
        """전체 배포 프로세스"""
        print(f"\n{'='*60}")
        print(f"🚀 배포 시작: {self.active_version} → {new_version}")
        print(f"{'='*60}\n")

        # 1단계: Blue 배포
        if not self.deploy_to_blue(new_version, "deployment_script.sh"):
            return False

        # 2단계: Blue 테스트
        if not self.test_blue_environment():
            print("❌ 테스트 실패 → 배포 중단")
            return False

        # 3단계: Blue 모니터링
        if not self.monitor_blue_environment():
            print("❌ 모니터링 중 이상 감지 → 자동 롤백")
            return self.switch_back_to_green()

        # 4단계: Blue로 전환
        if not self.switch_to_blue():
            return False

        # 5단계: Green 정리
        if not self.cleanup_old_green():
            return False

        self.status = DeploymentStatus.COMPLETED
        print(f"\n✅ 배포 완료: {new_version}")
        return True

    # 헬퍼 메서드들 (시뮬레이션)

    def _health_check(self) -> bool:
        """헬스 체크"""
        return True

    def _api_response_test(self) -> bool:
        """API 응답 테스트"""
        return True

    def _database_connection_test(self) -> bool:
        """DB 연결 테스트"""
        return True

    def _memory_leak_test(self) -> bool:
        """메모리 누수 테스트"""
        return True

    def _get_health_metric(self) -> HealthMetric:
        """헬스 메트릭 수집"""
        import random
        return HealthMetric(
            timestamp=time.time(),
            error_rate=random.uniform(0.001, 0.005),
            latency_p95=random.uniform(100, 300),
            cpu_usage=random.uniform(40, 70),
            memory_usage=random.uniform(50, 75),
            request_count=random.randint(10000, 50000)
        )

    def get_status(self) -> Dict:
        """현재 상태"""
        return {
            'active_version': self.active_version,
            'blue_version': self.blue_version,
            'green_version': self.green_version,
            'status': self.status.value,
            'deployment_count': len(self.deployment_history)
        }


# 사용 예시
if __name__ == "__main__":
    deployer = BlueGreenDeployment()

    # 초기 상태
    print("\n🔍 초기 상태:")
    print(deployer.get_status())

    # 배포 실행
    success = deployer.execute_deployment("v2.0.0")

    # 최종 상태
    print("\n🔍 최종 상태:")
    print(deployer.get_status())
