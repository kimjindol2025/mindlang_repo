#!/usr/bin/env python3
"""
MindLang Mock API Server
외부 API 의존성을 제거하기 위한 Mock 서버

지원 Mock 서비스:
1. Prometheus - 메트릭 API
2. Kubernetes - 배포 API
3. AlertManager - 알림 API
4. Docker Registry - 저장소 API
5. Datadog - 모니터링 API
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio
from enum import Enum
import random

app = FastAPI(title="MindLang Mock API Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 1. Prometheus Mock API
# ============================================================================

class PrometheusMetric(Enum):
    """Prometheus 메트릭 종류"""
    CPU_USAGE = "node_cpu_usage_percent"
    MEMORY_USAGE = "node_memory_usage_percent"
    ERROR_RATE = "http_error_rate"
    REQUEST_LATENCY = "http_request_duration_seconds"
    DISK_USAGE = "node_disk_usage_percent"


@app.get("/api/v1/query")
async def prometheus_query(query: str, time: Optional[str] = None):
    """
    Prometheus Query API Mock
    PromQL 형식의 쿼리를 받고 메트릭 응답 반환
    """
    # 간단한 PromQL 파싱
    if "node_cpu_usage_percent" in query or "cpu" in query.lower():
        value = random.uniform(20, 85)
        return {
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": [
                    {
                        "metric": {"__name__": "node_cpu_usage_percent"},
                        "value": [int(datetime.now().timestamp()), str(value)]
                    }
                ]
            }
        }
    elif "node_memory_usage_percent" in query or "memory" in query.lower():
        value = random.uniform(30, 80)
        return {
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": [
                    {
                        "metric": {"__name__": "node_memory_usage_percent"},
                        "value": [int(datetime.now().timestamp()), str(value)]
                    }
                ]
            }
        }
    elif "error_rate" in query.lower():
        value = random.uniform(0.001, 0.05)
        return {
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": [
                    {
                        "metric": {"__name__": "http_error_rate"},
                        "value": [int(datetime.now().timestamp()), str(value)]
                    }
                ]
            }
        }
    else:
        return {
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": []
            }
        }


@app.get("/api/v1/query_range")
async def prometheus_query_range(
    query: str,
    start: str,
    end: str,
    step: str = "60s"
):
    """Prometheus Range Query Mock"""
    results = []
    for i in range(5):
        results.append([
            int(datetime.now().timestamp()) - (5 - i) * 60,
            str(random.uniform(20, 85))
        ])

    return {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": "node_cpu_usage_percent"},
                    "values": results
                }
            ]
        }
    }


@app.get("/api/v1/targets")
async def prometheus_targets():
    """Prometheus Targets API Mock"""
    return {
        "status": "success",
        "data": {
            "activeTargets": [
                {
                    "discoveredLabels": {"job": "kubernetes-pods"},
                    "labels": {"job": "kubernetes-pods", "instance": "10.0.0.1:9090"},
                    "scrapePool": "kubernetes-pods",
                    "scrapeUrl": "http://10.0.0.1:9090/metrics",
                    "globalUrl": "http://prometheus:9090/graph",
                    "lastError": "",
                    "lastScrape": datetime.now().isoformat(),
                    "lastScrapeDuration": 0.001,
                    "health": "up"
                }
            ],
            "droppedTargets": []
        }
    }


# ============================================================================
# 2. Kubernetes Mock API
# ============================================================================

@app.get("/api/v1/namespaces/{namespace}/pods")
async def k8s_list_pods(namespace: str = "default"):
    """Kubernetes Pod List API Mock"""
    return {
        "apiVersion": "v1",
        "kind": "PodList",
        "metadata": {
            "resourceVersion": "12345",
            "selfLink": f"/api/v1/namespaces/{namespace}/pods"
        },
        "items": [
            {
                "metadata": {
                    "name": f"pod-{i}",
                    "namespace": namespace,
                    "creationTimestamp": (datetime.now() - timedelta(hours=i)).isoformat()
                },
                "spec": {
                    "containers": [
                        {
                            "name": "app",
                            "image": "mindlang:latest",
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "500m", "memory": "512Mi"}
                            }
                        }
                    ]
                },
                "status": {
                    "phase": random.choice(["Running", "Pending", "Succeeded"]),
                    "containerStatuses": [
                        {
                            "name": "app",
                            "ready": random.choice([True, True, True, False]),
                            "restartCount": random.randint(0, 3),
                            "state": {
                                "running": {
                                    "startedAt": (datetime.now() - timedelta(hours=i)).isoformat()
                                }
                            }
                        }
                    ]
                }
            }
            for i in range(3)
        ]
    }


@app.get("/api/v1/namespaces/{namespace}/deployments")
async def k8s_list_deployments(namespace: str = "default"):
    """Kubernetes Deployment List API Mock"""
    return {
        "apiVersion": "apps/v1",
        "kind": "DeploymentList",
        "metadata": {"resourceVersion": "12345"},
        "items": [
            {
                "metadata": {
                    "name": "mindlang-api",
                    "namespace": namespace
                },
                "spec": {
                    "replicas": random.randint(1, 5),
                    "selector": {"matchLabels": {"app": "mindlang"}},
                    "template": {
                        "metadata": {"labels": {"app": "mindlang"}},
                        "spec": {
                            "containers": [
                                {
                                    "name": "mindlang",
                                    "image": "mindlang:latest",
                                    "resources": {
                                        "requests": {"cpu": "100m", "memory": "128Mi"},
                                        "limits": {"cpu": "500m", "memory": "512Mi"}
                                    }
                                }
                            ]
                        }
                    }
                },
                "status": {
                    "replicas": random.randint(1, 5),
                    "updatedReplicas": random.randint(1, 5),
                    "readyReplicas": random.randint(1, 5),
                    "availableReplicas": random.randint(1, 5),
                    "observedGeneration": 3
                }
            }
        ]
    }


@app.post("/api/v1/namespaces/{namespace}/deployments/{name}/rollback")
async def k8s_rollback_deployment(namespace: str, name: str, body: Dict = None):
    """Kubernetes Deployment Rollback API Mock"""
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "status": {"observedGeneration": 3},
        "message": f"Rolled back deployment {name}"
    }


@app.patch("/api/v1/namespaces/{namespace}/deployments/{name}")
async def k8s_patch_deployment(namespace: str, name: str, body: Dict):
    """Kubernetes Deployment Patch API Mock"""
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "spec": body.get("spec", {}),
        "status": {"replicas": body.get("spec", {}).get("replicas", 1)}
    }


# ============================================================================
# 3. AlertManager Mock API
# ============================================================================

@app.get("/api/v1/alerts")
async def alertmanager_list_alerts():
    """AlertManager Alerts API Mock"""
    return [
        {
            "status": random.choice(["active", "suppressed"]),
            "labels": {
                "alertname": "HighErrorRate",
                "job": "mindlang-api",
                "severity": "critical"
            },
            "annotations": {
                "summary": "High error rate detected",
                "description": f"Error rate is {random.uniform(5, 15):.1f}%"
            },
            "startsAt": (datetime.now() - timedelta(hours=1)).isoformat(),
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph",
            "fingerprint": "abc123def456"
        },
        {
            "status": random.choice(["active", "suppressed"]),
            "labels": {
                "alertname": "HighMemoryUsage",
                "job": "mindlang-api",
                "severity": "warning"
            },
            "annotations": {
                "summary": "High memory usage detected",
                "description": f"Memory usage is {random.uniform(70, 90):.1f}%"
            },
            "startsAt": (datetime.now() - timedelta(hours=2)).isoformat(),
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph",
            "fingerprint": "xyz789uvw012"
        }
    ]


@app.post("/api/v1/alerts")
async def alertmanager_create_alert(body: Dict):
    """AlertManager Create Alert API Mock"""
    return {
        "status": "success",
        "message": f"Alert {body.get('labels', {}).get('alertname')} created"
    }


# ============================================================================
# 4. Docker Registry Mock API
# ============================================================================

@app.get("/v2/<name>/manifests/<reference>")
async def registry_get_manifest(name: str, reference: str):
    """Docker Registry Get Manifest Mock"""
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "size": 1234,
            "digest": "sha256:" + "a" * 64
        },
        "layers": [
            {
                "size": 5678,
                "digest": "sha256:" + "b" * 64
            }
        ]
    }


@app.get("/v2/<name>/tags/list")
async def registry_list_tags(name: str):
    """Docker Registry List Tags Mock"""
    return {
        "name": name,
        "tags": ["latest", "1.0.0", "1.0.1", "develop"]
    }


# ============================================================================
# 5. Datadog Mock API
# ============================================================================

@app.post("/api/v1/query")
async def datadog_query(body: Dict):
    """Datadog Query API Mock"""
    query = body.get("query", "")
    return {
        "status": "ok",
        "series": [
            {
                "metric": "system.cpu.user",
                "points": [
                    [int(datetime.now().timestamp()), random.uniform(20, 80)]
                    for _ in range(5)
                ],
                "host": "prod-01"
            }
        ],
        "from_date": int((datetime.now() - timedelta(hours=1)).timestamp()),
        "to_date": int(datetime.now().timestamp()),
        "query": query
    }


@app.get("/api/v1/host/{hostname}")
async def datadog_get_host(hostname: str):
    """Datadog Get Host API Mock"""
    return {
        "agent_version": "7.40.0",
        "apps": ["docker", "kubernetes"],
        "aws_id": "i-0123456789abcdef0",
        "host_aliases": ["prod-01", "prod-01.example.com"],
        "host_name": hostname,
        "is_muted": False,
        "last_reported_time": int(datetime.now().timestamp()),
        "meta": {
            "cpu_cores": 8,
            "gohai": "{}",
            "memory_mb": 16384
        },
        "mute_timeout": None,
        "name": hostname,
        "sources": ["kubernetes", "docker"],
        "status": "up",
        "tags": ["env:prod", "service:mindlang"],
        "up": True
    }


# ============================================================================
# 6. Health Check & Info
# ============================================================================

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "prometheus": "up",
            "kubernetes": "up",
            "alertmanager": "up",
            "docker-registry": "up",
            "datadog": "up"
        }
    }


@app.get("/info")
async def info():
    """서버 정보"""
    return {
        "name": "MindLang Mock API Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "description": "Mock API server for MindLang testing",
        "endpoints": {
            "prometheus": "/api/v1/query, /api/v1/query_range, /api/v1/targets",
            "kubernetes": "/api/v1/namespaces/{namespace}/pods, /deployments",
            "alertmanager": "/api/v1/alerts",
            "docker_registry": "/v2/<name>/manifests/<reference>",
            "datadog": "/api/v1/query, /api/v1/host/{hostname}"
        }
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Welcome to MindLang Mock API Server",
        "health_check": "/health",
        "info": "/info",
        "docs": "/docs"
    }


# ============================================================================
# Error Handling
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  🧠 MindLang Mock API Server                              ║
    ║                                                            ║
    ║  Supported Services:                                       ║
    ║  ✅ Prometheus (메트릭 API)                               ║
    ║  ✅ Kubernetes (배포 API)                                 ║
    ║  ✅ AlertManager (알림 API)                               ║
    ║  ✅ Docker Registry (저장소 API)                          ║
    ║  ✅ Datadog (모니터링 API)                                ║
    ║                                                            ║
    ║  Start: http://localhost:8000                             ║
    ║  Docs:  http://localhost:8000/docs                        ║
    ║  Health: http://localhost:8000/health                     ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
