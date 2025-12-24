# SafeGuard 统一 Dockerfile
# 支持多环境构建：function、uat、prod
# 使用多阶段构建 + 构建参数

# ================================
# 基础构建阶段
# ================================
FROM python:3.12-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置Python路径
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# ================================
# 依赖安装阶段
# ================================
FROM base as dependencies

# 只复制依赖文件，利用Docker缓存层
COPY requirements.txt ./

# 安装Python依赖到用户目录
RUN pip install --user -r requirements.txt

# ================================
# 应用构建阶段
# ================================
FROM base as app-build

# 复制依赖安装结果
COPY --from=dependencies /root/.local /root/.local

# 复制src目录内容到/app
COPY src/ ./

# 创建必要的目录并设置权限
RUN mkdir -p /app/data /app/alembic/versions /app/logs && \
    chmod 755 /app/data /app/logs /app/alembic/versions

# 确保启动脚本有执行权限
RUN chmod +x /app/docker-pre-start.sh

# 运行预启动脚本
RUN /app/docker-pre-start.sh

# ================================
# 运行时阶段
# ================================
FROM app-build as runtime

# 构建参数 - 默认为生产环境
ARG ENV_TYPE=prod
ARG EXPOSE_PORT=8080

# 设置环境变量
ENV ENV_TYPE=${ENV_TYPE}

# 暴露端口
EXPOSE ${EXPOSE_PORT}

# 启动容器
CMD ["python3", "run.py", "0.0.0.0", "${EXPOSE_PORT}"]

# ================================
# 环境特定构建目标
# ================================

# Function 环境
FROM runtime as function
ARG EXPOSE_PORT=9999
ENV ENV_TYPE=function
EXPOSE ${EXPOSE_PORT}

# UAT 环境  
FROM runtime as uat
ARG EXPOSE_PORT=8081
ENV ENV_TYPE=uat
EXPOSE ${EXPOSE_PORT}

# 生产环境
FROM runtime as production
ARG EXPOSE_PORT=8080
ENV ENV_TYPE=prod
EXPOSE ${EXPOSE_PORT}