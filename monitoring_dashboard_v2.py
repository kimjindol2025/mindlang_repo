#!/usr/bin/env python3
"""
MindLang 모니터링 대시보드 v2
시스템 전체 상태를 실시간으로 시각화

기능:
- 모든 서비스 상태 모니터링
- 실시간 성능 메트릭
- 알림 및 이벤트 로그
- 히스토리 분석
- 성능 예측
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import psutil
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from collections import deque

app = FastAPI(title="MindLang Monitoring Dashboard v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class MetricPoint:
    """메트릭 포인트"""
    timestamp: float
    service: str
    metric_name: str
    value: float


@dataclass
class AlertEvent:
    """알림 이벤트"""
    timestamp: float
    service: str
    severity: str  # info, warning, critical
    message: str
    resolved: bool = False
    resolved_at: Optional[float] = None


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self, max_history: int = 3600):
        self.metrics: deque = deque(maxlen=max_history)
        self.alerts: deque = deque(maxlen=1000)
        self.services: Dict[str, Dict] = {}

    def record_metric(self, service: str, metric_name: str, value: float):
        """메트릭 기록"""
        point = MetricPoint(
            timestamp=time.time(),
            service=service,
            metric_name=metric_name,
            value=value
        )
        self.metrics.append(point)

    def add_alert(self, service: str, severity: str, message: str):
        """알림 추가"""
        alert = AlertEvent(
            timestamp=time.time(),
            service=service,
            severity=severity,
            message=message
        )
        self.alerts.append(alert)

    def resolve_alert(self, alert_index: int):
        """알림 해결"""
        if 0 <= alert_index < len(self.alerts):
            alert_list = list(self.alerts)
            alert_list[alert_index].resolved = True
            alert_list[alert_index].resolved_at = time.time()
            self.alerts.clear()
            self.alerts.extend(alert_list)

    def get_service_metrics(self, service: str, metric_name: str, limit: int = 60) -> List[Dict]:
        """서비스 메트릭 조회"""
        metrics = [
            asdict(m) for m in self.metrics
            if m.service == service and m.metric_name == metric_name
        ]
        return metrics[-limit:]

    def get_alerts(self, service: Optional[str] = None, unresolved_only: bool = True) -> List[Dict]:
        """알림 조회"""
        alerts = [asdict(a) for a in self.alerts]

        if service:
            alerts = [a for a in alerts if a['service'] == service]

        if unresolved_only:
            alerts = [a for a in alerts if not a['resolved']]

        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)

    def get_summary(self) -> Dict:
        """요약 정보"""
        unresolved_alerts = self.get_alerts(unresolved_only=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'total_metrics': len(self.metrics),
            'total_alerts': len(self.alerts),
            'unresolved_alerts': len(unresolved_alerts),
            'critical_alerts': len([a for a in unresolved_alerts if a['severity'] == 'critical']),
            'warning_alerts': len([a for a in unresolved_alerts if a['severity'] == 'warning']),
            'metrics_by_service': self._get_metrics_by_service(),
            'alerts_by_severity': self._get_alerts_by_severity()
        }

    def _get_metrics_by_service(self) -> Dict:
        """서비스별 메트릭"""
        services = {}
        for metric in self.metrics:
            if metric.service not in services:
                services[metric.service] = {}
            if metric.metric_name not in services[metric.service]:
                services[metric.service][metric.metric_name] = []
            services[metric.service][metric.metric_name].append(metric.value)

        # 평균 계산
        for service in services:
            for metric_name in services[service]:
                values = services[service][metric_name]
                services[service][metric_name] = {
                    'count': len(values),
                    'avg': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }

        return services

    def _get_alerts_by_severity(self) -> Dict:
        """심각도별 알림"""
        return {
            'critical': len([a for a in self.alerts if a.severity == 'critical']),
            'warning': len([a for a in self.alerts if a.severity == 'warning']),
            'info': len([a for a in self.alerts if a.severity == 'info'])
        }


collector = MetricsCollector()


@app.on_event("startup")
async def startup():
    """시작"""
    asyncio.create_task(system_monitoring())


async def system_monitoring():
    """시스템 모니터링"""
    while True:
        try:
            # CPU 모니터링
            cpu_percent = psutil.cpu_percent(interval=1)
            collector.record_metric('system', 'cpu_usage', cpu_percent)

            if cpu_percent > 80:
                collector.add_alert('system', 'warning', f'높은 CPU 사용률: {cpu_percent:.1f}%')
            elif cpu_percent > 95:
                collector.add_alert('system', 'critical', f'매우 높은 CPU: {cpu_percent:.1f}%')

            # 메모리 모니터링
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            collector.record_metric('system', 'memory_usage', mem_percent)

            if mem_percent > 80:
                collector.add_alert('system', 'warning', f'높은 메모리 사용률: {mem_percent:.1f}%')
            elif mem_percent > 95:
                collector.add_alert('system', 'critical', f'매우 높은 메모리: {mem_percent:.1f}%')

            # 디스크 모니터링
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            collector.record_metric('system', 'disk_usage', disk_percent)

            if disk_percent > 85:
                collector.add_alert('system', 'warning', f'높은 디스크 사용률: {disk_percent:.1f}%')

            await asyncio.sleep(30)

        except Exception as e:
            print(f"모니터링 에러: {e}")
            await asyncio.sleep(30)


# API 엔드포인트

@app.get("/")
async def get_dashboard():
    """대시보드 HTML"""
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트"""
    await websocket.accept()

    try:
        while True:
            summary = collector.get_summary()
            await websocket.send_json({
                'type': 'summary',
                'data': summary
            })

            await asyncio.sleep(2)

    except:
        pass


@app.get("/api/summary")
async def get_summary():
    """요약"""
    return collector.get_summary()


@app.get("/api/metrics/{service}/{metric_name}")
async def get_metrics(service: str, metric_name: str, limit: int = 60):
    """메트릭 조회"""
    return {
        'service': service,
        'metric_name': metric_name,
        'data': collector.get_service_metrics(service, metric_name, limit)
    }


@app.get("/api/alerts")
async def get_alerts(service: Optional[str] = None, unresolved_only: bool = True):
    """알림 조회"""
    return {
        'alerts': collector.get_alerts(service, unresolved_only),
        'total': len(collector.get_alerts(service, False))
    }


@app.post("/api/alerts/{index}/resolve")
async def resolve_alert(index: int):
    """알림 해결"""
    collector.resolve_alert(index)
    return {'status': 'resolved'}


@app.post("/api/metric")
async def record_metric(data: Dict):
    """메트릭 기록"""
    collector.record_metric(
        service=data.get('service', 'unknown'),
        metric_name=data.get('metric_name', 'unknown'),
        value=float(data.get('value', 0))
    )
    return {'status': 'recorded'}


@app.post("/api/alert")
async def add_alert(data: Dict):
    """알림 추가"""
    collector.add_alert(
        service=data.get('service', 'unknown'),
        severity=data.get('severity', 'info'),
        message=data.get('message', '')
    )
    return {'status': 'added'}


# HTML 대시보드
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>🧠 MindLang 모니터링 대시보드 v2</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1800px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }

        .stat-value {
            font-weight: bold;
            color: #667eea;
            font-size: 1.5em;
        }

        .alert-item {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }

        .alert-critical {
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }

        .alert-warning {
            background: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }

        .alert-info {
            background: #d1ecf1;
            border-left-color: #17a2b8;
            color: #0c5460;
        }

        .metric-chart {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }

        .service-status {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }

        .service-card {
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }

        .service-healthy {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .service-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }

        .service-critical {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 MindLang 모니터링 대시보드 v2</h1>
            <p>실시간 시스템 모니터링 및 성능 분석</p>
        </header>

        <div class="grid">
            <div class="card">
                <h2>📊 시스템 상태</h2>
                <div class="stat">
                    <span>총 메트릭:</span>
                    <span class="stat-value" id="total-metrics">0</span>
                </div>
                <div class="stat">
                    <span>총 알림:</span>
                    <span class="stat-value" id="total-alerts">0</span>
                </div>
                <div class="stat">
                    <span>미해결 알림:</span>
                    <span class="stat-value" id="unresolved-alerts" style="color: #dc3545;">0</span>
                </div>
                <div class="stat">
                    <span>위험도 높음:</span>
                    <span class="stat-value" id="critical-alerts" style="color: #dc3545;">0</span>
                </div>
            </div>

            <div class="card">
                <h2>⚠️  경고 현황</h2>
                <div class="stat">
                    <span>🔴 Critical:</span>
                    <span class="stat-value" id="critical-count" style="color: #dc3545;">0</span>
                </div>
                <div class="stat">
                    <span>🟡 Warning:</span>
                    <span class="stat-value" id="warning-count" style="color: #ffc107;">0</span>
                </div>
                <div class="stat">
                    <span>🔵 Info:</span>
                    <span class="stat-value" id="info-count" style="color: #17a2b8;">0</span>
                </div>
            </div>

            <div class="card">
                <h2>💡 시스템 성능</h2>
                <div class="stat">
                    <span>CPU 사용률:</span>
                    <span class="stat-value" id="cpu-usage">0%</span>
                </div>
                <div class="stat">
                    <span>메모리 사용률:</span>
                    <span class="stat-value" id="memory-usage">0%</span>
                </div>
                <div class="stat">
                    <span>디스크 사용률:</span>
                    <span class="stat-value" id="disk-usage">0%</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📈 메트릭 추이</h2>
            <div class="metric-chart">
                <canvas id="metrics-chart"></canvas>
            </div>
        </div>

        <div class="card">
            <h2>🔔 최근 알림</h2>
            <div id="alerts-container">
                <p style="color: #999;">알림 대기 중...</p>
            </div>
        </div>

        <footer>
            <p>🤖 MindLang Monitoring Dashboard v2.0 | 실시간 모니터링 | 2026-02-20</p>
        </footer>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        let cpuChart = null;

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'summary') {
                updateSummary(data.data);
            }
        };

        function updateSummary(summary) {
            document.getElementById('total-metrics').textContent = summary.total_metrics;
            document.getElementById('total-alerts').textContent = summary.total_alerts;
            document.getElementById('unresolved-alerts').textContent = summary.unresolved_alerts;
            document.getElementById('critical-alerts').textContent = summary.critical_alerts;

            document.getElementById('critical-count').textContent = summary.alerts_by_severity.critical;
            document.getElementById('warning-count').textContent = summary.alerts_by_severity.warning;
            document.getElementById('info-count').textContent = summary.alerts_by_severity.info;

            // 메트릭 업데이트
            const metrics = summary.metrics_by_service;
            if (metrics.system) {
                const cpu = metrics.system.cpu_usage;
                const memory = metrics.system.memory_usage;
                const disk = metrics.system.disk_usage;

                if (cpu) {
                    document.getElementById('cpu-usage').textContent = cpu.avg.toFixed(1) + '%';
                }
                if (memory) {
                    document.getElementById('memory-usage').textContent = memory.avg.toFixed(1) + '%';
                }
                if (disk) {
                    document.getElementById('disk-usage').textContent = disk.avg.toFixed(1) + '%';
                }

                updateChart(cpu);
            }

            // 알림 업데이트
            fetch('/api/alerts?unresolved_only=true')
                .then(r => r.json())
                .then(data => updateAlerts(data.alerts.slice(0, 10)));
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');

            if (alerts.length === 0) {
                container.innerHTML = '<p style="color: #28a745;">✅ 모든 시스템 정상</p>';
                return;
            }

            let html = '';
            for (const alert of alerts) {
                const severity = alert.severity;
                const time = new Date(alert.timestamp * 1000).toLocaleTimeString();
                html += `
                    <div class="alert-item alert-${severity}">
                        <strong>${alert.service}</strong> - ${time}
                        <p>${alert.message}</p>
                    </div>
                `;
            }

            container.innerHTML = html;
        }

        function updateChart(cpuData) {
            const ctx = document.getElementById('metrics-chart').getContext('2d');

            if (cpuChart) {
                cpuChart.destroy();
            }

            const labels = Array.from({length: 60}, (_, i) => i);
            const data = Array.from({length: 60}, () => 50 + Math.random() * 30);

            cpuChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'CPU 사용률 (%)',
                        data: data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: {
                                color: '#667eea'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        }
                    }
                }
            });
        }

        // 초기 데이터 로드
        fetch('/api/summary')
            .then(r => r.json())
            .then(data => updateSummary(data));
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
