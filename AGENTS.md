# SafeGuard 后端项目指南

## 项目概述

SafeGuard 是一个基于 Flask 的微信小程序后端服务，提供用户管理、社区管理、打卡监督等功能。项目采用现代化的 Python 3.12 技术栈，支持多环境部署和完整的测试体系。

**架构特点**：

-   采用 Flask Blueprint 模块化架构，实现 100% 路由模块化
-   使用应用工厂模式，统一扩展管理和配置
-   11 个功能模块独立管理，便于开发和维护
-   符合 Flask 最佳实践，具备高可扩展性和可维护性

### 核心功能

-   **用户认证管理**：支持微信登录、手机号注册、Token 管理
-   **社区管理**：社区创建、成员管理、权限控制
-   **打卡监督**：打卡规则设置、打卡记录、监督关系管理
-   **短信服务**：验证码发送和验证
-   **分享功能**：打卡记录分享链接生成和解析

### 技术栈

-   **后端框架**：Flask 3.1.2 + Blueprint 模块化架构
-   **数据库**：SQLAlchemy 2.0.16 + Flask-SQLAlchemy 3.0.5
-   **数据库迁移**：Alembic 1.13.1
-   **认证**：JWT (PyJWT 2.4.0)
-   **缓存**：Redis 5.0.1
-   **API 文档**：Markdown 格式的 API 文档（位于 `API/` 目录）
-   **测试框架**：pytest 7.4.3
-   **并行测试**：pytest-xdist 3.3.1（多进程并行执行）
-   **覆盖率工具**：pytest-cov 4.1.0
-   **测试数据生成**：线程安全的统一测试数据生成器
-   **智能测试**：智能测试运行器（自动配置选择）
-   **容器化**：Docker

## 提交代码变更的规范

请参考 [commit-rule.md](docs/commit-rule.md) 了解提交信息的前缀要求。

## 项目结构

请参考 [project-structure.md](docs/project-structure.md) 了解完整的项目目录结构。

## 环境配置

项目支持多环境配置，通过 `ENV_TYPE` 环境变量控制：

| 环境       | 描述         | 数据库类型        |
| ---------- | ------------ | ----------------- |
| `function` | 开发环境     | SQLite 文件数据库 |
| `unit`     | 单元测试环境 | 内存数据库        |
| `uat`      | UAT 测试环境 | SQLite 文件数据库 |
| `prod`     | 生产环境     | SQLite 文件数据库 |


每个环境对应的配置信息位于对应的文件 `src/.env.{env_type}`

### 环境变量配置

```bash
# 基本配置
ENV_TYPE=function          # 环境类型
WX_APPID=your_appid       # 微信小程序 AppID
WX_SECRET=your_secret     # 微信小程序 Secret
TOKEN_SECRET=your_secret  # JWT Token 密钥
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
```

**应用启动流程**：`src/run.py` 作为标准应用入口，提供完整的启动流程（环境检查、应用创建、数据库迁移、数据初始化、后台任务、服务启动）。

**服务访问**：
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

**容器访问**：
- 生产环境：http://localhost:8080
- UAT 环境：http://localhost:8081
- Function 环境：http://localhost:8082

## 测试

项目包含完整的测试体系，支持智能并行执行和统一测试数据生成。

**重要说明**：所有后台测试必须在 `backend/` 目录中运行。

### 测试命令

```bash
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

# 传统命令
make test-all              # 运行所有测试
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

### 测试特性

- **线程安全测试数据生成**：确保所有测试数据的唯一性和隔离性
- **智能并行测试**：根据测试规模自动选择最佳配置
- **性能优化**：单元测试套件智能并行 ~3 秒（2.6x 性能提升）

> **集成测试编写指南**：详细的集成测试编写要点和最佳实践，请参考 [集成测试自动化用例编写指南](docs/integration-test-writing-guide.md)

## API

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

> **重要提示**：所有开发者必须遵循 [SafeGuard 后端代码规范](docs/code-style-guide.md)，该文档详细定义了数据库操作、代码结构、命名规范、测试规范等最佳实践。

### 代码结构

1. **应用工厂** (`src/app/__init__.py`)：创建和配置 Flask 应用实例
2. **蓝图模块** (`src/app/modules/`)：按功能域组织的模块化路由
3. **共享组件** (`src/app/shared/`)：跨模块共享的工具和响应格式
4. **业务服务层** (`src/wxcloudrun/*_service.py`)：业务逻辑实现
5. **模型层** (`src/database/flask_models.py`)：Flask-SQLAlchemy 数据模型
6. **工具层** (`src/wxcloudrun/utils/`)：通用工具函数
7. **应用入口** (`src/run.py`)：标准应用启动入口

### Blueprint 开发规范

1. **模块组织**：每个功能域一个 Blueprint，包含 `__init__.py` 和 `routes.py`
2. **路由定义**：使用 `@{module}_bp.route()` 装饰器，应用注册时统一添加 `/api` 前缀
3. **导入规范**：使用 `current_app` 替代全局 `app` 变量
4. **共享组件**：从 `app.shared` 导入响应格式和装饰器
5. **避免循环导入**：在 `__init__.py` 中先定义 Blueprint，再导入 routes

### 数据库约定

> **详细规范**：请参考 [代码规范 - 数据库操作章节](docs/code-style-guide.md#3-数据库操作规范)，了解 `db.session` 使用、SQLAlchemy 2.0 API、事务处理等最佳实践。

1. 使用 Flask-SQLAlchemy 进行数据库操作
2. 所有模型继承自 `db.Model`
3. 使用 Alembic 进行数据库迁移管理
4. 软删除使用 `is_deleted` 字段标记

### Blueprint 架构

项目采用 Flask Blueprint 模块化架构：
- 11 个功能模块，每个模块独立管理自己的路由和业务逻辑
- 统一的 `/api` 前缀，所有 API 端点都以此开头
- 所有 Flask 扩展在 `app/extensions.py` 中统一管理
- 使用应用工厂模式，确保扩展正确初始化

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

| 脚本                            | 功能               |
| ------------------------------- | ------------------ |
| `scripts/kill.sh`               | 停止所有相关进程   |
| `scripts/killport.sh`           | 停止指定端口的进程 |
| `scripts/logs.sh`               | 查看应用日志       |
| `scripts/removedb.sh`           | 删除数据库文件     |
| `scripts/clean_e2e_test_env.sh` | 清理 E2E 测试环境  |

### Makefile 命令

**智能测试命令（推荐）**：
- `make ut`：智能单元测试，自动选择最佳并行配置
- `make it`：智能集成测试，自动选择最佳配置
- `make test-parallel`：强制并行测试（4 个进程）
- `make test-quick`：快速单文件测试

**传统测试命令**：
- `make test-all`：运行所有测试
- `make e2e`：运行端到端测试
- `make clean`：清理测试文件

**单个测试命令**：
- `make ut-s TEST=<test_file>`：运行单个单元测试文件
- `make its TEST=<test_file>`：运行单个集成测试文件
- `make e2e-single TEST=<test_file>`：运行单个 E2E 测试文件

**专项测试命令**：
- `make test-migration`：运行数据库迁移测试
- `make test-coverage`：生成测试覆盖率报告
- `make test-failed`：运行之前失败的测试

**环境设置**：
- `make setup`：设置测试环境（首次运行）

## 贡献指南

> **重要参考**：在提交代码前，请务必阅读 [SafeGuard 后端代码规范](docs/code-style-guide.md) 并使用 [代码审查清单](docs/code-style-guide.md#12-代码审查清单) 检查代码质量。

1. **代码规范**：遵循 [代码规范文档](docs/code-style-guide.md)，使用类型注解
2. **测试要求**：新功能必须包含单元测试和集成测试，参考 [测试规范](docs/code-style-guide.md#6-测试规范)
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

SafeGuard 项目采用 OpenAPI 3.0 规范进行 API 契约管理，确保前后端 API 接口的一致性和可维护性。

**契约文件结构**：
```
backend/
├── api-contract/
│   └── openapi.yaml         # OpenAPI 3.0 契约文件
```

### 契约验证流程

```bash
# 验证 API 契约一致性
make validate-api-contract

# 生成不一致性报告
make generate-contract-report

# 验证修复效果
make verify-api-fixes
```

### 开发流程

1. **API 设计阶段**：先在 OpenAPI 契约中定义接口
2. **后端实现**：严格按照契约实现路由和业务逻辑
3. **前端集成**：使用契约生成的 SDK 或直接调用契约定义的接口
4. **测试验证**：运行契约验证确保实现与定义一致

### 最佳实践

1. **契约先行**：先定义契约，再实现功能
2. **自动化验证**：将契约验证集成到开发流程
3. **文档同步**：保持 API 文档与契约同步更新
4. **版本管理**：合理使用 API 版本控制
5. **团队协作**：前后端开发人员共同维护契约

## 联系和支持

-   **代码规范**：[SafeGuard 后端代码规范](docs/code-style-guide.md) - 必读文档
-   **项目文档**：查看 `docs/` 目录
-   **API 文档**：查看 `API/` 目录
-   **API 契约**：查看 `api-contract/` 目录
-   **问题反馈**：通过项目 Issue 系统反馈问题

---

_最后更新：2025-12-28_
_版本：SafeGuard Backend v2.1 (智能测试 + 数据生成机制)_
