# OpenHand 项目解读

## Workspace 概念解析

### Workspace 是什么

Workspace 是 **代码执行环境**的抽象，代表 Agent 操作代码的地方。

```
┌─────────────────────────────────────────────────────────────┐
│                        Conversation                         │
│  - 管理对话状态和事件循环                                       │
│  - send_message() → Agent.step() → LLM 调用                  │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│     Agent       │ ◄──────────►   │     LLM         │
│  - Agent 逻辑    │   调用 LLM     │   - 模型调用      │
│  - step()       │                │  - API 请求      │
└─────────────────┘                └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Workspace     │
│  - 代码执行环境   │
│  - 文件操作      │
│  - 命令执行      │
└─────────────────┘
```

### Workspace 的类型

| 类型                 | 说明                      | 使用场景              |
| -------------------- | ------------------------- | --------------------- |
| `LocalWorkspace`     | 本地文件系统              | 开发、调试            |
| `RemoteWorkspace`    | 连接到远程 Agent Server   | 生产、Docker 隔离环境 |
| `DockerWorkspace`    | 在 Docker 容器中运行      | SWE-bench 评测        |
| `APIRemoteWorkspace` | 通过 API 连接云端 runtime | 云端评测              |

### 与 Agent / ACPAgent / LLM 的关系

**1. Agent + LLM + LocalWorkspace**
```
Agent.step()
    ↓
LLM.completion(messages)  ← 调用远程 API
    ↓
Agent 执行 tools（通过 Workspace 操作文件/命令）
```

**2. Agent + LLM + RemoteWorkspace (agent-server)**
```
Local SDK                          Remote Agent Server
┌─────────────────┐               ┌─────────────────┐
│ Agent           │ ──HTTP API──► │ LLM (本地/远程)  │
│ RemoteWorkspace │               │   Tools 执行     │
└─────────────────┘               │    代码环境      │
                                  └─────────────────┘
```

**3. ACPAgent + RemoteWorkspace**
```
ACPAgent 不直接调用 LLM
    ↓
通过 ACP 协议启动子进程（Claude Code 等）
    ↓
子进程自己管理 LLM 调用
    ↓
通过 RemoteWorkspace 操作远程代码
```

### 关键区别

|           | Agent                | ACPAgent                  |
| --------- | -------------------- | ------------------------- |
| LLM 调用  | SDK 直接调用         | 委托给 ACP 服务器         |
| LLM 配置  | `agent.llm` 需要配置 | ACP 服务器自己管理        |
| Tools     | SDK 内置 tools       | ACP 服务器自己管理        |
| Workspace | 与 SDK 共享          | 通过 RemoteWorkspace 访问 |

