# SafeGuard 后端项目指南

## 项目概述

SafeGuard 是一个基于 Flask 的微信小程序后端服务，提供用户管理、社区管理、打卡监督等功能。项目采用现代化的 Python 3.12 技术栈，支持多环境部署和完整的测试体系。

### 核心功能
- **用户认证管理**：支持微信登录、手机号注册、Token 管理
- **社区管理**：社区创建、成员管理、权限控制
- **打卡监督**：打卡规则设置、打卡记录、监督关系管理
- **短信服务**：验证码发送和验证
- **分享功能**：打卡记录分享链接生成和解析

### 技术栈
- **后端框架**：Flask 3.1.2
- **数据库**：SQLAlchemy 2.0.16 + Flask-SQLAlchemy 3.0.5
- **数据库迁移**：Alembic 1.13.1
- **认证**：JWT (PyJWT 2.4.0)
- **缓存**：Redis 5.0.1
- **API 文档**：Markdown 格式的 API 文档（位于 `API/` 目录）
- **测试框架**：pytest
- **容器化**：Docker

## 项目结构

```
backend/
├── src/                    # 源代码目录
│   ├── wxcloudrun/        # 核心业务逻辑
│   │   ├── views/         # API 视图层
│   │   ├── utils/         # 工具函数
│   │   └── *.py           # 服务层
│   ├── database/          # 数据库相关
│   │   ├── flask_models.py    # SQLAlchemy 模型
│   │   ├── core.py            # 数据库核心（已迁移）
│   │   └── initialization.py  # 数据库初始化
│   ├── alembic/           # 数据库迁移脚本
│   └── main.py            # 应用入口
├── tests/                 # 测试目录
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── e2e/              # 端到端测试
├── API/                  # API 文档
├── scripts/              # 构建和部署脚本
├── docs/                 # 项目文档
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

# 方式2：手动启动
cd src
ENV_TYPE=function python3.12 main.py 0.0.0.0 9999
```

服务启动后访问：
- API 服务：http://localhost:9999
- 环境配置查看器：http://localhost:9999/env

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

# 运行端到端测试
make e2e

# 运行单个测试文件
make ut-s TEST=tests/unit/test_user_service.py
make its TEST=tests/integration/test_user_integration.py

# 生成测试覆盖率报告
make test-coverage

# 清理测试文件
make clean
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
1. **视图层** (`src/wxcloudrun/views/`)：处理 HTTP 请求，调用服务层
2. **服务层** (`src/wxcloudrun/*_service.py`)：业务逻辑实现
3. **模型层** (`src/database/flask_models.py`)：SQLAlchemy 数据模型
4. **工具层** (`src/wxcloudrun/utils/`)：通用工具函数

### 数据库约定
1. 使用 Flask-SQLAlchemy 进行数据库操作
2. 所有模型继承自 `db.Model`
3. 使用 Alembic 进行数据库迁移管理
4. 软删除使用 `is_deleted` 字段标记

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

## 贡献指南

1. **代码规范**：遵循现有代码风格，使用类型注解
2. **测试要求**：新功能必须包含单元测试和集成测试
3. **文档更新**：修改 API 后需要更新对应的 API 文档
4. **提交信息**：使用清晰的提交信息，说明修改内容和原因

## 联系和支持

- **项目文档**：查看 `docs/` 目录
- **API 文档**：查看 `API/` 目录
- **问题反馈**：通过项目 Issue 系统反馈问题

---

*最后更新：2025-12-24*
*版本：SafeGuard Backend v1.0*