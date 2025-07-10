https://a2aproject.github.io/A2A/v0.2.5/topics/what-is-a2a/

- 질문: 다양한 사람에 의해 만들어진, 다양한 기능을 하는 AI 에이전트끼리 어떻게 하면 효과적으로 소통할 수 있을까?

## The A2A Solution
- A common transport and format: JSON-RPC 2.0, HTTP(S)
- Discovery mechanisms (Agent Cards): 다른 에이전트가 이 에이전트를 발견할 수 있도록
- Task management workflows: 태스크 동작 방식 관리. e.g. long-running tasks, tasks require multiple turns of interaction
- Support for various data modalities: 텍스트뿐만 아니라 파일, 폼, 리치 미디어 지원
- Core principles for security and asynchronicity: secure communication, 시간이 많이 걸리는 작업, 사람의 개입이 필요한 작업에 대한 가이드라인 제공

## Key Design Principles of A2A
- Simplicity: 새로 다 만드는 대신 이미 잘 만들어져 있는 거 활용
- Enterprise Readiness: 엔터프라이즈에 필요한 기능들 지원 e.g. authentication, authorization, security, tracing, monitoring
- Asynchronous First: 긴 작업이나 유저가 계속 보고 있지 않을 것 같은 경우들을 네이티브 단에서 핸들링 (stream, push 사용)
- Modality Agnostic: 텍스트뿐만 아니라 다양한 타입의 content를 지원
- Opaque Execution: 구체적인 구현은 은닉.

## Benefits of Using A2A
- Increased Interoperability: AI 에이전트 간 사일로 해결. 협력할 수 있도록 함
- Enhanced Agent Capabilities: 개발자가 여러 에이전트를 활용해서 더 복잡한 서비스를 쉽게 만들 수 있도록 함
- Reduced Integration Complexity: AI 에이전트가 '어떻게' 소통하는지를 생각하지 않고 '뭘' 하게 할지를 더 고민할 수 있게 함
- Fostering Innovation: 생태계 활성화
- Future-Proofing: 에이전트 기술이 발전해도 유연한 프레임워크 제공
