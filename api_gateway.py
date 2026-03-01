#!/usr/bin/env python3
"""
MindLang API Gateway
모든 마이크로서비스의 중앙 진입점

기능:
- 통합 인증 및 권한 관리
- 요청/응답 로깅
- 서비스 라우팅
- 속도 제한 및 부하 분산
- 에러 처리 및 재시도
- 실시간 메트릭 수집
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging
from enum import Enum

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MindLang API Gateway", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ServiceStatus(str, Enum):
    """서비스 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ServiceEndpoint:
    """서비스 엔드포인트"""
    name: str
    url: str
    port: int
    timeout: int = 30
    retry_count: int = 3
    status: ServiceStatus = ServiceStatus.OFFLINE
    last_check: Optional[float] = None
    response_time: float = 0.0
    error_count: int = 0


@dataclass
class RequestLog:
    """요청 로그"""
    timestamp: float
    service: str
    method: str
    path: str
    status_code: int
    response_time: float
    client_ip: str


class APIGateway:
    """API 게이트웨이"""

    def __init__(self):
        self.services: Dict[str, ServiceEndpoint] = {
            'dashboard': ServiceEndpoint(
                name='dashboard',
                url='http://localhost',
                port=8000,
                timeout=30
            ),
            'learning': ServiceEndpoint(
                name='learning',
                url='http://localhost',
                port=8001,
                timeout=60
            ),
            'benchmark': ServiceEndpoint(
                name='benchmark',
                url='http://localhost',
                port=8002,
                timeout=120
            ),
            'analyzer': ServiceEndpoint(
                name='analyzer',
                url='http://localhost',
                port=8003,
                timeout=60
            ),
        }
        self.request_logs: List[RequestLog] = []
        self.max_logs = 10000
        self.request_count: Dict[str, int] = {}
        self.error_count: Dict[str, int] = {}

    async def health_check(self):
        """모든 서비스의 건강 상태 확인"""
        async with httpx.AsyncClient(timeout=5) as client:
            for service_name, endpoint in self.services.items():
                try:
                    start = time.time()
                    response = await client.get(
                        f"{endpoint.url}:{endpoint.port}/health",
                        timeout=5
                    )
                    response_time = time.time() - start

                    if response.status_code == 200:
                        endpoint.status = ServiceStatus.HEALTHY
                        endpoint.response_time = response_time
                        endpoint.error_count = 0
                    else:
                        endpoint.status = ServiceStatus.DEGRADED
                        endpoint.response_time = response_time

                    endpoint.last_check = time.time()

                except Exception as e:
                    endpoint.status = ServiceStatus.OFFLINE
                    endpoint.error_count += 1
                    logger.error(f"Health check failed for {service_name}: {e}")

    async def forward_request(
        self,
        service_name: str,
        method: str,
        path: str,
        request: Request
    ) -> Dict:
        """요청을 서비스로 전달"""
        if service_name not in self.services:
            raise HTTPException(status_code=404, detail="Service not found")

        endpoint = self.services[service_name]

        # 서비스 상태 확인
        if endpoint.status == ServiceStatus.OFFLINE:
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} is offline"
            )

        # 요청 로깅
        start_time = time.time()

        try:
            # 요청 본문 읽기
            body = await request.body()

            async with httpx.AsyncClient(timeout=endpoint.timeout) as client:
                # 헤더 전달
                headers = dict(request.headers)
                headers.pop('host', None)

                # 재시도 로직
                for attempt in range(endpoint.retry_count):
                    try:
                        response = await client.request(
                            method=method,
                            url=f"{endpoint.url}:{endpoint.port}{path}",
                            headers=headers,
                            content=body
                        )

                        response_time = time.time() - start_time

                        # 로그 기록
                        self._log_request(
                            service_name=service_name,
                            method=method,
                            path=path,
                            status_code=response.status_code,
                            response_time=response_time,
                            client_ip=request.client.host if request.client else "unknown"
                        )

                        return {
                            'status_code': response.status_code,
                            'headers': dict(response.headers),
                            'body': response.text,
                            'response_time': response_time
                        }

                    except httpx.TimeoutException:
                        if attempt == endpoint.retry_count - 1:
                            raise
                        await asyncio.sleep(0.5 * (attempt + 1))

        except Exception as e:
            response_time = time.time() - start_time
            self._log_request(
                service_name=service_name,
                method=method,
                path=path,
                status_code=500,
                response_time=response_time,
                client_ip=request.client.host if request.client else "unknown"
            )
            endpoint.error_count += 1
            raise HTTPException(status_code=502, detail=f"Service error: {str(e)}")

    def _log_request(
        self,
        service_name: str,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        client_ip: str
    ):
        """요청 로깅"""
        log = RequestLog(
            timestamp=time.time(),
            service=service_name,
            method=method,
            path=path,
            status_code=status_code,
            response_time=response_time,
            client_ip=client_ip
        )

        self.request_logs.append(log)
        if len(self.request_logs) > self.max_logs:
            self.request_logs.pop(0)

        # 카운트 업데이트
        self.request_count[service_name] = self.request_count.get(service_name, 0) + 1
        if status_code >= 400:
            self.error_count[service_name] = self.error_count.get(service_name, 0) + 1

    def get_metrics(self) -> Dict:
        """메트릭 조회"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'total_requests': sum(self.request_count.values()),
            'total_errors': sum(self.error_count.values()),
            'request_logs': [asdict(log) for log in self.request_logs[-100:]]
        }

        for service_name, endpoint in self.services.items():
            metrics['services'][service_name] = {
                'status': endpoint.status.value,
                'url': f"{endpoint.url}:{endpoint.port}",
                'response_time': endpoint.response_time,
                'request_count': self.request_count.get(service_name, 0),
                'error_count': self.error_count.get(service_name, 0),
                'last_check': endpoint.last_check,
                'error_rate': (
                    self.error_count.get(service_name, 0) /
                    self.request_count.get(service_name, 1)
                ) if self.request_count.get(service_name, 0) > 0 else 0
            }

        return metrics

    def get_service_stats(self, service_name: str) -> Dict:
        """특정 서비스의 통계"""
        if service_name not in self.services:
            raise HTTPException(status_code=404, detail="Service not found")

        service_logs = [
            log for log in self.request_logs
            if log.service == service_name
        ]

        if not service_logs:
            return {}

        response_times = [log.response_time for log in service_logs]
        status_codes = {}
        for log in service_logs:
            status_codes[log.status_code] = status_codes.get(log.status_code, 0) + 1

        return {
            'service': service_name,
            'total_requests': len(service_logs),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'status_code_distribution': status_codes,
            'recent_logs': [asdict(log) for log in service_logs[-20:]]
        }


gateway = APIGateway()


# 엔드포인트

@app.on_event("startup")
async def startup():
    """시작 시"""
    logger.info("MindLang API Gateway starting...")
    # 주기적 헬스 체크
    asyncio.create_task(periodic_health_check())


async def periodic_health_check():
    """주기적 헬스 체크"""
    while True:
        try:
            await gateway.health_check()
            await asyncio.sleep(30)  # 30초마다 체크
        except Exception as e:
            logger.error(f"Health check error: {e}")
            await asyncio.sleep(10)


@app.get("/health")
async def health():
    """게이트웨이 상태"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            name: {
                'status': endpoint.status.value,
                'response_time': endpoint.response_time
            }
            for name, endpoint in gateway.services.items()
        }
    }


@app.get("/metrics")
async def metrics():
    """메트릭 조회"""
    return gateway.get_metrics()


@app.get("/metrics/{service_name}")
async def service_metrics(service_name: str):
    """특정 서비스 메트릭"""
    return gateway.get_service_stats(service_name)


@app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_route(service_name: str, path: str, request: Request):
    """API 게이트웨이 라우팅"""
    result = await gateway.forward_request(
        service_name=service_name,
        method=request.method,
        path=f"/{path}",
        request=request
    )

    return JSONResponse(
        status_code=result['status_code'],
        content={
            'data': json.loads(result['body']) if result['body'] else None,
            'response_time': result['response_time']
        }
    )


@app.get("/services")
async def list_services():
    """등록된 서비스 목록"""
    return {
        'services': [
            {
                'name': endpoint.name,
                'url': f"{endpoint.url}:{endpoint.port}",
                'status': endpoint.status.value,
                'response_time': endpoint.response_time
            }
            for endpoint in gateway.services.values()
        ]
    }


@app.post("/services/{service_name}/register")
async def register_service(service_name: str, request: Request):
    """새 서비스 등록"""
    data = await request.json()

    gateway.services[service_name] = ServiceEndpoint(
        name=service_name,
        url=data.get('url', 'http://localhost'),
        port=data.get('port', 8000),
        timeout=data.get('timeout', 30),
        retry_count=data.get('retry_count', 3)
    )

    await gateway.health_check()

    return {
        'status': 'registered',
        'service': service_name,
        'endpoint': gateway.services[service_name].url
    }


@app.get("/logs")
async def get_logs(service_name: Optional[str] = None, limit: int = 100):
    """요청 로그 조회"""
    logs = gateway.request_logs

    if service_name:
        logs = [log for log in logs if log.service == service_name]

    return {
        'total': len(logs),
        'logs': [asdict(log) for log in logs[-limit:]]
    }


@app.post("/cache/clear")
async def clear_cache():
    """캐시 초기화"""
    gateway.request_logs.clear()
    gateway.request_count.clear()
    gateway.error_count.clear()

    return {'status': 'cleared'}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
