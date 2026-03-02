#!/usr/bin/env python3
"""
MindLang API Client
Mock API와 실제 API를 투명하게 처리하는 통합 클라이언트

사용 방법:
    from api_client import APIClient, Config

    # Mock API 활성화
    Config.USE_MOCK_API = True

    # 클라이언트 생성
    client = APIClient()

    # Prometheus 쿼리
    response = await client.prometheus_query("node_cpu_usage_percent")

    # Kubernetes API
    pods = await client.k8s_list_pods("default")

    # 자동으로 Mock/Real을 선택하여 요청
"""

import httpx
import asyncio
from typing import Dict, Optional, Any, List
from config import Config
import logging

# 로깅 설정
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class APIClient:
    """통합 API 클라이언트"""

    def __init__(self, timeout: float = 30.0):
        """
        APIClient 초기화

        Args:
            timeout: 요청 타임아웃 (초)
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._client:
            await self._client.aclose()

    @property
    async def client(self) -> httpx.AsyncClient:
        """클라이언트 반환 (필요시 생성)"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    # ========================================================================
    # Prometheus API
    # ========================================================================

    async def prometheus_query(
        self,
        query: str,
        time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prometheus instant query

        Args:
            query: PromQL 쿼리
            time: 시간 (ISO8601 또는 Unix timestamp)

        Returns:
            메트릭 응답
        """
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/query"

        params = {"query": query}
        if time:
            params["time"] = time

        logger.debug(f"Prometheus Query: {query}")
        return await self._get(url, params=params)

    async def prometheus_query_range(
        self,
        query: str,
        start: str,
        end: str,
        step: str = "60s"
    ) -> Dict[str, Any]:
        """
        Prometheus range query

        Args:
            query: PromQL 쿼리
            start: 시작 시간
            end: 종료 시간
            step: 샘플링 간격

        Returns:
            시계열 메트릭 응답
        """
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/query_range"

        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }

        logger.debug(f"Prometheus Range Query: {query}")
        return await self._get(url, params=params)

    async def prometheus_targets(self) -> Dict[str, Any]:
        """
        Prometheus targets 조회

        Returns:
            모니터링 대상 정보
        """
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/targets"

        logger.debug("Fetching Prometheus targets")
        return await self._get(url)

    # ========================================================================
    # Kubernetes API
    # ========================================================================

    async def k8s_list_pods(
        self,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Kubernetes Pod 목록 조회

        Args:
            namespace: 네임스페이스

        Returns:
            Pod 목록
        """
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/pods"

        logger.debug(f"Listing pods in namespace: {namespace}")
        return await self._get(url)

    async def k8s_list_deployments(
        self,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Kubernetes Deployment 목록 조회

        Args:
            namespace: 네임스페이스

        Returns:
            Deployment 목록
        """
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments"

        logger.debug(f"Listing deployments in namespace: {namespace}")
        return await self._get(url)

    async def k8s_rollback_deployment(
        self,
        namespace: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Kubernetes Deployment 롤백

        Args:
            namespace: 네임스페이스
            name: Deployment 이름

        Returns:
            롤백 결과
        """
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments/{name}/rollback"

        logger.info(f"Rolling back deployment: {name}")
        return await self._post(url, json={})

    async def k8s_patch_deployment(
        self,
        namespace: str,
        name: str,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Kubernetes Deployment 패치

        Args:
            namespace: 네임스페이스
            name: Deployment 이름
            spec: 패치할 스펙

        Returns:
            패치 결과
        """
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments/{name}"

        logger.info(f"Patching deployment: {name}")
        return await self._patch(url, json={"spec": spec})

    # ========================================================================
    # AlertManager API
    # ========================================================================

    async def alertmanager_list_alerts(self) -> List[Dict[str, Any]]:
        """
        AlertManager 활성 알림 조회

        Returns:
            알림 목록
        """
        base_url = Config.get_api_url("alertmanager")
        url = f"{base_url}/api/v1/alerts"

        logger.debug("Fetching alerts from AlertManager")
        return await self._get(url)

    async def alertmanager_create_alert(
        self,
        alert: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AlertManager에 알림 생성

        Args:
            alert: 알림 정보

        Returns:
            생성 결과
        """
        base_url = Config.get_api_url("alertmanager")
        url = f"{base_url}/api/v1/alerts"

        logger.info(f"Creating alert: {alert.get('labels', {}).get('alertname')}")
        return await self._post(url, json=alert)

    # ========================================================================
    # Docker Registry API
    # ========================================================================

    async def registry_get_manifest(
        self,
        name: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        Docker Registry manifest 조회

        Args:
            name: 이미지 이름
            reference: 태그 또는 다이제스트

        Returns:
            Manifest 정보
        """
        base_url = Config.get_api_url("docker_registry")
        url = f"{base_url}/v2/{name}/manifests/{reference}"

        logger.debug(f"Fetching manifest: {name}@{reference}")
        return await self._get(url)

    async def registry_list_tags(self, name: str) -> Dict[str, Any]:
        """
        Docker Registry 태그 목록 조회

        Args:
            name: 이미지 이름

        Returns:
            태그 목록
        """
        base_url = Config.get_api_url("docker_registry")
        url = f"{base_url}/v2/{name}/tags/list"

        logger.debug(f"Listing tags for: {name}")
        return await self._get(url)

    # ========================================================================
    # Datadog API
    # ========================================================================

    async def datadog_query(self, query: str) -> Dict[str, Any]:
        """
        Datadog 메트릭 쿼리

        Args:
            query: Datadog 쿼리

        Returns:
            메트릭 응답
        """
        base_url = Config.get_api_url("datadog")
        url = f"{base_url}/api/v1/query"

        logger.debug(f"Datadog Query: {query}")
        return await self._post(
            url,
            json={"query": query},
            headers={"DD-API-KEY": Config.DATADOG_API_KEY}
        )

    async def datadog_get_host(self, hostname: str) -> Dict[str, Any]:
        """
        Datadog 호스트 정보 조회

        Args:
            hostname: 호스트명

        Returns:
            호스트 정보
        """
        base_url = Config.get_api_url("datadog")
        url = f"{base_url}/api/v1/host/{hostname}"

        logger.debug(f"Fetching Datadog host: {hostname}")
        return await self._get(
            url,
            headers={"DD-API-KEY": Config.DATADOG_API_KEY}
        )

    # ========================================================================
    # 내부 메서드
    # ========================================================================

    async def _get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """GET 요청"""
        try:
            client = httpx.Client() if self._client is None else self._client
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def _post(
        self,
        url: str,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """POST 요청"""
        try:
            client = httpx.Client() if self._client is None else self._client
            response = client.post(url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def _patch(
        self,
        url: str,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """PATCH 요청"""
        try:
            client = httpx.Client() if self._client is None else self._client
            response = client.patch(url, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise


# ============================================================================
# 편의 함수들
# ============================================================================

async def test_prometheus():
    """Prometheus API 테스트"""
    client = APIClient()
    try:
        result = await client.prometheus_query("node_cpu_usage_percent")
        print(f"✅ Prometheus Query: {result['status']}")
    except Exception as e:
        print(f"❌ Prometheus Error: {e}")


async def test_kubernetes():
    """Kubernetes API 테스트"""
    client = APIClient()
    try:
        result = await client.k8s_list_pods()
        print(f"✅ K8s Pods: {len(result.get('items', []))} pods")
    except Exception as e:
        print(f"❌ K8s Error: {e}")


async def main():
    """테스트 실행"""
    print("\n" + "=" * 60)
    print("MindLang API Client Test")
    print("=" * 60)

    Config.print_config()

    await test_prometheus()
    await test_kubernetes()


if __name__ == "__main__":
    asyncio.run(main())
