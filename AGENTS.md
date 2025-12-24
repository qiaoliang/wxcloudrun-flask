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
- **测试框架**：pytest 7.4.3
- **并行测试**：pytest-xdist 3.3.1（多进程并行执行）
- **覆盖率工具**：pytest-cov 4.1.0
- **测试数据生成**：线程安全的统一测试数据生成器
- **智能测试**：智能测试运行器（自动配置选择）
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
│   │   ├── test_data_generator.py # 线程安全测试数据生成器
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
│   ├── config_manager.py  # 配置管理器
│   ├── smart_test_runner.py # 智能测试运行器
│   └── pytest.ini         # pytest配置文件
├── tests/                 # 测试目录
│   ├── unit/             # 单元测试（22个测试文件）
│   │   ├── conftest.py   # 单元测试配置
│   │   └── *.py         # 单元测试文件
│   ├── integration/      # 集成测试（2个测试文件）
│   │   ├── conftest.py   # 集成测试配置
│   │   └── *.py         # 集成测试文件
│   ├── e2e/              # 端到端测试
│   └── conftest.py        # pytest配置文件
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

项目包含完整的测试体系，支持智能并行执行和统一测试数据生成：

### 测试数据生成机制

项目实现了线程安全的统一测试数据生成机制，确保所有测试数据的唯一性和隔离性：

#### 核心特性
- **线程安全单例**：TestDataManager 支持多线程并发测试
- **全局唯一性**：自动生成唯一手机号码、昵称和用户名
- **前缀隔离**：昵称使用 `nickname_` 前缀，用户名使用 `uname_` 前缀
- **测试上下文追踪**：包含测试用例信息，便于调试
- **多进程支持**：支持 pytest-xdist 并行执行

#### 数据生成示例
```python
# 单元测试数据生成
手机号: 13900008000
昵称: nickname_test_context_12345678_8001
用户名: uname_test_context_12345678_8002

# 集成测试数据生成
手机号: 13900008003
昵称: nickname_integration_12345678_8004
用户名: uname_integration_12345678_8005
```

### 智能并行测试

项目实现了智能并行测试机制，根据测试规模自动选择最佳配置：

#### 智能配置策略
| 测试规模 | 文件数量 | 智能配置 | 性能优化 |
|---------|---------|---------|---------|
| 单个文件 | 1 | 串行执行 | 避免进程开销 |
| 小规模 | 2-5 | 2个进程 | 轻度并行 |
| 中等规模 | 6-20 | auto自动 | 智能检测 |
| 大规模 | 20+ | auto+loadscope | 最大并行 |

#### 并行测试支持
- **线程级并行**：单进程内多线程数据生成
- **进程级并行**：pytest-xdist 多进程测试执行
- **混合并行**：多进程+多线程混合模式
- **资源控制**：支持环境变量限制并行度

### 测试命令

**重要说明**：所有后台测试必须在 `backend/` 目录中运行，因为：
- 虚拟环境位于 `backend/venv_py312/`
- 配置文件和数据库文件相对于 `backend/` 目录
- Python 模块路径基于 `backend/src/` 目录

```bash
# 确保在backend目录中
cd backend

# 设置测试环境（首次运行）
make setup

# 智能单元测试（推荐）
make ut                    # 自动选择最佳并行配置
make ut VERBOSE=1         # 详细输出

# 智能集成测试（推荐）
make it                    # 自动选择最佳配置
make it VERBOSE=1         # 详细输出

# 强制并行测试
make test-parallel         # 强制4进程并行

# 快速测试
make test-quick            # 单个文件快速测试

# 传统命令（已升级）
make test-all              # 运行所有测试
make test-integration       # 运行集成测试
make e2e                   # 运行端到端测试

# 单个测试执行
make ut-s TEST=tests/unit/test_user_service.py
make its TEST=tests/integration/test_user_integration.py

# 覆盖率报告
make test-coverage

# 清理测试文件
make clean

# 失败测试重跑
make test-failed
```

### 智能测试运行器

项目提供智能测试运行器 `smart_test_runner.py`，支持高级配置：

```bash
# 智能测试执行
python smart_test_runner.py tests/

# 强制并行执行
python smart_test_runner.py tests/ -p --max-workers 4

# 详细输出
python smart_test_runner.py tests/unit/ -v

# 预览配置
python smart_test_runner.py tests/ --dry-run
```

### 环境变量控制

```bash
# 限制最大并行进程数
PYTEST_XDIST_AUTO_NUM_WORKERS=2 make ut

# 手动指定进程数
PYTEST_XDIST_WORKER_COUNT=4 make it

# 禁用并行（调试模式）
PYTEST_DISABLE_PLUGIN=xdist make ut
```

### 测试环境说明
- **单元测试**：使用内存数据库，支持并行执行，快速反馈
- **集成测试**：使用文件数据库，智能并行配置，模块间集成验证
- **端到端测试**：独立 Flask 进程，支持并行执行，真实环境模拟
- **数据隔离**：所有测试使用统一数据生成机制，完全隔离无冲突

### 性能基准

**单元测试套件（22个文件）**：
- 串行执行：~8秒
- 智能并行：~3秒（2.6x 性能提升）

**数据生成性能**：
- 单线程：~10,000 请求/秒
- 10线程并发：~69,000 请求/秒
- 完全线程安全：支持任意规模并发测试

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
项目使用 Makefile 管理测试和构建流程，支持智能并行执行：

#### 智能测试命令（推荐）
- **`make ut`**：智能单元测试，自动选择最佳并行配置
- **`make it`**：智能集成测试，自动选择最佳配置  
- **`make test-parallel`**：强制并行测试（4个进程）
- **`make test-quick`**：快速单文件测试
- **`make test-smart`**：智能测试执行（所有测试）

#### 传统测试命令（已升级）
- **`make test-all`**：运行所有测试
- **`make test-integration`**：运行集成测试
- **`make e2e`**：运行端到端测试
- **`make clean`**：清理测试文件

#### 单个测试命令
- **`make ut-s TEST=<test_file>`**：运行单个单元测试文件
- **`make its TEST=<test_file>`**：运行单个集成测试文件
- **`make e2e-single TEST=<test_file>`**：运行单个E2E测试文件

#### 专项测试命令
- **`make test-migration`**：运行数据库迁移测试
- **`make test-migration-performance`**：迁移性能测试
- **`make test-coverage`**：生成测试覆盖率报告
- **`make test-failed`**：运行之前失败的测试

#### 环境设置
- **`make setup`**：设置测试环境（首次运行）

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

## API 契约管理

### 概述
SafeGuard 项目采用 OpenAPI 3.0 规范进行 API 契约管理，确保前后端 API 接口的一致性和可维护性。通过系统化的契约管理机制，预防 API 不一致问题的发生。

### 契约文件结构
```
backend/
├── api-contract/
│   ├── openapi.yaml         # OpenAPI 3.0 契约文件
│   ├── schemas/            # 数据模型定义
│   └── examples/           # 请求/响应示例
```

### API 契约管理主方法

#### 1. 契约定义规范
- **路径命名规范**：统一使用 `/api/{module}/{resource}` 格式
- **HTTP 方法规范**：严格按照 RESTful 原则使用 GET/POST/PUT/DELETE
- **响应格式规范**：统一使用 `{code, msg, data}` 格式
- **错误处理规范**：统一错误码和错误消息格式

#### 2. 契约验证流程
```bash
# 验证 API 契约一致性
make validate-api-contract

# 生成不一致性报告
make generate-contract-report

# 验证修复效果
make verify-api-fixes
```

#### 3. 开发流程集成
- **API 设计阶段**：先在 OpenAPI 契约中定义接口
- **后端实现**：严格按照契约实现路由和业务逻辑
- **前端集成**：使用契约生成的 SDK 或直接调用契约定义的接口
- **测试验证**：运行契约验证确保实现与定义一致

#### 4. CI/CD 集成
- **自动化验证**：每次提交自动运行契约验证
- **报告生成**：自动生成不一致性报告
- **质量门禁**：契约验证失败阻止合并

#### 5. 版本管理策略
- **主版本**：不兼容的 API 变更
- **次版本**：向后兼容的功能新增
- **修订版本**：向后兼容的问题修正

### 常用命令

#### 契约验证命令
```bash
# 完整契约验证
python scripts/validate-api-contract.py \
  --contract api-contract/openapi.yaml \
  --backend src \
  --frontend ../frontend/src

# 生成修复报告
python scripts/generate-contract-report.py \
  --project-root . \
  --output api-report.md

# 验证修复效果
python scripts/verify-api-fixes.py
```

#### Makefile 集成命令
```bash
# API 契约相关命令
make validate-api-contract    # 验证 API 契约
make generate-contract-report # 生成不一致性报告
make verify-api-fixes        # 验证修复效果
make update-api-docs         # 更新 API 文档
```

### 契约文件维护

#### 添加新 API
1. 在 `api-contract/openapi.yaml` 中定义新的路径和操作
2. 添加相应的请求/响应模式定义
3. 更新 API 文档（`API/` 目录下的 Markdown 文件）
4. 运行契约验证确保定义正确

#### 修改现有 API
1. 先评估是否影响向后兼容性
2. 更新 OpenAPI 契约定义
3. 更新对应的实现代码
4. 运行完整的契约验证流程

#### API 版本升级
1. 在契约中定义新的版本路径
2. 保持旧版本 API 的兼容性
3. 逐步迁移客户端到新版本
4. 在适当时机废弃旧版本

### 错误处理和调试

#### 常见不一致问题
- **路径不匹配**：前端调用路径与后端实现路径不一致
- **方法不匹配**：HTTP 方法使用不当
- **参数不匹配**：请求参数名称或类型不一致
- **响应格式不匹配**：响应数据结构不一致

#### 调试工具
- **契约验证报告**：详细列出所有不一致问题
- **修复验证工具**：验证修复效果
- **API 文档对比**：对比契约文档和实际实现

### 最佳实践

1. **契约先行**：先定义契约，再实现功能
2. **自动化验证**：将契约验证集成到开发流程
3. **文档同步**：保持 API 文档与契约同步更新
4. **版本管理**：合理使用 API 版本控制
5. **团队协作**：前后端开发人员共同维护契约

## 联系和支持

- **项目文档**：查看 `docs/` 目录
- **API 文档**：查看 `API/` 目录
- **API 契约**：查看 `api-contract/` 目录
- **问题反馈**：通过项目 Issue 系统反馈问题

---

*最后更新：2025-12-24*
*版本：SafeGuard Backend v2.1 (智能测试 + 数据生成机制)*
*架构更新：完成 Flask Blueprint 模块化重构，共 11 个功能模块，84 个 API 路由*
*契约管理：建立完整的 API 契约管理机制，解决前后端 API 不一致问题*
*测试升级：实现线程安全测试数据生成器和智能并行测试机制*
*性能提升：单元测试性能提升 2.6x，支持大规模并行测试执行*