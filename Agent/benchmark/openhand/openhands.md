# openhand/benchmark  0基础测评指南

**前言：openhand agent环境非常恶心，不推荐自行搭建，推荐直接使用mini-swe-agent**

# 1 openhand benchmark环境准备

**1.1~1.3推荐在host执行**

# 1.1 x86仿真 + docker buildx环境

swe 运行依赖x86环境，所以需要安装x86仿真。 而openhand 构建workspace(agent运行环境)需要依赖buildx 跨平台的能力。

* x86仿真环境安装



* buildx 安装

先查询docker 版本，我这里使用的是20.10.8版本，对应安装buildx 0.9.1版本；对应关系直接问大模型即可。

buildx release包从官方链接获取：[Releases · docker/buildx](https://github.com/docker/buildx/releases?page=10)

```sh
# 假设在arm64上安装 0.9.1  这里根据自己情况进行调整
wget https://github.com/docker/buildx/releases/download/v0.9.1/buildx-v0.9.1.linux-arm64
mv buildx-v0.9.1.linux-arm64 docker-buildx 
mkdir -p ~/.docker/cli-plugins
mv docker-buildx ~/.docker/cli-plugins/
```

## 1.2 代码准备 

```sh
git clone https://github.com/OpenHands/benchmarks.git
cd benchmark
git submodule update --init --recursive  # 获取openhand-sdk-agent代码
```

## 1.3 创建容器启动脚本

贴一个创建容器的脚本，按需挂载NPU和目录，注意：**必须挂载宿主机docker**

```shell
#!/bin/bash
if [ $# -ne 2 ]; then
    echo "Usage: $0 <image-id> <container-name>"
    exit 1
fi

IMAGE_ID=$1
CONTAINER_NAME=$2

# 运行容器
docker run -it -d --net=host --shm-size=500g \
    --privileged \
    --name $CONTAINER_NAME \
    --device /dev/davinci0 \
    --device /dev/davinci1 \
    --device /dev/davinci2 \
    --device /dev/davinci3 \
    --device /dev/davinci4 \
    --device /dev/davinci5 \
    --device /dev/davinci6 \
    --device /dev/davinci7 \
    --device /dev/davinci8 \
    --device /dev/davinci9 \
    --device /dev/davinci10 \
    --device /dev/davinci11 \
    --device /dev/davinci12 \
    --device /dev/davinci13 \
    --device /dev/davinci14 \
    --device /dev/davinci15 \
    --device /dev/davinci_manager \
    --device /dev/devmm_svm \
    --device /dev/hisi_hdc \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/bin/docker:/usr/bin/docker \
    -v /root/.docker/cli-plugins:/root/.docker/cli-plugins \
    -v /usr/local/dcmi:/usr/local/dcmi \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
    -v /etc/ascend_install.info:/etc/ascend_install.info \
    -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
    -v /home/:/home/ \
    -v /data:/data \
    $IMAGE_ID bash
```

脚本使用示例：

`bash start_container.sh {镜像ID} {容器名}`

## 1.4 进入容器 +安装benchmark 及uv安装及源配置 TODO

已经提供预构建好的镜像：xxxx

将1.3中脚本命名为start_container.sh 

```sh
bash start_container.sh xxxx {容器名自己起，下面使用yejj_openhand}
docker exec -it yejj_openhand bash

####################检查uv环境 （rust实现python包管理工具）####################
uv -h 
#####################如果没有该命令，按照如下步骤安装####################
# uv默认是安装在~/.local/bin/目录下  一般我们不会将这个路径配置到PATH中，因此推荐直接安装到/usr/local/bin下
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

#####################  源配置 #################################
cat > ~/.config/uv/uv.toml << 'EOF'
[[index]]
url = "https://mirrors.aliyun.com/pypi/simple/"
default = true
EOF

################## 进入1.2中clone 的benchmark项目 ###################
make build
```

至此，基础运行环境和代码都准备完成

# 2 openhand agent准备

以下步骤均建议直接在容器内执行，构建镜像分为两步：1、构建builder 环境 openhands/eval-builder  2、构建swe eval运行环境 openhands/eval-base。

openhand会基于sdk-agent项目代码计算md5值用于计算镜像tag，如果tag已存在可以不需要

## 2.1 build image

构建agent镜像命令：

```shell
uv run python -m benchmarks.swebench.build_images --dataset princeton-nlp/SWE-bench_Lite --split test --image ghcr.io/openhands/eval-agent-server --target source-minimal --select ../instances.txt
```

推荐先创建一个用例进行流程打通，打通后进行完整测试。通过select参数传入一个文件，openhand/benchmark会读取该文件，加载对应的用例，instances.txt文件示例:  （一行放一个用例编号）

```txt
django__django-15819
```

如果build images时出现网络问题报错，最后日志大致停留在如下位置：

```sh
[03/31/26 20:48:50] INFO     Building builder: docker buildx build --file                        build_base_images.py:344
                             /tmp/agent-build-06603p21/unknown-0.0.0/Dockerfile --target builder                         
                             --platform linux/amd64 --tag                                                                
                             ghcr.milu.moe/openhands/eval-builder:62c2e7c --network host --load                          
                             /tmp/agent-build-06603p21/unknown-0.0.0 
```

问题出在docker buildx build使用的bridge模式，网络并不是使用host，可以修改benchmarks/swebench/build_base_images.py 

```python
    cmd = [
        "docker",
        "buildx",
        "build",
        "--file",
        str(dockerfile),
        "--target",
        "base-image-minimal",
        "--build-arg",
        f"BASE_IMAGE={base_image}",
        "--platform",
        platform,
        "--network",  # 添加这两行
        "host",       # 添加这两行
    ]  
```

同理，构建使用的dockerfile中可以配置一下uv源，为了更快的镜像构建，路径位于benchmarks/vendor/software-agent-sdk/openhands-agent-server/openhands/agent_server/docker/Dockerfile      贴一个修改后的dockerfile：

```dockerfile
# syntax=docker/dockerfile:1.7

# NOTE: LC_ALL/LANG must be set to C.UTF-8 for libtmux to work correctly with
# PyInstaller builds. Without proper locale, tmux converts UTF-8 separator
# characters to underscores, breaking libtmux's format parsing.
ARG BASE_IMAGE=nikolaik/python-nodejs:python3.13-nodejs22
ARG USERNAME=openhands
ARG UID=10001
ARG GID=10001
ARG PORT=8000

####################################################################################
# Builder (source mode)
# We copy source + build a venv here for local dev and debugging.
####################################################################################
FROM python:3.13-bookworm AS builder
ARG USERNAME UID GID
ENV UV_PROJECT_ENVIRONMENT=/agent-server/.venv
ENV UV_PYTHON_INSTALL_DIR=/agent-server/uv-managed-python

#############添加下面三行
ENV UV_HTTP_TIMEOUT=60
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV UV_DOWNLOAD_CONCURRENCY=5
############

COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

RUN groupadd -g ${GID} ${USERNAME} \
 && useradd -m -u ${UID} -g ${GID} -s /usr/sbin/nologin ${USERNAME}
USER ${USERNAME}
WORKDIR /agent-server
# Cache-friendly: lockfiles first
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml uv.lock README.md LICENSE ./
COPY --chown=${USERNAME}:${USERNAME} openhands-sdk ./openhands-sdk
COPY --chown=${USERNAME}:${USERNAME} openhands-tools ./openhands-tools
COPY --chown=${USERNAME}:${USERNAME} openhands-workspace ./openhands-workspace
COPY --chown=${USERNAME}:${USERNAME} openhands-agent-server ./openhands-agent-server
ARG INSTALL_BOTO3=true
RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv python install 3.13 && uv venv --python 3.13 .venv && uv sync --frozen --no-editable --managed-python $([ "$INSTALL_BOTO3" = "true" ] && echo "--extra boto3")

####################################################################################
# Binary Builder (binary mode)
# We run pyinstaller here to produce openhands-agent-server
####################################################################################
FROM builder AS binary-builder
ARG USERNAME UID GID

ARG INSTALL_BOTO3=true
# We need --dev for pyinstaller
RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv sync --frozen --dev --no-editable $([ "$INSTALL_BOTO3" = "true" ] && echo "--extra boto3")

RUN --mount=type=cache,target=/home/${USERNAME}/.cache,uid=${UID},gid=${GID} \
    uv run pyinstaller openhands-agent-server/openhands/agent_server/agent-server.spec
# Fail fast if the expected binary is missing
RUN test -x /agent-server/dist/openhands-agent-server

####################################################################################
# Base image (minimal)
# It includes only basic packages and the UV runtime.
# No Docker, no VNC, no Desktop, no VSCode Web.
# Suitable for running in headless/evaluation mode.
####################################################################################
FROM ${BASE_IMAGE} AS base-image-minimal
ARG USERNAME UID GID PORT

# Install base packages and create user
RUN set -eux; \
    # Install base packages (works for both Debian-based images)
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates curl wget sudo apt-utils git jq tmux build-essential \
        coreutils util-linux procps findutils grep sed \
        # Docker dependencies
        apt-transport-https gnupg lsb-release; \
    \
    # Create user and group
    (getent group ${GID} || groupadd -g ${GID} ${USERNAME}); \
    (id -u ${USERNAME} >/dev/null 2>&1 || useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME}); \
    # Add user to sudo group
    usermod -aG sudo ${USERNAME}; \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers; \
    # Create workspace directory
    mkdir -p /workspace/project; \
    chown -R ${USERNAME}:${USERNAME} /workspace; \
    rm -rf /var/lib/apt/lists/*

# Pre-install ACP servers for ACPAgent support (Claude Code + Codex)
# Install Node.js/npm if not present (SWE-bench base images may lack them)
# Set INSTALL_ACP=false to skip ACP installation (e.g. for benchmark images)
ARG INSTALL_ACP=true
RUN set -eux; \
    if ! command -v npm >/dev/null 2>&1; then \
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
        apt-get install -y --no-install-recommends nodejs && \
        rm -rf /var/lib/apt/lists/*; \
    fi; \
    if [ "$INSTALL_ACP" = "true" ]; then \
        npm install -g @zed-industries/claude-agent-acp @zed-industries/codex-acp; \
    fi

# Configure Claude Code managed settings for headless operation:
# Allow all tool permissions (no human in the loop to approve).
RUN mkdir -p /etc/claude-code && \
    echo '{"permissions":{"allow":["Edit","Read","Bash"]}}' > /etc/claude-code/managed-settings.json

# NOTE: we should NOT include UV_PROJECT_ENVIRONMENT here,
# since the agent might use it to perform other work (e.g. tools that use Python)
COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/

# SDK version metadata — placed AFTER expensive RUN layers (apt-get, npm)
# so that changing the SDK commit does not invalidate their cache.
# This lets BuildKit reuse cached base layers across SDK commits.
ARG OPENHANDS_BUILD_GIT_SHA=unknown
ARG OPENHANDS_BUILD_GIT_REF=unknown
ENV OPENHANDS_BUILD_GIT_SHA=${OPENHANDS_BUILD_GIT_SHA}
ENV OPENHANDS_BUILD_GIT_REF=${OPENHANDS_BUILD_GIT_REF}

USER ${USERNAME}
WORKDIR /
# Locale settings required for libtmux to work with PyInstaller builds
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV OH_ENABLE_VNC=false
ENV LOG_JSON=true
EXPOSE ${PORT}

####################################################################################
# Base image (full)
# It includes additional Docker, VNC, Desktop, and VSCode Web.
####################################################################################
FROM base-image-minimal AS base-image
ARG USERNAME

USER root
# --- VSCode Web ---
ENV EDITOR=code \
    VISUAL=code \
    GIT_EDITOR="code --wait" \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server
ARG RELEASE_TAG="openvscode-server-v1.98.2"
ARG RELEASE_ORG="gitpod-io"
RUN set -eux; \
    # Create necessary directories
    mkdir -p $(dirname ${OPENVSCODE_SERVER_ROOT}); \
    \
    # Determine architecture
    arch=$(uname -m); \
    if [ "${arch}" = "x86_64" ]; then \
        arch="x64"; \
    elif [ "${arch}" = "aarch64" ]; then \
        arch="arm64"; \
    elif [ "${arch}" = "armv7l" ]; then \
        arch="armhf"; \
    fi; \
    \
    # Download and install VSCode Server
    wget https://github.com/${RELEASE_ORG}/openvscode-server/releases/download/${RELEASE_TAG}/${RELEASE_TAG}-linux-${arch}.tar.gz; \
    tar -xzf ${RELEASE_TAG}-linux-${arch}.tar.gz; \
    if [ -d "${OPENVSCODE_SERVER_ROOT}" ]; then rm -rf "${OPENVSCODE_SERVER_ROOT}"; fi; \
    mv ${RELEASE_TAG}-linux-${arch} ${OPENVSCODE_SERVER_ROOT}; \
    cp ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/openvscode-server ${OPENVSCODE_SERVER_ROOT}/bin/remote-cli/code; \
    rm -f ${RELEASE_TAG}-linux-${arch}.tar.gz; \
    \
    # Set proper ownership
    chown -R ${USERNAME}:${USERNAME} ${OPENVSCODE_SERVER_ROOT}


# Include VSCode extensions alongside the server so targets inheriting base-image
# implicitly get the extensions; minimal images (without VSCode) won't.
COPY --chown=${USERNAME}:${USERNAME} --from=builder /agent-server/openhands-agent-server/openhands/agent_server/vscode_extensions ${OPENVSCODE_SERVER_ROOT}/extensions

# --- Docker ---
RUN set -eux; \
    # Determine OS type and install Docker accordingly
    if grep -q "ubuntu" /etc/os-release; then \
        # Handle Ubuntu
        install -m 0755 -d /etc/apt/keyrings; \
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc; \
        chmod a+r /etc/apt/keyrings/docker.asc; \
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null; \
    else \
        # Handle Debian
        install -m 0755 -d /etc/apt/keyrings; \
        curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc; \
        chmod a+r /etc/apt/keyrings/docker.asc; \
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null; \
    fi; \
    # Install Docker Engine, containerd, and Docker Compose
    apt-get update; \
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Configure Docker daemon with MTU 1450 to prevent packet fragmentation issues
RUN mkdir -p /etc/docker && \
    echo '{"mtu": 1450}' > /etc/docker/daemon.json

# --- GitHub CLI ---
RUN set -eux; \
    mkdir -p -m 755 /etc/apt/keyrings; \
    wget -nv -O /etc/apt/keyrings/githubcli-archive-keyring.gpg \
        https://cli.github.com/packages/githubcli-archive-keyring.gpg; \
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list; \
    apt-get update; \
    apt-get install -y gh; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# --- VNC + Desktop + noVNC ---
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    # GUI bits (remove entirely if headless)
    tigervnc-standalone-server xfce4 dbus-x11 novnc websockify \
    # Browser
    $(if grep -q "ubuntu" /etc/os-release; then echo "chromium-browser"; else echo "chromium"; fi); \
  apt-get clean; rm -rf /var/lib/apt/lists/*

ENV NOVNC_WEB=/usr/share/novnc \
    NOVNC_PORT=8002 \
    DISPLAY=:1 \
    VNC_GEOMETRY=1280x800 \
    CHROME_BIN=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"

RUN chown -R ${USERNAME}:${USERNAME} ${NOVNC_WEB}
# Override default XFCE wallpaper
COPY --chown=${USERNAME}:${USERNAME} openhands-agent-server/openhands/agent_server/docker/wallpaper.svg /usr/share/backgrounds/xfce/xfce-shapes.svg

USER ${USERNAME}
WORKDIR /
ENV OH_ENABLE_VNC=false
ENV LOG_JSON=true
EXPOSE ${PORT} ${NOVNC_PORT}


####################################################################################
####################################################################################
# Build Targets
####################################################################################
####################################################################################

############################
# Target A: source
# Local dev and debugging mode: copy source + venv from builder
############################
FROM base-image AS source
ARG USERNAME
ENV UV_PYTHON_INSTALL_DIR=/agent-server/uv-managed-python
COPY --chown=${USERNAME}:${USERNAME} --from=builder /agent-server /agent-server
ENTRYPOINT ["/agent-server/.venv/bin/python", "-m", "openhands.agent_server"]

FROM base-image-minimal AS source-minimal
ARG USERNAME
ENV UV_PYTHON_INSTALL_DIR=/agent-server/uv-managed-python
COPY --chown=${USERNAME}:${USERNAME} --from=builder /agent-server /agent-server
ENTRYPOINT ["/agent-server/.venv/bin/python", "-m", "openhands.agent_server"]

############################
# Target B: binary-runtime
# Production mode: build the binary inside Docker and copy it in.
# NOTE: no support for external artifact contexts anymore.
############################
FROM base-image AS binary
ARG USERNAME

COPY --chown=${USERNAME}:${USERNAME} --from=binary-builder /agent-server/dist/openhands-agent-server /usr/local/bin/openhands-agent-server
RUN chmod +x /usr/local/bin/openhands-agent-server
# Fix library path to use system GCC libraries instead of bundled ones
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENTRYPOINT ["/usr/local/bin/openhands-agent-server"]

FROM base-image-minimal AS binary-minimal
ARG USERNAME
COPY --chown=${USERNAME}:${USERNAME} --from=binary-builder /agent-server/dist/openhands-agent-server /usr/local/bin/openhands-agent-server
RUN chmod +x /usr/local/bin/openhands-agent-server
# Fix library path to use system GCC libraries instead of bundled ones
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:/usr/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
ENTRYPOINT ["/usr/local/bin/openhands-agent-server"]

```

正确运行后，如果出现了如下两个done日志，说明镜像构建成功：

```shell
Building:   0%| | 0/1 [00:00<?, ?it/s, 🛠 0  ⏭ 0  ❌ 0  🏃 1 (docker.io/swebench/sweb.eval.x86_64.django_1776_dja[03/31/26 21:18:39] INFO     Logging build output to                                          build_utils.py:289
                             /home/yejiajun/project/openhand_test/benchmarks/builds/princeton                   
                             -nlp/SWE-bench_Lite/test/base-logs/docker.io/swebench/sweb.eval.                   
                             x86_64.django_1776_django-15819:latest/build-2026-03-31T13-18-39                   
                             Z.log                                                                              
✅ Done: 100%|█████████████████████████████████████████████| 1/1 [16:15<00:00, 975.95s/it, 🛠 1  ⏭ 0  ❌ 0  🏃 0]
[03/31/26 21:34:55] INFO     Base images done. Built=1  Failed=0                        build_base_images.py:277
                             Manifest=/home/yejiajun/project/openhand_test/benchmarks/b                         
                             uilds/princeton-nlp/SWE-bench_Lite/test/base-manifest.json                         
                             l                                                                                  
[03/31/26 21:34:55] INFO     SDK submodule info: ref=unknown, sha=62c2e7c, version=1.14.0     build_utils.py:217
Queueing:   0%|                                                     | 0/1 [00:00<?, ?it/s, 🛠 0  ⏭ 0  ❌ 0  🏃 0]/root/.local/share/uv/python/cpython-3.12.13-linux-aarch64-gnu/lib/python3.12/multiprocessing/popen_fork.py:66: DeprecationWarning: This process (pid=86702) is multi-threaded, use of fork() may lead to deadlocks in the child.
  self.pid = os.fork()
Assembling:   0%| | 0/1 [00:00<?, ?it/s, 🛠 0  ⏭ 0  ❌ 0  🏃 1 (docker.io/swebench/sweb.eval.x86_64.django_1776_d[03/31/26 21:34:58] INFO     Logging build output to                                          build_utils.py:289
                             /home/yejiajun/project/openhand_test/benchmarks/builds/princeton                   
                             -nlp/SWE-bench_Lite/test/assembly-logs/docker.io/swebench/sweb.e                   
                             val.x86_64.django_1776_django-15819:latest/build-2026-03-31T13-3                   
                             4-58Z.log                                                                          
✅ Done: 100%|██████████████████████████████████████████████| 1/1 [00:27<00:00, 27.17s/it, 🛠 1  ⏭ 0  ❌ 0  🏃 0]
[03/31/26 21:35:22] INFO     Assembly done. Built=1  Skipped=0  Failed=0                build_base_images.py:677
                             Manifest=/home/yejiajun/project/openhand_test/benchmarks/b                         
                             uilds/princeton-nlp/SWE-bench_Lite/test/manifest.jsonl                             
/home/yejiajun/project/openhand_test/benchmarks/.venv/lib/python3.12/site-packages/litellm/llms/custom_httpx/async_client_cleanup.py:66: DeprecationWarning: There is no current event loop
```

## 1.3 运行 swebench-infer

需要首先准备一个llm 配置json:

```json
{
    // 格式按照：API规范/模型名称
    "model": "openai/qwen3",
    // ip必须使用具体IP，不能使用localhost、127.0.0.1, port根据自己情况进行调整
    "base_url": "http://192.168.13.157:6767/v1",  
    // 本地部署模型不需要api key, 随便给一个值即可
    "api_key": "dummy"
}
```

注意，tool-call parser 需要根据具体模型配置正确，对于qwen3-Coder-30B   配置为`qwen3_coder`,如果不知道应该配置什么，以vllm为例，打开代码: `vllm/vllm/tool_parsers/__init__.py`，找到最贴近自己模型的配置进行使用，多试几次即可。

跑之前还需要**修改代码：benchmarks/vendor/software-agent-sdk/openhands-workspace/openhands/workspace/docker/workspace.py    _wait_for_health函数的默认timeout**

默认120s在 A3上测试发现无法正确拉起workspace，这里可以设置的大一些，我配置的300s

然后执行评估命令：

```shell
uv run swebench-infer ../llm_config.json --select ../instances.txt --workspace docker --dataset princeton-nlp/SWE-bench_Lite --max-retries 1 --num-workers 1
# 根据具体情况配置 最大重试次数、并发数
```

运行结束后，会在当前目录生成一个eval_outputs文件夹，放置具体的推理数据，目录结构大致如下：

```shell
|-- conversations
|   `-- django__django-15819.tar.gz
|-- logs
|   |-- instance_django__django-15819.log
|   `-- instance_django__django-15819.output.log
|-- metadata.json
|-- output.critic_attempt_1.jsonl
`-- output.jsonl
```

## 1.4 运行swebench-eval

run-id标记每次运行的标记，一定需要提供，评估支持有模型和无模型参与两种，根据具体情况选择

```sh
uv run swebench-eval {输入1.3中 output.jsonl所在路径} --dataset princeton-nlp/SWE-bench_Lite --run-id eval1 --no-modal
```

评估过程会每条测试任务拉起专门的容器进行，使用前确保已下载swebench官方提供评估镜像

```shell
CONTAINER ID   IMAGE   COMMAND   CREATED    STATUS     PORTS     NAMES
72eb39a3d18b   swebench/sweb.eval.x86_64.django_1776_django-15819:latest   "tail -f /dev/null"      41 seconds ago   Up 40 seconds             sweb.eval.django__django-15819.eval1
```

运行会输出以下相关的内容，展示了多少用例通过、失败和报错
```shell
Running 1 instances...
Evaluation:   0%|                                                             | 0/1 [05:39<?, ?it/s, ✓=0, ✖=1, erroEvaluation: 100%|████████████████████████████████████████████████████| 1/1 [05:39<00:00, 339.98s/it, ✓=0, ✖=1, error=0]All instances run.
Evaluation: 100%|████████████████████████████████████████████████████| 1/1 [05:39<00:00, 339.98s/it, ✓=0, ✖=1, error=0]
Cleaning cached images...
```



# 常见问题记录

## 1 swebench-infer 陷入死循环

模型推理报错：

```shell
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323] Error in preprocessing prompt inputs
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323] Traceback (most recent call last):
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/vllm-workspace/vllm/vllm/entrypoints/openai/chat_completion/serving.py", line 301, in render_chat_request
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     conversation, engine_prompts = await self._preprocess_chat(
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/vllm-workspace/vllm/vllm/entrypoints/openai/engine/serving.py", line 1207, in _preprocess_chat
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     conversation, engine_prompt = await renderer.render_messages_async(
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/vllm-workspace/vllm/vllm/renderers/hf.py", line 607, in render_messages_async
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     conversation, mm_data, mm_uuids = await parse_chat_messages_async(
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/vllm-workspace/vllm/vllm/entrypoints/chat_utils.py", line 1635, in parse_chat_messages_async
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     _postprocess_messages(conversation)
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/vllm-workspace/vllm/vllm/entrypoints/chat_utils.py", line 1571, in _postprocess_messages
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     item["function"]["arguments"] = json.loads(content)
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]                                     ^^^^^^^^^^^^^^^^^^^
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/usr/local/python3.11.14/lib/python3.11/json/__init__.py", line 346, in loads
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     return _default_decoder.decode(s)
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]            ^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]   File "/usr/local/python3.11.14/lib/python3.11/json/decoder.py", line 340, in decode
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323]     raise JSONDecodeError("Extra data", s, end)
(APIServer pid=181814) ERROR 03-31 08:04:12 [serving.py:323] json.decoder.JSONDecodeError: Extra data: line 1 column 580 (char 579)
(APIServer pid=181814) INFO:     172.17.0.2:52418 - "POST /v1/chat/completions HTTP/1.1" 400 Bad Request
```

是agent的func call结果无法被模型解析，如果不清楚应该配置什么，可以参考定义逐个进行尝试：

`vllm/vllm/tool_parsers/__init__.py`
