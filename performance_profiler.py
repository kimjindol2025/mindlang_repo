#!/usr/bin/env python3
"""
MindLang 성능 프로파일러
시스템 병목 지점 찾기 및 분석

기능:
- CPU 프로파일링
- 메모리 프로파일링
- I/O 성능 분석
- 응답시간 측정
- 병목 지점 식별
"""

import time
import psutil
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from collections import defaultdict
import functools


@dataclass
class FunctionProfile:
    """함수 프로파일"""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    error_count: int = 0

    def update(self, elapsed_time: float):
        """프로파일 업데이트"""
        self.call_count += 1
        self.total_time += elapsed_time
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, elapsed_time)
        self.max_time = max(self.max_time, elapsed_time)


@dataclass
class SystemProfile:
    """시스템 프로파일"""
    timestamp: float
    duration: float
    cpu_percent: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


class PerformanceProfiler:
    """성능 프로파일러"""

    def __init__(self):
        self.function_profiles: Dict[str, FunctionProfile] = {}
        self.system_profiles: List[SystemProfile] = []
        self.last_io_counters = None
        self.last_network_io = None
        self._init_io_counters()

    def _init_io_counters(self):
        """I/O 카운터 초기화"""
        try:
            self.last_io_counters = psutil.disk_io_counters()
            self.last_network_io = psutil.net_io_counters()
        except:
            pass

    def profile_function(self, func):
        """함수 프로파일 데코레이터"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"

            if func_name not in self.function_profiles:
                self.function_profiles[func_name] = FunctionProfile(name=func_name)

            profile = self.function_profiles[func_name]

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                profile.update(elapsed)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                profile.update(elapsed)
                profile.error_count += 1
                raise

        return wrapper

    def profile_code_block(self, block_name: str):
        """코드 블록 프로파일 컨텍스트 매니저"""
        class ProfileContext:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
                self.start_time = None

            def __enter__(self):
                if self.name not in self.profiler.function_profiles:
                    self.profiler.function_profiles[self.name] = FunctionProfile(name=self.name)
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.time() - self.start_time
                self.profiler.function_profiles[self.name].update(elapsed)
                if exc_type is not None:
                    self.profiler.function_profiles[self.name].error_count += 1

        return ProfileContext(self, block_name)

    def record_system_profile(self) -> SystemProfile:
        """시스템 프로파일 기록"""
        start_time = time.time()

        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent

            # I/O 카운터
            io_counters = psutil.disk_io_counters()
            disk_read = 0.0
            disk_write = 0.0

            if self.last_io_counters:
                disk_read = (io_counters.read_bytes - self.last_io_counters.read_bytes) / 1024 / 1024
                disk_write = (io_counters.write_bytes - self.last_io_counters.write_bytes) / 1024 / 1024

            self.last_io_counters = io_counters

            # 네트워크 I/O
            net_io = psutil.net_io_counters()
            net_sent = 0.0
            net_recv = 0.0

            if self.last_network_io:
                net_sent = (net_io.bytes_sent - self.last_network_io.bytes_sent) / 1024 / 1024
                net_recv = (net_io.bytes_recv - self.last_network_io.bytes_recv) / 1024 / 1024

            self.last_network_io = net_io

            profile = SystemProfile(
                timestamp=start_time,
                duration=time.time() - start_time,
                cpu_percent=cpu,
                memory_percent=memory,
                disk_io_read_mb=disk_read,
                disk_io_write_mb=disk_write,
                network_sent_mb=net_sent,
                network_recv_mb=net_recv
            )

            self.system_profiles.append(profile)

            # 최근 1000개만 유지
            if len(self.system_profiles) > 1000:
                self.system_profiles.pop(0)

            return profile

        except Exception as e:
            print(f"프로파일 기록 오류: {e}")
            return None

    def get_bottlenecks(self, top_n: int = 10) -> List[Dict]:
        """병목 지점 식별"""
        bottlenecks = []

        for func_name, profile in self.function_profiles.items():
            bottlenecks.append({
                'function': func_name,
                'call_count': profile.call_count,
                'total_time': profile.total_time,
                'avg_time': profile.avg_time,
                'min_time': profile.min_time,
                'max_time': profile.max_time,
                'error_count': profile.error_count,
                'error_rate': (profile.error_count / profile.call_count * 100)
                if profile.call_count > 0 else 0
            })

        # 총 시간으로 정렬
        bottlenecks.sort(key=lambda x: x['total_time'], reverse=True)

        return bottlenecks[:top_n]

    def get_system_summary(self) -> Dict:
        """시스템 요약"""
        if not self.system_profiles:
            return {}

        profiles = self.system_profiles
        latest = profiles[-1]

        cpu_values = [p.cpu_percent for p in profiles]
        memory_values = [p.memory_percent for p in profiles]

        return {
            'latest': asdict(latest),
            'cpu': {
                'current': latest.cpu_percent,
                'avg': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values)
            },
            'memory': {
                'current': latest.memory_percent,
                'avg': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values)
            },
            'disk_io': {
                'total_read_mb': sum(p.disk_io_read_mb for p in profiles),
                'total_write_mb': sum(p.disk_io_write_mb for p in profiles)
            },
            'network': {
                'total_sent_mb': sum(p.network_sent_mb for p in profiles),
                'total_recv_mb': sum(p.network_recv_mb for p in profiles)
            }
        }

    def save_profile(self, filename: str = 'profile_report.json'):
        """프로파일 저장"""
        report = {
            'timestamp': time.time(),
            'function_profiles': [
                {
                    'name': name,
                    'call_count': profile.call_count,
                    'total_time': profile.total_time,
                    'avg_time': profile.avg_time,
                    'min_time': profile.min_time,
                    'max_time': profile.max_time,
                    'error_count': profile.error_count
                }
                for name, profile in self.function_profiles.items()
            ],
            'system_summary': self.get_system_summary(),
            'bottlenecks': self.get_bottlenecks()
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"프로파일 저장: {filename}")

    def print_report(self):
        """프로파일 리포트 출력"""
        print("\n" + "="*100)
        print("📊 성능 프로파일 리포트")
        print("="*100)

        # 시스템 요약
        summary = self.get_system_summary()
        if summary:
            print("\n💻 시스템 리소스")
            print(f"  CPU: {summary['cpu']['current']:.1f}% (평균: {summary['cpu']['avg']:.1f}%, 범위: {summary['cpu']['min']:.1f}%-{summary['cpu']['max']:.1f}%)")
            print(f"  메모리: {summary['memory']['current']:.1f}% (평균: {summary['memory']['avg']:.1f}%, 범위: {summary['memory']['min']:.1f}%-{summary['memory']['max']:.1f}%)")
            print(f"  디스크 읽기: {summary['disk_io']['total_read_mb']:.1f}MB")
            print(f"  디스크 쓰기: {summary['disk_io']['total_write_mb']:.1f}MB")
            print(f"  네트워크 송신: {summary['network']['total_sent_mb']:.1f}MB")
            print(f"  네트워크 수신: {summary['network']['total_recv_mb']:.1f}MB")

        # 병목 지점
        print("\n" + "-"*100)
        print("🔴 병목 지점 (Top 10)")
        print("-"*100)

        bottlenecks = self.get_bottlenecks(10)
        print(f"\n{'함수':<50} {'호출':<8} {'총시간':<12} {'평균':<10} {'에러':<8}")
        print("-"*100)

        for bn in bottlenecks:
            print(f"{bn['function']:<50} {bn['call_count']:<8} "
                  f"{bn['total_time']:<12.3f}s {bn['avg_time']:<10.6f}s {bn['error_count']:<8}")

        print("\n" + "="*100)


# 사용 예시
if __name__ == "__main__":
    profiler = PerformanceProfiler()

    # 함수 프로파일링
    @profiler.profile_function
    def slow_function():
        """느린 함수"""
        time.sleep(0.1)
        return "완료"

    @profiler.profile_function
    def fast_function():
        """빠른 함수"""
        return "완료"

    # 시뮬레이션
    print("🔍 성능 프로파일 시작\n")

    for i in range(100):
        slow_function()
        fast_function()

        # 코드 블록 프로파일
        with profiler.profile_code_block("데이터_처리"):
            time.sleep(0.01)

        # 시스템 프로파일
        if i % 10 == 0:
            profiler.record_system_profile()

    # 리포트 출력
    profiler.print_report()

    # 저장
    profiler.save_profile()
