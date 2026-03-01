#!/usr/bin/env python3
"""
MindLang 통합 오케스트레이터
모든 마이크로서비스의 생명주기 관리 및 자동화

기능:
- 서비스 시작/중지/재시작
- 의존성 관리
- 자동 복구
- 상태 동기화
- 리소스 최적화
"""

import asyncio
import subprocess
import psutil
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import signal
import os


class ServiceState(str, Enum):
    """서비스 상태"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    CRASHED = "crashed"


@dataclass
class ServiceConfig:
    """서비스 설정"""
    name: str
    script: str
    port: int
    startup_time: int = 5  # 시작 대기 시간
    timeout: int = 30
    retry_count: int = 3
    dependencies: List[str] = None
    resources: Dict = None  # {"memory_mb": 512, "cpu_percent": 50}

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.resources is None:
            self.resources = {}


@dataclass
class ServiceStatus:
    """서비스 상태"""
    name: str
    state: ServiceState
    port: int
    pid: Optional[int] = None
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    uptime: float = 0.0
    error_count: int = 0
    restart_count: int = 0
    last_check: float = 0.0
    last_error: Optional[str] = None
    startup_time: float = 0.0


class MindLangOrchestrator:
    """MindLang 오케스트레이터"""

    def __init__(self, config_file: str = 'orchestrator_config.json'):
        self.config_file = config_file
        self.services: Dict[str, ServiceConfig] = {}
        self.statuses: Dict[str, ServiceStatus] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.start_times: Dict[str, float] = {}
        self.load_config()

    def load_config(self):
        """설정 로드"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                for service_data in data.get('services', []):
                    config = ServiceConfig(**service_data)
                    self.services[config.name] = config
                    self.statuses[config.name] = ServiceStatus(
                        name=config.name,
                        state=ServiceState.STOPPED,
                        port=config.port
                    )
        except FileNotFoundError:
            self._create_default_config()

    def _create_default_config(self):
        """기본 설정 생성"""
        default_config = {
            'services': [
                {
                    'name': 'gateway',
                    'script': 'python api_gateway.py',
                    'port': 8100,
                    'startup_time': 3,
                    'dependencies': [],
                    'resources': {'memory_mb': 256}
                },
                {
                    'name': 'dashboard',
                    'script': 'python realtime_dashboard.py',
                    'port': 8000,
                    'startup_time': 5,
                    'dependencies': ['gateway'],
                    'resources': {'memory_mb': 512}
                },
                {
                    'name': 'learning',
                    'script': 'python learning_engine.py',
                    'port': 8001,
                    'startup_time': 5,
                    'dependencies': ['gateway'],
                    'resources': {'memory_mb': 512}
                },
                {
                    'name': 'benchmark',
                    'script': 'python ai_performance_benchmark.py',
                    'port': 8002,
                    'startup_time': 5,
                    'dependencies': ['gateway'],
                    'resources': {'memory_mb': 1024}
                },
                {
                    'name': 'analyzer',
                    'script': 'python decision_history_analyzer.py',
                    'port': 8003,
                    'startup_time': 5,
                    'dependencies': ['gateway'],
                    'resources': {'memory_mb': 512}
                }
            ]
        }

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        self.load_config()

    async def start_service(self, service_name: str) -> bool:
        """서비스 시작"""
        if service_name not in self.services:
            return False

        config = self.services[service_name]
        status = self.statuses[service_name]

        # 의존성 확인
        for dep in config.dependencies:
            if self.statuses.get(dep, {}).state != ServiceState.HEALTHY:
                print(f"⚠️  {service_name}: 의존성 {dep} 시작 필요")
                if not await self.start_service(dep):
                    status.state = ServiceState.STOPPED
                    status.last_error = f"의존성 {dep} 시작 실패"
                    return False

        status.state = ServiceState.STARTING
        print(f"🚀 {service_name} 시작 중... (포트: {config.port})")

        try:
            # 포트 사용 확인
            if self._is_port_in_use(config.port):
                print(f"⚠️  포트 {config.port} 이미 사용 중, 기존 프로세스 종료")
                self._kill_port_process(config.port)
                await asyncio.sleep(1)

            # 프로세스 시작
            process = subprocess.Popen(
                config.script,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes[service_name] = process
            self.start_times[service_name] = time.time()
            status.pid = process.pid
            status.startup_time = time.time()

            # 시작 시간 대기
            await asyncio.sleep(config.startup_time)

            # 포트 확인
            if self._is_port_in_use(config.port):
                status.state = ServiceState.HEALTHY
                print(f"✅ {service_name} 정상 시작 (PID: {process.pid})")
                return True
            else:
                status.state = ServiceState.CRASHED
                status.last_error = f"포트 {config.port} 응답 없음"
                print(f"❌ {service_name} 시작 실패: 포트 응답 없음")
                return False

        except Exception as e:
            status.state = ServiceState.CRASHED
            status.last_error = str(e)
            print(f"❌ {service_name} 시작 오류: {e}")
            return False

    async def stop_service(self, service_name: str) -> bool:
        """서비스 중지"""
        if service_name not in self.services:
            return False

        status = self.statuses[service_name]
        status.state = ServiceState.STOPPING

        print(f"🛑 {service_name} 중지 중...")

        try:
            if service_name in self.processes:
                process = self.processes[service_name]
                process.terminate()

                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                del self.processes[service_name]

            status.state = ServiceState.STOPPED
            print(f"✅ {service_name} 중지 완료")
            return True

        except Exception as e:
            status.last_error = str(e)
            print(f"❌ {service_name} 중지 오류: {e}")
            return False

    async def restart_service(self, service_name: str) -> bool:
        """서비스 재시작"""
        print(f"🔄 {service_name} 재시작...")

        if await self.stop_service(service_name):
            await asyncio.sleep(2)
            return await self.start_service(service_name)

        return False

    async def start_all(self) -> Dict[str, bool]:
        """모든 서비스 시작"""
        print("\n🚀 MindLang 전체 시작\n")
        results = {}

        # 의존성 순서로 정렬
        sorted_services = self._topological_sort()

        for service_name in sorted_services:
            success = await self.start_service(service_name)
            results[service_name] = success

            if not success:
                print(f"⚠️  {service_name} 시작 실패, 계속 진행...")

        print(f"\n📊 시작 결과: {sum(results.values())}/{len(results)}")
        return results

    async def stop_all(self) -> Dict[str, bool]:
        """모든 서비스 중지"""
        print("\n🛑 MindLang 전체 중지\n")
        results = {}

        # 역순으로 중지
        for service_name in reversed(self._topological_sort()):
            success = await self.stop_service(service_name)
            results[service_name] = success

        print(f"\n📊 중지 결과: {sum(results.values())}/{len(results)}")
        return results

    async def health_check(self) -> Dict[str, ServiceStatus]:
        """모든 서비스 헬스 체크"""
        for service_name, config in self.services.items():
            status = self.statuses[service_name]
            status.last_check = time.time()

            # 프로세스 확인
            if service_name not in self.processes:
                if status.state in [ServiceState.RUNNING, ServiceState.HEALTHY]:
                    status.state = ServiceState.CRASHED
                    status.error_count += 1
                    print(f"❌ {service_name}: 프로세스 없음")
                continue

            process = self.processes[service_name]

            # 프로세스 실행 확인
            if process.poll() is not None:
                status.state = ServiceState.CRASHED
                status.error_count += 1
                status.last_error = "프로세스 종료됨"
                print(f"❌ {service_name}: 프로세스 종료")

                # 자동 재시작
                if status.restart_count < 3:
                    status.restart_count += 1
                    print(f"🔄 {service_name} 자동 재시작 ({status.restart_count}/3)")
                    await self.restart_service(service_name)
                continue

            # 리소스 모니터링
            try:
                p = psutil.Process(process.pid)
                mem_info = p.memory_info()
                status.memory_mb = mem_info.rss / 1024 / 1024
                status.cpu_percent = p.cpu_percent(interval=0.1)
                status.uptime = time.time() - self.start_times.get(service_name, time.time())

                # 리소스 제한 확인
                resources = config.resources
                if resources.get('memory_mb') and status.memory_mb > resources['memory_mb']:
                    status.state = ServiceState.DEGRADED
                    print(f"⚠️  {service_name}: 메모리 초과 ({status.memory_mb:.1f}MB > {resources['memory_mb']}MB)")
                elif status.state != ServiceState.CRASHED:
                    status.state = ServiceState.HEALTHY

            except psutil.NoSuchProcess:
                status.state = ServiceState.CRASHED

        return self.statuses

    async def monitor_continuously(self, interval: int = 30):
        """지속적 모니터링"""
        print(f"\n📊 모니터링 시작 (간격: {interval}초)\n")

        try:
            while True:
                await self.health_check()

                # 상태 출력
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 서비스 상태:")
                for name, status in self.statuses.items():
                    icon = {
                        'healthy': '✅',
                        'degraded': '⚠️',
                        'crashed': '❌',
                        'stopped': '🛑'
                    }.get(status.state.value, '❓')

                    print(f"{icon} {name:<15} | 상태: {status.state.value:<10} | "
                          f"메모리: {status.memory_mb:>6.1f}MB | CPU: {status.cpu_percent:>5.1f}%")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n모니터링 중지")

    def _is_port_in_use(self, port: int) -> bool:
        """포트 사용 확인"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
        except:
            pass
        return False

    def _kill_port_process(self, port: int):
        """포트 사용 중인 프로세스 종료"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.net_connections():
                        if conn.laddr.port == port:
                            proc.kill()
                            print(f"프로세스 {proc.pid} 종료 (포트 {port})")
                except:
                    pass
        except:
            pass

    def _topological_sort(self) -> List[str]:
        """의존성을 고려한 토폴로지 정렬"""
        visited = set()
        result = []

        def visit(name):
            if name in visited:
                return
            visited.add(name)

            config = self.services.get(name)
            if config:
                for dep in config.dependencies:
                    visit(dep)

            result.append(name)

        for service_name in self.services:
            visit(service_name)

        return result

    def get_status_summary(self) -> Dict:
        """상태 요약"""
        healthy_count = sum(
            1 for s in self.statuses.values()
            if s.state == ServiceState.HEALTHY
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'total_services': len(self.services),
            'healthy_services': healthy_count,
            'total_uptime': sum(s.uptime for s in self.statuses.values()),
            'total_memory_mb': sum(s.memory_mb for s in self.statuses.values()),
            'total_errors': sum(s.error_count for s in self.statuses.values()),
            'services': {
                name: {
                    'state': status.state.value,
                    'memory_mb': status.memory_mb,
                    'cpu_percent': status.cpu_percent,
                    'uptime': status.uptime,
                    'errors': status.error_count
                }
                for name, status in self.statuses.items()
            }
        }

    def save_status(self):
        """상태 저장"""
        summary = self.get_status_summary()
        with open('orchestrator_status.json', 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


# CLI 인터페이스
async def main():
    """메인 함수"""
    import sys

    orchestrator = MindLangOrchestrator()

    if len(sys.argv) < 2:
        print("사용법: python orchestrator.py [start|stop|restart|status|monitor|service]")
        print("  start              - 모든 서비스 시작")
        print("  stop               - 모든 서비스 중지")
        print("  restart            - 모든 서비스 재시작")
        print("  status             - 상태 조회")
        print("  monitor            - 지속적 모니터링")
        print("  service <name> start   - 특정 서비스 시작")
        print("  service <name> stop    - 특정 서비스 중지")
        return

    command = sys.argv[1]

    if command == 'start':
        await orchestrator.start_all()
        await orchestrator.monitor_continuously()

    elif command == 'stop':
        await orchestrator.stop_all()

    elif command == 'restart':
        await orchestrator.stop_all()
        await asyncio.sleep(2)
        await orchestrator.start_all()
        await orchestrator.monitor_continuously()

    elif command == 'status':
        await orchestrator.health_check()
        summary = orchestrator.get_status_summary()
        print("\n📊 시스템 상태 요약\n")
        print(f"건강한 서비스: {summary['healthy_services']}/{summary['total_services']}")
        print(f"총 메모리: {summary['total_memory_mb']:.1f}MB")
        print(f"총 에러: {summary['total_errors']}")

        print("\n서비스별 상태:")
        for name, info in summary['services'].items():
            icon = '✅' if info['state'] == 'healthy' else '❌'
            print(f"{icon} {name:<15} | 메모리: {info['memory_mb']:>6.1f}MB | "
                  f"CPU: {info['cpu_percent']:>5.1f}%")

    elif command == 'monitor':
        await orchestrator.start_all()
        await orchestrator.monitor_continuously(interval=30)

    elif command == 'service':
        if len(sys.argv) < 4:
            print("사용법: python orchestrator.py service <name> <start|stop|restart>")
            return

        service_name = sys.argv[2]
        action = sys.argv[3]

        if action == 'start':
            await orchestrator.start_service(service_name)
        elif action == 'stop':
            await orchestrator.stop_service(service_name)
        elif action == 'restart':
            await orchestrator.restart_service(service_name)


if __name__ == "__main__":
    asyncio.run(main())
