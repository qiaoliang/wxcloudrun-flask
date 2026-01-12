# 端口配置说明

## 端口获取优先级

端口配置从环境变量读取，优先级如下：

1. **EXPOSE_PORT** 环境变量（最高优先级）
2. **PORT_{ENV_TYPE}** 环境变量（如 PORT_UAT、PORT_PROD）
3. **默认端口映射**（代码中的默认值）

## 默认端口映射

| 环境类型 | ENV_TYPE | 默认端口 | 环境变量名 |
|---------|----------|----------|-----------|
| 功能测试 | `func` | 9999 | `PORT_FUNC` |
| 开发环境 | `function` | 9999 | `PORT_FUNCTION` |
| 单元测试 | `unit` | 9999 | `PORT_UNIT` |
| UAT环境 | `uat` | 8080 | `PORT_UAT` |
| 生产环境 | `prod` | 8080 | `PORT_PROD` |

## 配置文件位置

- **统一配置**: `src/config_port.py` - 从环境变量读取端口配置
- **应用启动**: `src/run.py` - 使用 `config_port.py` 获取端口
- **Docker配置**: `Dockerfile` - 通过环境变量传递端口
- **启动脚本**: `scripts/run-*.sh` - 设置环境变量和端口映射

## 使用方式

### 1. 直接运行 Python 应用

```bash
# 使用默认端口
ENV_TYPE=function python3 src/run.py

# 使用环境变量指定端口
ENV_TYPE=uat PORT_UAT=9090 python3 src/run.py

# 使用 EXPOSE_PORT 覆盖
ENV_TYPE=prod EXPOSE_PORT=9000 python3 src/run.py
```

### 2. Docker 运行

```bash
# Function 环境（使用默认端口 9999）
docker run -p 9999:9999 -e ENV_TYPE=function safeguard-function-img

# UAT 环境（使用默认端口 8080）
docker run -p 8080:8080 -e ENV_TYPE=uat safeguard-uat-img

# 生产环境（使用默认端口 8080）
docker run -p 8080:8080 -e ENV_TYPE=prod safeguard-prod-img

# 自定义端口（使用 EXPOSE_PORT）
docker run -p 9000:9000 -e ENV_TYPE=uat -e EXPOSE_PORT=9000 safeguard-uat-img

# 自定义端口（使用 PORT_UAT）
docker run -p 9090:9090 -e ENV_TYPE=uat -e PORT_UAT=9090 safeguard-uat-img
```

### 3. 使用启动脚本

```bash
# Function 环境
./scripts/run-function.sh

# UAT 环境
./scripts/run-uat.sh

# 生产环境
./scripts/run-prod.sh
```

## 自定义端口

### 方式 1: 使用 EXPOSE_PORT（推荐）

```bash
# 适用于所有环境
docker run -p 9000:9000 -e ENV_TYPE=uat -e EXPOSE_PORT=9000 safeguard-uat-img
```

### 方式 2: 使用特定环境变量

```bash
# 适用于特定环境
docker run -p 9090:9090 -e ENV_TYPE=uat -e PORT_UAT=9090 safeguard-uat-img
docker run -p 8081:8081 -e ENV_TYPE=prod -e PORT_PROD=8081 safeguard-prod-img
```

## 注意事项

1. **环境变量优先**: 端口从环境变量读取，不要硬编码
2. **EXPOSE_PORT 优先级最高**: 适用于需要临时覆盖端口的场景
3. **Docker 端口映射**: Docker 的 `-p` 参数必须与容器内部端口一致
4. **避免冲突**: 确保同一时间只有一个环境使用特定端口

## 修改默认端口

如果需要修改默认端口，可以通过以下方式：

### 方式 1: 在环境变量中设置（推荐）

```bash
# 在 .env 文件中
PORT_UAT=8081
PORT_PROD=8081

# 或在命令行中
ENV_TYPE=uat PORT_UAT=8081 python3 src/run.py
```

### 方式 2: 修改代码默认值（不推荐）

编辑 `src/config_port.py` 中的默认值：

```python
default_ports = {
    'func': 9999,
    'function': 9999,
    'unit': 9999,
    'uat': 8081,      # 修改这里
    'prod': 8081,     # 修改这里
}
```

修改后需要重新构建 Docker 镜像。