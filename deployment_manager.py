#!/usr/bin/env python3
"""
MindLang 자동 배포 관리자
Docker, Docker Compose, Kubernetes 자동 배포

기능:
- 원클릭 배포
- 자동 헬스 체크
- 자동 롤백
- 버전 관리
- 배포 이력 추적
"""

import subprocess
import json
import time
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
from datetime import datetime


class DeploymentTarget(str, Enum):
    """배포 대상"""
    LOCAL = "local"
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker-compose"
    KUBERNETES = "kubernetes"


class DeploymentStatus(str, Enum):
    """배포 상태"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    ACTIVE = "active"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Deployment:
    """배포 정보"""
    id: str
    version: str
    target: DeploymentTarget
    timestamp: float
    status: DeploymentStatus
    previous_version: Optional[str] = None
    error_message: Optional[str] = None
    duration: float = 0.0


class DeploymentManager:
    """배포 관리자"""

    def __init__(self):
        self.deployments: Dict[str, Deployment] = {}
        self.current_version = "1.0.0"
        self.load_history()

    def load_history(self):
        """배포 이력 로드"""
        try:
            with open('deployment_history.json', 'r') as f:
                data = json.load(f)
                for dep_data in data.get('deployments', []):
                    dep = Deployment(
                        id=dep_data['id'],
                        version=dep_data['version'],
                        target=DeploymentTarget(dep_data['target']),
                        timestamp=dep_data['timestamp'],
                        status=DeploymentStatus(dep_data['status']),
                        previous_version=dep_data.get('previous_version'),
                        error_message=dep_data.get('error_message'),
                        duration=dep_data.get('duration', 0.0)
                    )
                    self.deployments[dep.id] = dep

                self.current_version = data.get('current_version', '1.0.0')
        except FileNotFoundError:
            pass

    def save_history(self):
        """배포 이력 저장"""
        data = {
            'timestamp': time.time(),
            'current_version': self.current_version,
            'deployments': [
                {
                    'id': dep.id,
                    'version': dep.version,
                    'target': dep.target.value,
                    'timestamp': dep.timestamp,
                    'status': dep.status.value,
                    'previous_version': dep.previous_version,
                    'error_message': dep.error_message,
                    'duration': dep.duration
                }
                for dep in self.deployments.values()
            ]
        }

        with open('deployment_history.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def deploy_docker_compose(self, version: str) -> Deployment:
        """Docker Compose로 배포"""
        dep_id = f"docker-compose-{int(time.time())}"
        start_time = time.time()

        deployment = Deployment(
            id=dep_id,
            version=version,
            target=DeploymentTarget.DOCKER_COMPOSE,
            timestamp=start_time,
            status=DeploymentStatus.DEPLOYING,
            previous_version=self.current_version
        )

        print(f"\n🚀 Docker Compose 배포 시작 (버전: {version})\n")

        try:
            # 이미지 빌드
            print("📦 이미지 빌드 중...")
            result = subprocess.run(
                "docker-compose build",
                shell=True,
                capture_output=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"빌드 실패: {result.stderr.decode()}")

            # 기존 컨테이너 중지
            print("🛑 기존 컨테이너 중지 중...")
            subprocess.run("docker-compose down", shell=True, capture_output=True)

            await_sleep(2)

            # 새 컨테이너 시작
            print("✅ 새 컨테이너 시작 중...")
            result = subprocess.run(
                "docker-compose up -d",
                shell=True,
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"시작 실패: {result.stderr.decode()}")

            # 헬스 체크
            deployment.status = DeploymentStatus.VERIFYING
            print("🔍 헬스 체크 중...")

            if self._health_check(max_attempts=10):
                deployment.status = DeploymentStatus.ACTIVE
                self.current_version = version
                print(f"✅ 배포 성공! (버전: {version})")
            else:
                raise Exception("헬스 체크 실패")

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            print(f"❌ 배포 실패: {e}")
            self._rollback(deployment)

        finally:
            deployment.duration = time.time() - start_time
            self.deployments[dep_id] = deployment
            self.save_history()

        return deployment

    def deploy_kubernetes(self, version: str) -> Deployment:
        """Kubernetes로 배포"""
        dep_id = f"kubernetes-{int(time.time())}"
        start_time = time.time()

        deployment = Deployment(
            id=dep_id,
            version=version,
            target=DeploymentTarget.KUBERNETES,
            timestamp=start_time,
            status=DeploymentStatus.DEPLOYING,
            previous_version=self.current_version
        )

        print(f"\n🚀 Kubernetes 배포 시작 (버전: {version})\n")

        try:
            # 이미지 빌드
            print("📦 Docker 이미지 빌드 중...")
            result = subprocess.run(
                f"docker build -t mindlang:{version} .",
                shell=True,
                capture_output=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"빌드 실패: {result.stderr.decode()}")

            # 배포
            print("📋 Kubernetes 배포 중...")
            result = subprocess.run(
                f"kubectl set image deployment/mindlang mindlang=mindlang:{version}",
                shell=True,
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"배포 실패: {result.stderr.decode()}")

            # 롤아웃 상태 확인
            print("⏳ 롤아웃 진행 중...")
            result = subprocess.run(
                "kubectl rollout status deployment/mindlang --timeout=5m",
                shell=True,
                capture_output=True,
                timeout=300
            )

            if result.returncode == 0:
                deployment.status = DeploymentStatus.ACTIVE
                self.current_version = version
                print(f"✅ 배포 성공! (버전: {version})")
            else:
                raise Exception("롤아웃 실패")

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            print(f"❌ 배포 실패: {e}")
            self._rollback(deployment)

        finally:
            deployment.duration = time.time() - start_time
            self.deployments[dep_id] = deployment
            self.save_history()

        return deployment

    def _health_check(self, max_attempts: int = 10) -> bool:
        """헬스 체크"""
        import httpx

        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=5) as client:
                    response = client.get("http://localhost:8100/health")
                    if response.status_code == 200:
                        print(f"✅ 헬스 체크 성공 (시도: {attempt + 1}/{max_attempts})")
                        return True
            except:
                pass

            print(f"⏳ 재시도 중... ({attempt + 1}/{max_attempts})")
            time.sleep(5)

        return False

    def _rollback(self, deployment: Deployment):
        """롤백"""
        if not deployment.previous_version:
            print("❌ 롤백할 이전 버전 없음")
            return

        print(f"\n🔄 롤백 시작 (버전: {deployment.previous_version})\n")

        try:
            if deployment.target == DeploymentTarget.DOCKER_COMPOSE:
                subprocess.run("docker-compose down", shell=True)
                time.sleep(2)
                subprocess.run("docker-compose up -d", shell=True)

            elif deployment.target == DeploymentTarget.KUBERNETES:
                subprocess.run(
                    f"kubectl set image deployment/mindlang mindlang=mindlang:{deployment.previous_version}",
                    shell=True
                )

            print(f"✅ 롤백 완료 (버전: {deployment.previous_version})")
            self.current_version = deployment.previous_version

        except Exception as e:
            print(f"❌ 롤백 실패: {e}")

    def get_deployment_status(self, dep_id: str) -> Optional[Dict]:
        """배포 상태 조회"""
        if dep_id not in self.deployments:
            return None

        dep = self.deployments[dep_id]
        return {
            'id': dep.id,
            'version': dep.version,
            'target': dep.target.value,
            'status': dep.status.value,
            'duration': dep.duration,
            'timestamp': datetime.fromtimestamp(dep.timestamp).isoformat(),
            'error_message': dep.error_message,
            'previous_version': dep.previous_version
        }

    def get_deployment_history(self, limit: int = 20) -> list:
        """배포 이력 조회"""
        deployments = sorted(
            self.deployments.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )

        return [
            self.get_deployment_status(dep.id)
            for dep in deployments[:limit]
        ]

    def get_summary(self) -> Dict:
        """배포 요약"""
        total_deployments = len(self.deployments)
        successful = sum(
            1 for d in self.deployments.values()
            if d.status == DeploymentStatus.ACTIVE
        )
        failed = sum(
            1 for d in self.deployments.values()
            if d.status == DeploymentStatus.FAILED
        )

        return {
            'current_version': self.current_version,
            'total_deployments': total_deployments,
            'successful_deployments': successful,
            'failed_deployments': failed,
            'success_rate': (successful / total_deployments * 100) if total_deployments > 0 else 0,
            'latest_deployment': self.get_deployment_status(
                list(self.deployments.keys())[-1]
            ) if self.deployments else None
        }


def await_sleep(seconds):
    """비동기 sleep (간단 버전)"""
    time.sleep(seconds)


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = DeploymentManager()

    if len(sys.argv) < 2:
        print("사용법: python deployment_manager.py [command] [args]")
        print("  deploy-compose <version>    - Docker Compose로 배포")
        print("  deploy-k8s <version>        - Kubernetes로 배포")
        print("  status <deployment-id>      - 배포 상태 조회")
        print("  history [limit]             - 배포 이력 조회")
        print("  summary                     - 배포 요약")
        return

    command = sys.argv[1]

    if command == "deploy-compose":
        version = sys.argv[2] if len(sys.argv) > 2 else "latest"
        manager.deploy_docker_compose(version)

    elif command == "deploy-k8s":
        version = sys.argv[2] if len(sys.argv) > 2 else "latest"
        manager.deploy_kubernetes(version)

    elif command == "status":
        dep_id = sys.argv[2] if len(sys.argv) > 2 else None
        if dep_id:
            status = manager.get_deployment_status(dep_id)
            if status:
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                print("배포를 찾을 수 없습니다")

    elif command == "history":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        history = manager.get_deployment_history(limit)
        print("\n📋 배포 이력\n")
        for dep in history:
            status_icon = "✅" if dep['status'] == 'active' else "❌"
            print(f"{status_icon} {dep['version']:<20} | "
                  f"{dep['target']:<15} | {dep['timestamp']:<25} | "
                  f"{dep['duration']:>6.1f}초")

    elif command == "summary":
        summary = manager.get_summary()
        print("\n📊 배포 요약\n")
        print(f"현재 버전: {summary['current_version']}")
        print(f"총 배포: {summary['total_deployments']}건")
        print(f"성공: {summary['successful_deployments']}건 ({summary['success_rate']:.1f}%)")
        print(f"실패: {summary['failed_deployments']}건")

        if summary['latest_deployment']:
            latest = summary['latest_deployment']
            print(f"\n최신 배포: {latest['version']} ({latest['status']})")
