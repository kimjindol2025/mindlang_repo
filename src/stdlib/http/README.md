# MindLang http 모듈

HTTP 요청/응답 처리를 위한 경량 클라이언트 라이브러리

## 📦 구성 요소

### 1. HttpRequest - HTTP 요청 객체

```typescript
import { HttpRequest } from '@mindlang/http';

const request = new HttpRequest('https://api.example.com/users');
request
  .setMethod('POST')
  .setJsonBody({ name: 'Alice', email: 'alice@example.com' })
  .setHeader('X-API-Key', 'secret123')
  .setTimeout(10000);
```

**주요 메서드:**
- `setMethod(method)` - HTTP 메서드 설정 (GET, POST, PUT, DELETE, PATCH, etc.)
- `setUrl(url)` - URL 설정
- `setHeader(name, value)` - 헤더 설정
- `setHeaders(headers)` - 여러 헤더 한 번에 설정
- `setBody(body)` - 요청 바디 설정
- `setJsonBody(data)` - JSON 바디 설정
- `setFormBody(data)` - Form 바디 설정
- `addQueryParams(params)` - 쿼리 파라미터 추가
- `setAuth(username, password)` - 기본 인증 설정
- `setBearerToken(token)` - Bearer 토큰 설정
- `setContentType(type)` - Content-Type 설정
- `setUserAgent(agent)` - User-Agent 설정
- `setTimeout(ms)` - 타임아웃 설정
- `setFollowRedirects(follow, maxRedirects)` - 리다이렉트 설정

### 2. HttpResponse - HTTP 응답 객체

```typescript
const response = await client.get('https://api.example.com/users/1');

console.log(response.getStatus());      // 200
console.log(response.isSuccess());      // true
console.log(response.getJson());        // { id: 1, name: 'Alice' }
console.log(response.getHeader('content-type'));  // 'application/json'
```

**상태 확인:**
- `isSuccess()` - 2xx 상태 확인
- `isRedirect()` - 3xx 상태 확인
- `isClientError()` - 4xx 상태 확인
- `isServerError()` - 5xx 상태 확인

**응답 조회:**
- `getStatus()` - 상태 코드
- `getStatusText()` - 상태 텍스트
- `getText()` - 응답 바디 (문자열)
- `getBuffer()` - 응답 바디 (Buffer)
- `getJson()` - 응답 바디 (JSON 파싱)
- `getHeader(name)` - 특정 헤더
- `getHeaders()` - 모든 헤더
- `getContentType()` - Content-Type
- `getContentLength()` - Content-Length
- `getCookies()` - 쿠키 파싱
- `getETag()` - ETag
- `getLastModified()` - Last-Modified
- `getCacheControl()` - Cache-Control
- `getLocation()` - 리다이렉트 주소

### 3. HttpClient - HTTP 클라이언트

```typescript
import { HttpClient } from '@mindlang/http';

const client = new HttpClient();
client.setDefaultHeader('X-API-Key', 'secret123');
client.setDefaultTimeout(10000);
```

**HTTP 메서드:**
```typescript
// GET
const response = await client.get('https://api.example.com/users');

// POST
const response = await client.post('https://api.example.com/users', {
  name: 'Alice',
  email: 'alice@example.com'
});

// PUT
const response = await client.put('https://api.example.com/users/1', {
  name: 'Alice Updated'
});

// DELETE
const response = await client.delete('https://api.example.com/users/1');

// PATCH
const response = await client.patch('https://api.example.com/users/1', {
  name: 'Alice'
});

// HEAD
const response = await client.head('https://api.example.com/users');

// OPTIONS
const response = await client.options('https://api.example.com/users');
```

**커스텀 요청:**
```typescript
const request = new HttpRequest('https://api.example.com/data')
  .setMethod('POST')
  .setJsonBody({ key: 'value' })
  .setAuth('username', 'password');

const response = await client.send(request);
```

**일괄 처리:**
```typescript
const requests = [
  new HttpRequest('https://api.example.com/users'),
  new HttpRequest('https://api.example.com/posts'),
  new HttpRequest('https://api.example.com/comments'),
];

const responses = await client.sendAll(requests);
```

## 📝 사용 예제

### 사용자 목록 조회

```typescript
const client = new HttpClient();

async function getUsers() {
  const response = await client.get('https://api.example.com/users?page=1&limit=10');

  if (response.isSuccess()) {
    const users = response.getJson();
    console.log(users);
  } else {
    console.error(`Error: ${response.getStatus()}`);
  }
}
```

### 사용자 생성

```typescript
async function createUser() {
  const client = new HttpClient();

  const response = await client.post('https://api.example.com/users', {
    name: 'Bob',
    email: 'bob@example.com',
    age: 30
  });

  if (response.getStatus() === 201) {
    const newUser = response.getJson();
    console.log('User created:', newUser);
  }
}
```

### API 키 인증

```typescript
const client = new HttpClient();
client.setDefaultHeader('X-API-Key', 'your-api-key');

const response = await client.get('https://api.example.com/protected');
```

### Bearer 토큰 인증

```typescript
const request = new HttpRequest('https://api.example.com/data');
request.setBearerToken('your-jwt-token');

const response = await client.send(request);
```

### 파일 업로드 (폼 데이터)

```typescript
const response = await client.post('https://api.example.com/upload', {
  filename: 'document.pdf',
  size: '2048'
});
```

### 리다이렉트 처리

```typescript
const request = new HttpRequest('https://api.example.com/redirect');
request.setFollowRedirects(true, 5);  // 최대 5번 리다이렉트

const response = await client.send(request);
console.log(response.getUrl());  // 최종 URL
```

### 쿠키 처리

```typescript
const response = await client.get('https://api.example.com/login');
const cookies = response.getCookies();

cookies.forEach(cookie => {
  console.log(`${cookie.name}=${cookie.value}`);
  console.log(`Path: ${cookie.path}, HttpOnly: ${cookie.httpOnly}`);
});
```

## 🧪 테스트 결과

```
Test Suites: 1 passed, 1 total
Tests:       41 passed, 41 total

HttpRequest:       15 테스트 ✓
HttpResponse:      10 테스트 ✓
HttpClient:        16 테스트 ✓
```

## 📊 코드 통계

| 항목 | 코드줄 | 테스트줄 | 테스트개 |
|------|--------|---------|---------|
| Request | 200 | 180 | 15 |
| Response | 250 | 150 | 10 |
| Client | 180 | 280 | 16 |
| Types | 70 | - | - |
| **합계** | **700** | **610** | **41** |

## 🚀 특징

- ✅ 경량 (모든 함수 구현, 외부 의존성 없음)
- ✅ Promise 기반 (async/await 지원)
- ✅ 자동 리다이렉트 처리
- ✅ 타입 안전 (TypeScript)
- ✅ 스트리밍 지원
- ✅ 쿠키 파싱
- ✅ 캐시 헤더 처리
- ✅ ETag 지원

## 🔜 다음 단계

- WebSocket 지원
- 타임아웃 재시도
- 프록시 지원
- HTTPS 인증서 검증

## 📝 라이센스

MIT
