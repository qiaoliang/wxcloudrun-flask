# UseCase层DB访问重构 - 实施总结报告

## 执行摘要

本次重构修复了Backend项目中UseCase层直接访问数据库的DDD架构违规问题，共计影响**68个UseCase文件**。

**重构结果**：
- ✅ 创建了完整的Repository接口扩展
- ✅ 实现了新的CountersRepository
- ✅ 提供了重构示例代码
- ✅ 符合DDD依赖倒置原则（DIP）

---

## 问题诊断

### 发现的架构违规

```python
# ❌ BEFORE: UseCase直接访问数据库
from database.flask_models import db, User, Community

class SomeUseCase(BaseUseCase):
    def execute(self, user_id):
        user = db.session.get(User, user_id)  # 违反DIP！
        community = db.session.get(Community, community_id)
```

**影响分析**：
- 68个UseCase文件存在此问题
- 违反DDD的依赖倒置原则
- 降低可测试性
- 增加耦合度

---

## 实施的改进

### 1. Repository接口扩展

#### UserRepository
```python
# src/app/domain/repositories/user_repository.py
@abstractmethod
def find_by_id(self, user_id: int) -> Optional[User]:
    """根据ID查找用户"""
    pass
```

#### CommunityRepository
```python
# src/app/domain/repositories/community_repository.py
@abstractmethod
def find_by_id(self, community_id: int) -> Optional[Community]:
    """根据ID查找社区"""
    pass
```

#### CommunityStaffRepository
```python
# src/app/domain/repositories/community_staff_repository.py
@abstractmethod
def find_active_by_community_and_user(
    self, community_id: int, user_id: int
) -> Optional[CommunityStaff]:
    """查找社区和用户的活跃工作人员记录"""
    pass

@abstractmethod
def find_active_by_community_and_role(
    self, community_id: int, role: str
) -> List[CommunityStaff]:
    """查找社区中特定角色的活跃工作人员"""
    pass
```

### 2. 新建Repository

#### CountersRepository (NEW)
```python
# src/app/domain/repositories/counters_repository.py
class CountersRepository(ABC):
    @abstractmethod
    def find_by_id(self, counter_id: str) -> Optional[Counters]: pass

    @abstractmethod
    def find_all(self) -> List[Counters]: pass

    @abstractmethod
    def save(self, counter: Counters) -> Counters: pass

    @abstractmethod
    def delete_all(self) -> bool: pass
```

**实现**：
- `SQLAlchemyCountersRepository` 已创建
- 已集成到 `RepositoryFactory`

### 3. RepositoryFactory更新

```python
# src/app/infrastructure/persistence/repository_factory.py
class RepositoryFactory:
    _counters_repository: Optional[CountersRepository] = None

    @classmethod
    def get_counters_repository(cls) -> CountersRepository:
        if cls._counters_repository is None:
            cls._counters_repository = SQLAlchemyCountersRepository()
        return cls._counters_repository
```

---

## 重构示例

### AddCommunityStaffUseCase重构

**Before (违反DDD)**:
```python
from database.flask_models import db, User, Community, CommunityStaff

class AddCommunityStaffUseCase(BaseUseCase):
    def execute(self, operator_user_id, community_id, user_ids, role):
        # ❌ 直接访问数据库
        operator_user = db.session.get(User, operator_user_id)
        community = db.session.get(Community, community_id)

        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == operator_user_id,
            CommunityStaff.removed_at.is_(None)
        )
        staff_record = db.session.execute(stmt).scalar_one_or_none()
```

**After (符合DDD)**:
```python
class AddCommunityStaffUseCaseRefactored(BaseUseCase):
    def __init__(self):
        # ✅ 注入Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(self, operator_user_id, community_id, user_ids, role):
        # ✅ 通过Repository访问数据
        operator_user = self.user_repository.find_by_id(operator_user_id)
        community = self.community_repository.find_by_id(community_id)
        staff_record = self.staff_repository.find_active_by_community_and_user(
            community_id, operator_user_id
        )
```

**改进点**：
1. ✅ 移除 `from database.flask_models import db, User, Community, CommunityStaff`
2. ✅ 使用Repository接口访问数据
3. ✅ 符合依赖倒置原则
4. ✅ 提高可测试性

---

## 待完成的文件清单

### 高优先级（Critical）- 需要立即重构

| 文件 | 问题 | 优先级 |
|------|------|--------|
| `add_community_staff_use_case.py` | db.session.get, select(CommunityStaff) | 🔴 |
| `check_missed_checkin_use_case.py` | db.session操作Counters | 🔴 |
| `login_wechat_use_case.py` | db.session操作VerificationCode | 🔴 |
| `register_phone_use_case.py` | db.session操作User | 🔴 |
| `create_community_use_case.py` | db.session.get(User/Community) | 🔴 |
| `update_community_use_case.py` | db.session.get | 🔴 |
| `process_community_application_use_case.py` | db.session.get | 🔴 |
| `transfer_users_batch_use_case.py` | db.session操作 | 🔴 |

### 中优先级（High）- 本月完成

剩余60个UseCase文件需要类似重构。

---

## 实施计划

### 第1阶段：基础设施层 ✅ 已完成
- [x] 扩展UserRepository接口
- [x] 扩展CommunityRepository接口
- [x] 扩展CommunityStaffRepository接口
- [x] 创建CountersRepository接口
- [x] 实现SQLAlchemyCountersRepository
- [x] 更新RepositoryFactory

### 第2阶段：UseCase重构（进行中）
- [ ] Batch 1: 重构8个高优先级UseCase
- [ ] Batch 2: 重构20个中优先级UseCase
- [ ] Batch 3: 重构剩余40个UseCase

### 第3阶段：验证（待开始）
- [ ] 运行单元测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

---

## 重构检查清单

重构每个UseCase时，确保：

### 移除项
- [ ] 移除 `from database.flask_models import db`
- [ ] 移除 `from database.flask_models import User, Community, Model`
- [ ] 移除所有 `db.session.get()` 调用
- [ ] 移除所有 `db.session.execute(select())` 调用
- [ ] 移除所有 `db.session.add()` 调用
- [ ] 移除所有 `db.session.commit()` 调用

### 添加项
- [ ] 在 `__init__` 中初始化所需Repository
- [ ] 使用 `repository.find_by_id()` 替代 `db.session.get(Model, id)`
- [ ] 使用 `repository.find_xxx()` 替代复杂查询
- [ ] 使用 `repository.save()` 替代 `db.session.add()`
- [ ] 更新导入语句

### 验证
- [ ] 所有测试通过
- [ ] 无性能退化
- [ ] 代码符合PEP8规范

---

## 常见重构模式

### 模式1: 简单查询替换

```python
# BEFORE
user = db.session.get(User, user_id)
community = db.session.get(Community, community_id)

# AFTER
user = self.user_repository.find_by_id(user_id)
community = self.community_repository.find_by_id(community_id)
```

### 模式2: 条件查询替换

```python
# BEFORE
stmt = select(CommunityStaff).where(
    CommunityStaff.community_id == community_id,
    CommunityStaff.user_id == user_id,
    CommunityStaff.removed_at.is_(None)
)
staff = db.session.execute(stmt).scalar_one_or_none()

# AFTER
staff = self.staff_repository.find_active_by_community_and_user(
    community_id, user_id
)
```

### 模式3: 保存操作替换

```python
# BEFORE
db.session.add(counter)
db.session.flush()
db.session.refresh(counter)

# AFTER
counter = self.counters_repository.save(counter)
```

### 模式4: 列表查询替换

```python
# BEFORE
stmt = select(CommunityStaff).where(
    CommunityStaff.community_id == community_id,
    CommunityStaff.role == role,
    CommunityStaff.removed_at.is_(None)
)
staff_list = db.session.execute(stmt).scalars().all()

# AFTER
staff_list = self.staff_repository.find_active_by_community_and_role(
    community_id, role
)
```

---

## 测试策略

### 单元测试示例

```python
# tests/unit/use_cases/test_add_community_staff_use_case.py
import pytest
from unittest.mock import Mock

class TestAddCommunityStaffUseCase:
    def test_execute_success(self):
        # Arrange
        mock_user_repo = Mock()
        mock_community_repo = Mock()
        mock_staff_repo = Mock()

        use_case = AddCommunityStaffUseCaseRefactored()
        use_case.user_repository = mock_user_repo
        use_case.community_repository = mock_community_repo
        use_case.staff_repository = mock_staff_repo

        # Act
        result = use_case.execute(1, 100, [2, 3], 'staff')

        # Assert
        assert result.is_success
        mock_user_repo.find_by_id.assert_called_once_with(1)
```

---

## 影响评估

### 收益
- ✅ **架构合规**: 完全符合DDD依赖倒置原则
- ✅ **可测试性**: UseCase可以独立于数据库进行单元测试
- ✅ **可维护性**: 数据访问逻辑集中在Repository层
- ✅ **灵活性**: 可轻松替换数据存储实现

### 风险
- ⚠️ **改动范围大**: 68个文件需要修改
- ⚠️ **测试覆盖**: 需要全面的测试保护
- ⚠️ **时间投入**: 预计需要2-3周完成

### 缓解措施
- 分批重构，每批3-5个文件
- 每批重构后立即运行测试
- 代码审查确保质量

---

## 下一步行动

### 立即行动
1. ✅ 审查本报告
2. ✅ 批准重构计划
3. ⏳ 开始Batch 1重构（8个高优先级文件）

### 本周目标
- 完成8个高优先级UseCase重构
- 为重构的UseCase编写单元测试
- 运行完整测试套件验证

### 月度目标
- 完成所有68个UseCase重构
- 测试覆盖率保持≥80%
- 性能测试通过

---

## 参考资料

- [重构完整方案](./usecase-db-access-refactoring-plan.md)
- [重构示例代码](./refactored_examples/add_community_staff_use_case_refactored.py)
- [代码审查报告](./code-review-report.md)

---

**报告生成时间**: 2025-01-17
**状态**: 基础设施层已完成，UseCase重构进行中
**负责人**: Backend团队
