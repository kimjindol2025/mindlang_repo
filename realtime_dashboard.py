#!/usr/bin/env python3
"""
MindLang 실시간 대시보드
FastAPI + WebSocket 기반 실시간 모니터링

시각화 항목:
- 4경로 추론 결과 (실시간)
- AI 의견 비교 (다중 AI)
- Red Team 분석 (자동 비판)
- 의사결정 히스토리
- 성능 메트릭
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List
import random


app = FastAPI(title="MindLang Dashboard")


@dataclass
class DecisionEvent:
    """의사결정 이벤트"""
    timestamp: float
    metrics: Dict
    path1: Dict
    path2: Dict
    path3: Dict
    path4: Dict
    final_decision: str
    confidence: float


class DashboardManager:
    """대시보드 관리자"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.decision_history: List[DecisionEvent] = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        """모든 클라이언트에게 브로드캐스트"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    def add_decision(self, event: DecisionEvent):
        """의사결정 이력 추가"""
        self.decision_history.append(event)
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)

    def get_stats(self) -> Dict:
        """통계 계산"""
        if not self.decision_history:
            return {}

        decisions = [e.final_decision for e in self.decision_history]
        decision_counts = {}
        for d in decisions:
            decision_counts[d] = decision_counts.get(d, 0) + 1

        confidences = [e.confidence for e in self.decision_history]
        avg_confidence = sum(confidences) / len(confidences)

        return {
            'total_decisions': len(self.decision_history),
            'decision_breakdown': decision_counts,
            'average_confidence': avg_confidence,
            'recent_decisions': [asdict(e) for e in self.decision_history[-10:]]
        }


manager = DashboardManager()


@app.get("/")
async def get_dashboard():
    """대시보드 HTML"""
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트"""
    await manager.connect(websocket)

    try:
        while True:
            # 초기 통계 전송
            stats = manager.get_stats()
            await websocket.send_json({
                'type': 'stats',
                'data': stats
            })

            await asyncio.sleep(2)

    except:
        manager.disconnect(websocket)


@app.post("/decision")
async def report_decision(decision_data: Dict):
    """의사결정 보고"""
    event = DecisionEvent(
        timestamp=time.time(),
        metrics=decision_data.get('metrics', {}),
        path1=decision_data.get('path1', {}),
        path2=decision_data.get('path2', {}),
        path3=decision_data.get('path3', {}),
        path4=decision_data.get('path4', {}),
        final_decision=decision_data.get('final_decision', 'UNKNOWN'),
        confidence=decision_data.get('confidence', 0.0)
    )

    manager.add_decision(event)

    # 모든 클라이언트에게 브로드캐스트
    await manager.broadcast({
        'type': 'decision',
        'timestamp': datetime.now().isoformat(),
        'decision': event.final_decision,
        'confidence': event.confidence,
        'path1': event.path1,
        'path2': event.path2,
        'path3': event.path3,
        'path4': event.path4,
        'metrics': event.metrics
    })

    return {'status': 'received'}


@app.get("/stats")
async def get_stats():
    """통계 조회"""
    return manager.get_stats()


@app.get("/history")
async def get_history(limit: int = 20):
    """의사결정 이력 조회"""
    return [asdict(e) for e in manager.decision_history[-limit:]]


# HTML 대시보드
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>🧠 MindLang 실시간 대시보드</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1600px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }

        header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        header p {
            color: #666;
            font-size: 1.1em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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

        .card h3 {
            color: #333;
            margin: 15px 0 10px 0;
            font-size: 1.1em;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }

        .metric-value {
            font-weight: bold;
            color: #667eea;
            font-size: 1.2em;
        }

        .path-item {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
        }

        .path-action {
            font-weight: bold;
            color: #764ba2;
            font-size: 1.1em;
        }

        .path-confidence {
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .decision-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            margin: 20px 0;
        }

        .status-active {
            color: #4caf50;
            font-weight: bold;
        }

        .status-inactive {
            color: #f44336;
            font-weight: bold;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }

        .red-team-alert {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }

        .red-team-critical {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            color: #721c24;
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
            <h1>🧠 MindLang 실시간 대시보드</h1>
            <p>4경로 추론 + Red Team + 다중 AI 의사결정 시스템</p>
        </header>

        <div class="grid">
            <!-- 현재 상태 -->
            <div class="card">
                <h2>📊 현재 상태</h2>
                <div class="metric">
                    <span>총 의사결정:</span>
                    <span class="metric-value" id="total-decisions">0</span>
                </div>
                <div class="metric">
                    <span>평균 신뢰도:</span>
                    <span class="metric-value" id="avg-confidence">0%</span>
                </div>
                <div class="metric">
                    <span>연결 상태:</span>
                    <span class="metric-value status-active">🟢 연결됨</span>
                </div>
            </div>

            <!-- 의사결정 분포 -->
            <div class="card">
                <h2>🎯 의사결정 분포</h2>
                <div id="decisions-breakdown">
                    <p style="color: #999;">데이터 대기 중...</p>
                </div>
            </div>

            <!-- 최신 의사결정 -->
            <div class="card">
                <h2>⚡ 최신 의사결정</h2>
                <div id="latest-decision">
                    <p style="color: #999;">데이터 대기 중...</p>
                </div>
            </div>
        </div>

        <!-- 4경로 분석 -->
        <div class="card">
            <h2>🔍 4경로 병렬 분석</h2>
            <div class="grid">
                <div>
                    <h3>Path 1: Error-Driven</h3>
                    <div id="path1-content">대기 중...</div>
                </div>
                <div>
                    <h3>Path 2: Performance-Driven</h3>
                    <div id="path2-content">대기 중...</div>
                </div>
                <div>
                    <h3>Path 3: Cost-Driven</h3>
                    <div id="path3-content">대기 중...</div>
                </div>
                <div>
                    <h3>Path 4: Red Team</h3>
                    <div id="path4-content">대기 중...</div>
                </div>
            </div>
        </div>

        <!-- 최종 결정 -->
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <h2 style="color: white; border-bottom-color: white;">🎯 최종 결정</h2>
            <div class="decision-box" style="background: transparent; border: 2px solid white;">
                <div id="final-decision" style="font-size: 2em;">대기 중...</div>
                <div id="final-confidence" style="font-size: 0.8em; margin-top: 10px; color: #ddd;">
                    신뢰도: --
                </div>
            </div>
        </div>

        <footer>
            <p>🤖 MindLang v2.0 | 다중 AI 의사결정 시스템 | 2026-02-20</p>
            <p>철학: "확신이 높을수록 더 신중하게"</p>
        </footer>
    </div>

    <script>
        // WebSocket 연결
        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'stats') {
                updateStats(data.data);
            } else if (data.type === 'decision') {
                updateDecision(data);
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket 에러:', error);
        };

        function updateStats(stats) {
            if (!stats.total_decisions) return;

            document.getElementById('total-decisions').textContent = stats.total_decisions;
            document.getElementById('avg-confidence').textContent =
                (stats.average_confidence * 100).toFixed(1) + '%';

            // 의사결정 분포
            const breakdown = stats.decision_breakdown || {};
            let html = '';
            for (const [decision, count] of Object.entries(breakdown)) {
                const percent = (count / stats.total_decisions * 100).toFixed(1);
                html += `
                    <div class="metric">
                        <span>${decision}</span>
                        <span class="metric-value">${count} (${percent}%)</span>
                    </div>
                `;
            }
            document.getElementById('decisions-breakdown').innerHTML = html || '<p>데이터 없음</p>';
        }

        function updateDecision(data) {
            // 최종 결정
            document.getElementById('final-decision').textContent = data.decision;
            document.getElementById('final-confidence').textContent =
                `신뢰도: ${(data.confidence * 100).toFixed(1)}%`;

            // 4경로 업데이트
            updatePath(1, data.path1);
            updatePath(2, data.path2);
            updatePath(3, data.path3);
            updatePath(4, data.path4);

            // 최신 의사결정
            const latestHtml = `
                <div class="path-item">
                    <div class="path-action">${data.decision}</div>
                    <div class="path-confidence">신뢰도: ${(data.confidence * 100).toFixed(1)}%</div>
                    <div class="path-confidence">${new Date(data.timestamp).toLocaleTimeString()}</div>
                </div>
            `;
            document.getElementById('latest-decision').innerHTML = latestHtml;
        }

        function updatePath(pathNum, pathData) {
            if (!pathData || !pathData.action) {
                document.getElementById(`path${pathNum}-content`).innerHTML = '데이터 대기 중...';
                return;
            }

            const html = `
                <div class="path-item">
                    <div class="path-action">${pathData.action}</div>
                    <div class="path-confidence">신뢰도: ${(pathData.confidence * 100).toFixed(1)}%</div>
                    <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                        ${pathData.reasoning || ''}
                    </div>
                </div>
            `;
            document.getElementById(`path${pathNum}-content`).innerHTML = html;
        }

        // 주기적으로 통계 업데이트
        setInterval(() => {
            fetch('/stats')
                .then(r => r.json())
                .then(data => updateStats(data));
        }, 3000);
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
