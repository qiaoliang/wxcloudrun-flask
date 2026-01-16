# DDD架构Service迁移实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 将UseCase和测试文件从旧的`wxcloudrun/`静态Service迁移到新的DDD架构UseCase（基于Repository模式）

**架构:** 采用DDD（领域驱动设计）分层架构：
- 表现层：`src/app/modules/*/routes.py` - 处理HTTP请求
- 应用层：`src/app/application/use_cases/` - 编排业务流程
- 领域层：`src/app/domain/repositories/` - 仓储接口
- 基础设施层：`src/app/infrastructure/persistence/` - 仓储实现

**技术栈:**
- Flask 3.1.2 + Blueprint路由
- SQLAlchemy 2.0.16 ORM
- RepositoryFactory依赖注入
- UseCaseResult标准化返回
- pytest单元测试 + 集成测试

---

## 迁移范围统计

| 类型 | 总数 | 需迁移 | 占比 |
|------|------|--------|------|
| UseCase文件 | 115 | 20 | 17.4% |
| 单元测试 | 56 | 19 | 33.9% |
| 集成测试 | 35 | 6 | 17.1% |

**总计: 45个文件需要迁移**

---

## 阶段一：迁移社区仪表板相关UseCase（优先级：高）

### Task 1.1: 迁移 GetAbnormalUsersUseCase

**背景:** 获取社区异常用户列表，当前使用`CommunityDashboardService.get_abnormal_users()`

**文件:**
- Modify: `src/app/application/use_cases/community_dashboard/get_abnormal_users_use_case.py`
- Reference: `wxcloudrun/community_dashboard_service.py:45-78`
- Test: `tests/unit/test_community_dashboard.py` (如存在则修改)

**Step 1: 分析旧Service实现**

```python
# 读取旧Service代码
# wxcloudrun/community_dashboard_service.py
```

Run: `cat backend/wxcloudrun/community_dashboard_service.py | grep -A 30 "def get_abnormal_users"`
Expected: 查看旧方法实现逻辑

**Step 2: 检查是否存在对应的Repository**

```bash
# 检查是否已有CommunityDashboardRepository
grep -r "class CommunityDashboardRepository" backend/src/app/infrastructure/persistence/
grep -r "def get_abnormal_users" backend/src/app/domain/repositories/
```

Expected: 如不存在，需要在Task 1.0中先创建Repository

**Step 3: 创建Repository（如需要）**

File: `src/app/domain/repositories/community_dashboard_repository.py`
```python
from abc import ABC, abstractmethod

class CommunityDashboardRepository(ABC):
    @abstractmethod
    def get_abnormal_users(self, community_id: int, days: int = 7):
        pass
```

File: `src/app/infrastructure/persistence/community_dashboard_repository_impl.py`
```python
from sqlalchemy.orm import Session
from src.app.domain.repositories.community_dashboard_repository import CommunityDashboardRepository
from src.app.infrastructure.persistence.database import db

class CommunityDashboardRepositoryImpl(CommunityDashboardRepository):
    def get_abnormal_users(self, community_id: int, days: int = 7):
        from datetime import datetime, timedelta
        from src.app.infrastructure.persistence.models import User, CheckinRecord

        cutoff_date = datetime.now() - timedelta(days=days)

        with db.session.begin():
            abnormal_users = db.session.query(User).join(
                CheckinRecord, User.id == CheckinRecord.user_id
            ).filter(
                User.community_id == community_id,
                CheckinRecord.checkin_time < cutoff_date,
                CheckinRecord.status == 'missed'
            ).all()

        return [user.to_dict() for user in abnormal_users]
```

File: `src/app/infrastructure/persistence/repository_factory.py` (添加)
```python
# 在get_community_dashboard_repository方法中
@staticmethod
def get_community_dashboard_repository() -> CommunityDashboardRepository:
    from src.app.infrastructure.persistence.community_dashboard_repository_impl import CommunityDashboardRepositoryImpl
    return CommunityDashboardRepositoryImpl()
```

**Step 4: 重写UseCase**

File: `src/app/application/use_cases/community_dashboard/get_abnormal_users_use_case.py`
```python
from src.app.application.use_cases.base_use_case import BaseUseCase, UseCaseResult, UseCaseStatus
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory

class GetAbnormalUsersUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.dashboard_repository = RepositoryFactory.get_community_dashboard_repository()

    def execute(self, community_id: int, days: int = 7) -> UseCaseResult:
        # 1. 参数验证
        if not community_id or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID无效',
                errors={'community_id': '必须为正整数'}
            )

        if days <= 0 or days > 30:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='天数参数无效',
                errors={'days': '必须在1-30之间'}
            )

        # 2. 业务逻辑处理
        try:
            abnormal_users = self.dashboard_repository.get_abnormal_users(
                community_id=community_id,
                days=days
            )

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                data={
                    'abnormal_users': abnormal_users,
                    'count': len(abnormal_users),
                    'days': days
                },
                message=f'成功获取{len(abnormal_users)}个异常用户'
            )
        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取异常用户失败: {str(e)}',
                errors={'exception': str(e)}
            )
```

**Step 5: 更新导入语句**

查找所有使用旧Service的文件并更新：

```bash
# 查找使用旧Service的文件
grep -r "from wxcloudrun.community_dashboard_service import" backend/src/
```

File: `src/app/modules/community_dashboard/routes.py` (修改导入)
```python
# 删除
# from wxcloudrun.community_dashboard_service import CommunityDashboardService

# 添加
from src.app.application.use_cases.community_dashboard.get_abnormal_users_use_case import GetAbnormalUsersUseCase
```

**Step 6: 更新路由调用**

File: `src/app/modules/community_dashboard/routes.py`
```python
@community_dashboard_bp.route('/abnormal-users', methods=['GET'])
def get_abnormal_users():
    from flask import request
    from src.app.shared.utils.response_utils import make_succ_response, make_err_response

    community_id = request.args.get('community_id', type=int)
    days = request.args.get('days', 7, type=int)

    use_case = GetAbnormalUsersUseCase()
    result = use_case.execute(community_id=community_id, days=days)

    if result.is_success:
        return make_succ_response(result.data)
    else:
        return make_err_response(result.data or {}, result.message)
```

**Step 7: 运行单元测试**

```bash
cd backend
pytest tests/unit/test_community_dashboard.py -v
```

Expected: 如有测试失败，检查Mock对象是否需要更新

**Step 8: 运行集成测试**

```bash
cd backend
pytest tests/integration/test_community_dashboard.py -v
```

Expected: 验证完整流程是否正常工作

**Step 9: 手动测试（可选）**

```bash
# 启动开发服务器
cd backend && ENV_TYPE=function ./localrun.sh

# 在另一个终端测试
curl -X GET "http://localhost:9999/api/community-dashboard/abnormal-users?community_id=1&days=7"
```

**Step 10: 提交更改**

```bash
cd backend
git add src/app/application/use_cases/community_dashboard/get_abnormal_users_use_case.py
git add src/app/modules/community_dashboard/routes.py
git add src/app/domain/repositories/community_dashboard_repository.py
git add src/app/infrastructure/persistence/community_dashboard_repository_impl.py
git add tests/unit/test_community_dashboard.py
git add tests/integration/test_community_dashboard.py

git commit -m "refactor: 迁移GetAbnormalUsersUseCase到DDD架构

- 创建CommunityDashboardRepository
- 使用RepositoryFactory注入依赖
- 返回标准化的UseCaseResult
- 更新路由层调用方式
- 更新相关测试

Refs: DDD架构迁移Task 1.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 1.2: 迁移 GetCommunityStatsUseCase

**文件:**
- Modify: `src/app/application/use_cases/community_dashboard/get_community_stats_use_case.py`
- Test: `tests/unit/test_community_dashboard.py`

**Step 1: 检查Repository方法**

```bash
grep -A 20 "def get_community_stats" backend/src/app/infrastructure/persistence/community_dashboard_repository_impl.py
```

Expected: 确认Repository中已实现`get_community_stats`方法

**Step 2: 重写UseCase**

File: `src/app/application/use_cases/community_dashboard/get_community_stats_use_case.py`
```python
from src.app.application.use_cases.base_use_case import BaseUseCase, UseCaseResult, UseCaseStatus
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory

class GetCommunityStatsUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.dashboard_repository = RepositoryFactory.get_community_dashboard_repository()

    def execute(self, community_id: int) -> UseCaseResult:
        # 1. 参数验证
        if not community_id or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID无效',
                errors={'community_id': '必须为正整数'}
            )

        # 2. 业务逻辑处理
        try:
            stats = self.dashboard_repository.get_community_stats(community_id)

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                data=stats,
                message='成功获取社区统计信息'
            )
        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取统计信息失败: {str(e)}',
                errors={'exception': str(e)}
            )
```

**Step 3: 更新路由**

File: `src/app/modules/community_dashboard/routes.py`
```python
from src.app.application.use_cases.community_dashboard.get_community_stats_use_case import GetCommunityStatsUseCase

@community_dashboard_bp.route('/stats', methods=['GET'])
def get_community_stats():
    from flask import request
    from src.app.shared.utils.response_utils import make_succ_response, make_err_response

    community_id = request.args.get('community_id', type=int)

    use_case = GetCommunityStatsUseCase()
    result = use_case.execute(community_id=community_id)

    if result.is_success:
        return make_succ_response(result.data)
    else:
        return make_err_response(result.data or {}, result.message)
```

**Step 4: 运行测试**

```bash
cd backend
pytest tests/unit/test_community_dashboard.py::test_get_community_stats -v
pytest tests/integration/test_community_dashboard.py::test_get_community_stats_integration -v
```

**Step 5: 提交更改**

```bash
git add src/app/application/use_cases/community_dashboard/get_community_stats_use_case.py
git add src/app/modules/community_dashboard/routes.py
git commit -m "refactor: 迁移GetCommunityStatsUseCase到DDD架构

Refs: DDD架构迁移Task 1.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 1.3: 迁移 GetPendingEventsUseCase

**步骤同Task 1.2，修改以下文件：**
- `src/app/application/use_cases/community_dashboard/get_pending_events_use_case.py`
- `src/app/modules/community_dashboard/routes.py`

**核心代码模式：**
```python
from src.app.application.use_cases.community_dashboard.get_pending_events_use_case import GetPendingEventsUseCase

@community_dashboard_bp.route('/pending-events', methods=['GET'])
def get_pending_events():
    community_id = request.args.get('community_id', type=int)
    use_case = GetPendingEventsUseCase()
    result = use_case.execute(community_id=community_id)
    # ... 处理结果
```

**提交：**
```bash
git commit -m "refactor: 迁移GetPendingEventsUseCase到DDD架构

Refs: DDD架构迁移Task 1.3
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 1.4: 迁移 GetTrendDataUseCase

**步骤同Task 1.2**

**提交：**
```bash
git commit -m "refactor: 迁移GetTrendDataUseCase到DDD架构

Refs: DDD架构迁移Task 1.4
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 1.5: 迁移 GetUserAbnormalityDetailUseCase

**步骤同Task 1.2**

**提交：**
```bash
git commit -m "refactor: 迁移GetUserAbnormalityDetailUseCase到DDD架构

Refs: DDD架构迁移Task 1.5
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段二：迁移社区签到规则相关UseCase（优先级：高）

### Task 2.1: 迁移 CreateCommunityCheckinRuleUseCase

**文件:**
- Modify: `src/app/application/use_cases/community_checkin/create_community_checkin_rule_use_case.py`
- Reference: `wxcloudrun/community_checkin_rule_service.py`
- Test: `tests/unit/test_community_checkin_rule.py`

**Step 1: 创建Repository接口**

File: `src/app/domain/repositories/community_checkin_rule_repository.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class CommunityCheckinRuleRepository(ABC):
    @abstractmethod
    def create_rule(self, community_id: int, rule_data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_rule_by_id(self, rule_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_rules_by_community(self, community_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_rule(self, rule_id: int) -> bool:
        pass

    @abstractmethod
    def enable_rule(self, rule_id: int) -> bool:
        pass

    @abstractmethod
    def disable_rule(self, rule_id: int) -> bool:
        pass
```

**Step 2: 实现Repository**

File: `src/app/infrastructure/persistence/community_checkin_rule_repository_impl.py`
```python
from sqlalchemy.orm import Session
from src.app.domain.repositories.community_checkin_rule_repository import CommunityCheckinRuleRepository
from src.app.infrastructure.persistence.database import db
from src.app.infrastructure.persistence.models import CommunityCheckinRule

class CommunityCheckinRuleRepositoryImpl(CommunityCheckinRuleRepository):
    def create_rule(self, community_id: int, rule_data: Dict[str, Any], created_by: int) -> Dict[str, Any]:
        with db.session.begin():
            rule = CommunityCheckinRule(
                community_id=community_id,
                created_by=created_by,
                **rule_data
            )
            db.session.add(rule)
            db.session.flush()
            return rule.to_dict()

    def get_rule_by_id(self, rule_id: int) -> Dict[str, Any]:
        with db.session.begin():
            rule = db.session.query(CommunityCheckinRule).filter_by(id=rule_id).first()
            return rule.to_dict() if rule else None

    def get_rules_by_community(self, community_id: int) -> List[Dict[str, Any]]:
        with db.session.begin():
            rules = db.session.query(CommunityCheckinRule).filter_by(
                community_id=community_id
            ).order_by(CommunityCheckinRule.created_at.desc()).all()
            return [rule.to_dict() for rule in rules]

    def update_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        with db.session.begin():
            rule = db.session.query(CommunityCheckinRule).filter_by(id=rule_id).first()
            if not rule:
                return None

            for key, value in rule_data.items():
                setattr(rule, key, value)

            return rule.to_dict()

    def delete_rule(self, rule_id: int) -> bool:
        with db.session.begin():
            rule = db.session.query(CommunityCheckinRule).filter_by(id=rule_id).first()
            if not rule:
                return False
            db.session.delete(rule)
            return True

    def enable_rule(self, rule_id: int) -> bool:
        with db.session.begin():
            rule = db.session.query(CommunityCheckinRule).filter_by(id=rule_id).first()
            if not rule:
                return False
            rule.is_active = True
            return True

    def disable_rule(self, rule_id: int) -> bool:
        with db.session.begin():
            rule = db.session.query(CommunityCheckinRule).filter_by(id=rule_id).first()
            if not rule:
                return False
            rule.is_active = False
            return True
```

**Step 3: 更新RepositoryFactory**

File: `src/app/infrastructure/persistence/repository_factory.py`
```python
# 添加导入
from src.app.domain.repositories.community_checkin_rule_repository import CommunityCheckinRuleRepository

# 添加方法
@staticmethod
def get_community_checkin_rule_repository() -> CommunityCheckinRuleRepository:
    from src.app.infrastructure.persistence.community_checkin_rule_repository_impl import CommunityCheckinRuleRepositoryImpl
    return CommunityCheckinRuleRepositoryImpl()
```

**Step 4: 重写UseCase**

File: `src/app/application/use_cases/community_checkin/create_community_checkin_rule_use_case.py`
```python
from src.app.application.use_cases.base_use_case import BaseUseCase, UseCaseResult, UseCaseStatus
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory

class CreateCommunityCheckinRuleUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def execute(self, community_id: int, rule_data: dict, created_by: int) -> UseCaseResult:
        # 1. 参数验证
        if not community_id or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID无效',
                errors={'community_id': '必须为正整数'}
            )

        if not rule_data.get('name'):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则名称不能为空',
                errors={'name': '必填字段'}
            )

        if not rule_data.get('checkin_time'):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='签到时间不能为空',
                errors={'checkin_time': '必填字段'}
            )

        # 2. 业务逻辑处理
        try:
            rule = self.rule_repository.create_rule(
                community_id=community_id,
                rule_data=rule_data,
                created_by=created_by
            )

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                data=rule,
                message='社区签到规则创建成功'
            )
        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建规则失败: {str(e)}',
                errors={'exception': str(e)}
            )
```

**Step 5: 更新路由**

File: `src/app/modules/community_checkin/routes.py`
```python
from src.app.application.use_cases.community_checkin.create_community_checkin_rule_use_case import CreateCommunityCheckinRuleUseCase

@community_checkin_bp.route('/rules', methods=['POST'])
def create_community_checkin_rule():
    from flask import request, g
    from src.app.shared.utils.response_utils import make_succ_response, make_err_response

    data = request.get_json()
    community_id = data.get('community_id')
    rule_data = {
        'name': data.get('name'),
        'checkin_time': data.get('checkin_time'),
        'timezone': data.get('timezone', 'Asia/Shanghai'),
        'grace_period_minutes': data.get('grace_period_minutes', 30)
    }
    created_by = g.user.get('id') if g.user else None

    use_case = CreateCommunityCheckinRuleUseCase()
    result = use_case.execute(
        community_id=community_id,
        rule_data=rule_data,
        created_by=created_by
    )

    if result.is_success:
        return make_succ_response(result.data, result.message)
    else:
        return make_err_response(result.data or {}, result.message)
```

**Step 6: 更新测试**

File: `tests/unit/test_community_checkin_rule.py`
```python
import pytest
from src.app.application.use_cases.community_checkin.create_community_checkin_rule_use_case import CreateCommunityCheckinRuleUseCase

def test_create_community_checkin_rule_success():
    """测试成功创建社区签到规则"""
    use_case = CreateCommunityCheckinRuleUseCase()
    result = use_case.execute(
        community_id=1,
        rule_data={
            'name': '早签到规则',
            'checkin_time': '08:00',
            'timezone': 'Asia/Shanghai',
            'grace_period_minutes': 30
        },
        created_by=1
    )

    assert result.is_success
    assert result.data['id'] > 0
    assert result.data['name'] == '早签到规则'

def test_create_community_checkin_rule_invalid_community():
    """测试无效社区ID"""
    use_case = CreateCommunityCheckinRuleUseCase()
    result = use_case.execute(
        community_id=-1,
        rule_data={'name': '测试', 'checkin_time': '08:00'},
        created_by=1
    )

    assert result.status == UseCaseStatus.VALIDATION_ERROR
    assert '社区ID无效' in result.message
```

**Step 7: 运行测试**

```bash
cd backend
pytest tests/unit/test_community_checkin_rule.py -v
pytest tests/integration/test_community_checkin_rule.py -v
```

**Step 8: 提交更改**

```bash
git add src/app/domain/repositories/community_checkin_rule_repository.py
git add src/app/infrastructure/persistence/community_checkin_rule_repository_impl.py
git add src/app/infrastructure/persistence/repository_factory.py
git add src/app/application/use_cases/community_checkin/create_community_checkin_rule_use_case.py
git add src/app/modules/community_checkin/routes.py
git add tests/unit/test_community_checkin_rule.py

git commit -m "refactor: 迁移CreateCommunityCheckinRuleUseCase到DDD架构

- 创建CommunityCheckinRuleRepository
- 实现7个核心CRUD方法
- 使用RepositoryFactory注入依赖
- 更新单元测试

Refs: DDD架构迁移Task 2.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.2: 迁移 GetCommunityCheckinRuleUseCase

**复用Task 2.1的Repository，只需重写UseCase**

File: `src/app/application/use_cases/community_checkin/get_community_checkin_rule_use_case.py`
```python
from src.app.application.use_cases.base_use_case import BaseUseCase, UseCaseResult, UseCaseStatus
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory

class GetCommunityCheckinRuleUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def execute(self, rule_id: int) -> UseCaseResult:
        # 1. 参数验证
        if not rule_id or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID无效'
            )

        # 2. 查询规则
        rule = self.rule_repository.get_rule_by_id(rule_id)

        if not rule:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message=f'规则 {rule_id} 不存在'
            )

        # 3. 返回结果
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            data=rule
        )
```

**提交：**
```bash
git commit -m "refactor: 迁移GetCommunityCheckinRuleUseCase到DDD架构

Refs: DDD架构迁移Task 2.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.3: 迁移 GetCommunityCheckinRulesUseCase

**步骤同Task 2.2**

**提交：**
```bash
git commit -m "refactor: 迁移GetCommunityCheckinRulesUseCase到DDD架构

Refs: DDD架构迁移Task 2.3
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.4: 迁移 UpdateCommunityCheckinRuleUseCase

**步骤同Task 2.2**

**提交：**
```bash
git commit -m "refactor: 迁移UpdateCommunityCheckinRuleUseCase到DDD架构

Refs: DDD架构迁移Task 2.4
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.5: 迁移 DeleteCommunityCheckinRuleUseCase

**步骤同Task 2.2**

**提交：**
```bash
git commit -m "refactor: 迁移DeleteCommunityCheckinRuleUseCase到DDD架构

Refs: DDD架构迁移Task 2.5
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.6: 迁移 EnableCommunityCheckinRuleUseCase

**步骤同Task 2.2**

**提交：**
```bash
git commit -m "refactor: 迁移EnableCommunityCheckinRuleUseCase到DDD架构

Refs: DDD架构迁移Task 2.6
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2.7: 迁移 DisableCommunityCheckinRuleUseCase

**步骤同Task 2.2**

**提交：**
```bash
git commit -m "refactor: 迁移DisableCommunityCheckinRuleUseCase到DDD架构

Refs: DDD架构迁移Task 2.7
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段三：迁移社区员工服务相关UseCase（优先级：中）

### Task 3.1: 迁移 ProcessCommunityApplicationUseCase

**文件:**
- Modify: `src/app/application/use_cases/community/process_community_application_use_case.py`
- Reference: `wxcloudrun/community_staff_service.py`

**Step 1: 创建CommunityStaffRepository**

File: `src/app/domain/repositories/community_staff_repository.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class CommunityStaffRepository(ABC):
    @abstractmethod
    def process_application(self, application_id: int, action: str, processed_by: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_super_admin(self, community_id: int, user_id: int) -> bool:
        pass
```

**Step 2: 实现Repository**

File: `src/app/infrastructure/persistence/community_staff_repository_impl.py`
```python
from src.app.domain.repositories.community_staff_repository import CommunityStaffRepository
from src.app.infrastructure.persistence.database import db

class CommunityStaffRepositoryImpl(CommunityStaffRepository):
    def process_application(self, application_id: int, action: str, processed_by: int) -> Dict[str, Any]:
        with db.session.begin():
            from src.app.infrastructure.persistence.models import CommunityApplication

            application = db.session.query(CommunityApplication).filter_by(
                id=application_id
            ).first()

            if not application:
                return None

            application.status = 'approved' if action == 'approve' else 'rejected'
            application.processed_by = processed_by
            application.processed_at = datetime.now()

            return application.to_dict()

    def set_super_admin(self, community_id: int, user_id: int) -> bool:
        with db.session.begin():
            from src.app.infrastructure.persistence.models import CommunityStaff

            # 移除现有超级管理员
            db.session.query(CommunityStaff).filter_by(
                community_id=community_id,
                role='super_admin'
            ).update({'role': 'admin'})

            # 设置新的超级管理员
            staff = CommunityStaff(
                community_id=community_id,
                user_id=user_id,
                role='super_admin'
            )
            db.session.add(staff)

            return True
```

**Step 3: 重写UseCase**

File: `src/app/application/use_cases/community/process_community_application_use_case.py`
```python
from src.app.application.use_cases.base_use_case import BaseUseCase, UseCaseResult, UseCaseStatus
from src.app.infrastructure.persistence.repository_factory import RepositoryFactory

class ProcessCommunityApplicationUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(self, application_id: int, action: str, processed_by: int) -> UseCaseResult:
        # 1. 参数验证
        if not application_id or application_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='申请ID无效'
            )

        if action not in ['approve', 'reject']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='操作类型必须是approve或reject'
            )

        # 2. 处理申请
        try:
            result = self.staff_repository.process_application(
                application_id=application_id,
                action=action,
                processed_by=processed_by
            )

            if not result:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='申请不存在'
                )

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                data=result,
                message=f'申请已{("批准" if action == "approve" else "拒绝")}'
            )
        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'处理申请失败: {str(e)}'
            )
```

**Step 4: 更新路由和测试**

**Step 5: 提交**

```bash
git commit -m "refactor: 迁移ProcessCommunityApplicationUseCase到DDD架构

Refs: DDD架构迁移Task 3.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3.2: 迁移 SetSuperAdminUseCase

**复用Task 3.1的Repository**

**提交：**
```bash
git commit -m "refactor: 迁移SetSuperAdminUseCase到DDD架构

Refs: DDD架构迁移Task 3.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段四：迁移认证和SMS相关UseCase（优先级：中）

### Task 4.1: 迁移 SendVerificationCodeUseCase

**文件:**
- Modify: `src/app/application/use_cases/sms/send_verification_code_use_case.py`
- Reference: `wxcloudrun/sms_service.py`

**注意:** 此UseCase涉及外部SMS服务调用，需要Mock外部依赖

**Step 1: 创建SMS Repository接口**

File: `src/app/domain/repositories/sms_repository.py`
```python
from abc import ABC, abstractmethod

class SMSRepository(ABC):
    @abstractmethod
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        pass

    @abstractmethod
    def check_rate_limit(self, phone_number: str) -> bool:
        pass
```

**Step 2: 实现Repository**

File: `src/app/infrastructure/persistence/sms_repository_impl.py`
```python
from src.app.domain.repositories.sms_repository import SMSRepository
from src.app.infrastructure.persistence.database import db
from datetime import datetime, timedelta

class SMSRepositoryImpl(SMSRepository):
    def send_verification_code(self, phone_number: str, code: str) -> bool:
        # 实际发送SMS的逻辑
        # 这里调用腾讯云或其他SMS服务
        pass

    def check_rate_limit(self, phone_number: str) -> bool:
        with db.session.begin():
            from src.app.infrastructure.persistence.models import SMSLog

            # 检查1分钟内是否已发送
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            recent_log = db.session.query(SMSLog).filter(
                SMSLog.phone_number == phone_number,
                SMSLog.created_at > one_minute_ago
            ).first()

            return recent_log is None
```

**Step 3: 重写UseCase**

**Step 4: 提交**

```bash
git commit -m "refactor: 迁移SendVerificationCodeUseCase到DDD架构

Refs: DDD架构迁移Task 4.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4.2: 迁移 LoginWechatUseCase

**提交：**
```bash
git commit -m "refactor: 迁移LoginWechatUseCase到DDD架构

Refs: DDD架构迁移Task 4.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段五：迁移社区基础服务UseCase（优先级：低）

### Task 5.1: 迁移 GetCommunityDailyStatsUseCase

### Task 5.2: 迁移 GetCommunityCheckinStatsUseCase

**提交：**
```bash
git commit -m "refactor: 迁移社区统计UseCase到DDD架构

- GetCommunityDailyStatsUseCase
- GetCommunityCheckinStatsUseCase

Refs: DDD架构迁移Task 5.1-5.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段六：迁移测试文件（批量处理）

### Task 6.1: 迁移社区相关单元测试（19个文件）

**批量处理策略：**

**Step 1: 更新import语句**

创建批量替换脚本：

File: `scripts/migrate_test_imports.py`
```python
#!/usr/bin/env python3
"""
批量迁移测试文件的import语句
"""
import re
import os

# 旧Service到新Service的映射
MIGRATION_MAP = {
    'from wxcloudrun.community_service import': 'from src.app.modules.community.services import',
    'from wxcloudrun.community_staff_service import': 'from src.app.modules.community.services import',
    'from wxcloudrun.user_service import': 'from src.app.modules.user.services import',
    'from wxcloudrun.community_checkin_rule_service import': 'from src.app.modules.community_checkin.services import',
    'from wxcloudrun.community_event_service import': 'from src.app.modules.events.services import',
    'from wxcloudrun.community_dashboard_service import': 'from src.app.modules.community_dashboard.services import',
}

def migrate_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    modified = False
    for old_import, new_import in MIGRATION_MAP.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f'Updated: {file_path}')

def main():
    test_dirs = [
        'tests/unit/',
        'tests/integration/'
    ]

    for test_dir in test_dirs:
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    migrate_file(file_path)

if __name__ == '__main__':
    main()
```

**Step 2: 运行迁移脚本**

```bash
cd backend
python scripts/migrate_test_imports.py
```

**Step 3: 批量运行测试验证**

```bash
cd backend
pytest tests/unit/ -v --tb=short 2>&1 | tee test_results.txt
```

**Step 4: 修复失败的测试**

对于每个失败的测试：
1. 查看错误信息
2. 更新Mock对象
3. 修复断言

**Step 5: 提交**

```bash
git add tests/
git commit -m "refactor: 批量迁移测试文件到新Service导入

- 更新19个单元测试文件的import语句
- 修复Mock对象和断言
- 所有单元测试通过

Refs: DDD架构迁移Task 6.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6.2: 迁移集成测试（6个文件）

**步骤同Task 6.1**

**提交：**
```bash
git commit -m "refactor: 批量迁移集成测试到新Service

- 更新6个集成测试文件的import语句
- 修复Repository Mock
- 所有集成测试通过

Refs: DDD架构迁移Task 6.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段七：清理旧代码

### Task 7.1: 删除未使用的旧Service文件

**Step 1: 验证没有文件使用旧Service**

```bash
cd backend
grep -r "from wxcloudrun." src/app/ tests/ || echo "No references found"
```

Expected: 没有输出表示已全部迁移

**Step 2: 备份旧Service文件**

```bash
cd backend
mkdir -p .archive/old_services
cp wxcloudrun/*_service.py .archive/old_services/
```

**Step 3: 删除旧Service文件**

```bash
cd wxcloudrun
# 删除已迁移的Service
rm community_dashboard_service.py
rm community_checkin_rule_service.py
rm community_staff_service.py
rm sms_service.py
# ... 其他已迁移的Service
```

**Step 4: 提交**

```bash
git add wxcloudrun/
git commit -m "refactor: 删除已迁移的旧Service文件

- 备份到.archive/old_services/
- 删除7个已迁移的Service文件

Refs: DDD架构迁移Task 7.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 阶段八：最终验证和文档更新

### Task 8.1: 运行完整测试套件

**Step 1: 运行所有单元测试**

```bash
cd backend
make ut
```

Expected: 全部通过

**Step 2: 运行所有集成测试**

```bash
cd backend
make it
```

Expected: 全部通过

**Step 3: 生成测试覆盖率报告**

```bash
cd backend
make test-coverage
```

Expected: 覆盖率没有下降

**Step 4: 手动测试关键功能**

```bash
cd backend
ENV_TYPE=function ./localrun.sh
```

测试端点：
- `POST /api/community-checkin/rules` - 创建规则
- `GET /api/community-dashboard/abnormal-users` - 获取异常用户
- `GET /api/community-dashboard/stats` - 获取统计

**Step 5: 提交验证结果**

```bash
git commit -m "test: 验证DDD架构迁移完成

- 所有单元测试通过 (56/56)
- 所有集成测试通过 (35/35)
- 测试覆盖率保持
- 手动验证关键功能正常

Refs: DDD架构迁移Task 8.1
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8.2: 更新项目文档

**Step 1: 更新架构文档**

File: `docs/architecture.md`
```markdown
## Service层架构

项目采用DDD（领域驱动设计）分层架构：

### 应用层（UseCase）
- 位置: `src/app/application/use_cases/`
- 所有业务逻辑通过UseCase实现
- 继承BaseUseCase，返回UseCaseResult

### 仓储模式
- 接口定义: `src/app/domain/repositories/`
- 实现: `src/app/infrastructure/persistence/*_repository_impl.py`
- 工厂: `RepositoryFactory.get_xxx_repository()`

### 旧Service迁移状态
- ✅ CommunityDashboardService (2026-01-16)
- ✅ CommunityCheckinRuleService (2026-01-16)
- ✅ CommunityStaffService (2026-01-16)
- ✅ SMSService (2026-01-16)
```

**Step 2: 更新开发指南**

File: `docs/development-guide.md`
添加新UseCase创建模板

**Step 3: 提交文档**

```bash
git add docs/
git commit -m "docs: 更新DDD架构相关文档

- 更新架构说明
- 添加UseCase开发指南
- 记录Service迁移历史

Refs: DDD架构迁移Task 8.2
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 执行检查清单

在执行此计划前，确保：

- [ ] 已阅读完整的迁移计划
- [ ] 理解DDD架构和Repository模式
- [ ] 已创建功能分支: `feature/ddd-service-migration`
- [ ] 已备份当前代码状态
- [ ] 已设置开发环境

每个Task完成后：

- [ ] 本地测试全部通过
- [ ] 代码已提交
- [ ] 更新任务进度

## 迁移进度跟踪

| 阶段 | 任务数 | 已完成 | 进度 |
|------|--------|--------|------|
| 阶段一：社区仪表板 | 5 | 0 | 0% |
| 阶段二：签到规则 | 7 | 0 | 0% |
| 阶段三：员工服务 | 2 | 0 | 0% |
| 阶段四：认证SMS | 2 | 0 | 0% |
| 阶段五：社区统计 | 2 | 0 | 0% |
| 阶段六：测试迁移 | 2 | 0 | 0% |
| 阶段七：清理旧码 | 1 | 0 | 0% |
| 阶段八：验证文档 | 2 | 0 | 0% |
| **总计** | **23** | **0** | **0%** |

---

## 风险和注意事项

1. **Repository不存在**: 需要先创建Repository再迁移UseCase
2. **外部依赖**: SMS、微信登录等外部服务需要特别处理Mock
3. **测试数据**: 集成测试需要确保测试数据生成器可用
4. **向后兼容**: 如果有其他系统调用旧Service，需要保留兼容层
5. **数据库事务**: 确保Repository方法正确使用`db.session.begin()`
6. **性能影响**: Repository抽象层可能带来轻微性能开销

---

## 回滚计划

如果迁移遇到问题，按以下步骤回滚：

1. 恢复旧Service文件:
```bash
cp .archive/old_services/*_service.py wxcloudrun/
```

2. 回滚代码:
```bash
git revert <commit-range>
```

3. 验证回滚:
```bash
make ut && make it
```
