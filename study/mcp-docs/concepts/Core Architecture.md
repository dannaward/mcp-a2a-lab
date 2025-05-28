- https://modelcontextprotocol.io/docs/concepts/architecture

# Core Architecture
## Overview
- MCP는 client-server 아키텍처
- Host: LLM 애플리케이션
- Client: 서버와 1:1 관계 맺음. Host application 안에 있음
- Server: client에 context, tool, prompt 제공

<img width="580" alt="image" src="https://github.com/user-attachments/assets/5efeade0-bdbb-4f46-83fd-b01c91cf0891" />

## Core Components
### Protocol layer
- Protocol layer handles:
  - message framing
  - request/response linking
  - high-level communication patterns
 
```typescript
class Protocol<Request, Notification, Result> {
    // Handle incoming requests
    setRequestHandler<T>(schema: T, handler: (request: T, extra: RequestHandlerExtra) => Promise<Result>): void

    // Handle incoming notifications
    setNotificationHandler<T>(schema: T, handler: (notification: T) => Promise<void>): void

    // Send requests and await responses
    request<T>(request: Request, schema: T, options?: RequestOptions): Promise<T>

    // Send one-way notifications
    notification(notification: Notification): Promise<void>
}
```

### Transport layer
- Transport layer는 client-server 간 실제 통신 handle
- 여러 가지 통신 방식 지원
  - Stdio transport
    - 표준 입출력 사용
    - 로컬 처리에 사용
    <img width="395" alt="image" src="https://github.com/user-attachments/assets/aaea89aa-b9cb-41ec-bb59-fe880d0f56d9" />
  - HTTP with SSE transport
    - Server-Sent Event를 활용해 서버에서 클라이언트로 단방향 메시지를 보냄
    - HTTP POST요청으로 클라이언트에서 서버로 메시지 보냄

### Message types
- Request
- Result
- Error
- Notification: response를 받지 않는 단방향 request

## Connection lifecycle
### 1. Initialization
<img width="413" alt="image" src="https://github.com/user-attachments/assets/5ba1a2d8-836f-471f-ad4b-a5a0ced8cd38" />

- 클라이언트가 initialize request를 보낸다
  - protocol version, capabilities 포함해야 함
    - capabilities? : 클라이언트가 어떤 기능을 지원하는지 서버에 알리는 역할
    - 예시 (LSP(Language Server Protocol))
      
    ```json
    {
      "method": "initialize",
      "params": {
        "protocolVersion": "1.0",
        "capabilities": {
          "supportsStreaming": true,
          "supportsIncrementalUpdates": false,
          "customFeatureX": true
        }
      }
    }
    ```
- 서버 응답
- 클라이언트가 initialized notification을 보낸다 (ack)
- 이제 양방향 메시지 전송 시작됨

### 2. Message exchange
- 초기화가 끝나면 지원되는 패턴들
  - Request-Response: 클라이언트나 서버가 request를 보내면 다른 한쪽이 응답
  - Notifications: 클라이언트나 서버가 단방향으로 메시지를 보냄
 
### 3. Termination
- 서버나 클라이언트가 연결을 끊을 수 있음
  - clean shutdown `close()` -> 정상 종료
  - transport disconnection -> 비정상 종료 - 전송 계층 (네트워크 장애 등)
  - error conditions -> 비정상 종료 - 프로토콜 내부
 
# Error Handling
- MCP는 JSON-RPC 표준 에러코드를 따름
  - https://www.jsonrpc.org/specification#error_object
- SDK나 애플리케이션은 각자 에러코드를 정의해 사용할 수 있음 (에러코드 -32000 이상이어야 함)
- 에러가 전달되는 과정
  - request를 보냈을 때 응답이 정상 데이터가 아닌 에러응답으로 돌아오는 경우
  - 전송 계층에서 이벤트 기반 오류가 발생하는 경우
    - disconnect
    - socket error
    - unexpected EOF
    - ...
  - 프로토콜 자체가 정의한 에러 처리 메커니즘을 통해 전파되는 경우
    - 메시지 형식 잘못됨
    - 순서가 어긋남 (initialize 전에 message 전송)
    - 허용되지 않은 메서드 호출
    - ...

# Implementation Example
- MCP 서버 만드는 예제
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: {
    resources: {}
  }
});

// Handle requests
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "example://resource",
        name: "Example Resource"
      }
    ]
  };
});

// Connect transport
const transport = new StdioServerTransport();
await server.connect(transport);
```

# Best Practices
## Transport selection
### 1. Local communication
- 로컬 통신에는 stdio stansport 사용
- 매우 빠르고 오버헤드 없음
- 복잡한 네트워크 설정 불필요
- 프로세스 실행/종료가 단순함

### 2. Remote communication
- HTTP 기반 시스템과의 호환이 필요한 경우엔 SSE (Server-Sent Events) 사용 권장
- 인증(auth) 과 권한 확인(authorization) 을 고려해야 함

## Message Handling
### Request processing
- 요청을 처리할 때 반드시 신경써야 할 것들
  - 입력값을 철저히 검증해라
  - 타입 안전한 스키마를 사용해라
  - 에러를 잘 처리해라
  - 타임아웃을 설정해라
 
### Progress reporting
- 오래 걸리는 작업을 처리할 때 클라이언트에 어디까지 처리가 되었는지 추적 수 있게 progress token을 제공해라
- 중간중간 현재 진행 상황을 전송해라
- 총 작업량을 파악 가능하다면 함께 포함해라 (예: 4/10)
- ex) `{ "type": "progress", "token": "abc123", "current": 3, "total": 10 }`
  - 이 값을 가지고 클라이언트가 Progress bar를 그릴 수 있도록

### Error Management
- 상황에 맞는 명확한 에러 코드 사용
- 사람이 이해할 수 있는 메시지 포함
- 에러 발생 시 자원 정리 (메모리, 파일, 세션 등)

## Security Considerations
### Transport security
- 원격 통신 시 HTTPS (TLS) 사용으로 데이터 암호화
- Web 환경이라면 CORS 또는 origin header 검사 필요
- 필요하다면 인증 (토큰, API 키, OAuth 등) 적용

### Message validation
- 인입되는 모든 메시지 검증 (메시지 구조/타입/필드 유효성 검사)
- 사용자 입력 정제 (XSS/SQL Injection 방지를 위해)
- 메시지 크기 한도 검사 (과도한 메시지로 인한 자원 고갈 방지)
- JSON-RPC 포맷 검증 (jsonrpc, method, params 등의 필드 구조 검증)

### Resource protection
- 사용자 권한/역할 기반의 접근 제어
- 자원 경로 관리 (파일 경로 등을 클라이언트가 직접 지정할 경우 경로 조작 방지 (../ 등))
- 자원 사용량 모니터링 (CPU, 메모리, 파일 핸들 등 사용량 모니터링)
- 요청 Rate limit 설정 (너무 잦은 요청을 막아 서비스 남용/DoS 방지)

### Error handling
- 에러 메시지에 민감 정보 포함 금지
- 보안 관련 에러 로깅 (인증 실패, 접근 거부 등은 보안 로그로 별도 저장)
- 정리 똑바로 (에러 발생 시 열린 핸들, 임시 파일, 세션 등 정리)
- Dos 시나리오 대비 (과도한 요청, 무한 루프 유도 등의 시나리오에 대한 방어)

## Debugging and Monitoring
### Logging
- 연결, 요청, 응답, 종료 등 프로토콜 수준의 주요 이벤트 기록
- 메시지 ID 기반으로 요청-응답 흐름을 추적 가능하게 로그 남김
- 요청 처리 시간, 대기 시간 등의 성능 지표도 모니터링
- 예외, 실패 응답, 타임아웃 등 모든 에러 상황은 상세히 기록
- 예시
```
[INFO] Received initialize request: id=1
[DEBUG] Handling method 'getStatus' for id=2
[ERROR] Invalid params in request id=3: missing 'target'
[INFO] Response time for id=2: 45ms
```

### Diagnostics
- 서버 상태를 확인할 수 있는 health check 구현
- 연결 수, 지속 시간, 연결 끊김 발생 횟수 등 추적
- 메모리, CPU, 파일 핸들 등 서버 자원 사용량 모니터링
- 느린 요청, 병목 지점, GC 등 성능 병목 분석 수행

### Testing
- stdio, SSE 등 다양한 전송 방식으로 테스트
- 잘못된 요청, timeout, malformed JSON 등 다양한 실패 케이스 검증
- 경계값, 빈 배열, null 등 비정상 상황에서의 안정성 확인
- 다수의 요청을 동시에 보내 성능 한계 및 병목 파악 (e.g. wrk, k6, locust)

---
느낀점:
- 뭔가 주니어 개발자를 위한 견고한 시스템 설계하기 101을 보는 것 같다. ㅋㅋㅋ
- MCP 철학이 담겨있을 줄 알았는데 예상외로 그냥 어디에도 적용될 수 있는 소프트웨어 기본 원칙 같은 느낌
  - 최근에 zookeeper 문서를 읽었을 때는 문서 전체에 철학이 잘 드러나있어서 좋았는데
