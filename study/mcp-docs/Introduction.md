- https://modelcontextprotocol.io/introduction

# Introduction

- MCP: 애플리케이션이 LLM에게 context를 제공하는 방식을 표준화한 프로토콜
  - ex) USB-C port for AI applications

## Why MCP?
- LLM에 data, tools 통합해야 할 때가 많음
- MCP가 제공하는 것들
  - LLM에 바로 연결 가능한 pre-built integration 제공
  - LLM provider, vendor 간 유연한 전환 지원
  - 인프라 내 데이터 보안 best practice 제공

### General architecture
- client-server architecture
  - host application이 여러 개의 server에 연결 가능
 
<img width="690" alt="image" src="https://github.com/user-attachments/assets/7d693d20-d7e4-4151-b96c-b5e171b4e70b" />

- 구성 요소
  - MCP Hosts: MCP를 통해 데이터에 접근하고자 하는 프로그램들
  - MCP Clients: 서버와 1:1 커넥션을 맺는 프로토콜 클라이언트
  - MCP Servers: MCP를 통해 각각 특정 기능을 제공하는 프로그램들
  - Local Data Sources: MCP 서버가 접근할 수 있는 로컬 데이터들
  - Remote Services: API 등을 통해 MCP 서버가 접근할 수 있는 외부 시스템
