#!/usr/bin/env python3
"""
MindLang Mock API Server (Flask 버전)
외부 API 의존성을 제거하기 위한 Mock 서버

지원 Mock 서비스:
1. Prometheus - 메트릭 API
2. Kubernetes - 배포 API
3. AlertManager - 알림 API
4. Docker Registry - 저장소 API
5. Datadog - 모니터링 API
"""

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import json
import random
import logging

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 1. Prometheus Mock API
# ============================================================================

@app.route('/api/v1/query', methods=['GET'])
def prometheus_query():
    """Prometheus Query API Mock"""
    query = request.args.get('query', '')

    logger.info(f"Prometheus Query: {query}")

    # 간단한 PromQL 파싱
    if "cpu" in query.lower():
        value = round(random.uniform(20, 85), 2)
        return jsonify({
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
        })
    elif "memory" in query.lower():
        value = round(random.uniform(30, 80), 2)
        return jsonify({
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
        })
    elif "error" in query.lower():
        value = round(random.uniform(0.001, 0.05), 4)
        return jsonify({
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
        })
    else:
        return jsonify({
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": []
            }
        })


@app.route('/api/v1/query_range', methods=['GET'])
def prometheus_query_range():
    """Prometheus Range Query Mock"""
    query = request.args.get('query', '')

    results = []
    for i in range(5):
        results.append([
            int(datetime.now().timestamp()) - (5 - i) * 60,
            str(round(random.uniform(20, 85), 2))
        ])

    return jsonify({
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
    })


@app.route('/api/v1/targets', methods=['GET'])
def prometheus_targets():
    """Prometheus Targets API Mock"""
    return jsonify({
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
    })


# ============================================================================
# 2. Kubernetes Mock API
# ============================================================================

@app.route('/api/v1/namespaces/<namespace>/pods', methods=['GET'])
def k8s_list_pods(namespace='default'):
    """Kubernetes Pod List API Mock"""
    logger.info(f"K8s List Pods: {namespace}")

    items = []
    for i in range(3):
        items.append({
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
        })

    return jsonify({
        "apiVersion": "v1",
        "kind": "PodList",
        "metadata": {
            "resourceVersion": "12345",
            "selfLink": f"/api/v1/namespaces/{namespace}/pods"
        },
        "items": items
    })


@app.route('/api/v1/namespaces/<namespace>/deployments', methods=['GET'])
def k8s_list_deployments(namespace='default'):
    """Kubernetes Deployment List API Mock"""
    logger.info(f"K8s List Deployments: {namespace}")

    replicas = random.randint(1, 5)
    return jsonify({
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
                    "replicas": replicas,
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
                    "replicas": replicas,
                    "updatedReplicas": replicas,
                    "readyReplicas": replicas,
                    "availableReplicas": replicas,
                    "observedGeneration": 3
                }
            }
        ]
    })


@app.route('/api/v1/namespaces/<namespace>/deployments/<name>/rollback', methods=['POST'])
def k8s_rollback_deployment(namespace, name):
    """Kubernetes Deployment Rollback API Mock"""
    logger.info(f"K8s Rollback: {namespace}/{name}")

    return jsonify({
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "status": {"observedGeneration": 3},
        "message": f"Rolled back deployment {name}"
    })


@app.route('/api/v1/namespaces/<namespace>/deployments/<name>', methods=['PATCH'])
def k8s_patch_deployment(namespace, name):
    """Kubernetes Deployment Patch API Mock"""
    logger.info(f"K8s Patch: {namespace}/{name}")

    data = request.get_json() or {}
    spec = data.get("spec", {})
    replicas = spec.get("replicas", 1)

    return jsonify({
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "spec": spec,
        "status": {"replicas": replicas}
    })


# ============================================================================
# 3. AlertManager Mock API
# ============================================================================

@app.route('/api/v1/alerts', methods=['GET', 'POST'])
def alertmanager_alerts():
    """AlertManager Alerts API Mock"""
    logger.info("AlertManager: Get/Create Alerts")

    if request.method == 'POST':
        return jsonify({
            "status": "success",
            "message": "Alert created"
        })

    return jsonify([
        {
            "status": random.choice(["active", "suppressed"]),
            "labels": {
                "alertname": "HighErrorRate",
                "job": "mindlang-api",
                "severity": "critical"
            },
            "annotations": {
                "summary": "High error rate detected",
                "description": f"Error rate is {round(random.uniform(5, 15), 1)}%"
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
                "description": f"Memory usage is {round(random.uniform(70, 90), 1)}%"
            },
            "startsAt": (datetime.now() - timedelta(hours=2)).isoformat(),
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "http://prometheus:9090/graph",
            "fingerprint": "xyz789uvw012"
        }
    ])


# ============================================================================
# 4. Docker Registry Mock API
# ============================================================================

@app.route('/v2/<name>/manifests/<reference>', methods=['GET'])
def registry_get_manifest(name, reference):
    """Docker Registry Get Manifest Mock"""
    logger.info(f"Registry: Get Manifest {name}@{reference}")

    return jsonify({
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
    })


@app.route('/v2/<name>/tags/list', methods=['GET'])
def registry_list_tags(name):
    """Docker Registry List Tags Mock"""
    logger.info(f"Registry: List Tags {name}")

    return jsonify({
        "name": name,
        "tags": ["latest", "1.0.0", "1.0.1", "develop"]
    })


# ============================================================================
# 5. Datadog Mock API
# ============================================================================

@app.route('/api/v1/query', methods=['POST'])
def datadog_query():
    """Datadog Query API Mock"""
    logger.info("Datadog: Query")

    data = request.get_json() or {}
    query = data.get("query", "")

    return jsonify({
        "status": "ok",
        "series": [
            {
                "metric": "system.cpu.user",
                "points": [
                    [int(datetime.now().timestamp()) - i * 60, round(random.uniform(20, 80), 2)]
                    for i in range(5)
                ],
                "host": "prod-01"
            }
        ],
        "from_date": int((datetime.now() - timedelta(hours=1)).timestamp()),
        "to_date": int(datetime.now().timestamp()),
        "query": query
    })


@app.route('/api/v1/host/<hostname>', methods=['GET'])
def datadog_get_host(hostname):
    """Datadog Get Host API Mock"""
    logger.info(f"Datadog: Get Host {hostname}")

    return jsonify({
        "agent_version": "7.40.0",
        "apps": ["docker", "kubernetes"],
        "aws_id": "i-0123456789abcdef0",
        "host_aliases": [hostname, f"{hostname}.example.com"],
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
    })


# ============================================================================
# 6. Health Check & Info
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "prometheus": "up",
            "kubernetes": "up",
            "alertmanager": "up",
            "docker-registry": "up",
            "datadog": "up"
        }
    })


@app.route('/info', methods=['GET'])
def info():
    """서버 정보"""
    return jsonify({
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
    })


@app.route('/', methods=['GET'])
def root():
    """루트 엔드포인트"""
    return jsonify({
        "message": "Welcome to MindLang Mock API Server",
        "health_check": "/health",
        "info": "/info",
        "docs": "See /info for endpoints"
    })


# ============================================================================
# Error Handling
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 에러"""
    return jsonify({
        "error": "Not Found",
        "message": request.path,
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def server_error(e):
    """500 에러"""
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e),
        "timestamp": datetime.now().isoformat()
    }), 500


if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  🧠 MindLang Mock API Server (Flask)                      ║
    ║                                                            ║
    ║  Supported Services:                                       ║
    ║  ✅ Prometheus (메트릭 API)                               ║
    ║  ✅ Kubernetes (배포 API)                                 ║
    ║  ✅ AlertManager (알림 API)                               ║
    ║  ✅ Docker Registry (저장소 API)                          ║
    ║  ✅ Datadog (모니터링 API)                                ║
    ║                                                            ║
    ║  Start: http://localhost:8000                             ║
    ║  Health: http://localhost:8000/health                     ║
    ║  Info: http://localhost:8000/info                         ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
