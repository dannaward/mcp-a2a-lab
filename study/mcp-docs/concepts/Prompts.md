- https://modelcontextprotocol.io/docs/concepts/prompts

# Prompts
- Prompt란?
  - 서버가 정의하는 재사용 가능한 프롬프트 템플릿과 워크플로우
- user-controlled
  - 모델이 알아서 프롬프트를 고르는 게 아니라 사용자 주도 하에 명시적으로 선택됨

## Overview
- MCP 프롬프트가 할 수 있는 것들
  - 동적 인자 구성
  - 리소스 포함
  - 여러 단계의 LLM 체인을 순차적으로 구성
  - 특정 워크플로우 유도
  - UI 상에서 명령형 요소로 사용 (ex: slash commands)

## Prompt structure
```
{
  name: string;              // Unique identifier for the prompt
  description?: string;      // Human-readable description
  arguments?: [              // Optional list of arguments
    {
      name: string;          // Argument identifier
      description?: string;  // Argument description
      required?: boolean;    // Whether argument is required
    }
  ]
}
```

## Discovering prompts
- 클라이언트는 사용 가능한 프롬프트를 `prompts/list`를 통해 조회 가능
``` javascript
// Request
{
  method: "prompts/list"
}

// Response
{
  prompts: [
    {
      name: "analyze-code",
      description: "Analyze code for potential improvements",
      arguments: [
        {
          name: "language",
          description: "Programming language",
          required: true
        }
      ]
    }
  ]
}
```

## Using prompts
- `prompts/get`을 통해 사용할 수 있음
```js
// Request
{
  method: "prompts/get",
  params: {
    name: "analyze-code",
    arguments: {
      language: "python"
    }
  }
}

// Response
{
  description: "Analyze Python code for potential improvements",
  messages: [
    {
      role: "user",
      content: {
        type: "text",
        text: "Please analyze the following Python code for potential improvements:\n\n```python\ndef calculate_sum(numbers):\n    total = 0\n    for num in numbers:\n        total = total + num\n    return total\n\nresult = calculate_sum([1, 2, 3, 4, 5])\nprint(result)\n```"
      }
    }
  ]
}
```

## Dynamic prompts
### Embedded resources context
``` json
{
  "name": "analyze-project",
  "description": "Analyze project logs and code",
  "arguments": [
    {
      "name": "timeframe",
      "description": "Time period to analyze logs",
      "required": true
    },
    {
      "name": "fileUri",
      "description": "URI of code file to review",
      "required": true
    }
  ]
}
```

- `prompts/get`
``` json
{
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Analyze these system logs and the code file for any issues:"
      }
    },
    {
      "role": "user",
      "content": {
        "type": "resource",
        "resource": {
          "uri": "logs://recent?timeframe=1h",
          "text": "[2024-03-14 15:32:11] ERROR: Connection timeout in network.py:127\n[2024-03-14 15:32:15] WARN: Retrying connection (attempt 2/3)\n[2024-03-14 15:32:20] ERROR: Max retries exceeded",
          "mimeType": "text/plain"
        }
      }
    },
    {
      "role": "user",
      "content": {
        "type": "resource",
        "resource": {
          "uri": "file:///path/to/code.py",
          "text": "def connect_to_service(timeout=30):\n    retries = 3\n    for attempt in range(retries):\n        try:\n            return establish_connection(timeout)\n        except TimeoutError:\n            if attempt == retries - 1:\n                raise\n            time.sleep(5)\n\ndef establish_connection(timeout):\n    # Connection implementation\n    pass",
          "mimeType": "text/x-python"
        }
      }
    }
  ]
}
```

## Multi-step workflows
``` json
const debugWorkflow = {
  name: "debug-error",
  async getMessages(error: string) {
    return [
      {
        role: "user",
        content: {
          type: "text",
          text: `Here's an error I'm seeing: ${error}`
        }
      },
      {
        role: "assistant",
        content: {
          type: "text",
          text: "I'll help analyze this error. What have you tried so far?"
        }
      },
      {
        role: "user",
        content: {
          type: "text",
          text: "I've tried restarting the service, but the error persists."
        }
      }
    ];
  }
};
```

## Example implementation
```json
import { Server } from "@modelcontextprotocol/sdk/server";
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema
} from "@modelcontextprotocol/sdk/types";

const PROMPTS = {
  "git-commit": {
    name: "git-commit",
    description: "Generate a Git commit message",
    arguments: [
      {
        name: "changes",
        description: "Git diff or description of changes",
        required: true
      }
    ]
  },
  "explain-code": {
    name: "explain-code",
    description: "Explain how code works",
    arguments: [
      {
        name: "code",
        description: "Code to explain",
        required: true
      },
      {
        name: "language",
        description: "Programming language",
        required: false
      }
    ]
  }
};

const server = new Server({
  name: "example-prompts-server",
  version: "1.0.0"
}, {
  capabilities: {
    prompts: {}
  }
});

// List available prompts
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: Object.values(PROMPTS)
  };
});

// Get specific prompt
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const prompt = PROMPTS[request.params.name];
  if (!prompt) {
    throw new Error(`Prompt not found: ${request.params.name}`);
  }

  if (request.params.name === "git-commit") {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Generate a concise but descriptive commit message for these changes:\n\n${request.params.arguments?.changes}`
          }
        }
      ]
    };
  }

  if (request.params.name === "explain-code") {
    const language = request.params.arguments?.language || "Unknown";
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Explain how this ${language} code works:\n\n${request.params.arguments?.code}`
          }
        }
      ]
    };
  }

  throw new Error("Prompt implementation not found");
});
```

## Best Practices
- 프롬프트 이름은 명확하고 설명적이게 작성
  - 예: summarize-meeting-notes, translate-to-french
-	프롬프트 및 인자의 설명(description)을 충분히 제공
  - 사용자 및 LLM이 의도를 잘 이해할 수 있도록
- 필수 인자는 모두 검증
  - 누락된 경우 유효한 기본값 안내 또는 에러 반환
- 인자가 빠졌을 경우 우아하게 처리
  - 사용자에게 힌트를 주거나 기본값 유도
- 프롬프트 템플릿 버전 관리 고려
  - 구조나 의미가 바뀔 경우 v1, v2 등 구분
- 동적 콘텐츠 캐싱 고려
  - 자주 사용하는 리소스 기반 프롬프트의 성능 개선
- 에러 처리 로직 구현
  - 프롬프트 실행 실패 시 명확한 에러 메시지 제공
- 인자 포맷 명시
  - 문자열, 숫자, 날짜 등 기대하는 형식 문서화
- 프롬프트 조합 가능성 고려 (composability)
  - 여러 프롬프트를 이어 붙일 수 있도록 설계
- 다양한 입력에 대해 프롬프트 테스트 수행
  -	엣지 케이스 및 오류 유도 입력 포함

## UI integration
- slash commands
- quick actions
- context menu items
- command palette entries
- guided workflows
- interactive forms

## Update and changes
- 서버는 프롬프트 변경 시 클라이언트에게 알릴 수 있음
  -	서버 기능: `prompts.listChanged`
	-	알림 메시지: `notifications/prompts/list_changed`
	-	클라이언트는 이 알림을 수신하고 프롬프트 목록을 재요청 `prompts.list`

## Security considerations
- 모든 인자 검증
  - 타입, 포맷, 허용된 값 등 체크
- 사용자 입력 정제 (sanitize)
  - XSS, 명령어 삽입 등 방어
- 요청에 대해 레이트 리밋 고려
  - 남용/오용 방지
- 접근 제어 적용
  - 권한에 따라 특정 프롬프트 제한
- 프롬프트 사용 로깅 및 감사 추적
  - 민감한 프롬프트 호출 이력 기록
- 민감한 데이터는 적절히 처리
  - 노출 방지, 암호화, 저장 제한 등
- LLM이 생성한 콘텐츠도 검증 필요
  - 부적절한 응답이나 악성 출력 차단
- 프롬프트 실행에 타임아웃 설정
  - 무한 대기, 지연 응답 방지
- 프롬프트 인젝션(Prompt Injection) 리스크 고려
  - 사용자 입력이 시스템 프롬프트를 교란하지 않도록 설계
- 보안 요구사항 문서화
  - 인증, 권한, 입력 정책 등 명시
