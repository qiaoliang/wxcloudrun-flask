# SafeGuard 后端项目指南

## 项目概述

SafeGuard 是一个基于 Flask 的社区安全管理系统后端服务，主要提供以下功能：

-   **用户认证系统**：支持微信登录、手机号注册/登录等多种认证方式
-   **社区管理**：完整的社区 CRUD 操作，工作人员管理，用户权限控制
-   **打卡功能**：用户日常打卡记录，规则管理，监督机制
-   **短信服务**：验证码发送，手机号验证
-   **监督功能**：监护人监督机制，邀请监督关系
-   **分享功能**：打卡记录分享，社交互动

### 技术栈

-   **后端框架**：Flask 3.1.2
-   **数据库**：SQLAlchemy 2.0.16 + Alembic 迁移系统
-   **认证**：JWT Token 认证
-   **测试框架**：pytest
-   **部署**：Docker 容器化部署
-   **Python 版本**：3.12

## 项目结构

```
backend/
├── src/                    # 源代码目录
│   ├── wxcloudrun/         # 主应用包
│   │   ├── views/          # API 视图模块
│   │   │   ├── auth.py     # 认证相关接口
│   │   │   ├── user.py     # 用户管理接口
│   │   │   ├── community.py # 社区管理接口
│   │   │   ├── checkin.py  # 打卡功能接口
│   │   │   ├── sms.py      # 短信服务接口
│   │   │   ├── supervision.py # 监督功能接口
│   │   │   ├── share.py    # 分享功能接口
│   │   │   └── misc.py     # 其他功能接口
│   │   ├── model.py        # 数据模型定义
│   │   ├── community_service.py # 社区业务逻辑
│   │   ├── background_tasks.py # 后台任务
│   │   └── utils/          # 工具模块
│   ├── alembic/            # 数据库迁移脚本
│   ├── config.py           # 配置文件
│   └── main.py             # 应用入口
├── tests/                  # 测试目录
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # 端到端测试
├── API/                    # API 文档
├── scripts/                # 构建和部署脚本
└── docs/                   # 项目文档
```

## 环境配置

项目支持多环境配置，通过 `ENV_TYPE` 环境变量控制：

-   **func**：开发环境
-   **unit**：单元测试环境（内存数据库）
-   **uat**：UAT 测试环境
-   **prod**：生产环境

### 配置文件

-   `.env.function`：开发环境配置
-   `.env.unit`：单元测试配置
-   `.env.uat`：UAT 环境配置
-   `.env.prod`：生产环境配置

## 构建和运行

### 本地开发环境

1. **设置虚拟环境**：

    ```bash
    make setup
    ```

2. **启动开发服务器**：

    ```bash
    ./localrun.sh
    ```

3. **访问服务**：
    - API 服务：http://localhost:9999
    - 环境配置查看器：http://localhost:9999/env

### 测试

项目提供完整的测试套件：

1. **运行所有测试**：

    ```bash
    make test-all
    ```

2. **运行单元测试**：

    ```bash
    make ut
    ```

3. **运行集成测试**：

    ```bash
    make test-integration
    ```

4. **运行端到端测试**：

    ```bash
    make e2e
    ```

5. **生成测试覆盖率报告**：
    ```bash
    make test-coverage
    ```

### 数据库迁移

项目使用 Alembic 进行数据库迁移：

1. **生成迁移脚本**：

    ```bash
    cd src
    alembic revision --autogenerate -m "migration description"
    ```

2. **执行迁移**：
    ```bash
    cd src
    alembic upgrade head
    ```

### Docker 部署

1. **构建镜像**：

    ```bash
    ./scripts/build.sh
    ```

2. **运行容器**：
    ```bash
    ./scripts/run-function.sh
    ```

## 开发规范

### 代码风格

-   使用 Python 3.12 语法特性
-   遵循 PEP 8 代码规范
-   使用类型提示（Type Hints）
-   函数和类需要完整的文档字符串

### 提交规范

提交消息必须遵循以下前缀规范：

| 前缀     | 用途                   |
| -------- | ---------------------- |
| feat     | 新功能                 |
| fix      | bug 修复               |
| docs     | 仅文档更改             |
| style    | 代码格式调整           |
| refactor | 代码重构               |
| perf     | 性能优化               |
| test     | 测试相关               |
| chore    | 构建工具或辅助工具更改 |

### API 设计规范

-   **HTTP 状态码**：统一返回 200（业务状态通过响应体 `code` 字段判断）
-   **响应格式**：
    ```json
    {
      "code": 1,        // 1-成功，0-失败
      "msg": "success", // 状态消息
      "data": {...}     // 响应数据
    }
    ```
-   **认证方式**：Bearer Token（请求头 `Authorization: Bearer <token>`）

## 核心功能模块

### 1. 认证系统 (auth.py)

-   微信小程序登录
-   手机号注册/登录
-   Token 刷新机制
-   用户登出

### 2. 用户管理 (user.py)

-   用户信息查询/更新
-   用户搜索（按昵称或手机号）
-   手机号绑定
-   身份验证

### 3. 社区管理 (community.py)

-   社区 CRUD 操作
-   工作人员管理（主管/专员）
-   社区用户管理
-   社区合并/拆分
-   特殊社区（安卡大家庭、黑屋）

### 4. 打卡功能 (checkin.py)

-   打卡规则管理
-   用户打卡记录
-   打卡历史查询
-   Missed 标记机制

### 5. 监督功能 (supervision.py)

-   监督邀请机制
-   监督关系管理
-   监督记录查询

### 6. 短信服务 (sms.py)

-   验证码发送
-   手机号验证

## 数据模型

### 核心实体

-   **User**：用户模型，支持多角色（独居者、监护人、社区工作人员），包含`community_id`和`community_joined_at`字段记录用户所属社区及加入时间
-   **Community**：社区模型，包含社区基本信息和状态
-   **CommunityStaff**：社区工作人员模型
-   **CheckinRule**：打卡规则模型
-   **CheckinRecord**：打卡记录模型

### 关系设计

-   用户与社区：一对多关系（每个用户只属于一个社区）
-   社区与工作人员：一对多关系
-   用户与打卡记录：一对多关系
-   监督关系：用户之间的多对多关系

## 常见问题

### 1. 环境变量未设置

确保在启动应用前设置 `ENV_TYPE` 环境变量：

```bash
export ENV_TYPE=function  # 开发环境
export ENV_TYPE=unit      # 测试环境
export ENV_TYPE=uat       # UAT 环境
export ENV_TYPE=prod      # 生产环境
```

### 2. 数据库迁移失败

检查数据库连接配置，确保数据库服务正常运行：

```bash
# 检查迁移状态
cd src
alembic current
alembic history
```

### 3. 测试失败

确保虚拟环境正确激活，依赖已安装：

```bash
make setup
make clean
make ut
```

## 开发工具

### 推荐的 IDE 配置

-   **VS Code**：安装 Python 扩展，配置虚拟环境
-   **PyCharm**：配置项目解释器为 `venv_py312/bin/python`

### 调试配置

项目支持 Flask 调试模式，通过 `DEBUG` 配置项控制。

### 日志管理

-   应用日志：`logs/` 目录
-   迁移日志：`logs/migration_*.log`
-   测试日志：控制台输出

## 部署说明

### 开发环境

使用 `localrun.sh` 脚本启动，自动处理数据库迁移。

### 生产环境

使用 Docker 容器化部署，支持多环境配置。

### 监控和日志

-   应用监控：通过日志文件监控
-   性能监控：建议集成 APM 工具
-   错误追踪：通过日志和错误报告机制

## 联系方式

如有问题，请查看项目文档或联系开发团队。
