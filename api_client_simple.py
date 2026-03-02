#!/usr/bin/env python3
"""
MindLang API Client (내장 라이브러리 버전)
Mock API와 실제 API를 투명하게 처리하는 통합 클라이언트

사용:
    from api_client_simple import APIClient
    from config import Config

    Config.USE_MOCK_API = True
    client = APIClient()

    response = client.prometheus_query("node_cpu_usage_percent")
"""

import urllib.request
import urllib.error
import json
from typing import Dict, Optional, Any
from config import Config
import logging

logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class APIClient:
    """통합 API 클라이언트 (urllib 기반)"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    # ========================================================================
    # Prometheus API
    # ========================================================================

    def prometheus_query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """Prometheus instant query"""
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/query?query={query}"
        if time:
            url += f"&time={time}"

        logger.debug(f"Prometheus Query: {query}")
        return self._get(url)

    def prometheus_query_range(
        self,
        query: str,
        start: str,
        end: str,
        step: str = "60s"
    ) -> Dict[str, Any]:
        """Prometheus range query"""
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/query_range?query={query}&start={start}&end={end}&step={step}"

        logger.debug(f"Prometheus Range Query: {query}")
        return self._get(url)

    def prometheus_targets(self) -> Dict[str, Any]:
        """Prometheus targets 조회"""
        base_url = Config.get_api_url("prometheus")
        url = f"{base_url}/api/v1/targets"

        logger.debug("Fetching Prometheus targets")
        return self._get(url)

    # ========================================================================
    # Kubernetes API
    # ========================================================================

    def k8s_list_pods(self, namespace: str = "default") -> Dict[str, Any]:
        """Kubernetes Pod 목록 조회"""
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/pods"

        logger.debug(f"Listing pods in namespace: {namespace}")
        return self._get(url)

    def k8s_list_deployments(self, namespace: str = "default") -> Dict[str, Any]:
        """Kubernetes Deployment 목록 조회"""
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments"

        logger.debug(f"Listing deployments in namespace: {namespace}")
        return self._get(url)

    def k8s_rollback_deployment(self, namespace: str, name: str) -> Dict[str, Any]:
        """Kubernetes Deployment 롤백"""
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments/{name}/rollback"

        logger.info(f"Rolling back deployment: {name}")
        return self._post(url, {})

    def k8s_patch_deployment(
        self,
        namespace: str,
        name: str,
        spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Kubernetes Deployment 패치"""
        base_url = Config.get_api_url("kubernetes")
        url = f"{base_url}/api/v1/namespaces/{namespace}/deployments/{name}"

        logger.info(f"Patching deployment: {name}")
        return self._patch(url, {"spec": spec})

    # ========================================================================
    # AlertManager API
    # ========================================================================

    def alertmanager_list_alerts(self) -> list:
        """AlertManager 활성 알림 조회"""
        base_url = Config.get_api_url("alertmanager")
        url = f"{base_url}/api/v1/alerts"

        logger.debug("Fetching alerts from AlertManager")
        result = self._get(url)
        return result if isinstance(result, list) else result.get('data', [])

    def alertmanager_create_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """AlertManager에 알림 생성"""
        base_url = Config.get_api_url("alertmanager")
        url = f"{base_url}/api/v1/alerts"

        logger.info(f"Creating alert: {alert.get('labels', {}).get('alertname')}")
        return self._post(url, alert)

    # ========================================================================
    # Docker Registry API
    # ========================================================================

    def registry_get_manifest(self, name: str, reference: str) -> Dict[str, Any]:
        """Docker Registry manifest 조회"""
        base_url = Config.get_api_url("docker_registry")
        url = f"{base_url}/v2/{name}/manifests/{reference}"

        logger.debug(f"Fetching manifest: {name}@{reference}")
        return self._get(url)

    def registry_list_tags(self, name: str) -> Dict[str, Any]:
        """Docker Registry 태그 목록 조회"""
        base_url = Config.get_api_url("docker_registry")
        url = f"{base_url}/v2/{name}/tags/list"

        logger.debug(f"Listing tags for: {name}")
        return self._get(url)

    # ========================================================================
    # Datadog API
    # ========================================================================

    def datadog_query(self, query: str) -> Dict[str, Any]:
        """Datadog 메트릭 쿼리"""
        base_url = Config.get_api_url("datadog")
        url = f"{base_url}/api/v1/query"

        logger.debug(f"Datadog Query: {query}")
        return self._post(url, {"query": query})

    def datadog_get_host(self, hostname: str) -> Dict[str, Any]:
        """Datadog 호스트 정보 조회"""
        base_url = Config.get_api_url("datadog")
        url = f"{base_url}/api/v1/host/{hostname}"

        logger.debug(f"Fetching Datadog host: {hostname}")
        return self._get(url)

    # ========================================================================
    # 내부 메서드
    # ========================================================================

    def _get(self, url: str) -> Dict[str, Any]:
        """GET 요청"""
        try:
            logger.debug(f"GET {url}")
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
        except urllib.error.URLError as e:
            logger.error(f"API Error: {e}")
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status": "error", "message": str(e)}

    def _post(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST 요청"""
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
        except urllib.error.URLError as e:
            logger.error(f"API Error: {e}")
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status": "error", "message": str(e)}

    def _patch(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PATCH 요청"""
        try:
            logger.debug(f"PATCH {url}")
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='PATCH'
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
                return json.loads(data.decode('utf-8'))
        except urllib.error.URLError as e:
            logger.error(f"API Error: {e}")
            return {"status": "error", "message": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("✅ API Client loaded successfully")
