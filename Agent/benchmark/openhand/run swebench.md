## 使用openhand/benchmark 完成SWE-bench 测评流程分析

SWE-bench 测评分为两个独立阶段：**Inference（推理）** 和 **Evaluate（评估）**。

---

### 1. Inference 阶段

**入口命令：**
```bash
swebench-infer --llm-config-path <config.json> [其他参数]
```

**核心流程：**

```
run_infer.py
    │
    ├── SWEBenchEvaluation.prepare_instances()
    │       └── get_dataset() → 从 HuggingFace 加载数据集 (SWE-bench_Verified)
    │
    ├── SWEBenchEvaluation.prepare_workspace(instance)
    │       ├── get_official_docker_image() → 获取实例对应的 Docker 镜像
    │       ├── ensure_local_image() → 确保本地有 agent server 镜像
    │       └── DockerWorkspace / APIRemoteWorkspace → 创建工作空间
    │
    └── SWEBenchEvaluation.evaluate_instance(instance, workspace)
            ├── Agent (openhands.sdk.Agent 或 ACPAgent) 初始化
            ├── Conversation → 建立 agent 与 workspace 的对话
            ├── workspace.execute_command("cp -r /testbed/. {repo_path}") → 复制代码库
            ├── git reset --hard → 重置到初始状态
            ├── get_instruction() → 用 Jinja2 渲染 prompt
            ├── conversation.send_message(instruction) → 发送任务指令
            ├── run_conversation_with_fake_user_response() → 运行 agent 对话
            ├── git add -A && git commit → 提交修改
            └── git diff {base_commit} HEAD → 生成 patch
```

**输出：** `output.jsonl`（每行一个 `EvalOutput`，包含 `instance_id`, `test_result.git_patch`, `history` 等）

**关键参数：**
- `--llm-config-path` - LLM 配置文件
- `--dataset` - 数据集名称（默认 `princeton-nlp/SWE-bench_Verified`）
- `--split` - 分割（默认 `test`）
- `--n-limit` - 限制实例数量
- `--num-workers` - 并发数（默认 30）
- `--workspace docker|remote` - 工作空间类型

---

### 2. Evaluate 阶段

**入口命令：**
```bash
swebench-eval <output.jsonl> --run-id <run_id> [其他参数]
```

**核心流程：**

```
eval_infer.py
    │
    ├── convert_to_swebench_format(input_file, output_file)
    │       ├── 读取 output.jsonl（OpenHands 格式）
    │       ├── 提取 test_result.git_patch
    │       ├── remove_files_from_patch() → 移除无关文件
    │       └── 转换为 SWE-Bench 格式：{instance_id, model_patch, model_name_or_path}
    │
    └── run_swebench_evaluation(predictions_file, run_id, ...)
            └── subprocess.run([
                "python", "-m", "swebench.harness.run_evaluation",
                "--dataset_name", dataset,
                "--predictions_path", predictions_file,
                "--max_workers", workers,
                "--run_id", run_id,
                "--split", split,
                "--timeout", timeout,
            ])
                    └── 内部调用 swebench 库的评估逻辑，对每个实例：
                            1. 克隆对应仓库
                            2. 应用 model_patch
                            3. 运行测试用例
                            4. 判断 PASS/FAIL
```

**输出：** `<model_name>.<run_id>.report.json`（包含每个实例的评测结果）

---

### 3. 完整示例

```bash
# 1. 安装依赖
make build

# 2. 运行 Inference（推理阶段）
swebench-infer \
    --llm-config-path .llm_config/my_config.json \
    --dataset princeton-nlp/SWE-bench_Lite \
    --split test \
    --n-limit 10 \
    --num-workers 4 \
    --output-dir ./outputs

# 3. 运行 Evaluate（评估阶段）
swebench-eval ./outputs/output.jsonl \
    --run-id my_eval_001 \
    --dataset princeton-nlp/SWE-bench_Lite
```

---

### 关键文件

| 文件                                  | 作用                                      |
| ------------------------------------- | ----------------------------------------- |
| `benchmarks/swebench/run_infer.py`    | 推理入口，SWEBenchEvaluation 类           |
| `benchmarks/swebench/eval_infer.py`   | 评估入口，格式转换 + 调用 swebench 库     |
| `benchmarks/utils/evaluation.py`      | 评估编排器基类（asyncio 并发处理）        |
| `benchmarks/swebench/build_images.py` | Docker 镜像构建工具                       |
| `benchmarks/swebench/config.py`       | 默认配置（INFER_DEFAULTS, EVAL_DEFAULTS） |

---

### 4. 镜像准备

SWE-bench 需要大量 Docker 镜像，在运行 inference 前通常需要先构建：

```bash
# 构建基础镜像
python -m benchmarks.swebench.build_base_images

# 构建完整评估镜像
python -m benchmarks.swebench.build_images --dataset <dataset>
```