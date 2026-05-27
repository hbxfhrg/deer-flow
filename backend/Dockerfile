# ================================================
# DeerFlow 后端 Dockerfile（生产环境）
# ================================================

# 第一阶段：构建依赖
FROM python:3.12-slim AS builder

WORKDIR /app

# 清理所有默认源配置，确保只使用国内源
RUN rm -rf /etc/apt/sources.list.d/* /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian/ trixie main contrib non-free" > /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian/ trixie-backports main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main contrib non-free" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 更换 pip 国内源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制所有必要文件
COPY pyproject.toml .
COPY packages/harness/pyproject.toml packages/harness/
COPY packages/harness/deerflow packages/harness/deerflow/

# 安装所有依赖（包括 harness 包）
RUN pip install --upgrade pip \
    && pip install --timeout=120 --retries=3 packages/harness asyncmy \
    && pip install --timeout=120 --retries=3 .

# 第二阶段：运行环境
FROM python:3.12-slim

WORKDIR /app

# 清理所有默认源配置
RUN rm -rf /etc/apt/sources.list.d/* /etc/apt/sources.list
RUN echo "deb http://mirrors.aliyun.com/debian/ trixie main contrib non-free" > /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian/ trixie-backports main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main contrib non-free" >> /etc/apt/sources.list

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 更换 pip 国内源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 gunicorn 和 uvicorn
RUN pip install gunicorn uvicorn

# 从构建阶段复制安装好的依赖
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制完整的应用代码（包括 packages/harness/deerflow）
COPY . .

# 复制配置文件（从项目根目录复制到backend目录，确保能被找到）
COPY config.yaml ./config.yaml

# 创建日志目录
RUN mkdir -p logs

# 设置 PYTHONPATH，确保 deerflow 模块可以被找到
ENV PYTHONPATH=/app:/app/packages/harness

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.gateway:app", "--bind", "0.0.0.0:8001"]
