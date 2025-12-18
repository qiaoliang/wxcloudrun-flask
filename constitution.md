# 后端项目

这是一个 python 编写的后端服务。

## 技术栈

-   **开发语言**: python 3.12
-   **虚拟环境**: venv_py312
-   **配置管理**：python-dotenv
-   **应用框架**: Flask 2.0.2
-   **ORM**: SQLAlchemy
-   **数据库**: Sqlite3 (使用 SQLAlchemy ORM)
-   **身份验证**: JWT (PyJWT 2.4.0)
-   **微信小程序集成**: 微信小程序 code2Session API
-   **部署**: Docker 容器化部署
-   **测试框架**：pytest

## 架构模式

采用分层架构：view（Route + Controller） -> Service -> Model -> Database

```
.
├── API             // 存放API 说明文档的目录
├── docs            // 存放需求说明文档的目录
│     └── plans     // 存放开发计划文件的目录
├── scripts         // 存放有关调试，打包，自动化测试的脚本
├── scr             // 生产代码的源文件
│     ├── alembic
│     │     └── versions    // 存放数据库迁移脚本
│     ├── data              // 存放程序运行时生成的Sqlite3数据文件 
│     ├── database          // 存放应用程序的 Model 类文件
│     ├── static            // 存放应用程序的靜态文件，如图片等
│     └── wxcloudrun        // 存放应用程序的 Service 类文件
│         ├── templates
│         ├── utils
│         └── views         // 存放应用程序的 Route 和 Controller 类文件
├── tests           // 存放自动化测试
│     ├── e2e               // 存放 end-to-end 自动化测试用例文件
│     ├── integration       // 存放 integration 自动化测试用例文件
│     └── unit              // 存放 unit 自动化测试用例文件
└── venv_py312              //应用程序运行调试时使用的虚拟环境目录

```

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

### 如何运行 unit tests 和 e2e test

可以执行 `make help` 命令了解运行指南。

## 部署配置

-   开发环境使用 Flask 内置服务器
-   生产环境使用 Flask 内置服务器
-   支持 Docker 容器化部署
-   数据库迁移使用 alembic 框架
