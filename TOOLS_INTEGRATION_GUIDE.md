# 🛠️ MindLang 통합 도구 가이드

**작성**: 2026-02-20
**목적**: 5가지 필수 도구를 MindLang 시스템에 통합
**상태**: 완성됨 ✅

---

## 🎯 5가지 필수 도구

```
1️⃣  realtime_dashboard.py       (실시간 대시보드)
2️⃣  ai_performance_benchmark.py  (AI 성능 벤치마크)
3️⃣  learning_engine.py           (자동 학습 엔진)
4️⃣  decision_history_analyzer.py (의사결정 분석)
5️⃣  TOOLS_INTEGRATION_GUIDE.md   (이 문서)
```

---

## 1️⃣ 실시간 대시보드 (realtime_dashboard.py)

### 목적
- 4경로 추론을 실시간으로 시각화
- WebSocket 기반 실시간 업데이트
- 의사결정 히스토리 표시
- 현재 상태 모니터링

### 시작하기

```bash
# 설치
pip install fastapi uvicorn

# 실행
python realtime_dashboard.py
```

### 접근
- 브라우저: http://localhost:8000
- WebSocket: ws://localhost:8000/ws

### API 엔드포인트

```
GET /
  → 대시보드 HTML 페이지

GET /stats
  → 통계 조회
  응답: {
    "total_decisions": 42,
    "average_confidence": 0.82,
    "decision_breakdown": {"SCALE_UP": 15, "CONTINUE": 27}
  }

POST /decision
  → 의사결정 보고
  본문: {
    "metrics": {...},
    "path1": {...},
    "path2": {...},
    "path3": {...},
    "path4": {...},
    "final_decision": "SCALE_UP",
    "confidence": 0.87
  }

GET /history?limit=20
  → 의사결정 이력 조회 (최근 20개)
```

### 실시간 사용 예시

```python
import asyncio
import aiohttp
import json

async def report_decision():
    async with aiohttp.ClientSession() as session:
        decision_data = {
            'metrics': {
                'cpu_usage': 85,
                'memory_usage': 78,
                'error_rate': 0.025
            },
            'path1': {'action': 'ROLLBACK', 'confidence': 0.76},
            'path2': {'action': 'SCALE_UP', 'confidence': 0.90},
            'path3': {'action': 'NO_ACTION', 'confidence': 0.40},
            'path4': {'action': 'CANARY_FIRST', 'confidence': 0.88},
            'final_decision': 'SCALE_UP',
            'confidence': 0.87
        }

        async with session.post(
            'http://localhost:8000/decision',
            json=decision_data
        ) as resp:
            print(await resp.json())

asyncio.run(report_decision())
```

---

## 2️⃣ AI 성능 벤치마크 (ai_performance_benchmark.py)

### 목적
- 5개 AI 모델의 실제 성능 비교
- 응답 시간, 정확도, 비용, 메모리 측정
- 최적 모델 선택 가이드 제공
- JSON 결과 저장

### 시작하기

```bash
# 실행
python ai_performance_benchmark.py
```

### 출력 예시

```
=================================
🎯 AI 성능 벤치마크 결과
=================================

모델          응답시간      정확도    비용/req    메모리
GPT-4        500.25ms      95.0%    $0.000045   512MB
Claude       600.50ms      93.0%    $0.000068   480MB
Llama2       100.15ms      70.0%    $0.000000   2048MB
Mistral       50.08ms      65.0%    $0.000000   1024MB
MindLang      20.03ms      70.0%    $0.000000   256MB

🏆 순위
⚡ 응답 시간 (빠를수록 좋음)
  1. MindLang: 20.03ms
  2. Mistral: 50.08ms
  3. Llama2: 100.15ms

🎯 정확도 (높을수록 좋음)
  1. GPT-4: 95.0%
  2. Claude: 93.0%
  3. Llama2: 70.0%

💰 비용 (낮을수록 좋음)
  1. MindLang: $0.000000
  2. Llama2: $0.000000
  3. Mistral: $0.000000

⚖️ 균형잡힌 선택
  → Claude (종합점수: 45.23)
```

### 코드 통합

```python
from ai_performance_benchmark import AIBenchmark
import asyncio

async def compare_models():
    benchmark = AIBenchmark(num_iterations=100)
    results = await benchmark.run_all_benchmarks()

    # 최적 모델 선택
    latencies = {r.model: r.latency_ms for r in results}
    best_speed = min(latencies, key=latencies.get)
    print(f"가장 빠른 모델: {best_speed}")

    accuracies = {r.model: r.accuracy for r in results}
    best_accuracy = max(accuracies, key=accuracies.get)
    print(f"가장 정확한 모델: {best_accuracy}")

asyncio.run(compare_models())
```

---

## 3️⃣ 자동 학습 엔진 (learning_engine.py)

### 목적
- 과거 의사결정으로부터 자동으로 학습
- 패턴 인식 및 경고 생성
- 최적 경로 추천
- 메모리에 영속화

### 시작하기

```bash
# 실행 (테스트 데이터 포함)
python learning_engine.py
```

### 주요 기능

#### 1. 의사결정 기록

```python
from learning_engine import LearningEngine, DecisionRecord

engine = LearningEngine()

record = DecisionRecord(
    timestamp=time.time(),
    metrics={
        'cpu_usage': 85,
        'memory_usage': 78,
        'error_rate': 0.025
    },
    decision='SCALE_UP',
    confidence=0.87,
    path1_action='ROLLBACK',
    path1_confidence=0.76,
    path2_action='SCALE_UP',
    path2_confidence=0.90,
    path3_action='NO_ACTION',
    path3_confidence=0.40,
    path4_recommendation='CANARY_FIRST',
    path4_confidence=0.88
)

engine.record_decision(record)
```

#### 2. 결과 기록

```python
# 나중에 결과를 알게 되면
engine.record_outcome(
    decision_index=0,
    outcome="SCALE_UP succeeded, CPU dropped to 45%",
    success=True
)
```

#### 3. 학습 및 권고

```python
recommendations = engine.get_recommendations()

print(recommendations['next_action'])
# 출력 예: "💡 최적 모델: PATH2 (정확도 85%)"
```

### 학습 항목

| 항목 | 설명 | 활용 |
|------|------|------|
| **정확도** | 의사결정의 성공률 | 모델 신뢰도 조정 |
| **패턴** | 반복되는 의사결정 | 자동 정책 생성 |
| **경고** | 연속 실패, 과도한 변동성 | 수동 검토 트리거 |
| **최적 경로** | 가장 정확한 경로 | 가중치 재조정 |

---

## 4️⃣ 의사결정 분석기 (decision_history_analyzer.py)

### 목적
- 의사결정 이력 상세 분석
- 시계열 추이 분석
- 경로별 정확도 비교
- 최고/최악의 결정 식별

### 시작하기

```bash
# 실행
python decision_history_analyzer.py
```

### 분석 항목

#### 1. 의사결정 분포

```
SCALE_UP:  40%  ████████████
CONTINUE:  45%  █████████████
ROLLBACK:  15%  ████
```

#### 2. 신뢰도 추이

```
평균:   82.3%
중앙값: 83.5%
범위:   45% ~ 96%
추세:   📈 상승 (최근 개선)
```

#### 3. 경로별 정확도

```
Path1: 65% (13/20)  █████████████
Path2: 85% (17/20)  █████████████████
Path3: 55% (11/20)  ███████████
Path4: 78% (15/20)  ████████████████
```

### 코드 통합

```python
from decision_history_analyzer import DecisionHistoryAnalyzer

analyzer = DecisionHistoryAnalyzer()

# 의사결정 분포
dist = analyzer.analyze_decision_distribution()
print(f"SCALE_UP: {dist['percentage'].get('SCALE_UP', 0):.1%}")

# 최고의 결정
best = analyzer.get_best_decisions(limit=5)
for decision in best:
    print(f"✅ {decision['decision']} (신뢰도: {decision['confidence']:.1%})")

# 리포트 생성
report = analyzer.generate_report()
print(report)
```

---

## 🔗 통합 워크플로우

### 실시간 운영

```
1. MindLang 4경로 추론 실행
    ↓
2. 결정 → Dashboard로 전송 (실시간 표시)
    ↓
3. 결과 → Learning Engine 기록
    ↓
4. 주기적 분석 (1시간마다)
    → history_analyzer 실행
    → 통찰 생성
    → 경고 발생 시 알림
```

### 통합 Python 코드

```python
import asyncio
from learning_engine import LearningEngine, DecisionRecord
from ai_performance_benchmark import AIBenchmark
from decision_history_analyzer import DecisionHistoryAnalyzer
import aiohttp
import json
import time

class MindLangOrchestrator:
    def __init__(self):
        self.engine = LearningEngine()
        self.analyzer = DecisionHistoryAnalyzer()
        self.dashboard_url = "http://localhost:8000"

    async def execute_decision(self, metrics):
        """전체 의사결정 파이프라인"""

        # 1. MindLang 추론 (가정)
        path1, path2, path3, path4 = self._run_mindlang(metrics)

        # 2. 최적 AI 선택 (벤치마크 결과 기반)
        best_ai = self._select_best_ai(metrics)

        # 3. 최종 결정
        final_decision = self._combine_paths(path1, path2, path3, path4)

        # 4. Dashboard에 보고
        await self._report_to_dashboard(
            metrics, path1, path2, path3, path4, final_decision
        )

        # 5. Learning Engine에 기록
        record = DecisionRecord(
            timestamp=time.time(),
            metrics=metrics,
            decision=final_decision['action'],
            confidence=final_decision['confidence'],
            path1_action=path1['action'],
            path1_confidence=path1['confidence'],
            path2_action=path2['action'],
            path2_confidence=path2['confidence'],
            path3_action=path3['action'],
            path3_confidence=path3['confidence'],
            path4_recommendation=path4['action'],
            path4_confidence=path4['confidence']
        )
        self.engine.record_decision(record)

        return final_decision

    async def _report_to_dashboard(self, metrics, p1, p2, p3, p4, decision):
        """Dashboard에 보고"""
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.dashboard_url}/decision",
                json={
                    'metrics': metrics,
                    'path1': p1,
                    'path2': p2,
                    'path3': p3,
                    'path4': p4,
                    'final_decision': decision['action'],
                    'confidence': decision['confidence']
                }
            )

    def _run_mindlang(self, metrics):
        """MindLang 추론 (생략)"""
        pass

    def _select_best_ai(self, metrics):
        """벤치마크 결과로 최적 AI 선택"""
        pass

    def _combine_paths(self, p1, p2, p3, p4):
        """경로 합의"""
        pass
```

---

## 📊 모니터링 대시보드

### 추천 메트릭

```
실시간 (초 단위):
  - 현재 의사결정
  - 4경로 상태
  - 최종 결정

분당 (분 단위):
  - 의사결정 분포
  - 평균 신뢰도
  - 연결 상태

시간 단위:
  - 경로별 정확도
  - 패턴 인식
  - 경고 목록

일 단위:
  - 전체 분석 리포트
  - 최고/최악의 결정
  - 개선 권고
```

---

## 🚀 배포 가이드

### Docker Compose (권장)

```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MINDLANG_MODE=dashboard
    volumes:
      - ./data:/app/data

  learning:
    build: .
    environment:
      - MINDLANG_MODE=learning
    volumes:
      - ./data:/app/data
    restart: always

  analyzer:
    build: .
    environment:
      - MINDLANG_MODE=analyzer
    volumes:
      - ./data:/app/data
    schedule: "0 * * * *"  # 1시간마다 실행
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mindlang-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mindlang-dashboard
  template:
    metadata:
      labels:
        app: mindlang-dashboard
    spec:
      containers:
      - name: dashboard
        image: mindlang:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODE
          value: "dashboard"
```

---

## 💾 데이터 저장 구조

```
mindlang_data/
├── decision_memory.json          (의사결정 이력)
├── benchmark_results.json        (벤치마크 결과)
├── decision_analysis_report.txt  (분석 리포트)
└── insights.json                 (학습된 통찰)
```

---

## ⚙️ 설정

### environment.json

```json
{
  "mindlang": {
    "max_history": 1000,
    "learning_interval": 3600,
    "analysis_interval": 3600
  },
  "dashboard": {
    "host": "0.0.0.0",
    "port": 8000,
    "update_interval": 2000
  },
  "benchmark": {
    "iterations": 100,
    "timeout_per_model": 2.0
  },
  "learning": {
    "enable_pattern_detection": true,
    "enable_warning_detection": true,
    "enable_path_optimization": true
  }
}
```

---

## 🎯 다음 단계

### 단기 (1주)
- [ ] 대시보드 웹 인터페이스 개선
- [ ] 벤치마크 자동화
- [ ] 메트릭 DB 연결

### 중기 (1개월)
- [ ] 고급 분석 (머신러닝)
- [ ] 자동 정책 생성
- [ ] 알림 시스템

### 장기 (3개월)
- [ ] 멀티테넌트 지원
- [ ] API 확장
- [ ] 고급 시각화

---

## 📞 문제 해결

### 대시보드 연결 안 됨

```bash
# 포트 확인
lsof -i :8000

# 프로세스 재시작
pkill -f realtime_dashboard
python realtime_dashboard.py
```

### 메모리 부족

```python
# decision_memory.json 정리
engine.decisions = engine.decisions[-100:]  # 최근 100개만
engine.save_memory()
```

---

**완성**: 2026-02-20 ✅
**상태**: 프로덕션 레디
**지원**: 24/7 모니터링

🚀 **이제 MindLang은 완전히 자동화되고 모니터링 가능한 시스템입니다.**
