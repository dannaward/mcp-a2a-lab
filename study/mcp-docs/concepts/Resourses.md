- https://modelcontextprotocol.io/docs/concepts/resources

# Resources
- resource란?
	- MCP에서 Resources는 서버가 클라이언트에게 제공할 수 있는 데이터/콘텐츠 단위
	- 이 리소스들은 LLM(Large Language Model)의 context로 활용될 수 있는 정보
- application-controlled
  - 리소스는 기본적으로 클라이언트 애플리케이션이 어떻게, 언제 사용할지를 결정
  - 즉, LLM이 직접 리소스를 불러오는 게 아니라, 클라이언트 앱이 리소스를 선택/활성화해야 함
- 클라이언트마다 리소스 처리 방식 다를 수 있음
  - 사용자가 수동으로 리소스를 선택하든, 모델이 자동으로 선택하든, 서버는 이 모든 경우를 지원할 수 있어야 함
  - 만약 LLM이 리소스를 직접 탐색하거나 요청하게 하고 싶다면, Resources가 아니라 Tools (도구) 같은 model-controlled primitive를 사용해야 함
    -	Resources: 사용자가 지정 → 모델은 읽기만 가능
    -	Tools: 모델이 능동적으로 선택하고 실행 가능 (예: 검색 툴, 계산기)

## Overview
- Resource는 아무거나 다 될 수 있음
  - file contents
  - database records
  - api responses
  - live system data
  - screenshots and images
  - log files
  - ...

## Resource URIs
- URI: `[protocol]://[host]/[path]`
  - `file:///home/user/documents/report.pdf`
  - `postgres://database/customers/schema`
  - `screen://localhost/display1`
- protocol, path 구조는 MCP 서버에 정의되어 있음
- 서버들은 각자 맘대로 URI scheme 정의 가능

## Resource Types
### Text resources
- UTF-8 encoded data
  - 소스코드
  - 설정파일
  - 로그 파일
  - JSON/XML 데이터
  - plain text

### Binary resources
- raw binary data (base64 인코딩)
  - 이미지
  - PDF
  - 오디오 파일
  - 비디오 파일
  - 그 외 다른 텍스트가 아닌 포맷들

## Resource Discovery
### Direct resource
- `resources/list`를 통해 리소스 목록 조회
```
{
  uri: string;           // Unique identifier for the resource
  name: string;          // Human-readable name
  description?: string;  // Optional description
  mimeType?: string;     // Optional MIME type
}
```

### Resource templates
- 동적 리소스는 URI templates 활용
```
{
  uriTemplate: string;   // URI template following RFC 6570
  name: string;          // Human-readable name for this type
  description?: string;  // Optional description
  mimeType?: string;     // Optional MIME type for all matching resources
}
```

## Reading Resources
- `resources/read`
```
{
  contents: [
    {
      uri: string;        // The URI of the resource
      mimeType?: string;  // Optional MIME type

      // One of:
      text?: string;      // For text resources
      blob?: string;      // For binary resources (base64 encoded)
    }
  ]
}
```

## Resource Updates
- MCP는 실시간 리소스 업데이트 지원함

### List changes
- 변경사항이 생겼을 때 서버가 클라이언트한테 직접 알림
- `notifications/resources/list_changed`

### Content changes
- 클라이언트가 변경사항 구독할 수 있음
  - 클라이언트: `resources/subscribe`에 resource URI 담아서 보냄
  - 서버: 리소스 변경되면 `notification/resources/updated` 보냄
  - 그걸 받은 클라이언트가 최신 리소스 받아옴 `resources/read`
  - 클라이언트 구독 취소 `resources/unsubscribe`

## Example Implementation
```typescript
const server = new Server({
  name: "example-server",
  version: "1.0.0"
}, {
  capabilities: {
    resources: {}
  }
});

// List available resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "file:///logs/app.log",
        name: "Application Logs",
        mimeType: "text/plain"
      }
    ]
  };
});

// Read resource contents
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  if (uri === "file:///logs/app.log") {
    const logContents = await readLogFile();
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: logContents
        }
      ]
    };
  }

  throw new Error("Resource not found");
});
```

## Best Practices
-	리소스 이름과 URI는 명확하고 직관적으로 지정
	- 예: project:meeting-notes:2024-05-01
-	LLM이 이해할 수 있도록 리소스에 설명(description) 포함
	-	문서 요약, 용도 설명 등 텍스트 제공
- 가능한 경우 MIME 타입 명시
	-	예: application/json, text/markdown, image/png 등
-	동적 콘텐츠 제공 시 리소스 템플릿(template) 사용
	-	예: /docs/{docId} 형태
-	자주 변경되는 리소스는 subscription 기능을 통해 최신 정보 제공
	-	클라이언트가 리소스 변경을 실시간으로 받을 수 있게
- 에러 발생 시 친절하고 명확한 메시지 제공
	-	예: "message": "Invalid resource ID: not found"
-	리소스가 많을 경우 pagination 적용
	-	?page=1&limit=50 등의 파라미터로 나눠서 제공
-	변경이 적은 리소스는 캐싱 적용 고려
	-	ETag, Cache-Control, 메모리 캐시 등 활용
-	URI 처리 전 사전 검증 수행
	-	스킴, 경로, 포맷 등 유효성 체크
-	커스텀 URI 스킴을 사용하는 경우 문서화
	-	예: mcp://user-notes/1234 → 어떤 규칙으로 구성되는지 명시

## Security Considerations
- Resource URI 검증
	-	인입되는 모든 리소스 URI는 사전에 철저히 검증
	-	잘못된 스킴, 허용되지 않은 경로 (mcp://, ../ 등) 차단
- 접근 제어
	-	리소스마다 사용자 권한/역할 기반의 접근 제어(Role-Based Access Control) 적용
	-	인증되지 않은 사용자에 대한 접근 차단
- 파일 경로 정제
	-	사용자 입력으로 경로 지정 시 경로 조작 방지 (../../etc/passwd 등)
	-	정규화된 경로만 처리 허용
- 바이너리 데이터 주의
	-	바이너리 리소스 처리 시:
	-	MIME 타입 확실히 확인
	-	크기 제한 설정
	-	인코딩 방식 명확히 정의
- Rate limit 설정
	-	리소스 요청에 대해 초당 횟수 제한(Rate Limiting) 적용
	-	자원 남용, DoS 방지를 위한 임계치 설정
- 접근 감사 (Audit)
	-	누가 어떤 리소스에 접근했는지 보안 로그로 남기기
	-	보안 사고 대응 및 추적을 위한 감사 기록 확보
- 데이터 전송 암호화
	-	민감한 리소스일 경우 TLS(HTTPS) 를 통해 암호화된 전송
	-	내부 통신이라도 민감하면 암호화 고려
- MIME 타입 검증
	-	리소스의 실제 내용과 명시된 MIME 타입 일치 여부 확인
	-	클라이언트 오작동 또는 보안 문제 방지
- 타임아웃 처리
	-	리소스 읽기 시간이 길어질 경우 타임아웃 설정으로 무한 대기 방지
	-	불안정한 클라이언트 연결로 인한 자원 낭비 예방
- 리소스 정리
	-	에러 또는 세션 종료 시:
	-	열린 핸들 닫기
	-	임시 파일 삭제
	-	캐시된 데이터 정리 등 리소스 클린업 철저
