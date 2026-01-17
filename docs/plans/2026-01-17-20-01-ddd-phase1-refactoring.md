# DDD Phase 1 重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 DDD 架构审查报告中的 P0 级别问题,建立符合 DDD 原则的领域层和仓储层

**Architecture:**
- 重构领域实体为纯 POPO (Plain Old Python Objects),不依赖 ORM 模型
- 仓储接口返回领域实体,仓储实现负责 ORM ↔ Entity 转换
- UseCase 层不再直接导入 database.flask_models
- 严格遵循依赖倒置原则: 领域层 ← 应用层 → 基础设施层

**Tech Stack:** Python 3.12, Flask 3.1.2, SQLAlchemy 2.0.16, pytest 7.4.3

---

## 前置条件

### 环境准备

```bash
# 确认当前在 backend 目录
pwd
# 预期输出: /Users/qiaoliang/working/code/safeGuard/backend

# 确认虚拟环境已激活
source venv_py312/bin/activate

# 设置测试环境变量
export ENV_TYPE=unit

# 运行 baseline 测试
make ut
# 记录当前测试通过数量
```

### Git Worktree 创建 (可选但推荐)

```bash
cd /Users/qiaoliang/working/code/safeGuard
git worktree add backend-ddd-phase1 dev
cd backend-ddd-phase1/backend
```

### 相关文档阅读

```bash
# 阅读审查报告
cat docs/plans/2026-01-17-16-17-ddd-architecture-review.md

# 阅读代码风格指南
cat docs/code-style-guide.md

# 阅读集成测试编写指南
cat docs/integration-test-writing-guide.md
```

---

## 任务 1: 重构 CheckinRuleEntity 为纯领域实体

**目标**: 将 CheckinRuleEntity 从依赖 ORM 模型改为纯领域实体

**文件**:
- 修改: `src/app/domain/entities/checkin_rule_entity.py`
- 测试: `tests/unit/test_checkin_rule_entity.py` (新建)

### 步骤 1: 编写领域实体的失败测试

**创建**: `tests/unit/test_checkin_rule_entity.py`

```python
"""
测试 CheckinRuleEntity 领域实体
"""
import pytest
from datetime import datetime, time
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity

class TestCheckinRuleEntityCreation:
    """测试领域实体创建"""

    def test_create_entity_with_required_fields(self):
        """测试使用必需字段创建实体"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=1,  # 每天一次
            time_slot_type=0,  # 早晨
            status=1  # 启用
        )

        assert entity.rule_id == 1
        assert entity.user_id == 100
        assert entity.rule_name == "晨间打卡"
        assert entity.frequency_type == 1
        assert entity.time_slot_type == 0
        assert entity.status == 1

    def test_entity_without_orm_dependency(self):
        """测试实体不依赖 ORM 模型"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        # 不应该有 _rule 属性
        assert not hasattr(entity, '_rule')
        # 应该有直接的属性
        assert hasattr(entity, 'rule_id')
        assert hasattr(entity, 'user_id')

class TestCheckinRuleEntityBusinessLogic:
    """测试实体业务逻辑"""

    def test_enable_rule(self):
        """测试启用规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=0  # 禁用
        )

        entity.enable()

        assert entity.status == 1
        assert entity.updated_at is not None

    def test_disable_rule(self):
        """测试禁用规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1  # 启用
        )

        entity.disable()

        assert entity.status == 0

    def test_soft_delete_rule(self):
        """测试软删除规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        entity.soft_delete()

        assert entity.status == 2  # 删除状态
        assert entity.is_deleted is True

class TestCheckinRuleEntityValidation:
    """测试实体验证逻辑"""

    def test_update_with_invalid_frequency_type(self):
        """测试使用无效的频率类型更新"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        # 无效的频率类型不应该更新
        original_frequency = entity.frequency_type
        entity.update(frequency_type=999)

        assert entity.frequency_type == original_frequency

    def test_update_with_invalid_time_format(self):
        """测试使用无效的时间格式更新"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=4,  # 自定义时间
            status=1
        )

        # 无效的时间格式不应该更新
        original_time = entity.custom_time
        entity.update(custom_time="invalid-time")

        assert entity.custom_time == original_time

class TestCheckinRuleEntityCalculations:
    """测试实体计算逻辑"""

    def test_calculate_planned_checkin_time_for_morning(self):
        """测试计算早晨打卡时间"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=1,
            time_slot_type=0,  # 早晨
            status=1
        )

        planned_time = entity.calculate_planned_checkin_time()

        assert planned_time is not None
        assert planned_time.hour == 8
        assert planned_time.minute == 0

    def test_calculate_planned_checkin_time_for_custom_time(self):
        """测试计算自定义打卡时间"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="自定义打卡",
            frequency_type=1,
            time_slot_type=4,  # 自定义时间
            custom_time="09:30:00",
            status=1
        )

        planned_time = entity.calculate_planned_checkin_time()

        assert planned_time is not None
        assert planned_time.hour == 9
        assert planned_time.minute == 30
```

**运行测试**:

```bash
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_checkin_rule_entity.py -v
```

**预期输出**: FAIL - "CheckinRuleEntity does not have 'create' method"

---

### 步骤 2: 重构 CheckinRuleEntity 为纯领域实体

**修改**: `src/app/domain/entities/checkin_rule_entity.py`

完整替换为以下内容:

```python
"""
打卡规则领域实体

纯领域实体,不依赖 ORM 模型,遵循 DDD 原则
"""
from typing import Optional
from datetime import datetime, time
from dataclasses import dataclass, field


@dataclass
class CheckinRuleEntity:
    """
    打卡规则领域实体

    这是一个纯领域实体,不依赖任何 ORM 框架。
    所有属性都通过数据类定义,确保不可变性和值对象语义。
    """
    # 基础属性
    rule_id: int
    user_id: int
    rule_name: str
    frequency_type: int  # 0:每天, 1:每周, 2:自定义
    time_slot_type: int  # 0:早晨, 1:中午, 2:傍晚, 3:晚上, 4:自定义
    status: int  # 0:禁用, 1:启用, 2:删除

    # 可选属性
    community_id: Optional[int] = None
    icon_url: Optional[str] = None
    custom_time: Optional[str] = None  # HH:MM:SS 格式
    week_days: Optional[str] = None  # 逗号分隔的星期几,如 "1,3,5"
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None

    # 时间戳
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    # 领域事件(由聚合根管理)
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(cls, rule_id: int, user_id: int, rule_name: str,
              frequency_type: int, time_slot_type: int, status: int = 1,
              **kwargs) -> 'CheckinRuleEntity':
        """
        工厂方法:创建打卡规则实体

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_name: 规则名称
            frequency_type: 频率类型
            time_slot_type: 时间段类型
            status: 状态(默认启用)
            **kwargs: 其他可选属性

        Returns:
            CheckinRuleEntity: 打卡规则实体
        """
        return cls(
            rule_id=rule_id,
            user_id=user_id,
            rule_name=rule_name[:100],  # 限制长度
            frequency_type=frequency_type,
            time_slot_type=time_slot_type,
            status=status,
            community_id=kwargs.get('community_id'),
            icon_url=kwargs.get('icon_url'),
            custom_time=kwargs.get('custom_time'),
            week_days=kwargs.get('week_days'),
            custom_start_date=kwargs.get('custom_start_date'),
            custom_end_date=kwargs.get('custom_end_date')
        )

    @property
    def is_enabled(self) -> bool:
        """规则是否启用"""
        return self.status == 1

    @property
    def is_deleted(self) -> bool:
        """规则是否已删除"""
        return self.status == 2

    def enable(self) -> None:
        """启用规则"""
        self.status = 1
        self.updated_at = datetime.now()

    def disable(self) -> None:
        """禁用规则"""
        self.status = 0
        self.updated_at = datetime.now()

    def soft_delete(self) -> None:
        """软删除规则"""
        self.status = 2
        self.updated_at = datetime.now()

    def update(self, name: Optional[str] = None, frequency_type: Optional[int] = None,
               time_slot_type: Optional[int] = None, custom_time: Optional[str] = None,
               icon_url: Optional[str] = None) -> None:
        """
        更新规则

        Args:
            name: 规则名称
            frequency_type: 频率类型
            time_slot_type: 时间段类型
            custom_time: 自定义时间
            icon_url: 图标URL
        """
        if name is not None and len(name.strip()) > 0:
            self.rule_name = name.strip()[:100]

        if frequency_type is not None and frequency_type in [0, 1, 2]:
            self.frequency_type = frequency_type

        if time_slot_type is not None and time_slot_type in [0, 1, 2, 3, 4]:
            self.time_slot_type = time_slot_type

        if custom_time is not None:
            # 验证时间格式 HH:MM:SS
            try:
                time.fromisoformat(custom_time)
                self.custom_time = custom_time
            except ValueError:
                pass  # 忽略无效的时间格式

        if icon_url is not None:
            if icon_url.startswith(('http://', 'https://')) and len(icon_url) <= 500:
                self.icon_url = icon_url.strip()

        self.updated_at = datetime.now()

    def calculate_planned_checkin_time(self, reference_date: Optional[datetime] = None) -> Optional[datetime]:
        """
        计算计划的打卡时间

        Args:
            reference_date: 参考日期(默认为今天)

        Returns:
            计划打卡时间,如果无法计算则返回 None
        """
        if reference_date is None:
            reference_date = datetime.now()

        if not self.is_enabled or self.is_deleted:
            return None

        # 自定义时间
        if self.time_slot_type == 4 and self.custom_time:
            try:
                time_obj = time.fromisoformat(self.custom_time)
                return datetime.combine(reference_date.date(), time_obj)
            except ValueError:
                return None

        # 预定义时间段
        time_mapping = {
            0: time(8, 0),   # 早晨
            1: time(12, 0),  # 中午
            2: time(18, 0),  # 傍晚
            3: time(21, 0)   # 晚上
        }

        time_obj = time_mapping.get(self.time_slot_type)
        if time_obj:
            return datetime.combine(reference_date.date(), time_obj)

        return None

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRuleEntity):
            return False
        return self.rule_id == other.rule_id

    def __hash__(self) -> int:
        return hash(self.rule_id)
```

**运行测试**:

```bash
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_checkin_rule_entity.py -v
```

**预期输出**: PASS - 所有测试通过

---

### 步骤 3: 提交领域实体重构

```bash
git add src/app/domain/entities/checkin_rule_entity.py \
        tests/unit/test_checkin_rule_entity.py

git commit -m "refactor: 重构 CheckinRuleEntity 为纯领域实体

- 移除对 ORM 模型的依赖,使用 dataclass 定义
- 添加 create() 工厂方法
- 实现纯领域实体的业务逻辑方法
- 添加完整的单元测试
- 符合 DDD 依赖倒置原则

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2: 重构 CheckinRecordEntity 为纯领域实体

**目标**: 将 CheckinRecordEntity 从依赖 ORM 模型改为纯领域实体

**文件**:
- 修改: `src/app/domain/entities/checkin_record_entity.py`
- 测试: `tests/unit/test_checkin_record_entity.py` (新建)

### 步骤 1: 编写打卡记录实体的失败测试

**创建**: `tests/unit/test_checkin_record_entity.py`

```python
"""
测试 CheckinRecordEntity 领域实体
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_record_entity import CheckinRecordEntity

class TestCheckinRecordEntityCreation:
    """测试打卡记录实体创建"""

    def test_create_entity_with_required_fields(self):
        """测试使用必需字段创建实体"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        assert entity.record_id == 1
        assert entity.rule_id == 10
        assert entity.user_id == 100
        assert entity.checkin_status == 0  # 默认为未打卡

    def test_entity_without_orm_dependency(self):
        """测试实体不依赖 ORM 模型"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        # 不应该有 _record 属性
        assert not hasattr(entity, '_record')

class TestCheckinRecordEntityStateTransitions:
    """测试状态转换"""

    def test_complete_checkin(self):
        """测试完成打卡"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.complete()

        assert entity.is_completed is True
        assert entity.checkin_time is not None

    def test_mark_as_missed(self):
        """测试标记为错过"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.mark_missed()

        assert entity.is_missed is True
        assert entity.checkin_status == 2

    def test_cancel_checkin(self):
        """测试取消打卡"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.cancel()

        assert entity.is_cancelled is True
        assert entity.checkin_status == 3

class TestCheckinRecordEntityBusinessRules:
    """测试业务规则"""

    def test_is_overdue(self):
        """测试超时检查"""
        from datetime import timedelta

        planned_time = datetime.now() - timedelta(hours=5)
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=planned_time
        )

        # 超过4小时应该算超时
        assert entity.is_overdue() is True

    def test_get_checkin_delay(self):
        """测试获取打卡延迟"""
        from datetime import timedelta

        planned_time = datetime.now() - timedelta(hours=2)
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=planned_time
        )

        entity.complete(checkin_time=datetime.now())
        delay = entity.get_checkin_delay()

        assert delay is not None
        assert delay.total_seconds() > 0
```

**运行测试**:

```bash
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_checkin_record_entity.py -v
```

**预期输出**: FAIL - "CheckinRecordEntity does not have 'create' method"

---

### 步骤 2: 重构 CheckinRecordEntity 为纯领域实体

**修改**: `src/app/domain/entities/checkin_record_entity.py`

完整替换为以下内容:

```python
"""
打卡记录领域实体

纯领域实体,不依赖 ORM 模型,遵循 DDD 原则
"""
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class CheckinStatus(Enum):
    """打卡状态枚举"""
    PENDING = 0  # 未打卡
    COMPLETED = 1  # 已打卡
    MISSED = 2  # 已错过
    CANCELLED = 3  # 已取消


@dataclass
class CheckinRecordEntity:
    """
    打卡记录领域实体

    这是一个纯领域实体,不依赖任何 ORM 框架。
    """
    # 基础属性
    record_id: int
    rule_id: int
    user_id: int
    planned_checkin_time: datetime

    # 状态
    checkin_status: int = CheckinStatus.PENDING.value

    # 可选属性
    community_rule_id: Optional[int] = None
    solo_user_id: Optional[int] = None  # 监督用户ID
    checkin_time: Optional[datetime] = None

    # 时间戳
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)

    # 领域事件
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def create(cls, record_id: int, rule_id: int, user_id: int,
              planned_checkin_time: datetime, **kwargs) -> 'CheckinRecordEntity':
        """
        工厂方法:创建打卡记录实体

        Args:
            record_id: 记录ID
            rule_id: 个人规则ID
            user_id: 用户ID
            planned_checkin_time: 计划打卡时间
            **kwargs: 其他可选属性

        Returns:
            CheckinRecordEntity: 打卡记录实体
        """
        return cls(
            record_id=record_id,
            rule_id=rule_id,
            user_id=user_id,
            planned_checkin_time=planned_checkin_time,
            community_rule_id=kwargs.get('community_rule_id'),
            solo_user_id=kwargs.get('solo_user_id'),
            checkin_status=kwargs.get('checkin_status', CheckinStatus.PENDING.value),
            checkin_time=kwargs.get('checkin_time')
        )

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.checkin_status == CheckinStatus.COMPLETED.value

    @property
    def is_missed(self) -> bool:
        """是否已错过"""
        return self.checkin_status == CheckinStatus.MISSED.value

    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.checkin_status == CheckinStatus.CANCELLED.value

    @property
    def actual_checkin_time(self) -> Optional[datetime]:
        """获取实际打卡时间"""
        return self.checkin_time

    def complete(self, checkin_time: Optional[datetime] = None) -> None:
        """
        完成打卡

        Args:
            checkin_time: 打卡时间(默认为当前时间)
        """
        if checkin_time is None:
            checkin_time = datetime.now()

        self.checkin_status = CheckinStatus.COMPLETED.value
        self.checkin_time = checkin_time
        self.updated_at = datetime.now()

    def mark_missed(self) -> None:
        """标记为错过"""
        self.checkin_status = CheckinStatus.MISSED.value
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """取消打卡"""
        self.checkin_status = CheckinStatus.CANCELLED.value
        self.updated_at = datetime.now()

    def update_checkin_time(self, checkin_time: datetime) -> None:
        """
        更新打卡时间

        Args:
            checkin_time: 打卡时间
        """
        self.checkin_time = checkin_time
        self.updated_at = datetime.now()

    def is_overdue(self, reference_time: Optional[datetime] = None) -> bool:
        """
        检查是否已超时

        Args:
            reference_time: 参考时间(默认为当前时间)

        Returns:
            bool: 是否已超时
        """
        if reference_time is None:
            reference_time = datetime.now()

        # 超过计划打卡时间4小时视为超时
        overdue_threshold = timedelta(hours=4)
        return reference_time > (self.planned_checkin_time + overdue_threshold)

    def get_checkin_delay(self) -> Optional[timedelta]:
        """
        获取打卡延迟时间

        Returns:
            延迟时间,如果未打卡或已取消则返回 None
        """
        if not self.is_completed or self.checkin_time is None:
            return None

        return self.checkin_time - self.planned_checkin_time

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRecordEntity):
            return False
        return self.record_id == other.record_id

    def __hash__(self) -> int:
        return hash(self.record_id)
```

**运行测试**:

```bash
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_checkin_record_entity.py -v
```

**预期输出**: PASS - 所有测试通过

---

### 步骤 3: 提交打卡记录实体重构

```bash
git add src/app/domain/entities/checkin_record_entity.py \
        tests/unit/test_checkin_record_entity.py

git commit -m "refactor: 重构 CheckinRecordEntity 为纯领域实体

- 移除对 ORM 模型的依赖,使用 dataclass 定义
- 添加 create() 工厂方法
- 添加 CheckinStatus 枚举
- 实现状态转换业务逻辑
- 添加完整的单元测试
- 符合 DDD 依赖倒置原则

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3: 重构仓储接口返回领域实体

**目标**: 更新仓储接口,使其返回领域实体而非 ORM 模型

**文件**:
- 修改: `src/app/domain/repositories/checkin_rule_repository.py`
- 修改: `src/app/domain/repositories/checkin_record_repository.py` (如果存在)

### 步骤 1: 更新 CheckinRuleRepository 接口

**修改**: `src/app/domain/repositories/checkin_rule_repository.py`

完整替换为以下内容:

```python
"""
打卡规则仓储接口

仓储接口定义在领域层,遵循依赖倒置原则
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_rule_entity import CheckinRuleEntity


class CheckinRuleRepository(ABC):
    """打卡规则仓储接口"""

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        """
        根据ID查找打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            Optional[CheckinRuleEntity]: 领域实体,不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRuleEntity]:
        """
        根据用户ID查找打卡规则

        Args:
            user_id: 用户ID
            include_disabled: 是否包含禁用的规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_active_by_user_id(self, user_id: int) -> List[CheckinRuleEntity]:
        """
        根据用户ID查找启用的打卡规则

        Args:
            user_id: 用户ID

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def save_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        保存打卡规则实体

        Args:
            entity: 打卡规则领域实体

        Returns:
            CheckinRuleEntity: 保存后的实体(包含生成的ID)
        """
        pass

    @abstractmethod
    def update_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        更新打卡规则实体

        Args:
            entity: 打卡规则领域实体

        Returns:
            CheckinRuleEntity: 更新后的实体
        """
        pass

    @abstractmethod
    def delete(self, rule_id: int) -> bool:
        """
        删除打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    def soft_delete(self, rule_id: int) -> bool:
        """
        软删除打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    def find_active_rules(self) -> List[CheckinRuleEntity]:
        """
        查找所有启用的打卡规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_all_day_rules(self) -> List[CheckinRuleEntity]:
        """
        查找所有启用的全天打卡规则

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_by_ids(self, rule_ids: List[int]) -> List[CheckinRuleEntity]:
        """
        根据ID列表查找打卡规则

        Args:
            rule_ids: 规则ID列表

        Returns:
            List[CheckinRuleEntity]: 领域实体列表
        """
        pass
```

---

### 步骤 2: 创建或更新 CheckinRecordRepository 接口

**检查文件是否存在**:

```bash
ls -la src/app/domain/repositories/checkin_record_repository.py
```

如果不存在,**创建**: `src/app/domain/repositories/checkin_record_repository.py`

```python
"""
打卡记录仓储接口

仓储接口定义在领域层,遵循依赖倒置原则
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_record_entity import CheckinRecordEntity


class CheckinRecordRepository(ABC):
    """打卡记录仓储接口"""

    @abstractmethod
    def find_by_id(self, record_id: int) -> Optional[CheckinRecordEntity]:
        """
        根据ID查找打卡记录

        Args:
            record_id: 记录ID

        Returns:
            Optional[CheckinRecordEntity]: 领域实体,不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_rule_id(self, rule_id: int) -> List[CheckinRecordEntity]:
        """
        根据规则ID查找打卡记录

        Args:
            rule_id: 规则ID

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, limit: int = 100) -> List[CheckinRecordEntity]:
        """
        根据用户ID查找打卡记录

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def find_today_records(self, user_id: int, rule_id: int) -> List[CheckinRecordEntity]:
        """
        查找用户今天对某个规则的打卡记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            List[CheckinRecordEntity]: 领域实体列表
        """
        pass

    @abstractmethod
    def save_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        保存打卡记录实体

        Args:
            entity: 打卡记录领域实体

        Returns:
            CheckinRecordEntity: 保存后的实体(包含生成的ID)
        """
        pass

    @abstractmethod
    def update_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        更新打卡记录实体

        Args:
            entity: 打卡记录领域实体

        Returns:
            CheckinRecordEntity: 更新后的实体
        """
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """
        删除打卡记录

        Args:
            record_id: 记录ID

        Returns:
            bool: 是否删除成功
        """
        pass
```

---

### 步骤 3: 提交仓储接口更新

```bash
git add src/app/domain/repositories/checkin_rule_repository.py \
        src/app/domain/repositories/checkin_record_repository.py

git commit -m "refactor: 更新仓储接口返回领域实体

- CheckinRuleRepository 接口方法返回 CheckinRuleEntity
- 新增 CheckinRecordRepository 接口
- 所有 save/update 方法改为 save_entity/update_entity
- 符合 DDD 仓储模式原则
- 领域层不再依赖基础设施层

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4: 重构 SQLAlchemyCheckinRuleRepository 实现

**目标**: 更新仓储实现,负责 ORM ↔ Entity 转换

**文件**:
- 修改: `src/app/infrastructure/persistence/sqlalchemy_checkin_rule_repository.py`
- 测试: `tests/unit/test_sqlalchemy_checkin_rule_repository.py` (新建)

### 步骤 1: 编写仓储实现的失败测试

**创建**: `tests/unit/test_sqlalchemy_checkin_rule_repository.py`

```python
"""
测试 SQLAlchemyCheckinRuleRepository
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.infrastructure.persistence.sqlalchemy_checkin_rule_repository import SQLAlchemyCheckinRuleRepository

class TestSQLAlchemyCheckinRuleRepositoryEntityConversion:
    """测试实体转换"""

    def test_find_by_id_returns_entity_not_orm(self):
        """测试 find_by_id 返回领域实体而非 ORM 模型"""
        # 这个测试需要数据库,使用测试数据
        pass  # 将在集成测试中实现

    def test_save_entity_converts_to_orm(self):
        """测试 save_entity 将实体转换为 ORM 模型"""
        entity = CheckinRuleEntity.create(
            rule_id=1,  # 假设已存在
            user_id=100,
            rule_name="测试规则",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        # 验证实体属性
        assert entity.rule_id == 1
        assert entity.user_id == 100
        # 应该是纯实体,不包含 ORM 模型
        assert not hasattr(entity, '_rule')
```

**运行测试**:

```bash
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_sqlalchemy_checkin_rule_repository.py -v
```

**预期输出**: FAIL 或 SKIP (需要数据库)

---

### 步骤 2: 重构 SQLAlchemyCheckinRuleRepository 实现

**修改**: `src/app/infrastructure/persistence/sqlalchemy_checkin_rule_repository.py`

完整替换为以下内容:

```python
"""
打卡规则仓储 SQLAlchemy 实现

负责 ORM 模型与领域实体之间的转换
"""
from typing import List, Optional
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRule
from app.domain.repositories.checkin_rule_repository import CheckinRuleRepository
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity


class SQLAlchemyCheckinRuleRepository(CheckinRuleRepository):
    """打卡规则仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话,如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        """根据ID查找打卡规则"""
        orm_model = self.session.get(CheckinRule, rule_id)
        if not orm_model:
            return None
        return self._to_entity(orm_model)

    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRuleEntity]:
        """根据用户ID查找打卡规则"""
        stmt = select(CheckinRule).where(CheckinRule.user_id == user_id)

        if not include_disabled:
            stmt = stmt.where(CheckinRule.status == 1)

        stmt = stmt.order_by(CheckinRule.created_at.desc())
        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_active_by_user_id(self, user_id: int) -> List[CheckinRuleEntity]:
        """根据用户ID查找启用的打卡规则"""
        return self.find_by_user_id(user_id, include_disabled=False)

    def save_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        保存打卡规则实体

        将领域实体转换为 ORM 模型并保存
        """
        orm_model = CheckinRule(
            rule_id=entity.rule_id,
            user_id=entity.user_id,
            rule_name=entity.rule_name,
            frequency_type=entity.frequency_type,
            time_slot_type=entity.time_slot_type,
            status=entity.status,
            community_id=entity.community_id,
            icon_url=entity.icon_url,
            custom_time=entity.custom_time,
            week_days=entity.week_days,
            custom_start_date=entity.custom_start_date,
            custom_end_date=entity.custom_end_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        self.session.add(orm_model)
        self.session.flush()

        # 返回更新后的实体
        return self._to_entity(orm_model)

    def update_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        更新打卡规则实体

        将领域实体转换为 ORM 模型并更新
        """
        orm_model = self.session.get(CheckinRule, entity.rule_id)
        if not orm_model:
            raise ValueError(f"CheckinRule with id {entity.rule_id} not found")

        # 更新 ORM 模型属性
        orm_model.rule_name = entity.rule_name
        orm_model.frequency_type = entity.frequency_type
        orm_model.time_slot_type = entity.time_slot_type
        orm_model.status = entity.status
        orm_model.community_id = entity.community_id
        orm_model.icon_url = entity.icon_url
        orm_model.custom_time = entity.custom_time
        orm_model.week_days = entity.week_days
        orm_model.custom_start_date = entity.custom_start_date
        orm_model.custom_end_date = entity.custom_end_date
        orm_model.updated_at = entity.updated_at

        self.session.flush()

        return self._to_entity(orm_model)

    def delete(self, rule_id: int) -> bool:
        """删除打卡规则"""
        orm_model = self.find_by_id(rule_id)
        if orm_model:
            # 需要先获取 ORM 模型
            model = self.session.get(CheckinRule, rule_id)
            if model:
                self.session.delete(model)
                self.session.flush()
                return True
        return False

    def soft_delete(self, rule_id: int) -> bool:
        """软删除打卡规则"""
        entity = self.find_by_id(rule_id)
        if entity:
            entity.soft_delete()
            return self.update_entity(entity) is not None
        return False

    def find_active_rules(self) -> List[CheckinRuleEntity]:
        """查找所有启用的打卡规则"""
        from sqlalchemy import and_

        stmt = select(CheckinRule).where(
            and_(
                CheckinRule.status != 2  # 排除已删除的规则
            )
        )

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_all_day_rules(self) -> List[CheckinRuleEntity]:
        """查找所有启用的全天打卡规则"""
        from sqlalchemy import and_

        stmt = select(CheckinRule).where(
            and_(
                CheckinRule.status == 1,  # 已启用
                CheckinRule.time_slot_type == 5  # 全天规则
            )
        )

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_by_ids(self, rule_ids: List[int]) -> List[CheckinRuleEntity]:
        """根据ID列表查找打卡规则"""
        if not rule_ids:
            return []

        stmt = select(CheckinRule).where(CheckinRule.rule_id.in_(rule_ids))
        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def _to_entity(self, orm_model: CheckinRule) -> CheckinRuleEntity:
        """
        将 ORM 模型转换为领域实体

        Args:
            orm_model: SQLAlchemy CheckinRule 模型

        Returns:
            CheckinRuleEntity: 领域实体
        """
        return CheckinRuleEntity(
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            rule_name=orm_model.rule_name,
            frequency_type=orm_model.frequency_type,
            time_slot_type=orm_model.time_slot_type,
            status=orm_model.status,
            community_id=orm_model.community_id,
            icon_url=orm_model.icon_url,
            custom_time=orm_model.custom_time,
            week_days=orm_model.week_days,
            custom_start_date=orm_model.custom_start_date,
            custom_end_date=orm_model.custom_end_date,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )
```

---

### 步骤 3: 提交仓储实现重构

```bash
git add src/app/infrastructure/persistence/sqlalchemy_checkin_rule_repository.py \
        tests/unit/test_sqlalchemy_checkin_rule_repository.py

git commit -m "refactor: 重构 SQLAlchemyCheckinRuleRepository 返回领域实体

- 添加 _to_entity() 方法转换 ORM → Entity
- save_entity() 将 Entity 转换为 ORM 后保存
- update_entity() 将 Entity 转换为 ORM 后更新
- 所有查询方法返回领域实体
- 符合 DDD 仓储模式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 5: 创建 SQLAlchemyCheckinRecordRepository 实现

**目标**: 创建打卡记录的仓储实现

**文件**:
- 创建: `src/app/infrastructure/persistence/sqlalchemy_checkin_record_repository.py`
- 测试: `tests/unit/test_sqlalchemy_checkin_record_repository.py` (新建)

### 步骤 1: 创建仓储实现

**创建**: `src/app/infrastructure/persistence/sqlalchemy_checkin_record_repository.py`

```python
"""
打卡记录仓储 SQLAlchemy 实现

负责 ORM 模型与领域实体之间的转换
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRecord
from app.domain.repositories.checkin_record_repository import CheckinRecordRepository
from app.domain.entities.checkin_record_entity import CheckinRecordEntity


class SQLAlchemyCheckinRecordRepository(CheckinRecordRepository):
    """打卡记录仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话,如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, record_id: int) -> Optional[CheckinRecordEntity]:
        """根据ID查找打卡记录"""
        orm_model = self.session.get(CheckinRecord, record_id)
        if not orm_model:
            return None
        return self._to_entity(orm_model)

    def find_by_rule_id(self, rule_id: int) -> List[CheckinRecordEntity]:
        """根据规则ID查找打卡记录"""
        stmt = select(CheckinRecord).where(
            CheckinRecord.rule_id == rule_id
        ).order_by(CheckinRecord.created_at.desc())

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_by_user_id(self, user_id: int, limit: int = 100) -> List[CheckinRecordEntity]:
        """根据用户ID查找打卡记录"""
        stmt = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id
        ).order_by(CheckinRecord.created_at.desc()).limit(limit)

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_today_records(self, user_id: int, rule_id: int) -> List[CheckinRecordEntity]:
        """查找用户今天对某个规则的打卡记录"""
        today = datetime.now().date()

        stmt = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id,
            CheckinRecord.rule_id == rule_id,
            db.func.date(CheckinRecord.created_at) == today
        ).order_by(CheckinRecord.created_at.desc())

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def save_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        保存打卡记录实体

        将领域实体转换为 ORM 模型并保存
        """
        orm_model = CheckinRecord(
            record_id=entity.record_id,
            rule_id=entity.rule_id,
            user_id=entity.user_id,
            community_rule_id=entity.community_rule_id,
            solo_user_id=entity.solo_user_id,
            planned_checkin_time=entity.planned_checkin_time,
            checkin_status=entity.checkin_status,
            checkin_time=entity.checkin_time,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        self.session.add(orm_model)
        self.session.flush()

        return self._to_entity(orm_model)

    def update_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        更新打卡记录实体

        将领域实体转换为 ORM 模型并更新
        """
        orm_model = self.session.get(CheckinRecord, entity.record_id)
        if not orm_model:
            raise ValueError(f"CheckinRecord with id {entity.record_id} not found")

        # 更新 ORM 模型属性
        orm_model.checkin_status = entity.checkin_status
        orm_model.checkin_time = entity.checkin_time
        orm_model.updated_at = entity.updated_at

        self.session.flush()

        return self._to_entity(orm_model)

    def delete(self, record_id: int) -> bool:
        """删除打卡记录"""
        orm_model = self.session.get(CheckinRecord, record_id)
        if orm_model:
            self.session.delete(orm_model)
            self.session.flush()
            return True
        return False

    def _to_entity(self, orm_model: CheckinRecord) -> CheckinRecordEntity:
        """
        将 ORM 模型转换为领域实体

        Args:
            orm_model: SQLAlchemy CheckinRecord 模型

        Returns:
            CheckinRecordEntity: 领域实体
        """
        return CheckinRecordEntity(
            record_id=orm_model.record_id,
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            planned_checkin_time=orm_model.planned_checkin_time,
            community_rule_id=orm_model.community_rule_id,
            solo_user_id=orm_model.solo_user_id,
            checkin_status=orm_model.checkin_status,
            checkin_time=orm_model.checkin_time,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )
```

---

### 步骤 2: 更新 RepositoryFactory

**修改**: `src/app/infrastructure/persistence/repository_factory.py`

在 RepositoryFactory 中添加 CheckinRecordRepository 的方法:

```python
@classmethod
def get_checkin_record_repository(cls) -> CheckinRecordRepository:
    """
    获取打卡记录仓储实例

    Returns:
        CheckinRecordRepository: 打卡记录仓储实例
    """
    if cls._checkin_record_repository is None:
        from app.infrastructure.persistence.sqlalchemy_checkin_record_repository import (
            SQLAlchemyCheckinRecordRepository
        )
        from app.domain.repositories.checkin_record_repository import CheckinRecordRepository

        cls._checkin_record_repository = SQLAlchemyCheckinRecordRepository()
    return cls._checkin_record_repository
```

---

### 步骤 3: 提交仓储实现

```bash
git add src/app/infrastructure/persistence/sqlalchemy_checkin_record_repository.py \
        src/app/infrastructure/persistence/repository_factory.py

git commit -m "feat: 创建 SQLAlchemyCheckinRecordRepository 实现

- 实现打卡记录仓储接口
- 添加 _to_entity() 方法转换 ORM → Entity
- save_entity/update_entity 方法处理实体转换
- 更新 RepositoryFactory 添加仓储实例
- 符合 DDD 仓储模式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 6: 重构 CheckinRuleAggregate 使用纯领域实体

**目标**: 更新聚合根使用新的纯领域实体

**文件**:
- 修改: `src/app/domain/aggregates/checkin_rule_aggregate.py`
- 测试: `tests/unit/test_checkin_rule_aggregate.py` (更新或新建)

### 步骤 1: 更新聚合根

**修改**: `src/app/domain/aggregates/checkin_rule_aggregate.py`

完整替换为以下内容:

```python
"""
打卡规则聚合根

打卡规则聚合是打卡规则相关的核心业务概念,包含规则本身及其关联的打卡记录。
"""
from typing import List, Optional
from datetime import datetime

from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.domain.entities.checkin_record_entity import CheckinRecordEntity
from app.domain.events.checkin_events import (
    CheckinCompletedEvent,
    CheckinMissedEvent,
    CheckinCancelledEvent,
    CheckinRuleEnabledEvent,
    CheckinRuleDisabledEvent
)
from app.domain.events.event_bus import event_bus


class CheckinRuleAggregate:
    """
    打卡规则聚合根

    聚合边界:
    - CheckinRuleEntity(打卡规则实体)
    - CheckinRecordEntity(打卡记录)

    业务不变性:
    - 规则必须关联到一个有效的用户
    - 规则的启用/禁用必须符合业务规则
    - 打卡记录必须符合规则的时间要求
    """

    def __init__(self, rule_entity: CheckinRuleEntity):
        """
        初始化打卡规则聚合根

        Args:
            rule_entity: 打卡规则实体
        """
        self._rule = rule_entity
        self._records: List[CheckinRecordEntity] = []
        self._events: List = []

    @property
    def rule(self) -> CheckinRuleEntity:
        """获取打卡规则实体"""
        return self._rule

    @property
    def records(self) -> List[CheckinRecordEntity]:
        """获取打卡记录列表"""
        return self._records

    @property
    def events(self) -> List:
        """获取待发布的领域事件"""
        return self._events

    def add_record(self, record: CheckinRecordEntity) -> None:
        """
        添加打卡记录

        Args:
            record: 打卡记录实体
        """
        self._records.append(record)

    def complete_checkin(self, record_id: int, checkin_time: datetime) -> None:
        """
        完成打卡

        Args:
            record_id: 打卡记录ID
            checkin_time: 打卡时间
        """
        # 查找记录
        record = next((r for r in self._records if r.record_id == record_id), None)
        if record:
            record.complete(checkin_time)

        # 发布事件
        event = CheckinCompletedEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            checkin_time=checkin_time
        )
        self._events.append(event)
        event_bus.publish(event)

    def miss_checkin(self, record_id: int, scheduled_time: datetime) -> None:
        """
        错过打卡

        Args:
            record_id: 打卡记录ID
            scheduled_time: 计划打卡时间
        """
        # 查找记录
        record = next((r for r in self._records if r.record_id == record_id), None)
        if record:
            record.mark_missed()

        # 发布事件
        event = CheckinMissedEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            scheduled_time=scheduled_time
        )
        self._events.append(event)
        event_bus.publish(event)

    def cancel_checkin(self, record_id: int, reason: str = None) -> None:
        """
        取消打卡

        Args:
            record_id: 打卡记录ID
            reason: 取消原因
        """
        # 查找记录
        record = next((r for r in self._records if r.record_id == record_id), None)
        if record:
            record.cancel()

        # 发布事件
        event = CheckinCancelledEvent(
            record_id=record_id,
            user_id=self._rule.user_id,
            rule_id=self._rule.rule_id,
            reason=reason
        )
        self._events.append(event)
        event_bus.publish(event)

    def enable(self) -> None:
        """启用规则"""
        self._rule.enable()
        event = CheckinRuleEnabledEvent(
            rule_id=self._rule.rule_id,
            user_id=self._rule.user_id
        )
        self._events.append(event)
        event_bus.publish(event)

    def disable(self) -> None:
        """禁用规则"""
        self._rule.disable()
        event = CheckinRuleDisabledEvent(
            rule_id=self._rule.rule_id,
            user_id=self._rule.user_id
        )
        self._events.append(event)
        event_bus.publish(event)

    def soft_delete(self) -> None:
        """软删除规则"""
        self._rule.soft_delete()

    def clear_events(self) -> None:
        """清除已发布的事件"""
        self._events.clear()

    def get_records_by_date(self, date: datetime) -> List[CheckinRecordEntity]:
        """
        获取指定日期的打卡记录

        Args:
            date: 日期

        Returns:
            打卡记录列表
        """
        return [
            record for record in self._records
            if record.planned_checkin_time.date() == date.date()
        ]

    def get_today_record(self, date: datetime) -> Optional[CheckinRecordEntity]:
        """
        获取今天的打卡记录

        Args:
            date: 日期

        Returns:
            打卡记录,如果不存在则返回 None
        """
        records = self.get_records_by_date(date)
        return records[0] if records else None

    def get_missed_records(self, days: int = 7) -> List[CheckinRecordEntity]:
        """
        获取最近N天错过的打卡记录

        Args:
            days: 天数

        Returns:
            错过的打卡记录列表
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            record for record in self._records
            if record.is_missed and record.planned_checkin_time >= cutoff_date
        ]

    def calculate_completion_rate(self, days: int = 7) -> float:
        """
        计算最近N天的完成率

        Args:
            days: 天数

        Returns:
            完成率(0-1之间的浮点数)
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_records = [
            record for record in self._records
            if record.planned_checkin_time >= cutoff_date
        ]

        if not recent_records:
            return 0.0

        completed = sum(1 for record in recent_records if record.is_completed)
        return completed / len(recent_records)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CheckinRuleAggregate):
            return False
        return self._rule == other._rule

    def __hash__(self) -> int:
        return hash(self._rule)
```

---

### 步骤 2: 提交聚合根重构

```bash
git add src/app/domain/aggregates/checkin_rule_aggregate.py

git commit -m "refactor: 更新 CheckinRuleAggregate 使用纯领域实体

- 移除对 ORM 模型的依赖
- 所有操作使用纯领域实体
- 业务逻辑封装在聚合根中
- 符合 DDD 聚合根模式

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 7: 更新 RepositoryFactory 导出

**目标**: 确保仓储接口可以正确导入

**文件**:
- 修改: `src/app/domain/repositories/__init__.py`
- 修改: `src/app/infrastructure/persistence/__init__.py`

### 步骤 1: 更新领域层 __init__.py

**修改**: `src/app/domain/repositories/__init__.py`

```python
"""
仓储接口导出
"""
from .checkin_rule_repository import CheckinRuleRepository
from .checkin_record_repository import CheckinRecordRepository

__all__ = [
    'CheckinRuleRepository',
    'CheckinRecordRepository',
]
```

---

### 步骤 2: 更新基础设施层 __init__.py

**修改**: `src/app/infrastructure/persistence/__init__.py`

```python
"""
仓储实现导出
"""
from .sqlalchemy_checkin_rule_repository import SQLAlchemyCheckinRuleRepository
from .sqlalchemy_checkin_record_repository import SQLAlchemyCheckinRecordRepository

__all__ = [
    'SQLAlchemyCheckinRuleRepository',
    'SQLAlchemyCheckinRecordRepository',
]
```

---

### 步骤 3: 提交导出更新

```bash
git add src/app/domain/repositories/__init__.py \
        src/app/infrastructure/persistence/__init__.py

git commit -m "refactor: 更新仓储接口导出

- 添加 CheckinRecordRepository 导出
- 更新基础设施层导出
- 确保模块可以正确导入

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 8: 更新 PerformCheckinUseCase 使用领域实体

**目标**: 重构 UseCase 使用新的领域实体和仓储接口

**文件**:
- 修改: `src/app/application/use_cases/checkin/perform_checkin_use_case.py`

### 步骤 1: 更新 UseCase 实现

**修改**: `src/app/application/use_cases/checkin/perform_checkin_use_case.py`

完整替换为以下内容:

```python
"""
执行打卡用例(重构版 - 符合DDD架构)

重构要点:
- 移除对 database.flask_models 的直接导入
- 使用仓储接口返回的领域实体
- 通过聚合根封装业务逻辑
- 符合依赖倒置原则
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.domain.entities.checkin_record_entity import CheckinRecordEntity
from app.domain.aggregates.checkin_rule_aggregate import CheckinRuleAggregate


class PerformCheckinUseCase(BaseUseCase):
    """执行打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # 通过仓储工厂获取仓储接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    def execute(
        self,
        rule_id: int,
        user_id: int,
        rule_source: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行打卡用例

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_source: 规则来源

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找打卡规则实体
            rule_entity = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule_entity:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 4. 验证规则归属
            if rule_entity.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限操作此打卡规则'
                )

            # 5. 检查今天是否已有打卡记录
            today = datetime.now().date()
            today_records = self.checkin_record_repository.find_today_records(user_id, rule_id)

            # 查找当天已有的打卡记录
            for record in today_records:
                if record.is_completed:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message='今日该事项已打卡,请勿重复打卡'
                    )

            # 6. 记录打卡时间
            checkin_time = datetime.now()

            # 7. 检查是否有未打卡状态的记录可以更新
            existing_unchecked = None
            for record in today_records:
                if not record.is_completed and not record.is_missed and not record.is_cancelled:
                    existing_unchecked = record
                    break

            if existing_unchecked:
                # 更新已有记录
                existing_unchecked.complete(checkin_time)
                updated_record = self.checkin_record_repository.update_entity(existing_unchecked)
            else:
                # 创建新的打卡记录实体
                planned_time = rule_entity.calculate_planned_checkin_time()
                if not planned_time:
                    planned_time = checkin_time

                new_record = CheckinRecordEntity.create(
                    record_id=0,  # 将由数据库生成
                    rule_id=rule_id,
                    user_id=user_id,
                    planned_checkin_time=datetime.combine(today, planned_time.time())
                )
                new_record.complete(checkin_time)
                updated_record = self.checkin_record_repository.save_entity(new_record)

            # 8. 发布领域事件
            try:
                # 创建聚合根
                aggregate = CheckinRuleAggregate(rule_entity)
                aggregate.complete_checkin(updated_record.record_id, checkin_time)
                self.logger.info(f'发布打卡完成事件: record_id={updated_record.record_id}')
            except Exception as e:
                self.logger.warning(f'发布领域事件失败(不影响打卡结果): {str(e)}')

            self.logger.info(f'执行打卡成功: rule_id={rule_id}, user_id={user_id}, record_id={updated_record.record_id}')

            # 9. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡成功',
                data={
                    'rule_id': rule_id,
                    'record_id': updated_record.record_id,
                    'user_id': updated_record.user_id,
                    'checkin_time': updated_record.actual_checkin_time.isoformat() if updated_record.actual_checkin_time else None,
                    'status': 'completed'
                }
            )

        except ValueError as e:
            self.logger.error(f'执行打卡失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'执行打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'执行打卡失败: {str(e)}'
            )
```

---

### 步骤 2: 提交 UseCase 重构

```bash
git add src/app/application/use_cases/checkin/perform_checkin_use_case.py

git commit -m "refactor: 重构 PerformCheckinUseCase 使用领域实体

- 移除对 database.flask_models 的直接导入
- 使用仓储接口返回的领域实体
- 所有数据操作通过仓储进行
- 符合 DDD 依赖倒置原则
- UseCase 层不再依赖基础设施层

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 9: 运行测试并验证

**目标**: 确保所有重构没有破坏现有功能

### 步骤 1: 运行单元测试

```bash
make ut
```

**预期输出**: 所有新增测试通过,现有测试不因重构而失败

---

### 步骤 2: 运行集成测试

```bash
make it
```

**预期输出**: 大部分测试通过,可能有少量测试需要更新以适配新的实体结构

---

### 步骤 3: 修复失败的测试(如果有)

如果测试失败,逐一修复:

```bash
# 查看失败的测试
ENV_TYPE=unit venv_py312/bin/python -m pytest tests/unit/test_checkin_rule_entity.py -v --tb=short

# 修复并重新运行
# ...
```

---

### 步骤 4: 提交测试修复

```bash
git add tests/

git commit -m "test: 修复测试以适配新的领域实体结构

- 更新测试以使用新的领域实体 API
- 修复因实体重构导致的测试失败
- 确保测试覆盖核心业务逻辑

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 10: 更新其他 UseCase (迭代进行)

**目标**: 逐步更新所有 UseCase 使用新的领域实体结构

**方法**:
1. 选择一个 UseCase
2. 按照任务 8 的步骤重构
3. 运行测试验证
4. 提交变更

**推荐的 UseCase 重构顺序**:

1. `GetTodayCheckinsUseCase` - 简单查询
2. `ReportMissCheckinUseCase` - 状态更新
3. `CancelCheckinUseCase` - 状态更新
4. `GetCheckinHistoryUseCase` - 复杂查询
5. `CreateCheckinRuleUseCase` - 创建实体
6. `UpdateCheckinRuleUseCase` - 更新实体
7. `DeleteCheckinRuleUseCase` - 删除实体

---

## 验收标准

### 功能验收

- [ ] 所有新增单元测试通过
- [ ] 现有单元测试不因重构而失败
- [ ] 集成测试通过率 >= 90%
- [ ] 无 UseCase 直接导入 `database.flask_models`

### 架构合规性验收

- [ ] 领域实体不依赖 ORM 模型
- [ ] 仓储接口返回领域实体
- [ ] 仓储实现负责 ORM ↔ Entity 转换
- [ ] 符合 DDD 依赖倒置原则

### 代码质量验收

- [ ] 代码风格检查通过(ruff check)
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 单元测试覆盖率 >= 80%

---

## 下一步阶段

完成第一阶段后,继续进行:

**第二阶段 (P1 问题)**:
1. 创建 DTO 层,从 Controller 移除数据转换逻辑
2. 为所有 UseCase 添加 `@transaction` 装饰器
3. 统一路由层使用辅助函数

**第三阶段 (P2 问题)**:
1. 实现事件总线机制
2. 实现 Outbox 模式保证事件可靠投递
3. 重构领域事件发布机制

---

**计划创建完成时间**: 2026-01-17 20:01
**预计完成时间**: 5-7 个工作日
**预计工作量**: 40-50 小时
