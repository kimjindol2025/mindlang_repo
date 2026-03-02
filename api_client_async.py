#!/usr/bin/env python3
"""
MindLang 비동기 API 클라이언트 (asyncio 버전)
여러 API를 병렬로 호출하여 성능 개선

사용:
    from api_client_async import AsyncAPIClient
    import asyncio

    async def main():
        client = AsyncAPIClient()
        metrics = await client.collect_all_metrics()
        print(metrics)

    asyncio.run(main())
"""

import asyncio
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from config import Config
import logging
import time

logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class AsyncAPIClient:
    """비동기 API 클라이언트 (urllib 기반, asyncio와 스레드풀 사용)"""

    def __init__(self, timeout: float = 10.0, max_workers: int = 5, use_mock_api: bool = True):
        # Mock API 활성화
        Config.USE_MOCK_API = use_mock_api

        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # asyncio 이벤트 루프 처리 (Python 3.10+ 호환성)
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                self.loop = asyncio.get_event_loop()
                if self.loop.is_closed():
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

        if use_mock_api:
            logger.info("✓ Mock API 활성화")
        else:
            logger.info("✓ 실제 API 사용")

    def _sync_get(self, url: str) -> Dict[str, Any]:
        """동기 GET 요청 (스레드풀에서 실행)"""
        try:
            logger.debug(f"GET {url}")
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"status": "error", "message": str(e)}

    def _sync_post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """동기 POST 요청 (스레드풀에서 실행)"""
        try:
            logger.debug(f"POST {url}")
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {"status": "error", "message": str(e)}

    async def prometheus_query_async(self, query: str) -> Dict[str, Any]:
        """비동기 Prometheus 쿼리"""
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/query?query={query}"
        return await self.loop.run_in_executor(self.executor, self._sync_get, url)

    async def k8s_list_deployments_async(self, namespace: str = "default") -> Dict[str, Any]:
        """비동기 Kubernetes Deployment 조회"""
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments"
        return await self.loop.run_in_executor(self.executor, self._sync_get, url)

    async def alertmanager_list_alerts_async(self) -> List[Dict[str, Any]]:
        """비동기 AlertManager 알림 조회"""
        base_url = Config.get_api_url("alertmanager")
        url = f"{base_url}/api/v1/alerts"
        result = await self.loop.run_in_executor(self.executor, self._sync_get, url)
        return result if isinstance(result, list) else result.get('data', [])

    async def registry_list_tags_async(self, name: str = "mindlang") -> Dict[str, Any]:
        """비동기 Docker Registry 태그 조회"""
        base_url = Config.get_api_url("docker_registry")
        url = f"{base_url}/v2/{name}/tags/list"
        return await self.loop.run_in_executor(self.executor, self._sync_get, url)

    async def datadog_get_host_async(self, hostname: str = "prod-01") -> Dict[str, Any]:
        """비동기 Datadog 호스트 조회"""
        base_url = Config.get_api_url("datadog")
        url = f"{base_url}/api/v1/host/{hostname}"
        return await self.loop.run_in_executor(self.executor, self._sync_get, url)

    # ========================================================================
    # 병렬 메트릭 수집
    # ========================================================================

    async def collect_error_metrics(self) -> Dict[str, Any]:
        """에러 관련 메트릭 수집 (병렬)"""
        logger.info("수집 중: 에러 메트릭 (Prometheus + AlertManager)")

        start = time.time()

        # 병렬로 2개 API 호출
        prometheus_task = self.prometheus_query_async("http_error_rate")
        alerts_task = self.alertmanager_list_alerts_async()

        prometheus_result, alerts = await asyncio.gather(
            prometheus_task,
            alerts_task,
            return_exceptions=True
        )

        elapsed = time.time() - start
        logger.info(f"✓ 에러 메트릭 수집 완료: {elapsed*1000:.1f}ms")

        return {
            'error_rate': prometheus_result,
            'alerts': alerts,
            'collection_time': elapsed
        }

    async def collect_performance_metrics(self) -> Dict[str, Any]:
        """성능 관련 메트릭 수집 (병렬)"""
        logger.info("수집 중: 성능 메트릭 (K8s + Docker Registry + Datadog)")

        start = time.time()

        # 병렬로 3개 API 호출
        k8s_task = self.k8s_list_deployments_async()
        registry_task = self.registry_list_tags_async()
        datadog_task = self.datadog_get_host_async()

        k8s_result, registry, datadog = await asyncio.gather(
            k8s_task,
            registry_task,
            datadog_task,
            return_exceptions=True
        )

        elapsed = time.time() - start
        logger.info(f"✓ 성능 메트릭 수집 완료: {elapsed*1000:.1f}ms")

        return {
            'deployments': k8s_result,
            'registry_tags': registry,
            'datadog_host': datadog,
            'collection_time': elapsed
        }

    async def collect_all_metrics(self) -> Dict[str, Any]:
        """모든 메트릭을 병렬로 수집"""
        logger.info("\n" + "="*70)
        logger.info("🚀 모든 메트릭 병렬 수집 시작")
        logger.info("="*70)

        start = time.time()

        # 에러와 성능 메트릭을 동시에 수집
        error_metrics_task = self.collect_error_metrics()
        performance_metrics_task = self.collect_performance_metrics()

        error_metrics, performance_metrics = await asyncio.gather(
            error_metrics_task,
            performance_metrics_task,
            return_exceptions=True
        )

        total_time = time.time() - start

        result = {
            'error_metrics': error_metrics,
            'performance_metrics': performance_metrics,
            'total_collection_time': total_time,
            'timestamp': time.time()
        }

        logger.info(f"\n✅ 전체 메트릭 수집 완료: {total_time*1000:.1f}ms")
        logger.info("="*70 + "\n")

        return result

    async def collect_metrics_sequential(self) -> Dict[str, Any]:
        """메트릭을 순차적으로 수집 (비교용)"""
        logger.info("\n" + "="*70)
        logger.info("🔄 메트릭 순차 수집 시작 (성능 비교용)")
        logger.info("="*70)

        start = time.time()

        # 순차 실행
        error_rate = await self.prometheus_query_async("http_error_rate")
        alerts = await self.alertmanager_list_alerts_async()
        deployments = await self.k8s_list_deployments_async()
        registry = await self.registry_list_tags_async()
        datadog = await self.datadog_get_host_async()

        total_time = time.time() - start

        result = {
            'error_rate': error_rate,
            'alerts': alerts,
            'deployments': deployments,
            'registry_tags': registry,
            'datadog_host': datadog,
            'total_collection_time': total_time
        }

        logger.info(f"\n✓ 순차 수집 완료: {total_time*1000:.1f}ms")
        logger.info("="*70 + "\n")

        return result


# ============================================================================
# 성능 벤치마크
# ============================================================================

async def benchmark_metrics_collection():
    """메트릭 수집 성능 벤치마크"""
    client = AsyncAPIClient(max_workers=5)

    print("\n" + "="*70)
    print("📊 메트릭 수집 성능 벤치마크")
    print("="*70)

    # 병렬 수집 (권장)
    parallel_result = await client.collect_all_metrics()
    parallel_time = parallel_result['total_collection_time']

    # 순차 수집 (비교용)
    sequential_result = await client.collect_metrics_sequential()
    sequential_time = sequential_result['total_collection_time']

    # 성능 개선율 계산
    improvement = (sequential_time - parallel_time) / sequential_time * 100
    speedup = sequential_time / parallel_time

    print(f"\n📈 **성능 비교**")
    print(f"  병렬 수집  : {parallel_time*1000:7.1f}ms ⚡")
    print(f"  순차 수집  : {sequential_time*1000:7.1f}ms 🐢")
    print(f"  개선율    : {improvement:6.1f}% 📈")
    print(f"  속도 향상  : {speedup:6.1f}x 🚀")

    if parallel_time < 0.3:  # 300ms
        print(f"\n✅ 성능 목표 달성: <300ms ✨")
    else:
        print(f"\n⚠️ 성능 목표 미달: {parallel_time*1000:.1f}ms (목표: <300ms)")

    print("="*70 + "\n")

    return {
        'parallel_time': parallel_time,
        'sequential_time': sequential_time,
        'improvement': improvement,
        'speedup': speedup
    }


if __name__ == "__main__":
    # 벤치마크 실행
    result = asyncio.run(benchmark_metrics_collection())

    print("\n📋 **벤치마크 결과**")
    print(f"  병렬 수집 : {result['parallel_time']*1000:.1f}ms")
    print(f"  순차 수집 : {result['sequential_time']*1000:.1f}ms")
    print(f"  개선율   : {result['improvement']:.1f}%")
    print(f"  속도 향상 : {result['speedup']:.1f}x\n")
