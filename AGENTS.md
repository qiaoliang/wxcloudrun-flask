# 安全守护项目后端代码库 (SafeGuard) - Agent 指南

## 项目概述

安全守护是一个为独居者提供安全监护服务的应用，项目采用前后端分离架构。当前目录包含基于 Flask 框架的后端服务，主要用于处理安全监护相关的业务逻辑，包括用户管理、打卡规则、打卡记录等功能。

后端项目代码对应的 Git 仓库地址: https://github.com/qiaoliang/wxcloudrun-flask

## 项目宪法

@./constitution_for_backend.md

## 项目需求文档

@../docs/PRD.md

## API 接口

@./docs/API/API_in_summary.md

## 技术栈

-   **开发语言**: Python 3.12
-   **虚拟环境**: ./backend/venv_py312
-   **配置管理**: python-dotenv
-   **应用框架**: Flask 2.0.2
-   **ORM**: Flask-SQLAlchemy + SQLAlchemy
-   **数据库**: MySQL (使用 SQLAlchemy ORM)
    -   生产环境：MySQL 8.4.3
    -   开发环境：SQLite 3
-   **身份验证**: JWT (PyJWT 2.4.0)
-   **微信小程序集成**: 微信小程序 code2Session API
-   **部署**: Docker 容器化部署
-   **测试框架**: pytest + requests-mock

## 项目架构

采用分层架构：Route -> Controller -> Service -> Model -> Database

### 主要模块

-   `wxcloudrun/__init__.py`: 应用初始化，包含 Flask 应用实例和数据库对象
-   `wxcloudrun/views.py`: API 路由和控制器，处理所有 HTTP 请求
-   `wxcloudrun/model.py`: 数据模型定义，包括用户、打卡规则、打卡记录等
-   `wxcloudrun/dao.py`: 数据访问对象，提供数据库操作方法
-   `wxcloudrun/response.py`: 统一响应格式构造器

## 核心功能

### 1. 用户认证

-   微信小程序登录（code2Session API）
-   JWT Token 认证
-   Refresh Token 机制
-   用户角色管理（独居者、监护人、社区工作人员）

### 2. 打卡管理

-   打卡规则设置（频率、时间、内容）
-   打卡执行和撤销（30 分钟内）
-   打卡历史查询
-   按日期范围查询打卡记录

### 3. 社区功能

-   社区工作人员身份验证
-   未打卡用户管理

## 环境配置

### 必需环境变量

-   `MYSQL_USERNAME`: MySQL 用户名（默认: root）
-   `MYSQL_PASSWORD`: MySQL 密码
-   `MYSQL_ADDRESS`: MySQL 地址和端口（默认: 127.0.0.1:3306）
-   `WX_APPID`: 微信小程序 AppID
-   `WX_SECRET`: 微信小程序 Secret
-   `TOKEN_SECRET`: JWT 令牌密钥

### 可选环境变量

-   `FLASK_ENV`: Flask 环境（testing/production 等）
-   `USE_SQLITE_FOR_TESTING`: 是否使用 SQLite 进行测试（默认: false）
-   `AUTO_RUN_MIGRATIONS`: 是否自动运行数据库迁移（默认: true）

## 数据库设计

### User (用户表)

-   `user_id`: 用户 ID（主键，自增）
-   `wechat_openid`: 微信 OpenID（唯一，必填）
-   `phone_number`: 手机号码（唯一）
-   `nickname`: 用户昵称
-   `avatar_url`: 用户头像 URL
-   `role`: 用户角色（1-独居者，2-监护人，3-社区工作人员）
-   `status`: 用户状态（1-正常，2-禁用）
-   `verification_status`: 验证状态（0-未申请，1-待审核，2-已通过，3-已拒绝）
-   `community_id`: 所属社区 ID（仅社区工作人员需要）
-   `created_at`: 创建时间
-   `updated_at`: 更新时间

### CheckinRule (打卡规则表)

-   `rule_id`: 规则 ID（主键，自增）
-   `solo_user_id`: 独居者用户 ID（外键）
-   `rule_name`: 规则名称
-   `icon_url`: 规则图标 URL
-   `frequency_type`: 频率类型（0-每天，1-每周，2-工作日，3-自定义）
-   `time_slot_type`: 时间段类型（1-上午，2-下午，3-晚上，4-自定义时间）
-   `custom_time`: 自定义时间
-   `week_days`: 一周中的天（位掩码表示）
-   `status`: 规则状态（1-启用，0-禁用）
-   `created_at`: 创建时间
-   `updated_at`: 更新时间

### CheckinRecord (打卡记录表)

-   `record_id`: 记录 ID（主键，自增）
-   `rule_id`: 打卡规则 ID（外键）
-   `solo_user_id`: 独居者用户 ID（外键）
-   `checkin_time`: 实际打卡时间
-   `status`: 状态（0-未打卡，1-已打卡，2-已撤销）
-   `planned_time`: 计划打卡时间
-   `created_at`: 创建时间
-   `updated_at`: 更新时间

## API 规范

-   RESTful API 设计风格
-   统一错误处理中间件
-   请求参数验证
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

## 开发命令

### 环境准备

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 本地开发模式运行

```bash
# 使用Docker Compose开发模式（代码热重载）
docker-compose -f docker-compose.dev.yml up --build

# 或直接运行应用
python run.py 0.0.0.0 8080
```

### 运行后台单元测试

```bash
# 运行单元测试（使用SQLite内存数据库）
cd ~/working/code/safeGuard/backend
source venv_py312/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
python scripts/unit_tests.py
```

### 运行后台集成测试

```bash
cd ~/working/code/safeGuard/backend
source venv_py312/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
# 运行后台集成测试
python scripts/function_tests.py
```

### 在本地运行所有的自动化测试

```bash
cd ~/working/code/safeGuard/backend
source venv_py312/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest scripts/run_tests.py
```

### 数据库迁移

```bash
# 生成新的迁移脚本
flask db migrate -m "描述性迁移信息"

# 应用迁移到数据库
flask db upgrade

# 查看当前迁移状态
flask db current
```

## 部署

### Docker 部署

```bash
# 构建并启动服务
docker-compose up --build -d

# 停止服务
docker-compose down
```

## 安全要求

-   路由访问需进行适当的认证和授权校验
-   敏感配置通过环境变量管理（.env 文件）
-   所有输入数据必须经过验证和清洗
-   错误信息返回需避免暴露系统内部实现细节
-   JWT Token 具备过期时间验证（2 小时有效期）
-   Refresh Token 具备有效期验证（7 天有效期）
