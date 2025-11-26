# py-safeClockin 项目文档

## 项目概述

这是一个基于 Flask 的微信云托管项目，实现了简单的计数器读写接口，并包含微信小程序登录功能。项目使用 MySQL 数据库存储数据，支持云托管部署。

### 主要技术栈
- **后端框架**: Flask 2.0.2
- **数据库**: MySQL (使用 SQLAlchemy ORM)
- **数据库连接**: PyMySQL 1.0.2
- **身份验证**: JWT (PyJWT 2.4.0)
- **微信小程序集成**: 微信小程序 code2Session API
- **部署**: Docker 容器化部署

### 项目架构
```
py-safeClockin/
├── wxcloudrun/           # 主要应用目录
│   ├── views.py         # 路由和业务逻辑
│   ├── dao.py           # 数据库访问层
│   ├── model.py         # 数据模型
│   ├── response.py      # 响应处理
│   └── templates/       # HTML 模板
├── config.py            # 配置文件
├── run.py               # 应用启动入口
├── requirements.txt     # Python 依赖
└── Dockerfile          # 容器化配置
```

## 构建和运行

### 本地开发环境设置

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **环境变量配置**:
   创建 `.env` 文件并配置以下变量：
   ```
   MYSQL_USERNAME=your_mysql_username
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_ADDRESS=127.0.0.1:3306
   WX_APPID=your_wechat_appid
   WX_SECRET=your_wechat_secret
   TOKEN_SECRET=your_jwt_secret
   ```

3. **数据库设置**:
   - 创建名为 `flask_demo` 的数据库
   - 项目会自动创建 `Counters` 表

4. **运行应用**:
   ```bash
   python run.py 0.0.0.0 8080
   ```

### Docker 部署

1. **构建镜像**:
   ```bash
   docker build -t py-safeclockin .
   ```

2. **运行容器**:
   ```bash
   docker run -p 8080:8080 py-safeclockin
   ```

## API 接口

### 1. 计数器接口

#### 获取计数 - GET /api/count
获取当前计数值

**响应示例**:
```json
{
  "code": 0,
  "data": 42
}
```

#### 更新计数 - POST /api/count
更新计数值（自增或清零）

**请求参数**:
```json
{
  "action": "inc"  // 或 "clear"
}
```

**响应示例**:
```json
{
  "code": 0,
  "data": 43
}
```

### 2. 登录接口

#### 微信小程序登录 - GET /api/login
通过微信小程序 code 获取用户信息并返回 JWT token

**请求参数**:
- `code`: 微信小程序登录凭证

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

## 开发约定

### 代码结构约定
- **views.py**: 包含所有路由处理函数和业务逻辑
- **dao.py**: 数据库操作，封装基本的 CRUD 操作
- **model.py**: SQLAlchemy 数据模型定义
- **response.py**: 统一的响应格式处理

### 数据库约定
- 使用 SQLAlchemy ORM 进行数据库操作
- 所有数据库操作都包含异常处理
- 表名使用大写字母（如 `Counters`）

### 响应格式约定
所有 API 响应都遵循统一格式：
- 成功响应: `{"code": 0, "data": ...}`
- 错误响应: `{"code": -1, "errorMsg": "错误信息"}`

### 身份验证约定
- 使用 JWT 进行身份验证
- Token 有效期为 7 天
- Token 包含 openid 和 session_key 信息

## 环境变量

项目依赖以下环境变量：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| MYSQL_USERNAME | MySQL 用户名 | root |
| MYSQL_PASSWORD | MySQL 密码 | root |
| MYSQL_ADDRESS | MySQL 地址 | 127.0.0.1:3306 |
| WX_APPID | 微信小程序 AppID | your-appid |
| WX_SECRET | 微信小程序 Secret | your-secret |
| TOKEN_SECRET | JWT 签名密钥 | your-token-secret |

## 注意事项

1. **数据库连接**: 确保数据库服务正在运行，并且连接参数正确
2. **微信小程序配置**: 需要在微信小程序后台配置服务器域名
3. **安全配置**: 生产环境中应使用强密码和安全的 JWT 密钥
4. **容器端口**: 应用默认运行在 8080 端口，确保端口可用

## 故障排除

1. **数据库连接失败**: 检查环境变量配置和数据库服务状态
2. **微信 API 调用失败**: 检查 AppID 和 Secret 配置是否正确
3. **JWT 验证失败**: 检查 TOKEN_SECRET 配置是否一致