# wxcloudrun Service 文件重构计划

## 文档目的

本文档详细说明如何系统地删除和重构 `src/wxcloudrun/` 目录中破坏 DDD 设计原则的 Service 文件。

## 背景分析

### 当前问题

`src/wxcloudrun/` 目录下的 Service 文件存在以下问题：

1. **违反 DDD 分层架构**：Service 层被直接从 UseCase 和路由层调用
2. **职责混乱**：同时包含数据访问、业务逻辑、应用逻辑
3. **与 DDD 架构冲突**：与新的 UseCase、Repository、Domain Service 层功能重叠
4. **维护困难**：新旧代码交织，难以理解和维护

### 文件清单

| 文件名 | 职责 | 代码行数（估算） |
|--------|------|-----------------|
| `sms_service.py` | 短信发送 | ~80 |
| `checkin_rule_service.py` | 打卡规则CRUD | ~300 |
| `checkin_record_service.py` | 打卡记录服务 | ~200 |
| `community_service.py` | 社区管理 | ~800 |
| `community_checkin_rule_service.py` | 社区打卡规则 | ~400 |
| `community_dashboard_service.py` | 社区看板统计 | ~300 |
| `community_event_service.py` | 社区事件管理 | ~250 |
| `community_staff_service.py` | 社区工作人员 | ~200 |
| `user_service.py` | 用户管理 | ~600 |
| `user_checkin_rule_service.py` | 用户打卡规则 | ~150 |
| `user_transfer_service.py` | 用户批量转移 | ~200 |
| `medical_history_service.py` | 病历管理 | ~300 |
| `background_tasks.py` | 后台任务 | ~100 |

## 依赖分析

### Service 文件引用统计

#### 被 UseCase 引用

| Service 文件 | 引用该 Service 的 UseCase 数量 |
|-------------|------------------------------|
| `community_dashboard_service.py` | 5 |
| `community_checkin_rule_service.py` | 7 |
| `sms_service.py` | 1 |
| `community_service.py` | 2 |
| `user_service.py` | 0 (间接) |

#### 被路由层引用

| Service 文件 | 引用该 Service 的路由模块 |
|-------------|------------------------|
| `community_service.py` | 16 处 |
| `user_service.py` | 9 处 |
| `checkin_rule_service.py` | 5 处 |

#### 被测试引用

几乎所有 Service 文件都被大量测试引用，特别是：
- `checkin_rule_service.py` - 20+ 测试文件
- `community_service.py` - 15+ 测试文件
- `community_staff_service.py` - 10+ 测试文件

## 重构策略

### 按优先级分类

#### 🔴 Phase 1: 快速胜利（1-2天）

**目标**：删除简单、独立、影响范围小的 Service

##### 1.1 `sms_service.py`

**当前状态**：
- ✅ 已被 `SendVerificationCodeUseCase` 替代
- 仅 1 个引用处

**迁移方案**：

```python
# 当前：src/app/application/use_cases/sms/send_verification_code_use_case.py
from wxcloudrun.sms_service import create_sms_provider, generate_code

# 迁移方案1：内联到 UseCase
class SendVerificationCodeUseCase(BaseUseCase):
    def execute(self, phone: str, purpose: str) -> UseCaseResult:
        # 直接在这里实现 SMS 逻辑
        import random
        code = ''.join(random.choices('0123456789', k=6))
        # ...
```

```python
# 迁移方案2：移至基础设施层
# src/app/infrastructure/sms/sms_provider.py
from abc import ABC, abstractmethod

class SMSProvider(ABC):
    @abstractmethod
    def send(self, phone: str, content: str) -> bool:
        pass

class MockSMSProvider(SMSProvider):
    def send(self, phone: str, content: str) -> bool:
        print(f"[MockSMS] to {phone}: {content}")
        return True

# src/app/application/use_cases/sms/send_verification_code_use_case.py
from app.infrastructure.sms.sms_provider import MockSMSProvider
```

**推荐**：方案2，符合 DDD 基础设施层模式

**影响范围**：
- 修改：1 个 UseCase
- 测试：需要更新导入

---

##### 1.2 `community_dashboard_service.py`

**当前状态**：
- 被 5 个 UseCase 引用
- 主要是数据聚合逻辑

**问题**：UseCase 不应该通过 Service 访问数据，应该直接使用 Repository

**迁移方案**：

```python
# 当前错误模式
# UseCase → Service → Repository
class GetCommunityStatsUseCase(BaseUseCase):
    def execute(self, community_id, user_id):
        from wxcloudrun.community_dashboard_service import CommunityDashboardService
        return CommunityDashboardService.get_community_stats(community_id)
```

```python
# 正确模式
# UseCase → Repository
class GetCommunityStatsUseCase(BaseUseCase):
    def __init__(self):
        self.community_repo = RepositoryFactory.get_community_repository()
        self.user_repo = RepositoryFactory.get_user_repository()
        self.checkin_record_repo = RepositoryFactory.get_checkin_record_repository()

    def execute(self, community_id, user_id):
        # 直接使用 Repository 获取数据
        community = self.community_repo.find_by_id(community_id)
        stats = self.checkin_record_repo.get_stats_by_community(community_id)
        # 聚合逻辑在 UseCase 中
        return UseCaseResult(status=UseCaseStatus.SUCCESS, data={...})
```

**对于复杂聚合逻辑**，创建 Domain Service：

```python
# src/app/domain/services/community_statistics_service.py
class CommunityStatisticsService:
    """社区统计领域服务 - 处理复杂的统计计算逻辑"""

    def calculate_community_stats(self, community: Community) -> CommunityStats:
        # 复杂的业务计算
        pass
```

**影响范围**：
- 修改：5 个 UseCase
- 可能需要：增强 Repository 能力
- 测试：更新相关测试

---

#### 🟡 Phase 2: 核心重构（1-2周）

**目标**：重构核心业务 Service，建立正确的 DDD 分层

##### 2.1 `community_checkin_rule_service.py`

**当前状态**：
- 被 7 个 UseCase 引用
- 包含 CRUD 和业务逻辑

**重构方案**：

```python
# 拆分策略：

# 1. CRUD 操作 → Repository
# src/app/infrastructure/persistence/repositories/community_checkin_rule_repository.py
class CommunityCheckinRuleRepository(Repository[CommunityCheckinRule]):
    def find_by_community_id(self, community_id: int) -> List[CommunityCheckinRule]:
        pass

    def find_by_id(self, rule_id: int) -> Optional[CommunityCheckinRule]:
        pass

    def save(self, rule: CommunityCheckinRule) -> CommunityCheckinRule:
        pass

# 2. 业务规则验证 → Entity 或 Domain Service
# src/app/domain/entities/community_checkin_rule_entity.py
class CommunityCheckinRuleEntity:
    def validate_time_slot(self, time_slot_type: int, custom_time: str) -> bool:
        """验证时间段配置是否有效"""
        pass

    def can_be_activated(self) -> tuple[bool, str]:
        """检查规则是否可以激活"""
        if not self.rule_name:
            return False, "规则名称不能为空"
        # ...

# 3. UseCase 编排流程
class CreateCommunityCheckinRuleUseCase(BaseUseCase):
    def execute(self, data: dict, community_id: int, creator_id: int):
        # 使用 Repository
        repo = RepositoryFactory.get_community_checkin_rule_repository()

        # 使用 Entity 进行业务验证
        rule_entity = CommunityCheckinRuleEntity(rule_data)
        can_activate, reason = rule_entity.can_be_activated()
        if not can_activate:
            return UseCaseResult(status=UseCaseStatus.VALIDATION_ERROR, message=reason)

        # 保存
        saved_rule = repo.save(rule_entity.user)
        return UseCaseResult(status=UseCaseStatus.SUCCESS, data=saved_rule)
```

**迁移步骤**：

1. 创建 `CommunityCheckinRuleRepository`（如不存在）
2. 将 Service 中的数据访问逻辑移到 Repository
3. 将业务验证逻辑移到 Entity 或 Domain Service
4. 更新 UseCase 直接使用 Repository
5. 运行测试验证
6. 删除 Service 文件

---

##### 2.2 `checkin_rule_service.py`

**当前状态**：
- 被路由和测试大量引用
- 混合了 CRUD 和业务逻辑

**重构方案**：

与 `community_checkin_rule_service.py` 类似，按职责拆分：

| 当前方法 | 迁移目标 | 原因 |
|---------|---------|------|
| `query_rules_by_user_id` | Repository | 数据查询 |
| `query_rule_by_id` | Repository | 数据查询 |
| `create_rule` | UseCase + Repository | 应用逻辑 + 数据持久化 |
| `delete_rule` | UseCase + Repository | 应用逻辑 + 数据持久化 |
| `calculate_planned_time` | Domain Service 或 Entity | 复杂业务逻辑 |
| `should_checkin_today` | Entity 方法 | 业务规则 |
| `get_today_checkin_records` | Repository 方法 | 数据查询 |

---

#### 🟢 Phase 3: 深度重构（长期）

**目标**：重构大型、复杂、高耦合的 Service

##### 3.1 `community_service.py`

**当前状态**：
- ~800 行代码
- 16 处引用
- 职责过多

**重构方案**：

**拆分策略**：

```
community_service.py (800行)
    ↓
┌─────────────────────────────────────┐
│ 1. CommunityRepository              │
│    - query_community_by_id()        │
│    - find_by_name()                 │
│    - save()                         │
├─────────────────────────────────────┤
│ 2. CommunityDomainService           │
│    - assign_user_to_community()     │
│    - calculate_community_stats()    │
├─────────────────────────────────────┤
│ 3. Multiple UseCases                │
│    - CreateCommunityUseCase         │
│    - UpdateCommunityUseCase         │
│    - DeleteCommunityUseCase         │
│    - AssignUserToCommunityUseCase   │
└─────────────────────────────────────┘
```

---

##### 3.2 `user_service.py`

**重构方案**：类似 `community_service.py`

---

##### 3.3 其他 Service

以下 Service 暂时保留，后续根据业务需求重构：

- `community_event_service.py`
- `community_staff_service.py`
- `user_checkin_rule_service.py`
- `user_transfer_service.py`
- `medical_history_service.py`
- `background_tasks.py`

## DDD 正确分层架构

```
┌───────────────────────────────────────────────┐
│          Presentation Layer                    │
│       (routes.py, controllers.py)              │
│  - HTTP 请求/响应处理                           │
│  - 参数验证                                    │
│  - 调用 UseCase                                │
└───────────────────┬───────────────────────────┘
                    │
                    ↓
┌───────────────────────────────────────────────┐
│       Application Layer (UseCases)             │
│  - 编排业务流程                                 │
│  - 调用 Domain Service 和 Repository           │
│  - 事务边界控制                                 │
│  - 返回 UseCaseResult                          │
└───────────────────┬───────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
┌───────────────────┐  ┌──────────────────┐
│  Domain Service   │  │   Repository     │
│  (无状态业务逻辑)  │  │  (数据访问)       │
│  - 复杂计算        │  │  - CRUD          │
│  - 跨聚合操作      │  │  - 查询          │
└─────────┬─────────┘  └──────────────────┘
          │
          ↓
┌───────────────────────────────────────────────┐
│            Domain Layer                        │
│  ┌─────────────────────────────────────┐     │
│  │  Entity (实体)                       │     │
│  │  - 核心业务逻辑                      │     │
│  │  - 不变式保护                        │     │
│  ├─────────────────────────────────────┤     │
│  │  Value Object (值对象)               │     │
│  │  - 不可变值                          │     │
│  ├─────────────────────────────────────┤     │
│  │  Aggregate (聚合根)                  │     │
│  │  - 一致性边界                        │     │
│  ├─────────────────────────────────────┤     │
│  │  Domain Event (领域事件)             │     │
│  │  - 领域状态变化通知                  │     │
│  └─────────────────────────────────────┘     │
└───────────────────────────────────────────────┘
                    │
                    ↓
┌───────────────────────────────────────────────┐
│       Infrastructure Layer                     │
│  - Repository 实现 (SQLAlchemy)                │
│  - 外部服务适配器 (SMS, 微信API等)             │
│  - 数据库配置                                  │
└───────────────────────────────────────────────┘
```

## 重构检查清单

### 开始重构前

- [ ] 确认 Service 的所有引用位置
- [ ] 编写或更新相关测试
- [ ] 创建必要的 Repository（如不存在）
- [ ] 准备回滚计划

### 重构过程中

- [ ] 一次只重构一个 Service
- [ ] 保持测试持续通过
- [ ] 提交小步快跑的 commits
- [ ] 更新相关文档

### 重构完成后

- [ ] 所有测试通过
- [ ] 删除旧的 Service 文件
- [ ] 更新导入语句
- [ ] 代码审查
- [ ] 更新架构文档

## 实施时间表

| Phase | 任务 | 预计时间 | 负责人 | 状态 |
|-------|------|---------|--------|------|
| Phase 1.1 | 重构 sms_service.py | 2小时 | 待定 | ⏳ 待开始 |
| Phase 1.2 | 重构 community_dashboard_service.py | 1天 | 待定 | ⏳ 待开始 |
| Phase 2.1 | 重构 community_checkin_rule_service.py | 3天 | 待定 | ⏳ 待开始 |
| Phase 2.2 | 重构 checkin_rule_service.py | 3天 | 待定 | ⏳ 待开始 |
| Phase 3.1 | 重构 community_service.py | 1周 | 待定 | ⏳ 待开始 |
| Phase 3.2 | 重构 user_service.py | 1周 | 待定 | ⏳ 待开始 |

## 风险与缓解措施

### 风险1：测试大规模失败

**缓解措施**：
- 一次只重构一个 Service
- 先运行测试，建立基准
- 逐步迁移，保持测试通过

### 风险2：业务逻辑遗漏

**缓解措施**：
- 详细对比 Service 和 UseCase 的逻辑
- 代码审查
- 完整的回归测试

### 风险3：性能下降

**缓解措施**：
- 性能基准测试
- 优化 Repository 查询
- 使用缓存（必要时）

## 附录

### A. 相关文档

- [DDD-MIGRATION-PLAN.md](./DDD-MIGRATION-PLAN.md) - DDD 迁移总计划
- [code-style-guide.md](./code-style-guide.md) - 代码风格指南
- [integration-test-writing-guide.md](./integration-test-writing-guide.md) - 集成测试指南

### B. Repository 模式参考

```python
# src/app/infrastructure/persistence/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Type, List, Optional

T = TypeVar('T')

class Repository(ABC):
    """Repository 基类"""

    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        pass
```

### C. Domain Service 模式参考

```python
# src/app/domain/services/community_statistics_service.py
from typing import Dict, Any
from app.domain.entities.community_entity import CommunityEntity

class CommunityStatisticsService:
    """社区统计领域服务"""

    def calculate_community_stats(
        self,
        community: CommunityEntity,
        checkin_records: List,
        users: List
    ) -> Dict[str, Any]:
        """
        计算社区统计数据

        这是一个无状态的领域服务，处理跨聚合的复杂计算
        """
        total_users = len(users)
        active_users = len([u for u in users if u.is_active()])

        return {
            'total_users': total_users,
            'active_users': active_users,
            'activation_rate': active_users / total_users if total_users > 0 else 0
        }
```

---

**文档版本**: 1.0
**创建日期**: 2026-01-15
**最后更新**: 2026-01-15
**维护者**: 开发团队
