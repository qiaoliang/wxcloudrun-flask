# 端口配置说明

## 端口映射规则

| 环境类型 | ENV_TYPE | 端口 | 用途 |
|---------|----------|------|------|
| 功能测试 | `func` | 9999 | 功能测试环境 |
| 开发环境 | `function` | 9999 | 本地开发 |
| 单元测试 | `unit` | 9999 | 单元测试 |
| UAT环境 | `uat` | 8080 | 用户验收测试 |
| 生产环境 | `prod` | 8080 | 生产环境 |

## 配置文件位置

- **统一配置**: `src/config_port.py` - 所有端口配置的单一来源
- **应用启动**: `src/run.py` - 使用 `config_port.py` 获取端口
- **Docker配置**: `Dockerfile` - 通过 ENV_TYPE 自动确定端口
- **启动脚本**: `scripts/run-*.sh` - 指定端口映射

## 使用方式

### 1. 直接运行 Python 应用

```bash
# Function 环境
ENV_TYPE=function python3 src/run.py

# UAT 环境
ENV_TYPE=uat python3 src/run.py

# 生产环境
ENV_TYPE=prod python3 src/run.py
```

### 2. Docker 运行

```bash
# Function 环境
docker run -p 9999:9999 -e ENV_TYPE=function safeguard-function-img

# UAT 环境
docker run -p 8080:8080 -e ENV_TYPE=uat safeguard-uat-img

# 生产环境
docker run -p 8080:8080 -e ENV_TYPE=prod safeguard-prod-img
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

如果需要覆盖默认端口，可以通过 `EXPOSE_PORT` 环境变量：

```bash
# 覆盖端口
docker run -p 9000:9000 -e ENV_TYPE=uat -e EXPOSE_PORT=9000 safeguard-uat-img
```

## 注意事项

1. **不要硬编码端口**: 所有端口配置都应通过 `config_port.py` 获取
2. **ENV_TYPE 优先**: 端口由 ENV_TYPE 决定，EXPOSE_PORT 只用于覆盖
3. **Docker 端口映射**: Docker 的 `-p` 参数必须与容器内部端口一致
4. **避免冲突**: 确保同一时间只有一个环境使用特定端口

## 修改端口配置

如需修改端口映射，只需编辑 `src/config_port.py` 中的 `PORT_CONFIG` 字典：

```python
PORT_CONFIG = {
    'func': 9999,
    'function': 9999,
    'unit': 9999,
    'uat': 8080,      # 修改这里
    'prod': 8080,     # 修改这里
}
```

修改后需要：
1. 重新构建 Docker 镜像
2. 更新启动脚本中的端口映射
3. 重启应用