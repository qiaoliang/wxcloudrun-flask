# 后端项目

这是一个python 编写的后端服务。

## 技术栈
- **开发语言**: python 3.12
- **虚拟环境**: ./backend/venv_py312
- **配置管理**：python-dotenv
- **应用框架**: Flask 2.0.2
- **ORM**: Flask-SQLAlchemy + SQLAlchemy
- **数据库**: MySQL (使用 SQLAlchemy ORM)
  - 生产环境：MySQL 8.4.3
  - 开发环境：SQLite 3
- **身份验证**: JWT (PyJWT 2.4.0)
- **微信小程序集成**: 微信小程序 code2Session API
- **部署**: Docker 容器化部署
- **测试框架**：pytest + requests-mock

## 架构模式

采用分层架构：Route -> Controller -> Service -> Model -> Database

## API 规范
- RESTful API 设计风格
- 统一错误处理中间件
- 请求参数验证使用 Pydantic
- 所有API响应都遵循以下统一格式：

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
- 路由访问需进行适当的认证和授权校验
- 敏感配置通过环境变量管理（.env 文件）
- 所有输入数据必须经过验证和清洗
- 错误信息返回需避免暴露系统内部实现细节

## 部署配置
- 开发环境使用 Flask 内置服务器
- 生产环境使用 Flask 内置服务器
- 支持 Docker 容器化部署
- 数据库迁移使用 Flask-Migrate
