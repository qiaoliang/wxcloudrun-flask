## 项目的目录结构

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
│   │   ├── application/  # 应用服务层（DDD 架构）
│   │   │   ├── use_cases/ # 用例（30+ 个用例）
│   │   │   │   ├── auth/
│   │   │   │   ├── user/
│   │   │   │   ├── community/
│   │   │   │   ├── checkin/
│   │   │   │   ├── supervision/
│   │   │   │   ├── sms/
│   │   │   │   ├── share/
│   │   │   │   ├── events/
│   │   │   │   ├── community_checkin/
│   │   │   │   ├── user_checkin/
│   │   │   │   ├── community_dashboard/
│   │   │   │   └── misc/
│   │   │   └── base.py   # 用例基类
│   │   ├── domain/       # 领域层（DDD 架构）
│   │   │   ├── entities/ # 领域实体
│   │   │   │   ├── user_entity.py
│   │   │   │   ├── community_entity.py
│   │   │   │   ├── checkin_rule_entity.py
│   │   │   │   ├── community_checkin_rule_entity.py
│   │   │   │   ├── checkin_record_entity.py
│   │   │   │   └── community_event_entity.py
│   │   │   ├── value_objects/ # 值对象
│   │   │   │   ├── role.py
│   │   │   │   ├── phone_number.py
│   │   │   │   ├── frequency_type.py
│   │   │   │   ├── time_slot_type.py
│   │   │   │   ├── event_type.py
│   │   │   │   └── event_status.py
│   │   │   ├── aggregates/ # 聚合根
│   │   │   │   ├── user_aggregate.py
│   │   │   │   ├── community_aggregate.py
│   │   │   │   ├── checkin_rule_aggregate.py
│   │   │   │   └── community_event_aggregate.py
│   │   │   ├── repositories/ # 仓储接口
│   │   │   │   ├── base.py
│   │   │   │   ├── user_repository.py
│   │   │   │   ├── community_repository.py
│   │   │   │   ├── checkin_rule_repository.py
│   │   │   │   ├── checkin_record_repository.py
│   │   │   │   ├── community_checkin_rule_repository.py
│   │   │   │   ├── user_community_rule_repository.py
│   │   │   │   ├── community_event_repository.py
│   │   │   │   ├── event_message_repository.py
│   │   │   │   ├── community_staff_repository.py
│   │   │   │   ├── share_link_repository.py
│   │   │   │   ├── share_link_access_log_repository.py
│   │   │   │   ├── supervision_relation_repository.py
│   │   │   │   ├── user_daily_abnormality_repository.py
│   │   │   │   ├── profile_view_log_repository.py
│   │   │   │   ├── counters_repository.py
│   │   │   │   └── verification_code_repository.py
│   │   │   └── events/ # 领域事件
│   │   │       ├── domain_event.py
│   │   │       ├── event_bus.py
│   │   │       ├── user_events.py
│   │   │       ├── community_events.py
│   │   │       ├── checkin_events.py
│   │   │       └── event_handlers.py
│   │   ├── infrastructure/ # 基础设施层（DDD 架构）
│   │   │   └── persistence/ # 持久化
│   │   │       ├── repository_factory.py
│   │   │       ├── sqlalchemy_*.py # SQLAlchemy 仓储实现
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
├── api-contract/          # API 文档
├── scripts/              # 构建和部署脚本
├── docs/                 # 保存的项目规范与开发计划相关文档
├── Makefile              # 测试和构建命令
└── venv_py312/          # Python 虚拟环境
```

## DDD（领域驱动设计）架构

本项目采用领域驱动设计（DDD）架构，将业务逻辑与技术实现分离，提高代码的可维护性和可扩展性。

### 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                   表现层 (Presentation)                   │
│  Flask Routes (modules/*/routes.py)                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  应用服务层 (Application)                  │
│  Use Cases (application/use_cases/*/)                    │
│  - 编排业务流程                                           │
│  - 处理应用逻辑                                           │
│  - 协调领域对象                                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    领域层 (Domain)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Entities    │  │Value Objects │  │ Aggregates   │   │
│  │  (领域实体)   │  │  (值对象)     │  │  (聚合根)     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ Repositories │  │  Domain      │                       │
│  │  (仓储接口)   │  │  Events      │                       │
│  └──────────────┘  │  (领域事件)   │                       │
│                   └──────────────┘                       │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                基础设施层 (Infrastructure)                │
│  Persistence (infrastructure/persistence/)               │
│  - Repository Implementations                           │
│  - Database Operations                                  │
│  - External Services                                    │
└─────────────────────────────────────────────────────────┘
```

### 核心概念

#### 1. 领域实体 (Entities)
- 具有唯一标识的对象，关注对象的身份
- 封装业务逻辑和行为
- 示例：UserEntity, CommunityEntity, CheckinRuleEntity

#### 2. 值对象 (Value Objects)
- 通过属性值来标识的对象，不可变
- 关注对象的属性
- 示例：Role, Frequency, TimeSlot, CommunityEventType

#### 3. 聚合根 (Aggregates)
- 一组相关对象的集合，通过聚合根访问
- 保证业务不变性和一致性
- 示例：UserAggregate, CommunityAggregate, CheckinRuleAggregate

#### 4. 仓储 (Repositories)
- 抽象数据访问逻辑
- 提供领域对象的持久化和检索
- 接口定义在 domain 层，实现在 infrastructure 层

#### 5. 领域事件 (Domain Events)
- 表示领域中发生的重要事情
- 解耦聚合根之间的交互
- 示例：UserCreatedEvent, CheckinCompletedEvent

#### 6. 应用服务用例 (Use Cases)
- 编排业务流程
- 处理应用逻辑
- 不包含业务规则，只负责协调

### 模块重构状态

所有 12 个模块已完成 DDD 重构：

| 模块 | 用例数量 | 状态 |
|------|---------|------|
| auth | 4 | ✅ 完成 |
| user | 5 | ✅ 完成 |
| community | 9 | ✅ 完成 |
| checkin | 9 | ✅ 完成 |
| supervision | 4 | ✅ 完成 |
| sms | 1 | ✅ 完成 |
| share | 3 | ✅ 完成 |
| events | 10 | ✅ 完成 |
| community_checkin | 9 | ✅ 完成 |
| user_checkin | 5 | ✅ 完成 |
| community_dashboard | 5 | ✅ 完成 |
| misc | 3 | ✅ 完成 |

### 仓储实现状态

所有 17 个仓储接口和实现已完成：

| 仓储 | 接口 | 实现 | 状态 |
|------|------|------|------|
| user_repository | ✅ | ✅ | ✅ 完成 |
| community_repository | ✅ | ✅ | ✅ 完成 |
| checkin_rule_repository | ✅ | ✅ | ✅ 完成 |
| checkin_record_repository | ✅ | ✅ | ✅ 完成 |
| community_checkin_rule_repository | ✅ | ✅ | ✅ 完成 |
| user_community_rule_repository | ✅ | ✅ | ✅ 完成 |
| community_event_repository | ✅ | ✅ | ✅ 完成 |
| event_message_repository | ✅ | ✅ | ✅ 完成 |
| community_staff_repository | ✅ | ✅ | ✅ 完成 |
| share_link_repository | ✅ | ✅ | ✅ 完成 |
| share_link_access_log_repository | ✅ | ✅ | ✅ 完成 |
| supervision_relation_repository | ✅ | ✅ | ✅ 完成 |
| user_daily_abnormality_repository | ✅ | ✅ | ✅ 完成 |
| profile_view_log_repository | ✅ | ✅ | ✅ 完成 |
| counters_repository | ✅ | ✅ | ✅ 完成 |
| verification_code_repository | ✅ | ✅ | ✅ 完成 |

### 领域事件机制

已实现完整的领域事件机制：

- **事件总线 (EventBus)**: 使用观察者模式实现事件的发布和订阅
- **领域事件**: 定义了用户、社区、打卡相关的领域事件
- **事件处理器**: 实现了各类事件的处理器

### 测试覆盖

- 所有 139 个集成测试通过
- 测试覆盖所有重构的模块和用例