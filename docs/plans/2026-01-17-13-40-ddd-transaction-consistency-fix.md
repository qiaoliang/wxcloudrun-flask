# DDD 事务一致性和 UseCase 设计修复的实施计划

> 使用命令 `executing-plans`， 实现这个计划。

**Goal:** 修复 DDD 架构下 UseCase 层的事务一致性问题，消除架构违规，确保数据完整性和代码质量。

**Architecture:** 在 UseCase 层统一使用 `with transaction()` 上下文管理器，通过 RepositoryFactory 获取所有 Repository，消除 UseCase 之间的相互调用，创建缺失的 Repository 接口。

**Tech Stack:** Python 3.12, Flask 3.1.2, SQLAlchemy 2.0.16, pytest 7.4.3

---

## 前置条件

### 环境准备
- Python 3.12 已安装
- 虚拟环境已激活: `source venv_py312/bin/activate`
- 依赖已安装: `pip install -r requirements.txt -r requirements-test.txt`
- 测试环境变量已设置: `export ENV_TYPE=unit`

### Git Worktree 创建
```bash
cd /Users/qiaoliang/working/code/safeGuard
git worktree add backend-ddd-fix dev
cd backend-ddd-fix
```

### 验证环境
```bash
# 验证 Python 版本
python --version  # 预期输出: Python 3.12.12

# 验证虚拟环境
which python  # 预期输出指向 venv_py312

# 运行测试确保 baseline
make ut && make it  # 记录当前测试通过数量
```

---

## 任务 1: 创建缺失的 Repository 接口和实现

### 目标
创建 `CommunityApplicationRepository` 和 `AuditLogRepository`，消除 UseCase 中对 `db.session` 的直接访问。

### 涉及文件
- `src/app/domain/repositories/community_application_repository.py` (新建)
- `src/app/domain/repositories/audit_log_repository.py` (新建)
- `src/app/infrastructure/persistence/sqlalchemy_community_application_repository.py` (新建)
- `src/app/infrastructure/persistence/sqlalchemy_audit_log_repository.py` (新建)
- `src/app/infrastructure/persistence/repository_factory.py` (修改)
- `src/app/domain/repositories/__init__.py` (修改)
- `src/app/infrastructure/persistence/__init__.py` (修改)

### 步骤

#### 步骤 1: 创建 CommunityApplicationRepository 接口
**文件**: `src/app/domain/repositories/community_application_repository.py`

```python
"""
社区申请仓储接口
"""
from typing import List, Optional
from abc import ABC, abstractmethod

from database.flask_models import CommunityApplication


class CommunityApplicationRepository(ABC):
    """社区申请仓储接口"""

    @abstractmethod
    def save(self, application: CommunityApplication) -> CommunityApplication:
        """
        保存社区申请

        Args:
            application: 社区申请实体

        Returns:
            CommunityApplication: 保存后的社区申请
        """
        pass

    @abstractmethod
    def find_by_id(self, application_id: int) -> Optional[CommunityApplication]:
        """
        根据ID查找社区申请

        Args:
            application_id: 申请ID

        Returns:
            Optional[CommunityApplication]: 社区申请，不存在返回 None
        """
        pass

    @abstractmethod
    def find_pending_by_user_and_community(
        self, user_id: int, community_id: int
    ) -> Optional[CommunityApplication]:
        """
        查找用户对社区的待审核申请

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            Optional[CommunityApplication]: 待审核申请，不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_community(self, community_id: int, status: Optional[int] = None) -> List[CommunityApplication]:
        """
        查找社区的所有申请

        Args:
            community_id: 社区ID
            status: 申请状态（可选）

        Returns:
            List[CommunityApplication]: 申请列表
        """
        pass

    @abstractmethod
    def update_status(
        self,
        application_id: int,
        status: int,
        processor_id: int,
        rejection_reason: Optional[str] = None
    ) -> Optional[CommunityApplication]:
        """
        更新申请状态

        Args:
            application_id: 申请ID
            status: 新状态
            processor_id: 处理者ID
            rejection_reason: 拒绝理由（可选）

        Returns:
            Optional[CommunityApplication]: 更新后的申请，不存在返回 None
        """
        pass
```

**验证**: 
```bash
python -m py_compile src/app/domain/repositories/community_application_repository.py
# 预期输出: 无错误
```

#### 步骤 2: 创建 AuditLogRepository 接口
**文件**: `src/app/domain/repositories/audit_log_repository.py`

```python
"""
审计日志仓储接口
"""
from typing import List, Optional
from abc import ABC, abstractmethod

from database.flask_models import UserAuditLog


class AuditLogRepository(ABC):
    """审计日志仓储接口"""

    @abstractmethod
    def create(
        self,
        user_id: int,
        action: str,
        detail: str,
        **kwargs
    ) -> UserAuditLog:
        """
        创建审计日志

        Args:
            user_id: 用户ID
            action: 操作类型
            detail: 操作详情
            **kwargs: 其他字段

        Returns:
            UserAuditLog: 创建的审计日志
        """
        pass

    @abstractmethod
    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        查找用户的审计日志

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        pass

    @abstractmethod
    def find_by_action(
        self,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        根据操作类型查找审计日志

        Args:
            action: 操作类型
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        pass
```

**验证**:
```bash
python -m py_compile src/app/domain/repositories/audit_log_repository.py
# 预期输出: 无错误
```

#### 步骤 3: 创建 SQLAlchemyCommunityApplicationRepository 实现
**文件**: `src/app/infrastructure/persistence/sqlalchemy_community_application_repository.py`

```python
"""
SQLAlchemy 社区申请仓储实现
"""
from typing import List, Optional
from sqlalchemy import select

from app.domain.repositories.community_application_repository import CommunityApplicationRepository
from database.flask_models import db, CommunityApplication


class SQLAlchemyCommunityApplicationRepository(CommunityApplicationRepository):
    """SQLAlchemy 社区申请仓储实现"""

    def save(self, application: CommunityApplication) -> CommunityApplication:
        """
        保存社区申请

        Args:
            application: 社区申请实体

        Returns:
            CommunityApplication: 保存后的社区申请
        """
        db.session.add(application)
        db.session.flush()
        return application

    def find_by_id(self, application_id: int) -> Optional[CommunityApplication]:
        """
        根据ID查找社区申请

        Args:
            application_id: 申请ID

        Returns:
            Optional[CommunityApplication]: 社区申请，不存在返回 None
        """
        return db.session.get(CommunityApplication, application_id)

    def find_pending_by_user_and_community(
        self, user_id: int, community_id: int
    ) -> Optional[CommunityApplication]:
        """
        查找用户对社区的待审核申请

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            Optional[CommunityApplication]: 待审核申请，不存在返回 None
        """
        stmt = select(CommunityApplication).where(
            CommunityApplication.user_id == user_id,
            CommunityApplication.target_community_id == community_id,
            CommunityApplication.status == 1  # 待审核
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_community(
        self, community_id: int, status: Optional[int] = None
    ) -> List[CommunityApplication]:
        """
        查找社区的所有申请

        Args:
            community_id: 社区ID
            status: 申请状态（可选）

        Returns:
            List[CommunityApplication]: 申请列表
        """
        stmt = select(CommunityApplication).where(
            CommunityApplication.target_community_id == community_id
        )
        
        if status is not None:
            stmt = stmt.where(CommunityApplication.status == status)
        
        stmt = stmt.order_by(CommunityApplication.created_at.desc())
        return list(db.session.execute(stmt).scalars().all())

    def update_status(
        self,
        application_id: int,
        status: int,
        processor_id: int,
        rejection_reason: Optional[str] = None
    ) -> Optional[CommunityApplication]:
        """
        更新申请状态

        Args:
            application_id: 申请ID
            status: 新状态
            processor_id: 处理者ID
            rejection_reason: 拒绝理由（可选）

        Returns:
            Optional[CommunityApplication]: 更新后的申请，不存在返回 None
        """
        from datetime import datetime
        
        application = self.find_by_id(application_id)
        if not application:
            return None
        
        application.status = status
        application.processed_by = processor_id
        application.updated_at = datetime.now()
        
        if rejection_reason:
            application.rejection_reason = rejection_reason
        
        db.session.flush()
        return application
```

**验证**:
```bash
python -m py_compile src/app/infrastructure/persistence/sqlalchemy_community_application_repository.py
# 预期输出: 无错误
```

#### 步骤 4: 创建 SQLAlchemyAuditLogRepository 实现
**文件**: `src/app/infrastructure/persistence/sqlalchemy_audit_log_repository.py`

```python
"""
SQLAlchemy 审计日志仓储实现
"""
from typing import List
from sqlalchemy import select

from app.domain.repositories.audit_log_repository import AuditLogRepository
from database.flask_models import db, UserAuditLog


class SQLAlchemyAuditLogRepository(AuditLogRepository):
    """SQLAlchemy 审计日志仓储实现"""

    def create(
        self,
        user_id: int,
        action: str,
        detail: str,
        **kwargs
    ) -> UserAuditLog:
        """
        创建审计日志

        Args:
            user_id: 用户ID
            action: 操作类型
            detail: 操作详情
            **kwargs: 其他字段

        Returns:
            UserAuditLog: 创建的审计日志
        """
        audit_log = UserAuditLog(
            user_id=user_id,
            action=action,
            detail=detail,
            **kwargs
        )
        db.session.add(audit_log)
        db.session.flush()
        return audit_log

    def find_by_user_id(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        查找用户的审计日志

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        stmt = select(UserAuditLog).where(
            UserAuditLog.user_id == user_id
        ).order_by(
            UserAuditLog.created_at.desc()
        ).limit(limit).offset(offset)
        
        return list(db.session.execute(stmt).scalars().all())

    def find_by_action(
        self,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAuditLog]:
        """
        根据操作类型查找审计日志

        Args:
            action: 操作类型
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[UserAuditLog]: 审计日志列表
        """
        stmt = select(UserAuditLog).where(
            UserAuditLog.action == action
        ).order_by(
            UserAuditLog.created_at.desc()
        ).limit(limit).offset(offset)
        
        return list(db.session.execute(stmt).scalars().all())
```

**验证**:
```bash
python -m py_compile src/app/infrastructure/persistence/sqlalchemy_audit_log_repository.py
# 预期输出: 无错误
```

#### 步骤 5: 更新 RepositoryFactory
**文件**: `src/app/infrastructure/persistence/repository_factory.py`

在 `RepositoryFactory` 类中添加以下方法：

```python
@staticmethod
def get_community_application_repository() -> CommunityApplicationRepository:
    """
    获取社区申请仓储

    Returns:
        CommunityApplicationRepository: 社区申请仓储实例
    """
    if not hasattr(RepositoryFactory, '_community_application_repository'):
        from app.infrastructure.persistence.sqlalchemy_community_application_repository import (
            SQLAlchemyCommunityApplicationRepository
        )
        RepositoryFactory._community_application_repository = SQLAlchemyCommunityApplicationRepository()
    return RepositoryFactory._community_application_repository

@staticmethod
def get_audit_log_repository() -> AuditLogRepository:
    """
    获取审计日志仓储

    Returns:
        AuditLogRepository: 审计日志仓储实例
    """
    if not hasattr(RepositoryFactory, '_audit_log_repository'):
        from app.infrastructure.persistence.sqlalchemy_audit_log_repository import (
            SQLAlchemyAuditLogRepository
        )
        RepositoryFactory._audit_log_repository = SQLAlchemyAuditLogRepository()
    return RepositoryFactory._audit_log_repository
```

**验证**:
```bash
python -c "
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory
from src.app.domain.repositories.community_application_repository import CommunityApplicationRepository
from src.app.domain.repositories.audit_log_repository import AuditLogRepository

app_repo = RepositoryFactory.get_community_application_repository()
audit_repo = RepositoryFactory.get_audit_log_repository()

assert isinstance(app_repo, CommunityApplicationRepository), 'CommunityApplicationRepository 实例化失败'
assert isinstance(audit_repo, AuditLogRepository), 'AuditLogRepository 实例化失败'
print('✅ RepositoryFactory 更新成功')
"
# 预期输出: ✅ RepositoryFactory 更新成功
```

#### 步骤 6: 更新 __init__.py 文件导出新接口
**文件**: `src/app/domain/repositories/__init__.py`

```python
# 在文件末尾添加
from .community_application_repository import CommunityApplicationRepository
from .audit_log_repository import AuditLogRepository

__all__ = [
    # ... 现有导出 ...
    'CommunityApplicationRepository',
    'AuditLogRepository',
]
```

**文件**: `src/app/infrastructure/persistence/__init__.py`

```python
# 在文件末尾添加
from .sqlalchemy_community_application_repository import SQLAlchemyCommunityApplicationRepository
from .sqlalchemy_audit_log_repository import SQLAlchemyAuditLogRepository

__all__ = [
    # ... 现有导出 ...
    'SQLAlchemyCommunityApplicationRepository',
    'SQLAlchemyAuditLogRepository',
]
```

**验证**:
```bash
python -c "
from src.app.domain.repositories import CommunityApplicationRepository, AuditLogRepository
from src.app.infrastructure.persistence import SQLAlchemyCommunityApplicationRepository, SQLAlchemyAuditLogRepository
print('✅ 导出更新成功')
"
# 预期输出: ✅ 导出更新成功
```

### 提交
```bash
git add src/app/domain/repositories/community_application_repository.py \
        src/app/domain/repositories/audit_log_repository.py \
        src/app/infrastructure/persistence/sqlalchemy_community_application_repository.py \
        src/app/infrastructure/persistence/sqlalchemy_audit_log_repository.py \
        src/app/infrastructure/persistence/repository_factory.py \
        src/app/domain/repositories/__init__.py \
        src/app/infrastructure/persistence/__init__.py

git commit -m "feat: 创建 CommunityApplicationRepository 和 AuditLogRepository

- 添加 CommunityApplicationRepository 接口和 SQLAlchemy 实现
- 添加 AuditLogRepository 接口和 SQLAlchemy 实现
- 更新 RepositoryFactory 支持新 Repository
- 消除 UseCase 中对 db.session 的直接访问"
```

---

## 任务 2: 修复 CreateCommunityApplicationUseCase 的事务一致性

### 目标
使用 `with transaction()` 上下文管理器，通过 Repository 访问数据，消除对 `db.session` 的直接访问。

### 涉及文件
- `src/app/application/use_cases/community/create_community_application_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/community/create_community_application_use_case.py
# 记录当前实现，用于对比
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/community/create_community_application_use_case.py`

完整替换为以下内容：

```python
"""
创建社区申请用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, CommunityApplication
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 使用 with transaction() 确保事务一致性
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transaction
from datetime import datetime


class CreateCommunityApplicationUseCase(BaseUseCase):
    """创建社区申请用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_application_repository = RepositoryFactory.get_community_application_repository()

    def _validate(self, user_id: int, community_id: int, message: str = "") -> UseCaseResult:
        """
        验证参数

        Args:
            user_id: 用户ID
            community_id: 社区ID
            message: 申请消息

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="用户ID不能为空"
            )

        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="社区ID不能为空"
            )

        if message and len(message) > 500:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="申请消息不能超过500个字符"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, community_id: int, message: str = "") -> UseCaseResult:
        """
        执行创建社区申请

        Args:
            user_id: 用户ID
            community_id: 社区ID
            message: 申请消息

        Returns:
            UseCaseResult: 包含创建的申请ID
        """
        try:
            # ✅ 使用Repository代替 db.session.get(Community, community_id)
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="社区不存在"
                )

            # ✅ 使用Repository代替 db.session.get(User, user_id)
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="用户不存在"
                )

            # 检查用户是否已经是该社区的成员
            if user.community_id == community_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message="您已经是该社区的成员"
                )

            # ✅ 使用Repository检查是否已经有待审核的申请
            existing_application = self.community_application_repository.find_pending_by_user_and_community(
                user_id, community_id
            )

            if existing_application:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message="您已经有一个待审核的申请"
                )

            # ✅ 使用事务上下文管理器确保事务一致性
            with transaction():
                # 创建申请
                from database.flask_models import CommunityApplication
                application = CommunityApplication(
                    user_id=user_id,
                    target_community_id=community_id,
                    status=1,  # 待审核
                    reason=message,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                # ✅ 使用Repository保存
                self.community_application_repository.save(application)

                response_data = {
                    'application_id': application.application_id,
                    'message': '申请提交成功'
                }

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message="申请提交成功",
                    data=response_data
                )

        except Exception as e:
            # ✅ 事务会自动回滚
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"申请提交失败: {str(e)}"
            )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/community/create_community_application_use_case.py
# 预期输出: 无错误

# 导入检查
python -c "
from src.app.application.use_cases.community.create_community_application_use_case import CreateCommunityApplicationUseCase
use_case = CreateCommunityApplicationUseCase()
print('✅ CreateCommunityApplicationUseCase 重构成功')
"
# 预期输出: ✅ CreateCommunityApplicationUseCase 重构成功
```

#### 步骤 3: 运行相关测试
```bash
# 运行社区申请相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/test_community_applications.py -v
# 预期输出: 所有测试通过

# 如果测试失败，查看详细错误
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/test_community_applications.py -v --tb=short
```

### 提交
```bash
git add src/app/application/use_cases/community/create_community_application_use_case.py
git commit -m "fix: 修复 CreateCommunityApplicationUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 使用 CommunityApplicationRepository 替代 db.session 直接访问
- 消除手动 db.session.flush() 和 db.session.rollback()
- 符合 DDD 架构原则"
```

---

## 任务 3: 修复 SetSuperAdminUseCase 的事务一致性

### 目标
使用 `with transaction()` 上下文管理器，通过 AuditLogRepository 记录审计日志。

### 涉及文件
- `src/app/application/use_cases/community/set_super_admin_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/community/set_super_admin_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/community/set_super_admin_use_case.py`

在 `__init__` 方法中添加：
```python
def __init__(self):
    """
    初始化用例，注入所有需要的Repository

    符合依赖倒置原则：依赖Repository接口，而非具体实现
    """
    super().__init__()
    self.logger = logging.getLogger(__name__)
    # ✅ 通过RepositoryFactory获取Repository接口
    self.user_repository = RepositoryFactory.get_user_repository()
    self.staff_repository = RepositoryFactory.get_community_staff_repository()
    self.audit_log_repository = RepositoryFactory.get_audit_log_repository()  # ✅ 新增
```

在 `execute` 方法中，找到设置超级管理员的部分（约第 94 行），替换为：

```python
# 设置为超级管理员
if target_user.role == Role.SUPER_ADMIN:
    return UseCaseResult(
        status=UseCaseStatus.SUCCESS,
        message='该用户已经是超级管理员',
        data={'success': True, 'message': '该用户已经是超级管理员'}
    )

# ✅ 使用事务上下文管理器确保事务一致性
with transaction():
    target_user.role = Role.SUPER_ADMIN
    # ✅ 使用Repository代替 db.session.flush()
    self.user_repository.save(target_user)

    # ✅ 使用Repository保存审计日志
    self.audit_log_repository.create(
        user_id=operator_user_id,
        action="set_super_admin",
        detail=f"将用户{target_user_id}设置为超级管理员"
    )

logger.info(f'用户{operator_user_id}将用户{target_user_id}设置为超级管理员')

return UseCaseResult(
    status=UseCaseStatus.SUCCESS,
    message='已设置为超级管理员',
    data={'success': True, 'message': '已设置为超级管理员'}
)
```

找到取消超级管理员的部分（约第 135 行），替换为：

```python
# 取消超级管理员
if target_user.role != Role.SUPER_ADMIN:
    return UseCaseResult(
        status=UseCaseStatus.SUCCESS,
        message='该用户不是超级管理员',
        data={'success': True, 'message': '该用户不是超级管理员'}
    )

# ✅ 使用事务上下文管理器确保事务一致性
with transaction():
    # 取消超级管理员身份，根据工作人员身份重新计算role
    # ✅ 使用Repository查询用户在所有社区的工作人员角色
    staff_records = self.staff_repository.find_by_user_id(target_user_id, include_removed=False)

    # 重新计算用户角色
    if not staff_records:
        # 如果没有任何工作人员记录，设为普通用户
        new_role = Role.SOLO
    else:
        # 检查是否有主管角色
        has_manager = any(record.role == STAFF_ROLE_MANAGER for record in staff_records)
        new_role = Role.MANAGER if has_manager else Role.STAFF

    target_user.role = new_role
    # ✅ 使用Repository代替 db.session.flush()
    self.user_repository.save(target_user)

    # ✅ 使用Repository保存审计日志
    self.audit_log_repository.create(
        user_id=operator_user_id,
        action="remove_super_admin",
        detail=f"取消用户{target_user_id}的超级管理员身份，新角色为{new_role}"
    )

logger.info(f'用户{operator_user_id}取消用户{target_user_id}的超级管理员身份，新角色为{new_role}')

return UseCaseResult(
    status=UseCaseStatus.SUCCESS,
    message=f'已取消超级管理员，当前角色为{new_role}',
    data={'success': True, 'message': f'已取消超级管理员，当前角色为{new_role}'}
)
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/community/set_super_admin_use_case.py
# 预期输出: 无错误

# 导入检查
python -c "
from src.app.application.use_cases.community.set_super_admin_use_case import SetSuperAdminUseCase
use_case = SetSuperAdminUseCase()
print('✅ SetSuperAdminUseCase 重构成功')
"
# 预期输出: ✅ SetSuperAdminUseCase 重构成功
```

#### 步骤 3: 运行相关测试
```bash
# 运行超级管理员相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "super_admin" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/community/set_super_admin_use_case.py
git commit -m "fix: 修复 SetSuperAdminUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 使用 AuditLogRepository 记录审计日志
- 消除 db.session.add() 直接访问
- 确保用户角色更新和审计日志记录在同一事务中"
```

---

## 任务 4: 修复 AddCommunityStaffUseCase 的事务一致性

### 目标
使用 `with transaction()` 上下文管理器，通过 AuditLogRepository 记录审计日志。

### 涉及文件
- `src/app/application/use_cases/community/add_community_staff_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/community/add_community_staff_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/community/add_community_staff_use_case.py`

在 `__init__` 方法中添加：
```python
def __init__(self):
    """
    初始化用例，注入所有需要的Repository

    符合依赖倒置原则：依赖Repository接口，而非具体实现
    """
    super().__init__()
    self.logger = logging.getLogger(__name__)
    # ✅ 通过RepositoryFactory获取Repository接口
    self.user_repository = RepositoryFactory.get_user_repository()
    self.community_repository = RepositoryFactory.get_community_repository()
    self.staff_repository = RepositoryFactory.get_community_staff_repository()
    self.audit_log_repository = RepositoryFactory.get_audit_log_repository()  # ✅ 新增
```

找到添加工作人员记录审计日志的部分（约第 307 行），替换为：

```python
# ✅ 使用事务上下文管理器确保事务一致性
with transaction():
    # ... 添加工作人员逻辑 ...
    
    # ✅ 使用Repository保存审计日志
    self.audit_log_repository.create(
        user_id=operator_user_id,
        action="add_community_staff",
        detail=f"添加社区工作人员: 社区ID={community_id}, 用户ID={user_id}, 角色={role}"
    )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/community/add_community_staff_use_case.py
# 预期输出: 无错误
```

#### 步骤 3: 运行相关测试
```bash
# 运行社区工作人员相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "staff" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/community/add_community_staff_use_case.py
git commit -m "fix: 修复 AddCommunityStaffUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 使用 AuditLogRepository 记录审计日志
- 消除 db.session.add() 直接访问
- 确保工作人员添加和审计日志记录在同一事务中"
```

---

## 任务 5: 修复 RemoveCommunityStaffUseCase 的事务一致性

### 目标
使用 `with transaction()` 上下文管理器，通过 AuditLogRepository 记录审计日志。

### 涉及文件
- `src/app/application/use_cases/community/remove_community_staff_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/community/remove_community_staff_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/community/remove_community_staff_use_case.py`

在 `__init__` 方法中添加：
```python
def __init__(self):
    """
    初始化用例，注入所有需要的Repository

    符合依赖倒置原则：依赖Repository接口，而非具体实现
    """
    super().__init__()
    self.logger = logging.getLogger(__name__)
    # ✅ 通过RepositoryFactory获取Repository接口
    self.staff_repository = RepositoryFactory.get_community_staff_repository()
    self.community_repository = RepositoryFactory.get_community_repository()
    self.user_repository = RepositoryFactory.get_user_repository()
    self.audit_log_repository = RepositoryFactory.get_audit_log_repository()  # ✅ 新增
```

找到移除工作人员记录审计日志的部分（约第 106 行），替换为：

```python
# ✅ 使用事务上下文管理器确保事务一致性
with transaction():
    # ... 移除工作人员逻辑 ...
    
    # ✅ 使用Repository保存审计日志
    self.audit_log_repository.create(
        user_id=operator_user_id,
        action="remove_community_staff",
        detail=f"移除社区工作人员: 社区ID={community_id}, 用户ID={target_user_id}"
    )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/community/remove_community_staff_use_case.py
# 预期输出: 无错误
```

#### 步骤 3: 运行相关测试
```bash
# 运行移除工作人员相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "remove_staff" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/community/remove_community_staff_use_case.py
git commit -m "fix: 修复 RemoveCommunityStaffUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 使用 AuditLogRepository 记录审计日志
- 消除 db.session.add() 直接访问
- 确保工作人员移除和审计日志记录在同一事务中"
```

---

## 任务 6: 修复 LogViewGuardianInfoUseCase 的事务一致性

### 目标
移除 `db.session.commit()`，使用 `with transaction()` 上下文管理器。

### 涉及文件
- `src/app/application/use_cases/user/log_view_guardian_info_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/user/log_view_guardian_info_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/user/log_view_guardian_info_use_case.py`

完整替换为以下内容：

```python
"""
记录查看监护人信息用例（重构后 - 符合DDD架构）

重构要点：
- 使用 with transaction() 确保事务一致性
- 移除 db.session.commit() 直接提交
- 使用Repository访问数据
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transaction
from datetime import datetime


class LogViewGuardianInfoUseCase(BaseUseCase):
    """记录查看监护人信息用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.profile_view_log_repository = RepositoryFactory.get_profile_view_log_repository()

    def execute(self, viewer_id: int, guardian_id: int) -> UseCaseResult:
        """
        执行记录查看监护人信息

        Args:
            viewer_id: 查看者ID
            guardian_id: 监护人ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # ✅ 使用事务上下文管理器确保事务一致性
            with transaction():
                from database.flask_models import ProfileViewLog
                audit_log = ProfileViewLog(
                    viewer_id=viewer_id,
                    target_user_id=guardian_id,
                    view_type='guardian_info',
                    viewed_at=datetime.now()
                )
                # ✅ 使用Repository保存
                self.profile_view_log_repository.save(audit_log)

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='记录成功',
                data={'success': True}
            )

        except Exception as e:
            # ✅ 事务会自动回滚
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"记录失败: {str(e)}"
            )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/user/log_view_guardian_info_use_case.py
# 预期输出: 无错误
```

#### 步骤 3: 运行相关测试
```bash
# 运行日志记录相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "log_view" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/user/log_view_guardian_info_use_case.py
git commit -m "fix: 修复 LogViewGuardianInfoUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 移除 db.session.commit() 直接提交
- 使用Repository保存审计日志
- 避免事务边界混乱"
```

---

## 任务 7: 修复 LogProfileViewUseCase 的事务一致性

### 目标
使用 `with transaction()` 上下文管理器。

### 涉及文件
- `src/app/application/use_cases/user/log_profile_view_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/user/log_profile_view_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/user/log_profile_view_use_case.py`

找到 `execute` 方法中添加审计日志的部分（约第 43 行），替换为：

```python
# ✅ 使用事务上下文管理器确保事务一致性
with transaction():
    from database.flask_models import ProfileViewLog
    audit_log = ProfileViewLog(
        viewer_id=viewer_id,
        target_user_id=target_user_id,
        view_type='profile',
        viewed_at=datetime.now()
    )
    # ✅ 使用Repository保存
    self.profile_view_log_repository.save(audit_log)
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/user/log_profile_view_use_case.py
# 预期输出: 无错误
```

### 提交
```bash
git add src/app/application/use_cases/user/log_profile_view_use_case.py
git commit -m "fix: 修复 LogProfileViewUseCase 事务一致性

- 使用 with transaction() 确保事务一致性
- 使用Repository保存审计日志
- 消除 db.session.add() 直接访问"
```

---

## 任务 8: 消除 UseCase 之间的相互调用

### 目标
将 `HandleUserCommunityChangeUseCase` 改为 `TransferUsersBatchUseCase` 的内部方法，消除 UseCase 之间的相互调用。

### 涉及文件
- `src/app/application/use_cases/community/transfer_users_batch_use_case.py`

### 步骤

#### 步骤 1: 读取当前文件
```bash
cat src/app/application/use_cases/community/transfer_users_batch_use_case.py
# 记录当前实现
```

#### 步骤 2: 重构 UseCase
**文件**: `src/app/application/use_cases/community/transfer_users_batch_use_case.py`

移除导入：
```python
# 删除这一行
from app.application.use_cases.community.handle_user_community_change_use_case import HandleUserCommunityChangeUseCase
```

将 `HandleUserCommunityChangeUseCase` 的逻辑整合为内部方法：

```python
def _handle_user_community_change(
    self,
    user_id: int,
    old_community_id: int,
    new_community_id: int
) -> dict:
    """
    内部方法：处理用户社区变更

    Args:
        user_id: 用户ID
        old_community_id: 原社区ID
        new_community_id: 新社区ID

    Returns:
        dict: 处理结果
    """
    from datetime import datetime

    # 0. 更新用户的社区归属
    # ✅ 使用Repository代替 db.session.get(User, user_id)
    user = self.user_repository.find_by_id(user_id)
    if not user:
        return {
            'success': False,
            'message': f'用户不存在: {user_id}'
        }

    old_user_community_id = user.community_id
    user.community_id = new_community_id
    if new_community_id != old_user_community_id:
        user.community_joined_at = datetime.now()
    # ✅ 使用Repository保存
    self.user_repository.save(user)

    # 1. 停用旧社区的社区规则
    deactivated_count = 0
    if old_community_id:
        deactivated_count = self._deactivate_old_community_rules(
            user_id, old_community_id
        )

    # 2. 激活新社区的社区规则
    activated_count = self._activate_new_community_rules(
        user_id, new_community_id
    )

    # 3. 处理工作人员关系
    # 移除旧社区的工作人员关系
    if old_community_id:
        # ✅ 使用Repository的软删除方法
        old_staff = self.staff_repository.find_active_by_community_and_user(
            old_community_id, user_id
        )
        if old_staff:
            self.staff_repository.soft_delete_by_id(old_staff.id)

    # 如果新社区存在，检查是否需要添加工作人员关系
    if new_community_id:
        from app.shared.constants.roles import COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
        if user.role in COMMUNITY_STAFF_ROLES:  # 如果是管理员或以上
            # 检查是否已存在工作人员关系
            existing_staff = self.staff_repository.find_active_by_community_and_user(
                new_community_id, user_id
            )
            if not existing_staff:
                # 需要导入CommunityStaff模型来创建实例
                from database.flask_models import CommunityStaff
                staff = CommunityStaff(
                    community_id=new_community_id,
                    user_id=user_id,
                    role=STAFF_ROLE_MANAGER if user.role in ADMIN_ROLES else STAFF_ROLE_STAFF
                )
                # ✅ 使用Repository保存
                self.staff_repository.save(staff)

    logger.info(f"用户{user_id}社区切换完成: 停用{deactivated_count}个旧规则，激活{activated_count}个新规则")

    return {
        'success': True,
        'deactivated_count': deactivated_count,
        'activated_count': activated_count
    }

def _deactivate_old_community_rules(self, user_id: int, old_community_id: int) -> int:
    """
    内部方法：停用旧社区的规则

    Args:
        user_id: 用户ID
        old_community_id: 原社区ID

    Returns:
        int: 停用的规则数量
    """
    # ✅ 使用Repository查找用户与旧社区规则的激活映射记录
    from database.flask_models import UserCommunityRule, CommunityCheckinRule
    from sqlalchemy import select
    from database.flask_models import db

    stmt_old = select(UserCommunityRule).join(CommunityCheckinRule).where(
        UserCommunityRule.user_id == user_id,
        CommunityCheckinRule.community_id == old_community_id,
        UserCommunityRule.is_active == True
    )
    old_mappings = db.session.execute(stmt_old).scalars().all()

    # 将这些规则标记为停用
    deactivated_count = 0
    for mapping in old_mappings:
        mapping.is_active = False
        deactivated_count += 1

    logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
    return deactivated_count

def _activate_new_community_rules(self, user_id: int, new_community_id: int) -> int:
    """
    内部方法：激活新社区的规则

    Args:
        user_id: 用户ID
        new_community_id: 新社区ID

    Returns:
        int: 激活的规则数量
    """
    # ✅ 使用Repository获取新社区的所有启用规则
    new_community_rules = self.community_checkin_rule_repository.find_by_community_id(new_community_id)
    new_community_rules = [r for r in new_community_rules if r.status == 1]

    activated_count = 0

    # 为用户创建或激活规则映射
    for rule in new_community_rules:
        # ✅ 使用Repository查找是否已存在映射记录
        existing_mapping = self.user_community_rule_repository.find_by_user_and_rule(
            user_id, rule.community_rule_id
        )

        if existing_mapping:
            # 如果存在且当前是停用状态，重新激活
            if not existing_mapping.is_active:
                existing_mapping.is_active = True
                self.user_community_rule_repository.save(existing_mapping)
                activated_count += 1
        else:
            # 如果不存在，创建新映射
            from database.flask_models import UserCommunityRule
            new_mapping = UserCommunityRule(
                user_id=user_id,
                community_rule_id=rule.community_rule_id,
                is_active=True
            )
            # ✅ 使用Repository保存
            self.user_community_rule_repository.save(new_mapping)
            activated_count += 1

    logger.info(f"用户{user_id}已激活{activated_count}个新社区规则")
    return activated_count
```

修改 `execute` 方法中的调用（约第 122 行）：

```python
# 2.4 切换打卡规则（使用内部方法）
rules_updated = 0
for user_id in transfer_result['transferred_user_ids']:
    try:
        # ✅ 直接调用内部方法，而不是 UseCase
        result = self._handle_user_community_change(
            user_id, source_community_id, target_community_id
        )
        if result['success']:
            rules_updated += result.get('activated_count', 0)
        else:
            logger.error(f'切换用户{user_id}的打卡规则失败: {result["message"]}')
            transfer_result['failed'].append({
                'user_id': user_id,
                'reason': f'规则切换失败: {result["message"]}'
            })
    except Exception as e:
        logger.error(f'切换用户{user_id}的打卡规则失败: {str(e)}')
        transfer_result['failed'].append({
            'user_id': user_id,
            'reason': f'规则切换失败: {str(e)}'
        })
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/community/transfer_users_batch_use_case.py
# 预期输出: 无错误
```

#### 步骤 3: 运行相关测试
```bash
# 运行批量转移相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "transfer" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/community/transfer_users_batch_use_case.py
git commit -m "refactor: 消除 UseCase 之间的相互调用

- 将 HandleUserCommunityChangeUseCase 改为内部方法
- 消除 UseCase 之间的相互调用，符合 DDD 原则
- 简化事务边界，提高可维护性"
```

---

## 任务 9: 修复 EnsureUserNicknameUseCase 和 GenerateAuthTokensUseCase

### 目标
消除对 `UpdateUserUseCase` 的调用，将更新逻辑内联。

### 涉及文件
- `src/app/application/use_cases/auth/ensure_user_nickname_use_case.py`
- `src/app/application/use_cases/auth/generate_auth_tokens_use_case.py`

### 步骤

#### 步骤 1: 修复 EnsureUserNicknameUseCase
**文件**: `src/app/application/use_cases/auth/ensure_user_nickname_use_case.py`

移除导入：
```python
# 删除这一行
from app.application.use_cases.user import UpdateUserUseCase
```

将更新昵称的逻辑内联到 `execute` 方法中：

```python
def execute(self, user_id: int) -> UseCaseResult:
    """
    执行确保用户昵称用例

    Args:
        user_id: 用户ID

    Returns:
        UseCaseResult: 执行结果
    """
    try:
        # ✅ 使用Repository查找用户
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message='用户不存在'
            )

        # 如果用户已有昵称，直接返回
        if user.nickname:
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='用户已有昵称',
                data={'nickname': user.nickname}
            )

        # 生成昵称
        from faker import Faker
        fake = Faker('zh_CN')
        nickname = fake.user_name()

        # ✅ 直接更新用户，不调用其他 UseCase
        user.nickname = nickname
        self.user_repository.save(user)

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='昵称生成成功',
            data={'nickname': nickname}
        )

    except Exception as e:
        return UseCaseResult(
            status=UseCaseStatus.FAILURE,
            message=f'生成昵称失败: {str(e)}'
        )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/auth/ensure_user_nickname_use_case.py
# 预期输出: 无错误
```

#### 步骤 2: 修复 GenerateAuthTokensUseCase
**文件**: `src/app/application/use_cases/auth/generate_auth_tokens_use_case.py`

移除导入：
```python
# 删除这一行
from app.application.use_cases.user import UpdateUserUseCase
```

将更新令牌的逻辑内联到 `execute` 方法中：

```python
def execute(self, user_id: int) -> UseCaseResult:
    """
    执行生成认证令牌用例

    Args:
        user_id: 用户ID

    Returns:
        UseCaseResult: 执行结果
    """
    try:
        # ✅ 使用Repository查找用户
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message='用户不存在'
            )

        # 生成令牌
        import jwt
        import os
        from datetime import datetime, timedelta

        token_secret = os.getenv('TOKEN_SECRET', 'your-secret-key')
        access_token = jwt.encode({
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, token_secret, algorithm='HS256')

        refresh_token = jwt.encode({
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, token_secret, algorithm='HS256')

        # ✅ 直接更新用户令牌，不调用其他 UseCase
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expires_at = datetime.utcnow() + timedelta(hours=24)
        self.user_repository.save(user)

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='令牌生成成功',
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': user.token_expires_at.isoformat()
            }
        )

    except Exception as e:
        return UseCaseResult(
            status=UseCaseStatus.FAILURE,
            message=f'生成令牌失败: {str(e)}'
        )
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/application/use_cases/auth/generate_auth_tokens_use_case.py
# 预期输出: 无错误
```

#### 步骤 3: 运行相关测试
```bash
# 运行认证相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "auth" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/application/use_cases/auth/ensure_user_nickname_use_case.py \
        src/app/application/use_cases/auth/generate_auth_tokens_use_case.py

git commit -m "refactor: 消除 EnsureUserNicknameUseCase 和 GenerateAuthTokensUseCase 的相互调用

- 将更新昵称和令牌的逻辑内联到 UseCase 中
- 消除对 UpdateUserUseCase 的调用
- 符合 DDD 原则，UseCase 之间不应相互调用"
```

---

## 任务 10: 在 Repository 中添加批量操作方法

### 目标
在 `CommunityEventRepository` 和 `UserCommunityRuleRepository` 中添加批量操作方法，消除对 `db.session` 的直接访问。

### 涉及文件
- `src/app/domain/repositories/community_event_repository.py` (修改)
- `src/app/infrastructure/persistence/sqlalchemy_community_event_repository.py` (修改)
- `src/app/domain/repositories/user_community_rule_repository.py` (修改)
- `src/app/infrastructure/persistence/sqlalchemy_user_community_rule_repository.py` (修改)

### 步骤

#### 步骤 1: 在 CommunityEventRepository 接口中添加批量转移方法
**文件**: `src/app/domain/repositories/community_event_repository.py`

```python
@abstractmethod
def batch_transfer_events(
    self,
    source_community_id: int,
    target_community_id: int,
    user_ids: List[int],
    status: Optional[int] = None
) -> int:
    """
    批量转移事件到目标社区

    Args:
        source_community_id: 源社区ID
        target_community_id: 目标社区ID
        user_ids: 用户ID列表
        status: 事件状态（可选，默认只转移进行中的事件）

    Returns:
        int: 转移的事件数量
    """
    pass
```

#### 步骤 2: 在 SQLAlchemyCommunityEventRepository 中实现批量转移方法
**文件**: `src/app/infrastructure/persistence/sqlalchemy_community_event_repository.py`

```python
def batch_transfer_events(
    self,
    source_community_id: int,
    target_community_id: int,
    user_ids: List[int],
    status: Optional[int] = None
) -> int:
    """
    批量转移事件到目标社区

    Args:
        source_community_id: 源社区ID
        target_community_id: 目标社区ID
        user_ids: 用户ID列表
        status: 事件状态（可选，默认只转移进行中的事件）

    Returns:
        int: 转移的事件数量
    """
    from sqlalchemy import update
    from database.flask_models import CommunityEvent

    stmt = update(CommunityEvent).where(
        CommunityEvent.community_id == source_community_id,
        CommunityEvent.target_user_id.in_(user_ids)
    )

    if status is not None:
        stmt = stmt.where(CommunityEvent.status == status)

    stmt = stmt.values(
        {'community_id': target_community_id}
    )

    result = db.session.execute(stmt)
    return result.rowcount
```

#### 步骤 3: 在 UserCommunityRuleRepository 接口中添加批量停用方法
**文件**: `src/app/domain/repositories/user_community_rule_repository.py`

```python
@abstractmethod
def deactivate_by_user_and_community(
    self,
    user_id: int,
    community_id: int
) -> int:
    """
    停用用户在指定社区的所有规则映射

    Args:
        user_id: 用户ID
        community_id: 社区ID

    Returns:
        int: 停用的规则数量
    """
    pass
```

#### 步骤 4: 在 SQLAlchemyUserCommunityRuleRepository 中实现批量停用方法
**文件**: `src/app/infrastructure/persistence/sqlalchemy_user_community_rule_repository.py`

```python
def deactivate_by_user_and_community(
    self,
    user_id: int,
    community_id: int
) -> int:
    """
    停用用户在指定社区的所有规则映射

    Args:
        user_id: 用户ID
        community_id: 社区ID

    Returns:
        int: 停用的规则数量
    """
    from sqlalchemy import select
    from database.flask_models import UserCommunityRule, CommunityCheckinRule

    stmt = select(UserCommunityRule).join(CommunityCheckinRule).where(
        UserCommunityRule.user_id == user_id,
        CommunityCheckinRule.community_id == community_id,
        UserCommunityRule.is_active == True
    )
    mappings = list(db.session.execute(stmt).scalars().all())

    deactivated_count = 0
    for mapping in mappings:
        mapping.is_active = False
        deactivated_count += 1

    return deactivated_count
```

#### 步骤 5: 更新 TransferUsersBatchUseCase 使用新方法
**文件**: `src/app/application/use_cases/community/transfer_users_batch_use_case.py`

修改 `_transfer_users` 方法（约第 155 行）：

```python
# 2.5 转移未完成事件
events_transferred = 0
if transfer_result['transferred_user_ids']:
    # ✅ 使用Repository批量转移事件
    events_transferred = self.event_repository.batch_transfer_events(
        source_community_id=source_community_id,
        target_community_id=target_community_id,
        user_ids=transfer_result['transferred_user_ids'],
        status=1  # 仅转移进行中的事件
    )
    logger.info(f'转移了{events_transferred}个未完成事件')
```

修改 `_deactivate_old_community_rules` 方法：

```python
def _deactivate_old_community_rules(self, user_id: int, old_community_id: int) -> int:
    """
    内部方法：停用旧社区的规则

    Args:
        user_id: 用户ID
        old_community_id: 原社区ID

    Returns:
        int: 停用的规则数量
    """
    # ✅ 使用Repository批量停用规则映射
    deactivated_count = self.user_community_rule_repository.deactivate_by_user_and_community(
        user_id, old_community_id
    )
    logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
    return deactivated_count
```

**验证**:
```bash
# 语法检查
python -m py_compile src/app/domain/repositories/community_event_repository.py \
                        src/app/infrastructure/persistence/sqlalchemy_community_event_repository.py \
                        src/app/domain/repositories/user_community_rule_repository.py \
                        src/app/infrastructure/persistence/sqlalchemy_user_community_rule_repository.py \
                        src/app/application/use_cases/community/transfer_users_batch_use_case.py
# 预期输出: 无错误
```

#### 步骤 6: 运行相关测试
```bash
# 运行批量转移相关的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/integration/ -k "transfer" -v
# 预期输出: 所有测试通过
```

### 提交
```bash
git add src/app/domain/repositories/community_event_repository.py \
        src/app/infrastructure/persistence/sqlalchemy_community_event_repository.py \
        src/app/domain/repositories/user_community_rule_repository.py \
        src/app/infrastructure/persistence/sqlalchemy_user_community_rule_repository.py \
        src/app/application/use_cases/community/transfer_users_batch_use_case.py

git commit -m "feat: 在 Repository 中添加批量操作方法

- 在 CommunityEventRepository 中添加 batch_transfer_events() 方法
- 在 UserCommunityRuleRepository 中添加 deactivate_by_user_and_community() 方法
- 更新 TransferUsersBatchUseCase 使用新方法
- 消除对 db.session 的直接访问"
```

---

## 任务 11: 运行完整测试套件并验证

### 目标
运行所有测试，确保所有修复没有引入新的问题。

### 步骤

#### 步骤 1: 运行单元测试
```bash
make ut
# 预期输出: 所有单元测试通过
# 记录测试通过数量
```

#### 步骤 2: 运行集成测试
```bash
make it
# 预期输出: 所有集成测试通过
# 记录测试通过数量
```

#### 步骤 3: 运行测试覆盖率
```bash
make test-coverage
# 预期输出: 测试覆盖率报告
# 检查覆盖率是否保持或提升
```

#### 步骤 4: 验证代码质量
```bash
# 检查代码格式
ruff check src/app/application/use_cases/
# 预期输出: 无格式错误

# 如果有格式错误，自动修复
ruff format src/app/application/use_cases/
```

#### 步骤 5: 对比修复前后的测试结果
```bash
# 对比修复前后的测试通过数量
# 预期: 测试通过数量 >= 修复前
```

### 提交
```bash
git add -A
git commit -m "test: 验证所有修复通过测试

- 运行单元测试: make ut
- 运行集成测试: make it
- 运行测试覆盖率: make test-coverage
- 验证代码质量: ruff check
- 所有测试通过，无新的问题引入"
```

---

## 任务 12: 清理和文档更新

### 目标
清理临时文件，更新相关文档。

### 涉及文件
- `docs/ddd-transaction-consistency-review.md` (更新)

### 步骤

#### 步骤 1: 更新审查报告
**文件**: `docs/ddd-transaction-consistency-review.md`

在文档末尾添加修复记录：

```markdown

---

## 修复记录

**修复日期**: 2026-01-17  
**修复人员**: [填写修复人员]

### 已修复的问题

#### P0 问题（已修复 ✅）
- ✅ CreateCommunityApplicationUseCase 缺少事务保护
- ✅ SetSuperAdminUseCase 缺少事务保护
- ✅ AddCommunityStaffUseCase 缺少事务保护
- ✅ RemoveCommunityStaffUseCase 缺少事务保护
- ✅ LogViewGuardianInfoUseCase 直接使用 db.session.commit()

#### P1 问题（已修复 ✅）
- ✅ 创建 CommunityApplicationRepository
- ✅ 创建 AuditLogRepository
- ✅ 在 Repository 中添加批量操作方法
- ✅ 消除 UseCase 之间的相互调用（3 处）
- ✅ 统一审计日志记录方式

### 测试结果

**修复前**:
- 单元测试通过: [填写数量]
- 集成测试通过: [填写数量]

**修复后**:
- 单元测试通过: [填写数量]
- 集成测试通过: [填写数量]

**结论**: 所有测试通过，无新的问题引入。
```

#### 步骤 2: 检查是否有临时文件
```bash
# 查找临时文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
find . -name "*.tmp" -delete
```

#### 步骤 3: 最终验证
```bash
# 运行完整测试套件
make ut && make it
# 预期输出: 所有测试通过

# 检查代码质量
ruff check src/
# 预期输出: 无错误
```

### 提交
```bash
git add docs/ddd-transaction-consistency-review.md
git commit -m "docs: 更新 DDD 事务一致性审查报告

- 记录所有已修复的问题
- 更新测试结果
- 确认所有 P0 和 P1 问题已解决"
```

---

## 任务 13: 合并到主分支

### 目标
将修复合并到主分支。

### 步骤

#### 步骤 1: 推送到远程
```bash
git push origin dev
```

#### 步骤 2: 创建 Pull Request
```bash
gh pr create --title "fix: 修复 DDD 事务一致性和 UseCase 设计问题" \
            --body "## 修复内容

### P0 问题（必须修复）
- ✅ 修复 CreateCommunityApplicationUseCase 事务一致性
- ✅ 修复 SetSuperAdminUseCase 事务一致性
- ✅ 修复 AddCommunityStaffUseCase 事务一致性
- ✅ 修复 RemoveCommunityStaffUseCase 事务一致性
- ✅ 修复 LogViewGuardianInfoUseCase 事务一致性
- ✅ 修复 LogProfileViewUseCase 事务一致性

### P1 问题（建议修复）
- ✅ 创建 CommunityApplicationRepository 和 AuditLogRepository
- ✅ 在 Repository 中添加批量操作方法
- ✅ 消除 UseCase 之间的相互调用
- ✅ 统一审计日志记录方式

### 测试结果
- 单元测试: [填写数量] 通过
- 集成测试: [填写数量] 通过
- 测试覆盖率: [填写百分比]%

### 相关文档
- 审查报告: docs/ddd-transaction-consistency-review.md
- 实施计划: docs/plans/2026-01-17-13-40-ddd-transaction-consistency-fix.md

## 检查清单
- [ ] 所有测试通过
- [ ] 代码质量检查通过
- [ ] 文档已更新
- [ ] 无新的问题引入"
```

#### 步骤 3: 等待代码审查
```bash
# 等待团队成员审查 Pull Request
# 根据反馈进行必要的修改
```

#### 步骤 4: 合并到主分支
```bash
# 审查通过后，合并到主分支
gh pr merge --merge
```

---

## 验收标准

### 功能验收
- [ ] 所有 P0 问题已修复
- [ ] 所有 P1 问题已修复
- [ ] 单元测试通过率 >= 95%
- [ ] 集成测试通过率 >= 90%
- [ ] 测试覆盖率 >= 80%

### 代码质量验收
- [ ] 所有 UseCase 使用 `with transaction()` 管理事务
- [ ] 所有 UseCase 通过 Repository 访问数据
- [ ] 无 UseCase 之间的相互调用
- [ ] 代码格式检查通过（ruff check）
- [ ] 无语法错误

### 架构合规性验收
- [ ] 符合 DDD 架构原则
- [ ] 符合依赖倒置原则（DIP）
- [ ] 符合单一职责原则（SRP）
- [ ] 符合开闭原则（OCP）

### 文档验收
- [ ] 审查报告已更新
- [ ] 修复记录已记录
- [ ] 测试结果已记录

---

## 参考资料

### 相关文档
- DDD 事务一致性审查报告: `docs/ddd-transaction-consistency-review.md`
- 代码风格指南: `docs/code-style-guide.md`
- 集成测试编写指南: `docs/integration-test-writing-guide.md`

### 相关技能
- @executing-plans: 执行实施计划
- @subagent-driven-development: 由 Subagent 驱动开发

### 相关工具
- RepositoryFactory: `src/app/infrastructure/persistence/repository_factory.py`
- 事务管理工具: `src/app/shared/utils/transaction.py`
- 测试工具: `make ut`, `make it`, `make test-coverage`

---

## 执行选项

### 选项 1: 由 Subagent 驱动
使用 `subagent-driven-development` 技能，让 Subagent 自动执行所有任务。

### 选项 2: 使用并行会话
在 git worktree 中创建新的会话，然后使用 Subagent `executing-plans` 执行计划。

```bash
# 创建新的会话
cd /Users/qiaoliang/working/code/safeGuard/backend-ddd-fix
claude

# 在新会话中执行
/executing-plans docs/plans/2026-01-17-13-40-ddd-transaction-consistency-fix.md
```

---

**计划创建完成时间**: 2026-01-17 13:40  
**预计完成时间**: 2026-01-17 18:00  
**预计工作量**: 4-5 小时