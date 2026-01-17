# UseCase层DB访问重构方案

## 问题分析

### 当前状态
- **68个UseCase文件**直接导入`database.flask_models`
- 违反DDD的**依赖倒置原则（DIP）**
- UseCase层直接依赖基础设施层的实现细节

### 违反的DDD原则
```
正确的依赖方向：
UseCase → Repository(Interface) ← Repository(Implementation)

当前的错误依赖：
UseCase → DB Models (直接访问)
```

## 重构策略

### 阶段1：扩展Repository接口（优先级：CRITICAL）

#### 1.1 UserRepository扩展
```python
# 需要添加的方法
def find_by_id(user_id: int) -> Optional[User]:
    """根据ID查找用户（替代db.session.get(User, id)）"""
    pass
```

#### 1.2 CommunityRepository扩展
```python
def find_by_id(community_id: int) -> Optional[Community]:
    """根据ID查找社区"""
    pass
```

#### 1.3 CommunityStaffRepository扩展
```python
def find_active_by_community_and_user(
    community_id: int,
    user_id: int
) -> Optional[CommunityStaff]:
    """查找社区和用户的活跃工作人员记录"""

def find_active_by_community_and_role(
    community_id: int,
    role: str
) -> List[CommunityStaff]:
    """查找社区中特定角色的活跃工作人员"""
```

#### 1.4 CountersRepository（新建）
```python
class CountersRepository(ABC):
    """计数器仓储接口"""

    @abstractmethod
    def find_by_id(self, counter_id: str) -> Optional[Counters]:
        pass

    @abstractmethod
    def find_all(self) -> List[Counters]:
        pass

    @abstractmethod
    def save(self, counter: Counters) -> Counters:
        pass

    @abstractmethod
    def delete_all(self) -> bool:
        pass
```

#### 1.5 VerificationCodeRepository扩展
```python
def find_by_phone_and_code(
    phone: str,
    code: str
) -> Optional[VerificationCode]:
    """查找指定手机号和验证码的记录"""

def save(self, verification_code: VerificationCode) -> VerificationCode:
    """保存验证码记录"""
```

### 阶段2：实现Repository（优先级：CRITICAL）

#### 2.1 SQLAlchemyUserRepository扩展
```python
# src/app/infrastructure/persistence/sqlalchemy_user_repository.py

def find_by_id(self, user_id: int) -> Optional[User]:
    """根据ID查找用户"""
    stmt = select(User).where(User.user_id == user_id)
    return self._session.execute(stmt).scalar_one_or_none()
```

#### 2.2 SQLAlchemyCommunityRepository扩展
```python
# src/app/infrastructure/persistence/sqlalchemy_community_repository.py

def find_by_id(self, community_id: int) -> Optional[Community]:
    """根据ID查找社区"""
    stmt = select(Community).where(Community.community_id == community_id)
    return self._session.execute(stmt).scalar_one_or_none()
```

#### 2.3 SQLAlchemyCommunityStaffRepository扩展
```python
# src/app/infrastructure/persistence/sqlalchemy_community_staff_repository.py

def find_active_by_community_and_user(
    self,
    community_id: int,
    user_id: int
) -> Optional[CommunityStaff]:
    """查找社区和用户的活跃工作人员记录"""
    stmt = select(CommunityStaff).where(
        CommunityStaff.community_id == community_id,
        CommunityStaff.user_id == user_id,
        CommunityStaff.removed_at.is_(None)
    )
    return self._session.execute(stmt).scalar_one_or_none()

def find_active_by_community_and_role(
    self,
    community_id: int,
    role: str
) -> List[CommunityStaff]:
    """查找社区中特定角色的活跃工作人员"""
    stmt = select(CommunityStaff).where(
        CommunityStaff.community_id == community_id,
        CommunityStaff.role == role,
        CommunityStaff.removed_at.is_(None)
    )
    return self._session.execute(stmt).scalars().all()
```

#### 2.4 新建SQLAlchemyCountersRepository
```python
# src/app/infrastructure/persistence/sqlalchemy_counters_repository.py

class SQLAlchemyCountersRepository(CountersRepository):
    """计数器仓储实现"""

    def __init__(self):
        self._session = db.session

    def find_by_id(self, counter_id: str) -> Optional[Counters]:
        stmt = select(Counters).where(Counters.id == counter_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_all(self) -> List[Counters]:
        stmt = select(Counters)
        return self._session.execute(stmt).scalars().all()

    def save(self, counter: Counters) -> Counters:
        self._session.add(counter)
        self._session.flush()
        self._session.refresh(counter)
        return counter

    def delete_all(self) -> bool:
        try:
            self._session.execute(delete(Counters))
            self._session.commit()
            return True
        except Exception:
            self._session.rollback()
            return False
```

#### 2.5 SQLAlchemyVerificationCodeRepository扩展
```python
def find_by_phone_and_code(
    self,
    phone: str,
    code: str
) -> Optional[VerificationCode]:
    """查找指定手机号和验证码的记录"""
    stmt = select(VerificationCode).where(
        VerificationCode.phone == phone,
        VerificationCode.code == code
    ).order_by(VerificationCode.created_at.desc())
    return self._session.execute(stmt).scalar_one_or_none()

def save(self, verification_code: VerificationCode) -> VerificationCode:
    """保存验证码记录"""
    self._session.add(verification_code)
    self._session.flush()
    return verification_code
```

### 阶段3：更新RepositoryFactory（优先级：CRITICAL）

```python
# src/app/infrastructure/persistence/repository_factory.py

class RepositoryFactory:
    """仓储工厂"""

    # ... 现有仓储 ...

    _counters_repository: Optional[CountersRepository] = None

    @classmethod
    def get_counters_repository(cls) -> CountersRepository:
        """获取计数器仓储实例"""
        if cls._counters_repository is None:
            cls._counters_repository = SQLAlchemyCountersRepository()
        return cls._counters_repository
```

### 阶段4：重构UseCase文件（优先级：HIGH）

#### 4.1 AddCommunityStaffUseCase重构示例

**Before:**
```python
from database.flask_models import db, User, Community, CommunityStaff

class AddCommunityStaffUseCase(BaseUseCase):
    def execute(self, operator_user_id, community_id, user_ids, role):
        # ❌ 直接访问数据库
        operator_user = db.session.get(User, operator_user_id)
        community = db.session.get(Community, community_id)

        stmt_staff = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == operator_user_id,
            CommunityStaff.removed_at.is_(None)
        )
        staff_record = db.session.execute(stmt_staff).scalar_one_or_none()
```

**After:**
```python
# ✅ 通过Repository访问
class AddCommunityStaffUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(self, operator_user_id, community_id, user_ids, role):
        # ✅ 通过Repository访问
        operator_user = self.user_repository.find_by_id(operator_user_id)
        community = self.community_repository.find_by_id(community_id)
        staff_record = self.staff_repository.find_active_by_community_and_user(
            community_id, operator_user_id
        )
```

#### 4.2 CheckMissedCheckinUseCase重构示例

**Before:**
```python
from database.flask_models import db, Counters

counter = db.session.execute(
    select(Counters).filter_by(id=counter_id)
).scalar_one_or_none()
db.session.add(counter)
db.session.flush()
```

**After:**
```python
self.counters_repository = RepositoryFactory.get_counters_repository()

counter = self.counters_repository.find_by_id(counter_id)
self.counters_repository.save(counter)
```

#### 4.3 LoginWechatUseCase重构示例

**Before:**
```python
from database.flask_models import db, VerificationCode

vc = db.session.execute(
    select(VerificationCode).filter_by(phone=phone, code=code)
).scalar_one_or_none()
db.session.add(vc)
```

**After:**
```python
self.verification_code_repository = RepositoryFactory.get_verification_code_repository()

vc = self.verification_code_repository.find_by_phone_and_code(phone, code)
self.verification_code_repository.save(vc)
```

### 阶段5：批量重构脚本（优先级：MEDIUM）

创建自动化重构脚本：

```bash
#!/bin/bash
# scripts/refactor-usecase-db-access.sh

# 查找所有直接导入db的UseCase
find src/app/application/use_cases -name "*.py" -exec grep -l "from database.flask_models import" {} \;

# 对每个文件进行重构
# 1. 移除 db, Model 导入
# 2. 添加 Repository 初始化
# 3. 替换 db.session.get() 为 repository.find_by_id()
# 4. 替换 db.session.execute(select()) 为 repository.find_xxx()
# 5. 替换 db.session.add() 为 repository.save()
```

## 实施计划

### 第1周：基础设施层
- [ ] 扩展所有Repository接口
- [ ] 实现新的Repository方法
- [ ] 更新RepositoryFactory
- [ ] 为新方法编写单元测试

### 第2-3周：UseCase重构
按优先级分批重构：

**Batch 1 (Critical)：**
- add_community_staff_use_case.py
- check_missed_checkin_use_case.py
- login_wechat_use_case.py
- register_phone_use_case.py

**Batch 2 (High)：**
- create_community_use_case.py
- update_community_use_case.py
- create_community_event_use_case.py
- perform_checkin_use_case.py

**Batch 3 (Medium)：**
- 其余60个UseCase文件

### 第4周：验证和优化
- [ ] 运行所有单元测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

## 验证清单

重构完成后，确保：

- [ ] ✅ UseCase层不再导入`database.flask_models`
- [ ] ✅ UseCase层不再使用`db.session`
- [ ] ✅ 所有数据访问通过Repository接口
- [ ] ✅ 所有测试通过
- [ ] ✅ 无性能退化
- [ ] ✅ 代码覆盖率保持≥80%

## 影响评估

### 风险
- **中等风险**：68个文件需要修改
- **缓解措施**：分批重构，每批都有测试覆盖

### 收益
- ✅ 符合DDD架构原则
- ✅ 提高可测试性（可以Mock Repository）
- ✅ 降低耦合度
- ✅ 便于未来数据源替换

## 完成标准

1. **零直接DB访问**：UseCase层不再有`from database.flask_models import`
2. **完整测试覆盖**：新Repository方法100%测试覆盖
3. **性能无退化**：关键接口性能保持不变
4. **代码审查通过**：所有重构代码通过Code Review
