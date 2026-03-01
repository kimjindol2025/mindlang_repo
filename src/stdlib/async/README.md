# MindLang async 모듈

비동기 작업을 위한 Promise/A+ 호환 구현 및 동시성 제어 도구

## 📦 구성 요소

### 1. MindPromise - Promise/A+ 호환 구현 (45개 테스트)

```typescript
// 기본 사용
const p = new MindPromise((resolve, reject) => {
  resolve(42);
});

p.then(value => console.log(value))
  .catch(error => console.error(error))
  .finally(() => console.log('완료'));
```

**주요 메서드:**
- `then(onFulfilled?, onRejected?)` - 콜백 등록
- `catch(onRejected)` - 에러 처리
- `finally(onFinally)` - 항상 실행
- `Promise.resolve(value)` - resolved Promise 생성
- `Promise.reject(reason)` - rejected Promise 생성
- `Promise.all(promises)` - 모든 Promise 완료 대기
- `Promise.race(promises)` - 첫 번째 완료 Promise 반환
- `Promise.allSettled(promises)` - 모든 Promise 결과 반환
- `Promise.any(promises)` - 첫 번째 성공 Promise 반환

**테스트 커버리지:**
- resolve/reject: 6개
- then/catch/finally: 13개
- 정적 메서드: 26개

### 2. Queue - 순차 실행 큐 (19개 테스트)

```typescript
const queue = new Queue();

queue.enqueue(async () => {
  console.log('작업 1');
  return 'result1';
});

queue.enqueue(async () => {
  console.log('작업 2');
  return 'result2';
});

const results = await queue.waitAll();
```

**주요 메서드:**
- `enqueue(task)` - 작업 추가
- `process()` - 큐 처리 시작
- `waitAll()` - 모든 작업 완료 대기
- `size()` - 큐 크기
- `isEmpty()` - 비어있는지 확인
- `isRunning()` - 실행 중인지 확인
- `cancel()` - 대기 중인 작업 취소
- `clear()` - 큐 초기화
- `getResults()` - 결과 조회

**특징:**
- FIFO 순서 보장
- 한 번에 하나씩만 실행
- 에러 발생해도 계속 진행

### 3. Semaphore - 동시성 제어 (15개 테스트)

```typescript
const semaphore = new Semaphore(2); // 최대 2개 동시 실행

// 방법 1: acquire/release
await semaphore.acquire();
try {
  // 작업 수행
} finally {
  semaphore.release();
}

// 방법 2: run 메서드
await semaphore.run(async () => {
  // 작업 수행
});
```

**주요 메서드:**
- `acquire()` - Permit 획득
- `release()` - Permit 반환
- `run(fn)` - 함수 실행 (자동 permit 관리)
- `availablePermits()` - 사용 가능 Permit
- `waitingCount()` - 대기 중인 작업
- `setPermits(count)` - Permit 재설정
- `drainPermits()` - 모든 Permit 회수

**활용:**
- API 요청 동시성 제어
- 리소스 풀 관리
- 연결 풀 제어

### 4. Utils - 유틸리티 함수 (20개 테스트)

#### sleep - 대기
```typescript
await sleep(1000); // 1초 대기
```

#### timeout - 타임아웃 추가
```typescript
try {
  const result = await timeout(promise, 5000);
} catch (e) {
  console.log('5초 초과');
}
```

#### retry - 재시도
```typescript
const result = await retry(
  async () => fetchData(),
  3,      // 최대 3회 시도
  1000,   // 1초 대기
  true    // 지수 백오프 활성화
);
```

#### debounce - 디바운스
```typescript
const debouncedSearch = debounce((query) => {
  console.log('검색:', query);
}, 500);

// 빠른 호출도 500ms 후 한 번만 실행
input.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});
```

#### throttle - 스로틀
```typescript
const throttledResize = throttle(() => {
  console.log('리사이즈');
}, 300);

window.addEventListener('resize', throttledResize);
```

#### retry와 조건부 재시도
```typescript
// 특정 에러만 재시도
await retryIf(
  async () => fetchData(),
  (error) => error.code === 'NETWORK_ERROR',
  3,
  1000
);
```

#### 작업 실행 방식
```typescript
// 순차 실행
const results = await sequential([
  async () => task1(),
  async () => task2(),
  async () => task3(),
]);

// 병렬 실행
const results = await parallel([
  async () => task1(),
  async () => task2(),
  async () => task3(),
]);

// 반복 실행
const results = await repeat(
  async () => Math.random(),
  100,  // 100ms 간격
  5     // 5회
);
```

## 🧪 테스트 결과

```
Test Suites: 4 passed, 4 total
Tests:       99 passed, 99 total

Promise:    45 테스트 ✓
Queue:      19 테스트 ✓
Semaphore:  15 테스트 ✓
Utils:      20 테스트 ✓
```

## 📊 코드 통계

| 컴포넌트 | 코드줄 | 테스트줄 | 테스트개 |
|---------|--------|---------|---------|
| Promise | 330 | 507 | 45 |
| Queue | 100 | 240 | 19 |
| Semaphore | 100 | 165 | 15 |
| Utils | 200 | 310 | 20 |
| **합계** | **730** | **1,222** | **99** |

## 🚀 다음 단계

- Day 3-5: http 모듈 포팅 (50개 테스트)
- Week 2: json, fs, process, db, redis 모듈 포팅
- Month 2: FFI 통합 및 성능 최적화

## 📝 라이센스

MIT
