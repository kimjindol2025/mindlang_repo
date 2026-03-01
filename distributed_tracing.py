#!/usr/bin/env python3
"""
MindLang 분산 추적 시스템
마이크로서비스 간 요청 흐름을 추적하고 성능 병목 식별

기능:
- 분산 트레이스 생성 및 추적
- 서비스 간 호출 체인 추적
- 성능 병목 자동 식별
- 지연시간 분석
- 서비스 맵 생성
- 의존성 분석
"""

import json
import time
import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SpanStatus(Enum):
    """스팬 상태"""
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class Tag:
    """스팬 태그"""
    key: str
    value: str


@dataclass
class Log:
    """스팬 로그"""
    timestamp: float
    message: str
    level: str = "info"  # info, warning, error


@dataclass
class Span:
    """분산 추적 스팬"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "running"
    tags: List[Tag] = field(default_factory=list)
    logs: List[Log] = field(default_factory=list)
    error_message: Optional[str] = None
    http_status_code: Optional[int] = None
    request_size_bytes: int = 0
    response_size_bytes: int = 0

    def end(self, status: str = SpanStatus.SUCCESS.value):
        """스팬 종료"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_tag(self, key: str, value: str):
        """태그 추가"""
        self.tags.append(Tag(key=key, value=value))

    def add_log(self, message: str, level: str = "info"):
        """로그 추가"""
        self.logs.append(Log(timestamp=time.time(), message=message, level=level))


@dataclass
class Trace:
    """전체 트레이스 (여러 스팬)"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = 0.0
    end_time: Optional[float] = None
    total_duration_ms: float = 0.0
    service_count: int = 0
    error_count: int = 0
    root_service: Optional[str] = None

    def add_span(self, span: Span):
        """스팬 추가"""
        self.spans.append(span)

    def finalize(self):
        """트레이스 완료"""
        if self.spans:
            self.start_time = min(s.start_time for s in self.spans)
            self.end_time = max((s.end_time or time.time()) for s in self.spans)
            self.total_duration_ms = (self.end_time - self.start_time) * 1000
            self.service_count = len(set(s.service_name for s in self.spans))
            self.error_count = sum(1 for s in self.spans if s.status == SpanStatus.ERROR.value)

            root_spans = [s for s in self.spans if s.parent_span_id is None]
            if root_spans:
                self.root_service = root_spans[0].service_name


class DistributedTracer:
    """분산 추적 시스템"""

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.active_traces: Dict[str, Trace] = {}
        self.service_map: Dict[str, List[str]] = {}  # service → [dependent_services]
        self.span_duration_stats: Dict[str, List[float]] = {}  # operation → [durations]

    def create_trace(self, root_service: str, root_operation: str) -> str:
        """새 트레이스 시작"""
        trace_id = str(uuid.uuid4())
        trace = Trace(trace_id=trace_id)

        # 루트 스팬 생성
        root_span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=None,
            service_name=root_service,
            operation_name=root_operation,
            start_time=time.time()
        )

        trace.add_span(root_span)
        trace.root_service = root_service

        self.active_traces[trace_id] = trace
        print(f"🟢 트레이스 시작: {trace_id}")

        return trace_id

    def create_span(self, trace_id: str, parent_span_id: str, service_name: str, operation_name: str) -> Span:
        """자식 스팬 생성"""
        if trace_id not in self.active_traces:
            print(f"❌ 트레이스 {trace_id}를 찾을 수 없음")
            return None

        trace = self.active_traces[trace_id]

        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            service_name=service_name,
            operation_name=operation_name,
            start_time=time.time()
        )

        trace.add_span(span)

        # 서비스 맵 업데이트
        root_service = trace.root_service
        if root_service not in self.service_map:
            self.service_map[root_service] = []

        if service_name not in self.service_map[root_service]:
            self.service_map[root_service].append(service_name)

        return span

    def end_span(self, span: Span, status: str = SpanStatus.SUCCESS.value, error_msg: str = None):
        """스팬 종료"""
        if error_msg:
            span.error_message = error_msg
            status = SpanStatus.ERROR.value

        span.end(status)

        # 통계 업데이트
        operation = f"{span.service_name}.{span.operation_name}"
        if operation not in self.span_duration_stats:
            self.span_duration_stats[operation] = []

        self.span_duration_stats[operation].append(span.duration_ms)

    def end_trace(self, trace_id: str):
        """트레이스 완료"""
        if trace_id not in self.active_traces:
            return

        trace = self.active_traces[trace_id]
        trace.finalize()

        self.traces[trace_id] = trace
        del self.active_traces[trace_id]

        print(f"🟡 트레이스 완료: {trace_id} ({trace.total_duration_ms:.1f}ms)")

    def simulate_request_flow(self, root_service: str = "api-gateway") -> str:
        """요청 흐름 시뮬레이션"""
        print(f"\n🔄 요청 흐름 시뮬레이션: {root_service}\n")

        trace_id = self.create_trace(root_service, "http.request")

        # 시뮬레이션 흐름
        root_span = self.active_traces[trace_id].spans[0]

        # API Gateway 처리
        time.sleep(0.01)

        # Auth Service 호출
        auth_span = self.create_span(trace_id, root_span.span_id, "auth-service", "authenticate")
        auth_span.add_tag("user", "user123")
        time.sleep(random.uniform(0.01, 0.05))
        self.end_span(auth_span, SpanStatus.SUCCESS.value)

        # Business Logic Service 호출
        logic_span = self.create_span(trace_id, root_span.span_id, "business-service", "process_request")
        logic_span.add_tag("request_type", "data_process")

        # DB 쿼리
        db_span = self.create_span(trace_id, logic_span.span_id, "database", "query")
        db_span.add_tag("query_type", "select")
        db_span.add_tag("table", "users")
        time.sleep(random.uniform(0.02, 0.1))
        self.end_span(db_span, SpanStatus.SUCCESS.value)

        # Cache 조회
        cache_span = self.create_span(trace_id, logic_span.span_id, "cache", "get")
        cache_span.add_tag("key", "user_data_123")
        time.sleep(0.001)
        self.end_span(cache_span, SpanStatus.SUCCESS.value)

        time.sleep(random.uniform(0.05, 0.1))
        self.end_span(logic_span, SpanStatus.SUCCESS.value)

        # 응답 생성
        response_span = self.create_span(trace_id, root_span.span_id, "api-gateway", "format_response")
        time.sleep(0.005)
        self.end_span(response_span, SpanStatus.SUCCESS.value)

        # 루트 스팬 종료
        root_span.end(SpanStatus.SUCCESS.value)
        self.end_trace(trace_id)

        return trace_id

    def identify_bottlenecks(self) -> Dict:
        """병목 지점 식별"""
        print(f"\n🔍 병목 지점 분석\n")

        bottlenecks = {
            'slowest_operations': [],
            'most_common_errors': [],
            'critical_paths': []
        }

        # 가장 느린 작업
        operation_stats = {}

        for operation, durations in self.span_duration_stats.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)

                operation_stats[operation] = {
                    'avg_ms': avg_duration,
                    'max_ms': max_duration,
                    'min_ms': min_duration,
                    'count': len(durations)
                }

        # 느린 순서로 정렬
        slowest = sorted(operation_stats.items(), key=lambda x: x[1]['avg_ms'], reverse=True)

        for operation, stats in slowest[:5]:
            print(f"🐢 {operation}")
            print(f"   평균: {stats['avg_ms']:.2f}ms, 최대: {stats['max_ms']:.2f}ms")
            bottlenecks['slowest_operations'].append({
                'operation': operation,
                'avg_ms': stats['avg_ms'],
                'max_ms': stats['max_ms'],
                'count': stats['count']
            })

        # 에러 분석
        error_traces = [t for t in self.traces.values() if t.error_count > 0]
        if error_traces:
            print(f"\n❌ 에러 발생 트레이스: {len(error_traces)}개")
            for trace in error_traces[:3]:
                error_spans = [s for s in trace.spans if s.status == SpanStatus.ERROR.value]
                for span in error_spans:
                    print(f"   - {span.service_name}.{span.operation_name}: {span.error_message}")

        return bottlenecks

    def generate_service_map(self) -> Dict:
        """서비스 맵 생성"""
        print(f"\n🗺️  서비스 맵\n")

        service_map = {}

        for service, dependents in self.service_map.items():
            service_map[service] = dependents
            print(f"{service}")
            for dep in dependents:
                print(f"  └─ {dep}")

        return service_map

    def get_trace_details(self, trace_id: str) -> Optional[Dict]:
        """트레이스 상세 정보"""
        if trace_id not in self.traces:
            return None

        trace = self.traces[trace_id]

        details = {
            'trace_id': trace.trace_id,
            'total_duration_ms': trace.total_duration_ms,
            'service_count': trace.service_count,
            'span_count': len(trace.spans),
            'error_count': trace.error_count,
            'root_service': trace.root_service,
            'spans': []
        }

        for span in sorted(trace.spans, key=lambda s: s.start_time):
            span_detail = {
                'service': span.service_name,
                'operation': span.operation_name,
                'duration_ms': span.duration_ms,
                'status': span.status,
                'tags': [(t.key, t.value) for t in span.tags]
            }
            details['spans'].append(span_detail)

        return details

    def print_trace_timeline(self, trace_id: str):
        """트레이스 타임라인 출력"""
        if trace_id not in self.traces:
            print(f"❌ 트레이스 {trace_id}를 찾을 수 없음")
            return

        trace = self.traces[trace_id]

        print(f"\n📊 트레이스 타임라인: {trace_id}")
        print(f"   총 지속 시간: {trace.total_duration_ms:.1f}ms")
        print(f"   서비스: {trace.service_count}개, 스팬: {len(trace.spans)}개\n")

        print(f"{'서비스':<20} {'작업':<25} {'지속시간':<12} {'상태':<10}")
        print("-" * 70)

        for span in sorted(trace.spans, key=lambda s: s.start_time):
            status_symbol = "✅" if span.status == "success" else "❌" if span.status == "error" else "⏱️"
            print(f"{span.service_name:<20} {span.operation_name:<25} {span.duration_ms:<12.2f}ms {status_symbol}")

        print()

    def export_trace(self, trace_id: str, filename: str = None) -> Optional[str]:
        """트레이스 내보내기"""
        if trace_id not in self.traces:
            return None

        trace = self.traces[trace_id]

        if filename is None:
            filename = f"trace_{trace_id}.json"

        trace_data = {
            'trace_id': trace.trace_id,
            'timestamp': datetime.now().isoformat(),
            'total_duration_ms': trace.total_duration_ms,
            'service_count': trace.service_count,
            'error_count': trace.error_count,
            'root_service': trace.root_service,
            'spans': [
                {
                    'span_id': s.span_id,
                    'parent_span_id': s.parent_span_id,
                    'service': s.service_name,
                    'operation': s.operation_name,
                    'duration_ms': s.duration_ms,
                    'status': s.status,
                    'tags': {t.key: t.value for t in s.tags},
                    'error_message': s.error_message
                }
                for s in trace.spans
            ]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(trace_data, f, indent=2)

            print(f"✅ 트레이스 내보내기: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None

    def get_tracer_stats(self) -> Dict:
        """추적기 통계"""
        total_traces = len(self.traces)
        total_spans = sum(len(t.spans) for t in self.traces.values())
        error_traces = sum(1 for t in self.traces.values() if t.error_count > 0)

        avg_duration = 0
        if total_traces > 0:
            avg_duration = sum(t.total_duration_ms for t in self.traces.values()) / total_traces

        return {
            'total_traces': total_traces,
            'total_spans': total_spans,
            'error_traces': error_traces,
            'average_duration_ms': avg_duration,
            'services_tracked': len(self.service_map)
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_tracer_stats()

        print("\n" + "=" * 70)
        print("📊 분산 추적 시스템 통계")
        print("=" * 70 + "\n")

        print(f"추적된 트레이스: {stats['total_traces']}개")
        print(f"총 스팬: {stats['total_spans']}개")
        print(f"에러 트레이스: {stats['error_traces']}개")
        print(f"평균 지속시간: {stats['average_duration_ms']:.1f}ms")
        print(f"추적된 서비스: {stats['services_tracked']}개\n")

        print("=" * 70 + "\n")


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    tracer = DistributedTracer()

    if len(sys.argv) < 2:
        print("사용법: python distributed_tracing.py [command] [args]")
        print("  simulate [service]  - 요청 흐름 시뮬레이션")
        print("  bottlenecks         - 병목 지점 식별")
        print("  service_map         - 서비스 맵 생성")
        print("  stats               - 추적 통계")
        return

    command = sys.argv[1]

    if command == "simulate":
        service = sys.argv[2] if len(sys.argv) > 2 else "api-gateway"

        # 여러 번 시뮬레이션
        for i in range(3):
            trace_id = tracer.simulate_request_flow(service)
            time.sleep(0.5)

        # 타임라인 출력
        traces = list(tracer.traces.keys())
        if traces:
            tracer.print_trace_timeline(traces[-1])

    elif command == "bottlenecks":
        # 먼저 시뮬레이션
        for i in range(5):
            tracer.simulate_request_flow()

        tracer.identify_bottlenecks()

    elif command == "service_map":
        # 먼저 시뮬레이션
        for i in range(3):
            tracer.simulate_request_flow()

        tracer.generate_service_map()

    elif command == "stats":
        tracer.print_stats()
