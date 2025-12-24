# SafeGuard 后端项目指南

## 项目概述

SafeGuard 是一个基于 Flask 的微信小程序后端服务，提供用户管理、社区管理、打卡监督等功能。项目采用现代化的 Python 3.12 技术栈，支持多环境部署和完整的测试体系。

**架构特点**：
- 采用 Flask Blueprint 模块化架构，实现 100% 路由模块化
- 使用应用工厂模式，统一扩展管理和配置
- 11 个功能模块独立管理，便于开发和维护
- 符合 Flask 最佳实践，具备高可扩展性和可维护性

### 核心功能
- **用户认证管理**：支持微信登录、手机号注册、Token 管理
- **社区管理**：社区创建、成员管理、权限控制
- **打卡监督**：打卡规则设置、打卡记录、监督关系管理
- **短信服务**：验证码发送和验证
- **分享功能**：打卡记录分享链接生成和解析

### 技术栈
- **后端框架**：Flask 3.1.2 + Blueprint 模块化架构
- **数据库**：SQLAlchemy 2.0.16 + Flask-SQLAlchemy 3.0.5
- **数据库迁移**：Alembic 1.13.1
- **认证**：JWT (PyJWT 2.4.0)
- **缓存**：Redis 5.0.1
- **API 文档**：Markdown 格式的 API 文档（位于 `API/` 目录）
- **测试框架**：pytest
- **容器化**：Docker
- **应用架构**：Flask Application Factory 模式
- **模块化设计**：11 个功能模块 Blueprint

## 项目结构

```
backend/
├── src/                    # 源代码目录
│   ├── app/               # Flask 应用工厂和模块化架构
│   │   ├── __init__.py    # 应用工厂，创建和配置 Flask 应用
│   │   ├── extensions.py  # Flask 扩展管理（SQLAlchemy 等）
│   │   ├── modules/       # Blueprint 模块（11个功能模块）
│   │   │   ├── auth/      # 认证模块
│   │   │   ├── user/      # 用户管理模块
│   │   │   ├── community/ # 社区管理模块
│   │   │   ├── checkin/   # 打卡模块
│   │   │   ├── supervision/ # 监督模块
│   │   │   ├── sms/       # 短信服务模块
│   │   │   ├── share/     # 分享功能模块
│   │   │   ├── events/    # 事件管理模块
│   │   │   ├── community_checkin/ # 社区打卡模块
│   │   │   ├── user_checkin/     # 用户打卡模块
│   │   │   └── misc/      # 杂项功能模块
│   │   └── shared/        # 共享组件
│   │       ├── response.py # 统一响应格式
│   │       ├── decorators.py # 装饰器
│   │       └── utils/     # 工具函数
│   ├── wxcloudrun/        # 核心业务逻辑（业务服务层）
│   │   ├── utils/         # 工具函数
│   │   ├── *_service.py   # 业务服务层
│   │   ├── background_tasks.py # 后台任务
│   │   └── wxchat_api.py  # 微信API接口
│   ├── database/          # 数据库相关
│   │   ├── flask_models.py    # Flask-SQLAlchemy 模型
│   │   ├── core.py            # 数据库核心（已迁移）
│   │   └── initialization.py  # 数据库初始化
│   ├── alembic/           # 数据库迁移脚本
│   ├── run.py             # 标准应用入口（使用 app.create_app()）
│   ├── config.py          # 配置文件
│   └── config_manager.py  # 配置管理器
├── tests/                 # 测试目录
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── e2e/              # 端到端测试
├── API/                  # API 文档
├── scripts/              # 构建和部署脚本
├── docs/                 # 项目文档
├── Makefile              # 测试和构建命令
└── venv_py312/          # Python 虚拟环境
```

## 环境配置

项目支持多环境配置，通过 `ENV_TYPE` 环境变量控制：

| 环境 | 描述 | 数据库类型 |
|------|------|------------|
| `function` | 开发环境 | SQLite 文件数据库 |
| `unit` | 单元测试环境 | 内存数据库 |
| `uat` | UAT 测试环境 | SQLite 文件数据库 |
| `prod` | 生产环境 | SQLite 文件数据库 |

### 环境变量配置
```bash
# 基本配置
ENV_TYPE=function          # 环境类型
WX_APPID=your_appid       # 微信小程序 AppID
WX_SECRET=your_secret     # 微信小程序 Secret
TOKEN_SECRET=your_secret  # JWT Token 密钥

# 数据库配置（自动根据 ENV_TYPE 加载）
# 配置文件位于 src/.env.* 文件
```

## 开发指南

### 1. 环境设置

```bash
# 创建虚拟环境（Python 3.12）
python3.12 -m venv venv_py312

# 激活虚拟环境
source venv_py312/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt  # 测试依赖
```

### 2. 本地开发运行

```bash
# 方式1：使用本地运行脚本（推荐）
./localrun.sh

# 方式2：手动启动（使用应用工厂）
cd src
ENV_TYPE=function python3.12 run.py 0.0.0.0 9999

# 方式3：使用Flask应用工厂直接启动
cd src
ENV_TYPE=function python3.12 -c "
from app import create_app
app = create_app()
app.run(host='0.0.0.0', port=9999, debug=True)
"
```

### 应用启动流程
`src/run.py` 作为标准应用入口，提供完整的启动流程：

1. **环境检查**：验证 `ENV_TYPE` 环境变量已设置
2. **应用创建**：使用应用工厂 `create_app()` 创建 Flask 实例
3. **数据库迁移**：根据环境类型自动执行数据库迁移
4. **数据初始化**：在非测试环境自动创建超级管理员和默认社区
5. **后台任务**：在非 unit 环境启动后台打卡检测服务
6. **服务启动**：启动 Flask 开发服务器

服务启动后访问：
- API 服务：http://localhost:9999
- 环境配置查看器：http://localhost:9999/api/env

### 3. 数据库迁移

```bash
# 进入 src 目录
cd src

# 生成迁移脚本（首次运行）
alembic revision --autogenerate -m "init_db"

# 执行迁移
alembic upgrade head

# 查看迁移历史
alembic history

# 回滚迁移
alembic downgrade -1
```

## 构建和部署

### Docker 构建

```bash
# 构建所有环境镜像
./scripts/build.sh

# 构建特定环境
./scripts/build-function.sh    # Function 环境
./scripts/build-uat.sh         # UAT 环境
./scripts/build-prod.sh        # 生产环境
```

### Docker 运行

```bash
# 运行生产环境
./scripts/run-prod.sh

# 运行 UAT 环境
./scripts/run-uat.sh

# 运行 Function 环境
./scripts/run-function.sh

# 查看容器状态
./scripts/status.sh

# 停止所有容器
./scripts/stop-all.sh
```

### 容器访问
- 生产环境：http://localhost:8080
- UAT 环境：http://localhost:8081
- Function 环境：http://localhost:8082

## 测试

项目包含完整的测试体系：

### 测试命令

```bash
# 设置测试环境（首次运行）
make setup

# 运行所有测试
make test-all

# 运行单元测试
make ut

# 运行集成测试
make test-integration
make it  # 运行所有集成测试用例的简写

# 运行端到端测试
make e2e

# 运行单个测试文件
make ut-s TEST=tests/unit/test_user_service.py
make its TEST=tests/integration/test_user_integration.py

# 运行特定测试类或方法
make test-class CLASS=TestAccountMerging
make test-method METHOD=test_account_merge_functionality

# 运行数据库迁移测试
make test-migration

# 生成测试覆盖率报告
make test-coverage

# 清理测试文件
make clean

# 运行之前失败的测试
make test-failed
```

### 测试环境说明
- **单元测试**：使用内存数据库，快速执行
- **集成测试**：使用文件数据库，测试模块间集成
- **端到端测试**：启动独立的 Flask 进程，模拟真实环境

## API 文档

详细的 API 文档位于 `API/` 目录：

| 功能域 | 文档文件 | 描述 |
|--------|----------|------|
| 认证域 | `API_auth.md` | 用户身份验证、登录、注册 |
| 用户管理 | `API_user.md` | 用户信息管理、搜索 |
| 社区管理 | `API_community.md` | 社区 CRUD、工作人员管理 |
| 打卡功能 | `API_checkin.md` | 打卡规则、记录管理 |
| 短信服务 | `API_sms.md` | 验证码发送和验证 |
| 监督功能 | `API_supervision.md` | 监督关系管理 |
| 分享功能 | `API_share.md` | 分享链接管理 |
| 其他功能 | `API_misc.md` | 计数器、环境配置等 |

### API 响应格式
```json
{
  "code": 1,        // 1-成功，0-失败
  "msg": "success", // 状态消息
  "data": {...}     // 响应数据
}
```

### 认证方式
需要认证的接口使用 Bearer Token：
```
Authorization: Bearer <token>
```

## 开发约定

### 代码结构
1. **应用工厂** (`src/app/__init__.py`)：创建和配置 Flask 应用实例
2. **蓝图模块** (`src/app/modules/`)：按功能域组织的模块化路由
3. **共享组件** (`src/app/shared/`)：跨模块共享的工具和响应格式
4. **业务服务层** (`src/wxcloudrun/*_service.py`)：业务逻辑实现
5. **模型层** (`src/database/flask_models.py`)：Flask-SQLAlchemy 数据模型
6. **工具层** (`src/wxcloudrun/utils/`)：通用工具函数
7. **应用入口** (`src/run.py`)：标准应用启动入口，集成数据库迁移和初始化

### Blueprint 开发规范
1. **模块组织**：每个功能域一个 Blueprint，包含 `__init__.py` 和 `routes.py`
2. **路由定义**：使用 `@{module}_bp.route()` 装饰器，应用注册时统一添加 `/api` 前缀
3. **导入规范**：使用 `current_app` 替代全局 `app` 变量
4. **共享组件**：从 `app.shared` 导入响应格式和装饰器
5. **避免循环导入**：在 `__init__.py` 中先定义 Blueprint，再导入 routes
6. **蓝图前缀**：每个 Blueprint 可定义自己的模块级前缀（如 `/auth`, `/user`），最终路径为 `/api/{module_prefix}/{route}`

### 数据库约定
1. 使用 Flask-SQLAlchemy 进行数据库操作
2. 所有模型继承自 `db.Model`
3. 使用 Alembic 进行数据库迁移管理
4. 软删除使用 `is_deleted` 字段标记

### Blueprint 架构说明
项目采用 Flask Blueprint 模块化架构，具有以下特点：

**模块组织**
- 11 个功能模块，每个模块独立管理自己的路由和业务逻辑
- 统一的 `/api` 前缀，所有 API 端点都以此开头
- 模块间通过共享组件进行通信，避免耦合

**扩展管理**
- 所有 Flask 扩展在 `app/extensions.py` 中统一管理
- 使用应用工厂模式，确保扩展正确初始化
- 避免循环导入问题，保持代码清晰

**开发流程**
1. 新功能开发时，在对应的 Blueprint 模块中添加路由
2. 使用 `current_app` 访问应用实例，而非全局变量
3. 共享的工具函数和装饰器放在 `app/shared/` 目录
4. 业务逻辑在 `wxcloudrun/*_service.py` 中实现
5. 应用启动通过 `src/run.py` 统一管理，包含数据库迁移和初始化流程

**部署优势**
- 模块化架构便于独立测试和部署
- 清晰的依赖关系，降低维护成本
- 符合 Flask 最佳实践，便于团队协作

### 错误处理
1. HTTP 状态码统一返回 200
2. 业务状态通过 `code` 字段判断（1-成功，0-失败）
3. 错误消息在 `msg` 字段中返回

## 常见问题

### 1. 数据库迁移失败
```bash
# 检查迁移脚本
cd src
alembic current

# 手动修复迁移
alembic downgrade base
alembic upgrade head
```

### 2. 环境变量未设置
```bash
# 检查当前环境变量
echo $ENV_TYPE

# 设置环境变量
export ENV_TYPE=function
```

### 3. 端口冲突
```bash
# 查看占用端口的进程
lsof -i :9999

# 停止占用进程
./scripts/killport.sh 9999
```

### 4. 虚拟环境问题
```bash
# 重新创建虚拟环境
rm -rf venv_py312
make setup
```

## 维护脚本

项目提供了一系列维护脚本：

| 脚本 | 功能 |
|------|------|
| `scripts/kill.sh` | 停止所有相关进程 |
| `scripts/killport.sh` | 停止指定端口的进程 |
| `scripts/logs.sh` | 查看应用日志 |
| `scripts/removedb.sh` | 删除数据库文件 |
| `scripts/clean_e2e_test_env.sh` | 清理 E2E 测试环境 |

### Makefile 命令
项目使用 Makefile 管理测试和构建流程：

- **测试管理**：`make setup`, `make test-all`, `make clean`
- **单元测试**：`make ut`, `make ut-s TEST=<test_file>`
- **集成测试**：`make test-integration`, `make it`, `make its TEST=<test_file>`
- **E2E测试**：`make e2e`, `make e2e-single TEST=<test_file>`
- **迁移测试**：`make test-migration`, `make test-migration-performance`
- **覆盖率报告**：`make test-coverage`

## 贡献指南

1. **代码规范**：遵循现有代码风格，使用类型注解
2. **测试要求**：新功能必须包含单元测试和集成测试
3. **文档更新**：修改 API 后需要更新对应的 API 文档
4. **提交信息**：使用清晰的提交信息，说明修改内容和原因
5. **Blueprint 开发**：
   - 新功能应该在对应的 Blueprint 模块中开发
   - 遵循模块化设计原则，避免跨模块直接调用
   - 使用 `current_app` 而非全局 `app` 变量
   - 共享组件放在 `app/shared/` 目录
6. **导入规范**：
   - 避免循环导入，Blueprint 定义要在路由导入之前
   - 使用相对导入处理模块内部依赖
   - 从 `app.shared` 导入共享组件

## 联系和支持

- **项目文档**：查看 `docs/` 目录
- **API 文档**：查看 `API/` 目录
- **问题反馈**：通过项目 Issue 系统反馈问题

---

*最后更新：2025-12-24*
*版本：SafeGuard Backend v2.0 (Blueprint 架构)*
*架构更新：完成 Flask Blueprint 模块化重构，共 11 个功能模块，84 个 API 路由*