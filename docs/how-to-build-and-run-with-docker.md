# 后端构建和运行Docker容器指南

本文档介绍如何构建 Docker 镜像，并运行安全守护后端服务的不同环境的Docker 容器。

## 目录结构

```
backend/
├── scripts/           # 构建和运行脚本
│   ├── build-*.sh    # 构建脚本
│   ├── run-*.sh      # 运行脚本
│   ├── stop-all.sh   # 停止所有容器
│   ├── status.sh     # 查看容器状态
│   └── logs.sh       # 查看容器日志
├── dockerfiles/      # Docker 配置文件
└── docs/            # 文档
```

## 环境说明

项目支持三个运行环境：

| 环境 | 容器名称 | 端口映射 | 用途 |
|------|----------|----------|------|
| Function | s-function | 9999:9999 | 功能测试环境 |
| UAT | s-uat | 8080:8080 | 用户验收测试环境 |
| Production | s-prod | 8080:8080 | 生产环境 |

## 构建镜像

### Function 环境

```bash
./scripts/build-function.sh
```

构建 Function 环境的 Docker 镜像，镜像名称：`safeguard-function-img`

### UAT 环境

```bash
./scripts/build-uat.sh
```

构建 UAT 环境的 Docker 镜像，镜像名称：`safeguard-uat-img`

### Production 环境

```bash
./scripts/build-prod.sh
```

构建 Production 环境的 Docker 镜像，镜像名称：`safeguard-prod-img`

## 运行容器

### Function 环境

```bash
./scripts/run-function.sh
```

- 自动停止并删除现有的 s-function 容器
- 检查并停止其他占用 9999 端口的容器
- 启动新的 s-function 容器
- 访问地址：http://localhost:9999

### UAT 环境

```bash
./scripts/run-uat.sh
```

- 自动停止并删除现有的 s-uat 容器
- 检查并停止其他占用 8080 端口的容器
- 启动新的 s-uat 容器
- 访问地址：http://localhost:8080

### Production 环境

```bash
./scripts/run-prod.sh
```

- 自动停止并删除现有的 s-prod 容器
- 检查并停止其他占用 8080 端口的容器
- 启动新的 s-prod 容器
- 访问地址：http://localhost:8080
- 需要配置环境变量：WX_APPID, WX_SECRET, TOKEN_SECRET

## 容器管理

### 查看容器状态

```bash
./scripts/status.sh
```

显示所有安全守护相关容器的状态、端口映射和镜像信息。

### 查看容器日志

```bash
# 查看所有容器的最近20行日志
./scripts/logs.sh

# 实时跟踪所有容器日志
./scripts/logs.sh -f

# 查看指定容器的日志
./scripts/logs.sh s-function
./scripts/logs.sh s-uat
./scripts/logs.sh s-prod

# 实时跟踪指定容器日志
./scripts/logs.sh -f s-function

# 显示最后50行日志
./scripts/logs.sh -t 50 s-uat
```

### 停止所有容器

```bash
./scripts/stop-all.sh
```

停止并删除所有安全守护相关的容器（s-function, s-uat, s-prod）。

## 端口管理

脚本会自动处理端口冲突：

- Function 环境使用 9999 端口
- UAT 和 Production 环境都使用 8080 端口
- 启动新环境时会自动检查并停止占用目标端口的其他容器

## 环境变量配置

### UAT 环境

UAT 环境自动配置以下环境变量：
- `ENV_TYPE=uat`
- 微信API使用Mock服务
- 短信服务使用真实服务

### Production 环境

Production 环境需要手动配置以下环境变量：
- `ENV_TYPE=prod`
- `WX_APPID=your_wx_appid`
- `WX_SECRET=your_wx_secret`
- `TOKEN_SECRET=your_token_secret`

## API 访问

### Function 环境 (端口 9999)

- 查看应用状态：http://localhost:9999
- 计数器 API：http://localhost:9999/api/count
- 微信登录测试：http://localhost:9999/api/login 

### UAT/Production 环境 (端口 8080)

- 查看应用状态：http://localhost:8080
- 计数器 API：http://localhost:8080/api/count
- 微信登录测试：http://localhost:8080/api/login

## 故障排除

### 端口被占用

如果遇到端口被占用的问题，运行脚本时会自动检测并停止占用端口的容器。

### 容器启动失败

1. 检查镜像是否存在：
   ```bash
   docker images | grep safeguard
   ```

2. 查看容器日志：
   ```bash
   ./scripts/logs.sh -f [容器名称]
   ```

3. 重新构建镜像：
   ```bash
   ./scripts/build-[环境].sh
   ```

### 清理环境

如果需要完全清理环境：

```bash
# 停止所有容器
./scripts/stop-all.sh

# 删除所有镜像
docker rmi safeguard-function-img safeguard-uat-img safeguard-prod-img
```

## 开发工作流

典型的开发工作流程：

1. **开发阶段**：使用 Function 环境进行功能测试
   ```bash
   ./scripts/build-function.sh
   ./scripts/run-function.sh
   ```

2. **测试阶段**：使用 UAT 环境进行集成测试
   ```bash
   ./scripts/build-uat.sh
   ./scripts/run-uat.sh
   ```

3. **部署阶段**：使用 Production 环境
   ```bash
   ./scripts/build-prod.sh
   ./scripts/run-prod.sh
   ```

## 注意事项

1. **端口冲突**：UAT 和 Production 环境都使用 8080 端口，不能同时运行
2. **环境隔离**：每个环境使用独立的容器和镜像
3. **日志管理**：使用 `logs.sh` 脚本方便查看和管理日志
4. **资源清理**：使用 `stop-all.sh` 脚本停止所有容器释放资源
5. **镜像更新**：代码更新后需要重新构建相应的镜像