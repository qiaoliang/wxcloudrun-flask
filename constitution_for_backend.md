# 后端项目

这是一个 python 编写的后端服务。

## 技术栈

-   **开发语言**: python 3.12
-   **虚拟环境**: ./backend/venv_py312
-   **配置管理**：python-dotenv
-   **应用框架**: Flask 2.0.2
-   **ORM**: Flask-SQLAlchemy + SQLAlchemy
-   **数据库**: MySQL (使用 SQLAlchemy ORM)
    -   生产环境：MySQL 8.4.3
    -   开发环境：SQLite 3
-   **身份验证**: JWT (PyJWT 2.4.0)
-   **微信小程序集成**: 微信小程序 code2Session API
-   **部署**: Docker 容器化部署
-   **测试框架**：pytest + requests-mock

## 架构模式

采用分层架构：Route -> Controller -> Service -> Model -> Database

## API 规范

-   RESTful API 设计风格
-   统一错误处理中间件
-   请求参数验证使用 Pydantic
-   所有 API 响应都遵循以下统一格式：

### 成功响应

```json
{
    "code": 1,
    "data": {},
    "msg": "success"
}
```

### 错误响应

```json
{
    "code": 0,
    "data": {},
    "msg": "error message"
}
```

## 安全要求

-   路由访问需进行适当的认证和授权校验
-   敏感配置通过环境变量管理（.env 文件）
-   所有输入数据必须经过验证和清洗
-   错误信息返回需避免暴露系统内部实现细节

## 本后端项目的测试基础设施

项目包含全面的自动化测试套件，使用 pytest 框架。根据测试需求和环境不同，有不同的运行方式。

### 如何准备环境并运行单元测试

#### a) 前置条件

1. 执行下面的操作时，必须保证是在项目根目录下，即 backend 目录中执行。
2. 在单元测试环境中，必须使用 SQLite 内存数据库，不需要数据库迁移。
3. 运行单元测试前，必须使用 python3.12 激活虚拟环境 `source venv_py312/bin/activate`。
4. 激活虚拟环境后，必须安装测试依赖 `pip install -r requirements.txt requirements-test.txt`。
5. 运行单元测试前，必须查看 .env.unit 文件，因为其中有单元测试所必须的环境变量

#### b) 运行单元测试

下面是在不同场景下，运行单元测试的脚本命令。需要满足前置条件。

1. 使用下面的命令运行完整的单元测试用例集：

```bash
pytest tests/unit/
```

2. 当需要生成测试覆盖率报告时，使用下面的命令：

```bash
# 生成覆盖率报告
pytest tests/unit/ --cov=wxcloudrun --cov-report=html
```

1. 执行单个测试模块和用例（同样需要满足前置条件）

```bash

# 执行单个测试模块（例如：test_models.py）
python -m pytest tests/unit/test_models.py -v

# 执行单个测试模块中的某个特定的测试用例（例如：test_models.py 中的 test_user_exists 函数）
python -m pytest tests/unit/test_models.py::test_user_exists -v

```

### 2. 如何准备并运行本地的自动集成测试

#### a) 前置条件

1. 执行下面的操作时，必须保证是在当前后端项目根目录下，即 backend 目录中执行。
2. 在自动集成测试环境中，必须使用 MySQL 数据库，需要数据库迁移。
3. 运行自动集成测试前，必须使用 python3.12 激活虚拟环境 `source venv_py312/bin/activate`。
4. 激活虚拟环境后，必须安装测试依赖 `pip install -r requirements.txt requirements-test.txt`。
5. 运行自动集成测试前，必须查看 .env.integration 文件，因为其中有自动集成测试所必须的环境变量
6. 确保 docker 服务已经启动，因为自动集成测试会使用 docker-compose 启动一个 MySQL 容器。
7. 确保 docker-compose 配置文件 docker-compose.dev.yml 存在。

#### b) 运行自动集成测试的脚本命令

1. 运行完整的功能集成测试集的所有测试用例。

```bash
pytest tests/integration/
```

## 部署配置

-   开发环境使用 Flask 内置服务器
-   生产环境使用 Flask 内置服务器
-   支持 Docker 容器化部署
-   数据库迁移使用 Flask-Migrate
