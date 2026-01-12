# 端口配置说明

## 端口映射规则

| 环境类型 | ENV_TYPE | 端口 | 用途 |
|---------|----------|------|------|
| 功能测试 | `func` | 9999 | 功能测试环境 |
| 开发环境 | `function` | 9999 | 本地开发 |
| 单元测试 | `unit` | 9999 | 单元测试 |
| UAT环境 | `uat` | 8080 | 用户验收测试 |
| 生产环境 | `prod` | 8080 | 生产环境 |

## 端口获取优先级

1. **EXPOSE_PORT** 环境变量（最高优先级，用于临时覆盖）
2. **ENV_TYPE** 环境类型（根据配置映射获取默认端口）

## 配置文件位置

- **统一配置**: `src/config_port.py` - 根据 ENV_TYPE 映射端口
- **应用启动**: `src/run.py` - 使用 `config_port.py` 获取端口
- **Docker配置**: `Dockerfile` - 通过 ENV_TYPE 自动确定端口
- **启动脚本**: `scripts/run-*.sh` - 指定端口映射

## 使用方式

### 1. 直接运行 Python 应用

```bash
# 使用默认端口（根据 ENV_TYPE 自动决定）
ENV_TYPE=function python3 src/run.py
ENV_TYPE=uat python3 src/run.py
ENV_TYPE=prod python3 src/run.py

# 使用 EXPOSE_PORT 覆盖默认端口
ENV_TYPE=uat EXPOSE_PORT=9000 python3 src/run.py
```

### 2. Docker 运行

```bash
# Function 环境（默认端口 9999）
docker run -p 9999:9999 -e ENV_TYPE=function safeguard-function-img

# UAT 环境（默认端口 8080）
docker run -p 8080:8080 -e ENV_TYPE=uat safeguard-uat-img

# 生产环境（默认端口 8080）
docker run -p 8080:8080 -e ENV_TYPE=prod safeguard-prod-img

# 自定义端口（使用 EXPOSE_PORT 覆盖）
docker run -p 9000:9000 -e ENV_TYPE=uat -e EXPOSE_PORT=9000 safeguard-uat-img
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

如果需要临时覆盖默认端口，使用 `EXPOSE_PORT` 环境变量：

```bash
# Docker 运行
docker run -p 9000:9000 -e ENV_TYPE=uat -e EXPOSE_PORT=9000 safeguard-uat-img

# 直接运行
ENV_TYPE=uat EXPOSE_PORT=9000 python3 src/run.py
```

## 注意事项

1. **只需 ENV_TYPE**: 端口由 ENV_TYPE 决定，不需要额外的 PORT_xxx 变量
2. **EXPOSE_PORT 用于覆盖**: 仅在需要临时修改端口时使用
3. **Docker 端口映射**: Docker 的 `-p` 参数必须与容器内部端口一致
4. **避免冲突**: 确保同一时间只有一个环境使用特定端口

## 修改默认端口

如需修改默认端口，编辑 `src/config_port.py` 中的 `PORT_CONFIG` 字典：

```python
PORT_CONFIG = {
    'func': 9999,
    'function': 9999,
    'unit': 9999,
    'uat': 8081,      # 修改这里
    'prod': 8081,     # 修改这里
}
```

修改后需要：
1. 重新构建 Docker 镜像
2. 更新启动脚本中的端口映射
3. 重启应用