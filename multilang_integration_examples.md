# 🌐 MindLang 다중 언어 통합 실예

**목표**: MindLang을 다양한 언어에서 사용하는 실제 예제

---

## 📌 기본 MindLang 프로그램

```mindlang
program sentiment_analysis {
  query "이 제품 정말 좋아요!" -> q
  encode q -> z
  fork z -> {z_a, z_b, z_c}

  path_a = analytical_reasoning(z_a)
  path_b = creative_reasoning(z_b)
  path_c = empirical_reasoning(z_c)

  ensemble [0.5, 0.25, 0.25] [path_a, path_b, path_c] -> result

  return result
}
```

---

## 1️⃣ **TypeScript/JavaScript** (네이티브 ⭐⭐⭐⭐⭐)

### TypeScript 예제
```typescript
import { MindLangInterpreter } from 'mindlang/src/main';
import * as fs from 'fs';

// MindLang 프로그램 로드
const mindlangCode = fs.readFileSync('sentiment.ml', 'utf-8');

// 인터프리터 생성 및 실행
const interpreter = new MindLangInterpreter(mindlangCode);
const context = interpreter.execute();

// 결과 처리
console.log('Vector:', context.variables.get('result'));
console.log('Confidence:', context.metadata.confidence);

// 또는 async 방식
async function analyzeAsync(text: string) {
  const agent = new MindLangAgent();
  const result = await agent.think(text);
  return result;
}
```

### JavaScript 예제
```javascript
const MindLang = require('mindlang');

// 간단한 사용법
const code = `
  program quick_analysis {
    query "test input" -> q
    encode q -> z
    return z
  }
`;

const interpreter = new MindLang.Interpreter(code);
const result = interpreter.run();
console.log(result);
```

**성능**: 최고 (네이티브) | **복잡도**: 낮음

---

## 2️⃣ **Python** (REST API ⭐⭐⭐)

### Python REST 클라이언트 예제

```python
import requests
import json
import numpy as np

class MindLangClient:
    def __init__(self, endpoint='http://localhost:3000'):
        self.endpoint = endpoint

    def execute(self, ml_code: str):
        """MindLang 코드 실행"""
        response = requests.post(
            f'{self.endpoint}/execute',
            json={'code': ml_code},
            headers={'Content-Type': 'application/json'}
        )
        return response.json()

    def batch_execute(self, queries: list):
        """배치 실행"""
        results = []
        for query in queries:
            result = self.execute(f'program batch {{ query "{query}" -> q }}')
            results.append(result['vector'])
        return results

# 사용 예제
client = MindLangClient()

# 단일 실행
ml_code = '''
program sentiment {
  query "이 제품 좋아요" -> q
  encode q -> z
  fork z -> {z_a, z_b, z_c}
  return z_a
}
'''

result = client.execute(ml_code)
vector = np.array(result['vector'])

# NumPy 통합
print(f"Vector shape: {vector.shape}")  # (256,)
print(f"Mean: {np.mean(vector):.4f}")
print(f"Std: {np.std(vector):.4f}")

# PyTorch 통합
import torch
torch_tensor = torch.from_numpy(vector)
print(f"PyTorch tensor: {torch_tensor.shape}")

# TensorFlow 통합
import tensorflow as tf
tf_tensor = tf.convert_to_tensor(vector)
print(f"TensorFlow tensor: {tf_tensor.shape}")
```

**성능**: 중간 (REST 오버헤드) | **복잡도**: 중간

---

## 3️⃣ **Go** (gRPC ⭐⭐⭐⭐)

### Go gRPC 클라이언트 예제

```go
package main

import (
    "context"
    "log"
    pb "mindlang/grpc"
    "google.golang.org/grpc"
)

func main() {
    // gRPC 연결
    conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
    if err != nil {
        log.Fatal(err)
    }
    defer conn.Close()

    client := pb.NewMindLangServiceClient(conn)

    // MindLang 코드 실행
    req := &pb.ExecuteRequest{
        Program: "sentiment_analysis",
        Code: `
            program sentiment {
                query "I love this product!" -> q
                encode q -> z
                fork z -> {z_a, z_b, z_c}
                return z_a
            }
        `,
    }

    // 동기 실행
    resp, err := client.Execute(context.Background(), req)
    if err != nil {
        log.Fatal(err)
    }

    log.Printf("Result: %v", resp.Vector)
    log.Printf("Confidence: %f", resp.Confidence)

    // 또는 스트림 방식
    streamResp, err := client.ExecuteStream(context.Background(), req)
    for {
        result, err := streamResp.Recv()
        if err != nil {
            break
        }
        log.Printf("Batch result: %v", result)
    }
}

// 마이크로서비스 통합
func ProcessQueryWithMindLang(query string) ([]float64, error) {
    conn, _ := grpc.Dial("mindlang-service:50051", grpc.WithInsecure())
    defer conn.Close()

    client := pb.NewMindLangServiceClient(conn)
    resp, _ := client.Execute(context.Background(), &pb.ExecuteRequest{
        Program: "quick_analysis",
        Code:    fmt.Sprintf(`query "%s" -> q`, query),
    })

    return resp.Vector, nil
}
```

**성능**: 높음 (gRPC) | **복잡도**: 중간

---

## 4️⃣ **Rust** (WASM ⭐⭐⭐⭐⭐)

### Rust WASM 예제

```rust
use wasm_bindgen::prelude::*;
use web_sys::console;

#[wasm_bindgen]
pub fn execute_mindlang_program(code: &str) -> js_sys::Array {
    // MindLang 컴파일러 호출
    let result = compile_and_run(code);

    // 벡터를 JavaScript 배열로 변환
    let arr = js_sys::Array::new();
    for (i, val) in result.iter().enumerate() {
        arr.set(i as u32, JsValue::from_f64(*val));
    }
    arr
}

#[wasm_bindgen]
pub fn batch_process(queries: js_sys::Array) -> js_sys::Array {
    let results = js_sys::Array::new();

    for i in 0..queries.length() {
        let query = queries.get(i);
        if let Some(q) = query.as_string() {
            let code = format!(r#"
                program batch {{
                    query "{}" -> q
                    encode q -> z
                    return z
                }}
            "#, q);

            let result = execute_mindlang_program(&code);
            results.push(&result);
        }
    }

    results
}

// 고성능 벡터 연산 (ndarray)
use ndarray::Array1;

#[wasm_bindgen]
pub fn fast_encode(text: &str) -> js_sys::Array {
    // ndarray로 고속 처리
    let mut vector = Array1::zeros(768);

    for (i, ch) in text.chars().enumerate() {
        vector[i % 768] += (ch as u32 as f64) / 256.0;
    }

    // JavaScript 배열로 변환
    let arr = js_sys::Array::new();
    for (i, val) in vector.iter().enumerate() {
        arr.set(i as u32, JsValue::from_f64(*val));
    }
    arr
}
```

### Rust 호출 (JavaScript에서)

```javascript
import * as wasm from "mindlang_wasm";

// WASM 함수 직접 호출
const result = wasm.execute_mindlang_program(`
    program analysis {
        query "test" -> q
        encode q -> z
        return z
    }
`);

console.log("Result vector:", result);

// 배치 처리
const queries = ["첫 번째", "두 번째", "세 번째"];
const batchResults = wasm.batch_process(queries);

// 고속 인코딩
const encoded = wasm.fast_encode("빠른 인코딩");
```

**성능**: 최고 (WASM) | **복잡도**: 높음

---

## 5️⃣ **Java** (REST API ⭐⭐)

### Java REST 클라이언트 예제

```java
import okhttp3.*;
import com.google.gson.*;
import java.util.ArrayList;

public class MindLangClient {
    private String endpoint;
    private OkHttpClient client;

    public MindLangClient(String endpoint) {
        this.endpoint = endpoint;
        this.client = new OkHttpClient();
    }

    public JsonObject execute(String mlCode) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("code", mlCode);

        Request request = new Request.Builder()
            .url(endpoint + "/execute")
            .post(RequestBody.create(body.toString(), MediaType.get("application/json")))
            .build();

        Response response = client.newCall(request).execute();
        String responseBody = response.body().string();

        return JsonParser.parseString(responseBody).getAsJsonObject();
    }

    public ArrayList<double[]> batchExecute(ArrayList<String> queries) {
        ArrayList<double[]> results = new ArrayList<>();

        for (String query : queries) {
            String code = String.format(
                "program batch { query \"%s\" -> q encode q -> z return z }",
                query
            );

            try {
                JsonObject result = execute(code);
                JsonArray vector = result.getAsJsonArray("vector");

                double[] arr = new double[vector.size()];
                for (int i = 0; i < vector.size(); i++) {
                    arr[i] = vector.get(i).getAsDouble();
                }
                results.add(arr);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        return results;
    }
}

// 사용 예제
public class Main {
    public static void main(String[] args) throws Exception {
        MindLangClient client = new MindLangClient("http://localhost:3000");

        String mlCode = "program sentiment { query \"좋아요\" -> q encode q -> z return z }";
        JsonObject result = client.execute(mlCode);

        System.out.println("Result: " + result);
    }
}
```

**성능**: 중간 (REST) | **복잡도**: 중간

---

## 6️⃣ **C++** (Native Binding ⭐⭐)

### C++ Node.js Native Addon 예제

```cpp
#include <node.h>
#include <v8.h>

namespace mindlang {

using v8::FunctionCallbackInfo;
using v8::Isolate;
using v8::Local;
using v8::Object;
using v8::String;
using v8::Value;
using v8::Array;

void ExecuteMindLang(const FunctionCallbackInfo<Value>& args) {
    Isolate* isolate = args.GetIsolate();

    // JavaScript 문자열 받기
    v8::String::Utf8Value code(isolate, args[0]);

    // MindLang 실행
    std::vector<double> result = run_mindlang(*code);

    // 결과를 JavaScript 배열로 변환
    Local<Array> array = Array::New(isolate, result.size());
    for (size_t i = 0; i < result.size(); ++i) {
        array->Set(isolate->GetCurrentContext(), i,
                   v8::Number::New(isolate, result[i]));
    }

    args.GetReturnValue().Set(array);
}

void Initialize(Local<Object> exports) {
    NODE_SET_METHOD(exports, "execute", ExecuteMindLang);
}

NODE_MODULE(mindlang, Initialize)

}
```

**성능**: 최고 (Native) | **복잡도**: 매우 높음

---

## 7️⃣ **C#** (gRPC ⭐⭐)

### C# .NET 클라이언트 예제

```csharp
using Grpc.Net.Client;
using MindLang;

class MindLangClient {
    public async Task ExecuteAsync(string code) {
        var channel = GrpcChannel.ForAddress("http://localhost:50051");
        var client = new MindLangService.MindLangServiceClient(channel);

        var request = new ExecuteRequest {
            Program = "sentiment_analysis",
            Code = code
        };

        var reply = await client.ExecuteAsync(request);

        Console.WriteLine($"Vector: {string.Join(", ", reply.Vector)}");
        Console.WriteLine($"Confidence: {reply.Confidence}");
    }

    public async Task BatchProcessAsync(List<string> queries) {
        using (var channel = GrpcChannel.ForAddress("http://localhost:50051"))
        {
            var client = new MindLangService.MindLangServiceClient(channel);

            var streamingCall = client.ExecuteStream(
                new ExecuteRequest { Program = "batch" }
            );

            foreach (var query in queries) {
                await streamingCall.RequestStream.WriteAsync(
                    new ExecuteRequest { Code = query }
                );
            }

            await foreach (var response in streamingCall.ResponseStream.ReadAllAsync()) {
                Console.WriteLine($"Batch result: {response.Vector}");
            }
        }
    }
}

// 사용
var client = new MindLangClient();
await client.ExecuteAsync("program test { query \"hello\" -> q }");
```

**성능**: 중간 (gRPC) | **복잡도**: 중간

---

## 📊 통합 방식 비교표

| 언어 | 방식 | 설정 시간 | 성능 | 복잡도 | 추천 |
|------|------|----------|------|--------|------|
| **TS/JS** | Native | 5분 | ⭐⭐⭐⭐⭐ | 낮음 | ✅ 최고 |
| **Python** | REST | 10분 | ⭐⭐⭐ | 중간 | ✅ 권장 |
| **Go** | gRPC | 15분 | ⭐⭐⭐⭐ | 중간 | ✅ 권장 |
| **Rust** | WASM | 30분 | ⭐⭐⭐⭐⭐ | 높음 | ✅ 권장 |
| **Java** | REST | 10분 | ⭐⭐⭐ | 중간 | ⚠️ 기본 |
| **C++** | Native | 60분 | ⭐⭐⭐⭐⭐ | 매우 높음 | ⚠️ 선택 |
| **C#** | gRPC | 20분 | ⭐⭐⭐ | 중간 | ⚠️ 선택 |

---

## 🚀 최고의 다중 언어 스택

### 권장 조합
```
프론트엔드:     TypeScript/JavaScript
백엔드:         Go (마이크로서비스) + Python (ML)
고성능:         Rust (WASM)
엔터프라이즈:   C# / Java (REST API)
```

### 예제: 풀 스택 애플리케이션

```
┌─────────────────┐
│ Web Frontend    │
│ (TypeScript)    │ MindLang Native API
└────────┬────────┘
         │
┌────────▼────────┐
│ Node.js Server  │  MindLang Interpreter
│ (TypeScript)    │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │          │        │        │
┌───▼──┐  ┌───▼──┐ ┌──▼───┐ ┌─▼────┐
│ Go   │  │Python│ │Rust  │ │Java  │
│gRPC  │  │REST  │ │WASM  │ │REST  │
└──────┘  └──────┘ └──────┘ └──────┘
```

---

## 🎓 결론

**MindLang 호환성 현황:**

- ✅ **TypeScript/JavaScript**: 100% 네이티브 지원 (권장)
- ✅ **Python/Go/Rust**: 부분 지원 (API/gRPC/WASM)
- ⚠️ **Java/C#/C++**: 기본 지원 (REST/gRPC/Native)

**선택 기준:**
1. **성능 최고**: TypeScript, Rust (WASM)
2. **편의성 최고**: TypeScript, Python
3. **확장성 최고**: Go (마이크로서비스)
4. **엔터프라이즈**: Java, C#

