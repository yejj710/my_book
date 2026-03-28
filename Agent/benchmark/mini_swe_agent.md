## mini-SWE-agent 与 SWE-bench 的配合关系

### 本质角色

**mini-SWE-agent 是一个 Code Agent（编程代理）**，而 **SWE-bench 是评估框架**。它们是**测评流程的两个不同环节**：

```
mini-SWE-agent (解题) ──→ SWE-bench (评分)
```

### 工作流程

| 阶段        | 工具           | 职责                                          |
| ----------- | -------------- | --------------------------------------------- |
| **1. 解题** | mini-SWE-agent | 接收 GitHub issue，通过 LLM + bash 生成 patch |
| **2. 评分** | SWE-bench      | 应用 patch 到代码库，运行测试，判定是否解决   |

### 与其他模型的对比

SWE-bench 不仅可以评估 mini-SWE-agent，实际上可以评估**任何能生成 patch 的模型/agent**：

```
Claude / GPT-4 / mini-SWE-agent / 其他模型  ──→ 生成 patch
                                            ↓
                              SWE-bench 框架验证 patch 正确性
```

### 测评流程详解

1. **输入**: GitHub issue + 仓库代码
2. **生成**: Agent/LLM 生成修复 patch
3. **验证**: SWE-bench 在 Docker 容器中应用 patch，运行测试
4. **输出**: PASS/FAIL 状态

所以 **mini-SWE-agent 是参与测评的"选手"，SWE-bench 是裁判和赛场**。