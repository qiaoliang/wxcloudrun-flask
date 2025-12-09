# wxcloudrun-flask
## 服务 API 文档

### `GET /api/count`

获取当前计数

#### 请求参数

无

#### 响应结果

- `code`：状态码 (1为成功，0为失败)
- `data`：当前计数值
- `msg`：响应消息

##### 响应结果示例

```json
{
  "code": 1,
  "data": 42,
  "msg": "success"
}
```

#### 调用示例

```
curl https://<云托管服务域名>/api/count
```



### `POST /api/count`

更新计数，自增或者清零

#### 请求参数

- `action`：`string` 类型，枚举值
  - 等于 `"inc"` 时，表示计数加一
  - 等于 `"clear"` 时，表示计数重置（清零）

##### 请求参数示例

```
{
  "action": "inc"
}
```

#### 响应结果

- `code`：状态码 (1为成功，0为失败)
- `data`：当前计数值
- `msg`：响应消息

##### 响应结果示例

```json
{
  "code": 1,
  "data": 43,
  "msg": "success"
}
```

#### 调用示例

```
curl -X POST -H 'content-type: application/json' -d '{"action": "inc"}' https://<云托管服务域名>/api/count
```

## 使用注意
如果不是通过微信云托管控制台部署模板代码，而是自行复制/下载模板代码后，手动新建一个服务并部署，需要在「服务设置」中补全以下环境变量：
- `WX_APPID`、`WX_SECRET`
- `TOKEN_SECRET`
（数据库文件路径不再在多处配置，应用会根据 `ENV_TYPE` 自动选择默认路径；如需自定义，单独设置 `SQLITE_DB_PATH` 即可）



## Docker Compose 本地开发模式

使用本地挂载方式的 Docker Compose 进行开发，可以实现代码实时更新，无需重新构建镜像。

### 环境准备

确保已安装 Docker 和 Docker Compose，并配置必要的环境变量：

```bash
# 在项目根目录创建 .env 文件，配置环境变量
echo "WX_APPID=your_wechat_appid" >> .env
echo "WX_SECRET=your_wechat_secret" >> .env
echo "TOKEN_SECRET=your_jwt_secret" >> .env
```

### 本地开发模式运行

使用开发配置文件启动服务，该配置会将本地代码目录挂载到容器中，实现代码实时更新：

```bash
# 启动开发模式（本地挂载）
docker-compose -f docker-compose.dev.yml up --build

# 或在后台运行
docker-compose -f docker-compose.dev.yml up --build -d
```

### 本地开发模式停止

```bash
# 停止开发模式服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除挂载的数据卷
docker-compose -f docker-compose.dev.yml down -v
```

### 生产模式运行

如果需要运行生产模式（不使用本地挂载，使用构建的镜像）：

```bash
# 启动生产模式服务
docker-compose up --build

# 或在后台运行
docker-compose up --build -d
```

## 数据库配置

本项目统一使用 SQLite：

- `ENV_TYPE=unit`：SQLite 内存数据库（不落盘），用于单元测试
- `ENV_TYPE=function`：SQLite 文件数据库，默认 `./data/function.db`
- `ENV_TYPE=prod`：SQLite 文件数据库，默认 `/app/data/prod.db`
如需自定义路径，仅在一个位置设置 `SQLITE_DB_PATH` 即可，避免多处重复配置。

所有模型使用通用类型，兼容 SQLite；无需 MySQL 相关环境变量。

### 运行自动化测试

**重要：请确保使用 Python 3.12 环境运行测试。**

运行测试时，系统会自动使用 SQLite 内存数据库，无需额外配置：

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 运行所有测试
pytest

# 或使用测试脚本
python scripts/run_tests.py
```

## 运行测试

项目包含全面的自动化测试套件，使用 pytest 框架。根据测试需求和环境不同，有三种运行方式，通过不同的环境变量配置文件实现：

### 1. 单元测试（使用SQLite）
在单元测试环境中，系统自动使用SQLite内存数据库，无需外部依赖：

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 安装测试依赖
pip install -r requirements-test.txt

# 创建单元测试环境变量文件（可选，脚本有默认值）
cat > .env.unit << EOF
USE_SQLITE_FOR_TESTING=true  # 启用测试模式，使用SQLite内存数据库
FLASK_ENV=testing            # Flask环境设置
WX_APPID=test_appid          # 微信小程序AppID（测试值会跳过微信API测试）
WX_SECRET=test_secret        # 微信小程序Secret（测试值会跳过微信API测试）
TOKEN_SECRET=test_token      # JWT令牌密钥
EOF

# 运行所有单元测试
pytest

# 或使用单元测试脚本（推荐，会自动加载.env.unit）
python scripts/unit_tests.py

# 生成覆盖率报告
python scripts/unit_tests.py --coverage
```

### 2. 集成测试
当前测试套件以 SQLite 为主，CI/CD 可直接使用 `ENV_TYPE=function` 加载文件数据库，无需 MySQL。

### 3. 手动集成测试
若需使用真实微信凭证，请在 `.env.function` 或 `.env.prod` 中设置 `WX_APPID`、`WX_SECRET` 与 `TOKEN_SECRET`，其余数据库配置保持 SQLite。

### 环境变量说明

以下是在不同测试场景中使用的环境变量及其含义：

#### 数据库相关变量
- `SQLITE_DB_PATH`: SQLite 文件数据库路径（例如 `./data/app.db` 或 `/app/data/app.db`）
- `FLASK_ENV`: Flask环境（testing/production等，默认: 根据测试类型自动设置）
- `USE_REAL_WECHAT_CREDENTIALS`: 是否使用真实微信凭证进行测试（true/false，默认: false）
- `RUN_DOCKER_INTEGRATION_TESTS`: 是否运行Docker集成测试（true/false，默认: false）

#### 微信API相关变量
- `WX_APPID`: 微信小程序AppID
  - 测试环境：使用包含"test"的值会跳过微信API相关测试
  - 手动测试：使用真实值会执行完整的微信API测试
- `WX_SECRET`: 微信小程序Secret
  - 测试环境：使用包含"test"的值会跳过微信API相关测试
  - 手动测试：使用真实值会执行完整的微信API测试
- `TOKEN_SECRET`: JWT令牌签名密钥

#### 脚本相关变量
- `.env.unit`: 单元测试环境变量文件
- `.env.integration`: 自动集成测试环境变量文件
- `.env.manual`: 手动集成测试环境变量文件
- `DOCKER_STARTUP_TIMEOUT`: Docker容器启动超时时间（秒，默认: 180）

### 测试结构

项目包含以下测试模块：

- `tests/test_*.py`: 单元测试（API、DAO、模型、响应、登录等）
- `tests/integration_test_*.py`: 集成测试（使用MySQL，根据环境变量决定是否跳过微信API测试）
- `tests/conftest.py`: 测试配置和共享fixture

### 测试配置

- 测试文件位于 `tests/` 目录
- 项目使用 pytest 进行测试运行和管理
- 脚本会自动加载 `.env.unit` (单元测试) 或 `.env.integration` (集成测试) 文件
- 覆盖率检查最低要求为 80%
- 单元测试和集成测试均使用SQLite
- 微信API测试根据WX_APPID和WX_SECRET值决定是否跳过


## License

[MIT](./LICENSE)
