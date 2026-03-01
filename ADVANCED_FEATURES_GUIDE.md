# 🚀 MindLang 고급 기능 가이드

**작성**: 2026-02-20
**버전**: 2.0
**상태**: 프로덕션 레디 ✅

## 📋 목차

1. [API 게이트웨이](#-api-게이트웨이)
2. [CLI 도구](#-cli-도구)
3. [자동 정책 엔진](#-자동-정책-엔진)
4. [통합 아키텍처](#-통합-아키텍처)
5. [사용 예제](#-사용-예제)

---

## 🌐 API 게이트웨이

### 목적

모든 마이크로서비스의 중앙 진입점으로 작동하는 통합 API 게이트웨이입니다.

**기능:**
- 통합 인증 및 권한 관리
- 요청/응답 로깅 및 모니터링
- 서비스 라우팅 및 로드 밸런싱
- 속도 제한 및 부하 분산
- 자동 재시도 및 에러 처리
- 실시간 메트릭 수집

### 설치 및 시작

```bash
# 포트 8100에서 시작
python api_gateway.py
```

### API 엔드포인트

```
# 시스템 상태
GET  /health
GET  /metrics
GET  /metrics/{service_name}

# 서비스 관리
GET  /services
POST /services/{service_name}/register

# 로깅 및 모니터링
GET  /logs?service={name}&limit=100
POST /cache/clear

# 라우팅 (모든 마이크로서비스)
{METHOD} /{service_name}/{path}
```

### 사용 예시

```bash
# 게이트웨이 상태 확인
curl http://localhost:8100/health

# 메트릭 조회
curl http://localhost:8100/metrics

# 특정 서비스 메트릭
curl http://localhost:8100/metrics/dashboard

# 로그 조회
curl "http://localhost:8100/logs?service=dashboard&limit=50"

# 서비스 요청 (라우팅)
curl -X POST http://localhost:8100/dashboard/decision \
  -H "Content-Type: application/json" \
  -d '{"metrics": {"cpu": 85, "memory": 78}}'
```

### 서비스 등록

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8100/services/my-service/register",
        json={
            "url": "http://localhost",
            "port": 9000,
            "timeout": 30,
            "retry_count": 3
        }
    )
```

### 메트릭 수집

게이트웨이는 자동으로 다음 메트릭을 수집합니다:

```json
{
  "timestamp": "2026-02-20T10:30:00",
  "services": {
    "dashboard": {
      "status": "healthy",
      "response_time": 0.045,
      "request_count": 1024,
      "error_count": 2,
      "error_rate": 0.002,
      "last_check": 1708414200.5
    }
  },
  "total_requests": 4096,
  "total_errors": 8
}
```

---

## 💻 CLI 도구

### 목적

커맨드 라인에서 MindLang 시스템의 모든 기능을 제어합니다.

**기능:**
- 의사결정 실행
- 이력 분석
- 모델 벤치마크
- 대시보드 관리
- 시스템 상태 모니터링
- 로그 조회

### 설치

```bash
# 의존성 설치
pip install typer rich httpx

# CLI 권한 설정
chmod +x mindlang_cli.py
```

### 명령어

#### 1. 의사결정 실행

```bash
# 기본 사용
python mindlang_cli.py decision cpu:85,mem:78,error:0.05

# 상세 출력
python mindlang_cli.py decision cpu:85,mem:78 --verbose

# JSON 출력
python mindlang_cli.py decision cpu:85,mem:78 --output json

# 결과 저장
python mindlang_cli.py decision cpu:85,mem:78 --save

# 복합 메트릭
python mindlang_cli.py decision "cpu:85,mem:78,error:0.025,latency:250" -v -s
```

**출력 예:**
```
🤔 의사결정 실행 중...
✅ 의사결정 완료
결정: SCALE_UP | 신뢰도: 87.0%
💾 결과 저장: decision_result.json
```

#### 2. 이력 분석

```bash
# 기본 분석
python mindlang_cli.py analyze

# 리포트 생성
python mindlang_cli.py analyze --report

# 결과 저장
python mindlang_cli.py analyze --report --save

# 최근 200개 레코드 분석
python mindlang_cli.py analyze --limit 200
```

**출력 예:**
```
📊 분석 시작...

분석 요약
의사결정 분포:
  SCALE_UP: 45개
  CONTINUE: 38개
  ROLLBACK: 17개

평균 신뢰도: 82.3%
신뢰도 범위: 45.0% ~ 96.0%
```

#### 3. 벤치마크

```bash
# 모든 모델 벤치마크
python mindlang_cli.py benchmark --models all

# 특정 모델만
python mindlang_cli.py benchmark --models gpt4,claude

# 더 많은 반복
python mindlang_cli.py benchmark --iterations 100

# 결과 저장
python mindlang_cli.py benchmark --save
```

**출력 예:**
```
⚡ 벤치마크 실행 중...

벤치마크 결과
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━━┓
┃ 모델      ┃ 응답시간 ┃ 정확도 ┃ 비용 ┃ 메모리  ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━━┩
│ GPT-4     │ 500ms  │ 95%   │ $45  │ 512MB  │
│ Claude    │ 600ms  │ 93%   │ $68  │ 480MB  │
│ MindLang  │ 20ms   │ 70%   │ $0   │ 256MB  │
└───────────┴────────┴───────┴──────┴────────┘
```

#### 4. 대시보드 관리

```bash
# 대시보드 시작
python mindlang_cli.py dashboard --start

# 포트 변경하여 시작
python mindlang_cli.py dashboard --start --port 9000

# 브라우저에서 자동 열기
python mindlang_cli.py dashboard --start --open

# 현재 상태만 조회
python mindlang_cli.py dashboard
```

#### 5. 시스템 상태

```bash
# 기본 상태
python mindlang_cli.py status

# 상세 정보
python mindlang_cli.py status --detailed
```

**출력 예:**
```
시스템 상태
게이트웨이: healthy
시간: 2026-02-20T10:30:00

서비스 상태:
✅ dashboard: healthy (0.045s)
✅ learning: healthy (0.032s)
✅ benchmark: healthy (0.018s)
⚠️ analyzer: degraded (0.156s)
```

#### 6. 로그 조회

```bash
# 최근 20개 로그
python mindlang_cli.py logs

# 특정 서비스만
python mindlang_cli.py logs dashboard --limit 50

# 에러만 표시
python mindlang_cli.py logs --error
```

#### 7. 설정 관리

```bash
# 전체 설정 표시
python mindlang_cli.py config show

# 특정 설정 조회
python mindlang_cli.py config get gateway.port

# 설정 변경
python mindlang_cli.py config set gateway.timeout 60
```

#### 8. 도움말 및 버전

```bash
# 버전 정보
python mindlang_cli.py version

# 사용 가이드
python mindlang_cli.py help
```

### Python에서 사용

```python
from mindlang_cli import APIClient
import asyncio

async def example():
    client = APIClient()

    # 의사결정 실행
    result = await client.call_service(
        "dashboard",
        method="POST",
        path="/decision",
        data={
            "metrics": {"cpu": 85, "memory": 78},
            "timestamp": "2026-02-20T10:30:00"
        }
    )

    print(result)
    await client.close()

asyncio.run(example())
```

---

## 🧠 자동 정책 엔진

### 목적

학습 엔진의 결과를 정책으로 자동 변환하고 적용합니다.

**기능:**
- 패턴 기반 정책 생성
- 임계값 기반 정책 생성
- 신뢰도 기반 우선순위 지정
- 정책 충돌 해결
- 정책 효과 검증
- 자동 롤백

### 정책 유형

#### 1. Threshold (임계값)
```
CPU > 85% → SCALE_UP
Memory > 90% → ROLLBACK
```

#### 2. Pattern (패턴)
```
High CPU + High Error → ROLLBACK_AND_MONITOR
Stable Metrics → CONTINUE
```

#### 3. Time-Based (시간 기반)
```
업무 시간 (9-18) → 적극적 SCALE_UP
야간 (18-9) → 보수적 CONTINUE
```

#### 4. Correlation (상관관계)
```
CPU ↑ → Memory ↓ (스케일업 효과)
Error ↑ → Latency ↑ (피드백 루프)
```

#### 5. Learned (학습 기반)
```
과거 80% 성공한 패턴 → 정책화
```

### 사용 방법

#### 패턴 기반 정책 생성

```python
from auto_policy_engine import AutoPolicyEngine

engine = AutoPolicyEngine()

# 패턴으로부터 정책 생성
policy = engine.create_policy_from_pattern(
    pattern_name="High CPU → Scale Up",
    pattern_description="CPU 사용률이 85% 이상일 때는 SCALE_UP이 최적",
    condition={"cpu_usage": ">85"},
    recommended_action="SCALE_UP",
    confidence=0.87,  # 87% 신뢰도
    evidence_count=42  # 42개 사례 기반
)
```

#### 임계값 기반 정책 생성

```python
# 임계값 기반 정책 생성
policy = engine.create_policy_from_threshold(
    metric_name="error_rate",
    threshold_value=0.05,
    comparison=">",  # 초과할 때
    recommended_action="ROLLBACK",
    confidence=0.92,
    evidence_count=35
)
```

#### 정책 활성화 및 평가

```python
# 정책 활성화
engine.activate_policy(policy.id)

# 메트릭으로 정책 평가
metrics = {
    'cpu_usage': 88,
    'memory_usage': 70,
    'error_rate': 0.02
}

action, policy_id, confidence = engine.evaluate_policies(metrics)
print(f"추천 동작: {action}")
print(f"신뢰도: {confidence:.1%}")

# 적용 기록
engine.record_application(
    policy_id=policy_id,
    metrics=metrics,
    result=action,
    success=True,  # 실제 결과가 성공했는지
    feedback="CPU 빠르게 정상화됨"
)
```

#### 정책 권고사항 조회

```python
recommendations = engine.get_policy_recommendations()

for rec in recommendations['recommendations']:
    print(f"{rec['type']}: {rec['policy_name']}")
    print(f"  이유: {rec['reason']}")
```

**출력 예:**
```
승격 권고: High CPU → Scale Up
  이유: 높은 성공률 (87.5%)

롤백 권고: Memory Threshold Policy
  이유: 낮은 성공률 (42.3%)

활성화 권고: Pattern-Based Cost Control
  이유: 높은 신뢰도 (78.5%)
```

#### 정책 통계

```python
stats = engine.get_policy_statistics()

print(f"총 정책: {stats['total_policies']}")
print(f"활성 정책: {stats['by_status']['active']}")
print(f"평균 신뢰도: {stats['avg_confidence']:.1%}")
print(f"전체 성공률: {stats['success_rate_overall']:.1%}")
```

### 정책 상태 머신

```
DRAFT (작성중)
  ↓
TESTING (테스트)
  ↓ (성공 ≥80%)
ACTIVE (활성)
  ↓ (실패 ≤50%)
ROLLBACK (롤백)

또는

DRAFT → DEPRECATED (사용중단)
```

### 정책 충돌 해결

```python
# 충돌하는 정책 찾기
conflicts = engine.get_conflicting_policies()

for policy1, policy2 in conflicts:
    print(f"충돌: {policy1.name} ↔ {policy2.name}")
    print(f"  우선순위: {policy1.priority} vs {policy2.priority}")
```

---

## 🔗 통합 아키텍처

### 시스템 흐름

```
┌─────────────────────────────────────────────────────┐
│                 CLI / API Client                     │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────▼──────────────┐
        │   API Gateway (8100)      │
        │  - 라우팅                 │
        │  - 인증                   │
        │  - 로깅                   │
        │  - 메트릭 수집            │
        └────┬───────┬───────┬──────┘
             │       │       │
   ┌─────────▼─┐ ┌───▼──────┐ ┌──────┬─────────────┐
   │ Dashboard │ │ Learning │ │      │             │
   │ (8000)    │ │ (8001)   │ │      │ Analyzer    │
   │           │ │          │ │      │ (8003)      │
   │ Real-time │ │ Auto-    │ │      │             │
   │ Updates   │ │ Learning │ │      │ History     │
   └───────────┘ └──────────┘ │      │ Analysis    │
                               │      └─────────────┘
                      ┌────────▼──────────┐
                      │ Policy Engine     │
                      │ - 정책 생성       │
                      │ - 자동 활성화     │
                      │ - 충돌 해결       │
                      │ - 롤백 관리       │
                      └───────────────────┘
```

### 데이터 흐름

```
1. 의사결정
   MindLang 4경로 → 최종 결정

2. 대시보드
   결정 결과 → 실시간 시각화

3. 학습
   결과 기록 → 패턴 인식 → 통찰 생성

4. 정책 생성
   통찰 → 정책화 → 신뢰도 계산

5. 정책 검증
   정책 적용 → 결과 기록 → 성공률 계산

6. 피드백
   성공률 ≥80% → 승격
   성공률 ≤50% → 롤백
```

---

## 📊 사용 예제

### 예제 1: 완전한 의사결정 사이클

```bash
#!/bin/bash

# 1. 의사결정 실행
echo "1️⃣ 의사결정 실행"
python mindlang_cli.py decision cpu:87,mem:82,error:0.03 -v -s

# 2. 현재 상태 확인
echo "2️⃣시스템 상태 확인"
python mindlang_cli.py status --detailed

# 3. 이력 분석
echo "3️⃣ 이력 분석"
python mindlang_cli.py analyze --report

# 4. 벤치마크 실행
echo "4️⃣ AI 모델 벤치마크"
python mindlang_cli.py benchmark --iterations 20 -s

# 5. 로그 확인
echo "5️⃣ 시스템 로그"
python mindlang_cli.py logs --limit 30
```

### 예제 2: Python에서 통합 사용

```python
from learning_engine import LearningEngine, DecisionRecord
from auto_policy_engine import AutoPolicyEngine
from api_gateway import APIGateway
import asyncio
import time

async def example():
    # 1. 의사결정 기록
    engine = LearningEngine()

    record = DecisionRecord(
        timestamp=time.time(),
        metrics={'cpu': 85, 'memory': 78, 'error_rate': 0.025},
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

    # 2. 학습 및 권고
    recommendations = engine.get_recommendations()
    print("학습 결과:")
    for insight in recommendations['insights']:
        print(f"  {insight['type']}: {insight['description']}")

    # 3. 정책 생성
    policy_engine = AutoPolicyEngine()

    for insight in recommendations['insights']:
        if insight['type'] == 'pattern':
            # 패턴을 정책으로 변환
            policy = policy_engine.create_policy_from_pattern(
                pattern_name=f"Auto-{insight['type']}",
                pattern_description=insight['description'],
                condition={'cpu': '>85'},
                recommended_action='SCALE_UP',
                confidence=insight['confidence'],
                evidence_count=1
            )
            policy_engine.activate_policy(policy.id)

    # 4. 다음 메트릭에 정책 적용
    new_metrics = {'cpu': 88, 'memory': 75, 'error_rate': 0.01}
    action, policy_id, conf = policy_engine.evaluate_policies(new_metrics)

    print(f"\n정책 적용 결과:")
    print(f"  동작: {action}")
    print(f"  신뢰도: {conf:.1%}")

asyncio.run(example())
```

### 예제 3: API Gateway를 통한 통합 호출

```python
import httpx
import asyncio

async def example():
    async with httpx.AsyncClient() as client:
        # 1. 게이트웨이 상태
        health = await client.get("http://localhost:8100/health")
        print(f"게이트웨이 상태: {health.json()['status']}")

        # 2. 대시보드 의사결정 호출
        decision = await client.post(
            "http://localhost:8100/dashboard/decision",
            json={
                "metrics": {"cpu": 85, "memory": 78},
                "path1": {"action": "ROLLBACK", "confidence": 0.76},
                "path2": {"action": "SCALE_UP", "confidence": 0.90},
                "path3": {"action": "NO_ACTION", "confidence": 0.40},
                "path4": {"action": "CANARY_FIRST", "confidence": 0.88},
                "final_decision": "SCALE_UP",
                "confidence": 0.87
            }
        )
        print(f"의사결정 결과: {decision.json()}")

        # 3. 메트릭 조회
        metrics = await client.get("http://localhost:8100/metrics")
        print(f"수집된 메트릭: {metrics.json()['total_requests']}개 요청")

asyncio.run(example())
```

---

## 🚀 배포 및 운영

### Docker Compose

```yaml
version: '3.8'

services:
  gateway:
    build: .
    ports:
      - "8100:8100"
    environment:
      - MINDLANG_MODE=gateway
    volumes:
      - ./logs:/app/logs

  dashboard:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MINDLANG_MODE=dashboard
    depends_on:
      - gateway

  learning:
    build: .
    environment:
      - MINDLANG_MODE=learning
    depends_on:
      - gateway
    volumes:
      - ./data:/app/data

  policy:
    build: .
    environment:
      - MINDLANG_MODE=policy
    depends_on:
      - learning
    volumes:
      - ./data:/app/data
```

### 운영 체크리스트

- ✅ 게이트웨이 상태 모니터링
- ✅ 서비스 헬스 체크 (30초 주기)
- ✅ 요청 로깅 (최근 10,000개 유지)
- ✅ 에러율 모니터링 (5% 이상 경고)
- ✅ 정책 성공률 추적
- ✅ 자동 롤백 트리거

---

## 📈 성능 최적화

### API Gateway
- 평균 응답시간: < 50ms
- 처리량: 1,000+ 요청/초
- 에러 복구: 3회 자동 재시도

### CLI
- 응답속도: < 100ms
- 병렬 실행: 최대 10개 동시 명령
- 캐싱: 메트릭 캐시 (5초)

### 정책 엔진
- 정책 평가: < 1ms
- 정책 생성: 10-50ms
- 메모리: < 100MB (1000개 정책)

---

## 📝 라이선스 및 지원

**작성자**: Kim
**버전**: 2.0
**최종 수정**: 2026-02-20
**상태**: 프로덕션 레디 ✅

---

🤖 **MindLang은 계속 진화합니다.**
