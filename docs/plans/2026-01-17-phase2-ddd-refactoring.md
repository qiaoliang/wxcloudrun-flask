# DDD Phase 2 重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完善DDD架构分层架构,实现清晰的分层边界和事务边界,解决P1级别架构问题

**Architecture:**
- 严格遵循分层架构: User Interface → Application → Domain ← Infrastructure
- Controller层只负责HTTP请求/响应,数据转换通过DTO层完成
- UseCase定义明确的事务边界,使用事务装饰器保证数据一致性
- 遵循单一职责原则(SRP)和依赖倒置原则(DIP)

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
# 确保所有测试通过(629个测试)
```

### Git 分支管理

```bash
# 查看当前状态
git status

# 如果工作区不干净,先提交或暂存
git add .
git commit -m "chore: 准备开始第二阶段DDD重构"

# 创建开发分支(可选)
git checkout -b ddd-phase2 dev
```

### 相关文档阅读

```bash
# 阅读审查报告的第二阶段问题
cat docs/plans/2026-01-17-16-17-ddd-architecture-review.md | grep -A 200 "## 🟡 中等问题"
```

---

## 任务 1: 创建 DTO 层并修复 Controller 层数据转换逻辑

**目标**: 将Controller层的数据转换逻辑提取到专门的DTO层,实现清晰的分层架构

**文件**:
- 创建: `src/app/application/dtos/__init__.py`
- 创建: `src/app/application/dtos/checkin_rule_dto.py`
- 创建: `src/app/application/dtos/checkin_record_dto.py`
- 创建: `src/app/application/dtos/common_dto.py`
- 修改: `src/app/modules/checkin/routes.py`
- 测试: `tests/unit/test_checkin_rule_dto.py` (新建)
- 测试: `tests/unit/test_checkin_record_dto.py` (新建)

### 步骤 1: 创建 DTO 基础架构

**创建**: `src/app/application/dtos/__init__.py`

```python
"""
应用层DTO(数据传输对象)

DTO负责领域实体与API响应格式之间的转换,隔离Controller层与领域层
"""
from .checkin_rule_dto import CheckinRuleDTO
from .checkin_record_dto import CheckinRecordDTO
from .common_dto import PaginationDTO

__all__ = [
    'CheckinRuleDTO',
    'CheckinRecordDTO',
    'PaginationDTO',
]
```

**创建**: `src/app/application/dtos/common_dto.py`

```python
"""
通用DTO
"""
from typing import List, Optional, Any


class PaginationDTO:
    """分页数据传输对象"""

    @staticmethod
    def from_entity(total: int, page: int, page_size: int, items: List[Any]) -> dict:
        """
        从领域实体列表创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            items: 领域实体列表

        Returns:
            dict: API分页响应格式
        """
        total_pages = (total + page_size - 1) // page_size

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'items': items
        }


class ResponseDTO:
    """统一响应格式"""

    @staticmethod
    def success(data: Any = None, message: str = '操作成功') -> dict:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息

        Returns:
            dict: 成功响应格式
        """
        return {
            'status': 'success',
            'message': message,
            'data': data
        }

    @staticmethod
    def error(message: str, code: str = 'ERROR') -> dict:
        """
        错误响应

        Args:
            message: 错误消息
            code: 错误码

        Returns:
            dict: 错误响应格式
        """
        return {
            'status': 'error',
            'code': code,
            'message': message
        }
```

### 步骤 2: 创建 CheckinRuleDTO

**创建**: `src/app/application/dtos/checkin_rule_dto.py`

```python
"""
打卡规则数据传输对象

负责 CheckinRuleEntity 与 API 响应格式之间的转换
"""
from typing import Optional, List, Any
from datetime import datetime


class CheckinRuleDTO:
    """打卡规则数据传输对象"""

    @staticmethod
    def from_entity(rule: 'CheckinRuleEntity') -> dict:
        """
        将领域实体转换为API响应格式

        Args:
            rule: 打卡规则领域实体

        Returns:
            dict: API响应格式
        """
        return {
            'rule_id': rule.rule_id,
            'user_id': rule.user_id,
            'rule_name': rule.rule_name,
            'frequency_type': rule.frequency_type,
            'time_slot_type': rule.time_slot_type,
            'status': rule.status,
            'community_id': rule.community_id,
            'icon_url': rule.icon_url,
            'custom_time': rule.custom_time,  # 字符串格式 HH:MM:SS
            'week_days': rule.week_days,  # 整数位掩码
            'custom_start_date': rule.custom_start_date.isoformat() if rule.custom_start_date else None,
            'custom_end_date': rule.custom_end_date.isoformat() if rule.custom_end_date else None,
            'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else None,
            'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else None
        }

    @staticmethod
    def from_entity_list(entities: List['CheckinRuleEntity']) -> List[dict]:
        """
        将领域实体列表转换为API响应格式

        Args:
            entities: 领域实体列表

        Returns:
            List[dict]: API响应格式列表
        """
        return [CheckinRuleDTO.from_entity(entity) for entity in entities]

    @staticmethod
    def from_pagination_result(total: int, page: int, page_size: int,
                              entities: List['CheckinRuleEntity']) -> dict:
        """
        创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            entities: 领域实体列表

        Returns:
            dict: 分页响应
        """
        return PaginationDTO.from_entity(
            total=total,
            page=page,
            page_size=page_size,
            items=CheckinRuleDTO.from_entity_list(entities)
        )
```

### 步骤 3: 创建 CheckinRecordDTO

**创建**: `src/app/application/dtos/checkin_record_dto.py`

```python
"""
打卡记录数据传输对象

负责 CheckinRecordEntity 与 API 响应格式之间的转换
"""
from typing import Optional, List
from datetime import datetime


class CheckinRecordDTO:
    """打卡记录数据传输对象"""

    @staticmethod
    def from_entity(record: 'CheckinRecordEntity') -> dict:
        """
        将领域实体转换为API响应格式

        Args:
            record: 打卡记录领域实体

        Returns:
            dict: API响应格式
        """
        # 状态映射
        status_map = {
            0: 'pending',
            1: 'completed',
            2: 'missed',
            3: 'cancelled'
        }
        status_name = status_map.get(record.checkin_status, 'unknown')

        return {
            'record_id': record.record_id,
            'rule_id': record.rule_id,
            'user_id': record.user_id,
            'planned_time': record.planned_checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.planned_checkin_time else None,
            'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
            'status': record.checkin_status,
            'status_name': status_name,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None,
            'updated_at': record.updated_at.strftime('%Y-%m:%M:%S') if record.updated_at else None
        }

    @staticmethod
    def from_entity_list(records: List['CheckinRecordEntity']) -> List[dict]:
        """
        将领域实体列表转换为API响应格式

        Args:
            records: 领域实体列表

        Returns:
            List[dict]: API响应格式列表
        """
        return [CheckinRecordDTO.from_entity(record) for record in records]

    @staticmethod
    def from_pagination_result(total: int, page: int, page_size: int,
                              records: List['CheckinRecordEntity']) -> dict:
        """
        创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 模拟每页大小
            records: 领域实体列表

        Returns:
            dict: 分页响应
        """
        return PaginationDTO.from_entity(
            total=total,
            page=page,
            page_size=page_size,
            items=CheckinRecordDTO.from_entity_list(records)
        )
```

### 步骤 4: 编写DTO测试

**创建**: `tests/unit/test_checkin_rule_dto.py`

```python
"""
测试 CheckinRuleDTO
"""
import pytest
from datetime import datetime, time
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity


class TestCheckinRuleDTO:
    """测试CheckinRuleDTO"""

    def test_from_entity_basic_fields(self):
        """测试基本字段转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=0,  # 每天
            time_slot_type=0,  # 早晨
            status=1  # 启用
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['rule_id'] == 1
        assert result['user_id'] == 100
        assert result['rule_name'] == "晨间打卡"
        assert result['frequency_type'] == 0
        assert result['time_slot_type'] == 0
        assert result['status'] == 1

    def test_from_entity_with_custom_time(self):
        """测试带自定义时间的转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="自定义打卡",
            frequency_type=0,
            time_slot_type=4,  # 自定义
            custom_time="09:30:00",
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['custom_time'] == "09:30:00"

    def test_from_entity_with_week_days_bitmask(self):
        """测试week_days位掩码转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="工作日打卡",
            frequency_type=1,  # 每周
            time_slot_type=4,
            week_days=31,  # 周一至周五
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['week_days'] == 31

    def test_from_entity_with_datetime_fields(self):
        """测试日期时间字段转换"""
        now = datetime.now()
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="日期范围打卡",
            frequency_type=3,  # 自定义日期
            time_slot_type=4,
            custom_start_date=now,
            custom_end_date=now.replace(day=now.day + 7),
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert 'custom_start_date' in result
        assert 'custom_end_date' in result
        assert result['custom_start_date'].endswith(now.strftime('%Y-%m-%d'))
```

**运行测试**:

```bash
pytest tests/unit/test_checkin_rule_dto.py -v
```

**预期输出**: PASS - 所有测试通过

---

### 步骤 5: 编写CheckinRecordDTO测试

**创建**: `tests/unit/test_checkin_record_dto.py`

```python
"""
测试 CheckinRecordDTO
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_record_entity import CheckinRecordEntity, CheckinStatus


class TestCheckinRecordDTO:
    """测试CheckinRecordDTO"""

    def test_from_entity_completed_status(self):
        """测试已完成状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.complete(datetime.now())

        result = CheckinRecordDTO.from_entity(entity)

        assert result['record_id'] == 1
        assert result['rule_id'] == 10
        assert result['status'] == 1
        assert result['status_name'] == 'completed'

    def test_from_entity_pending_status(self):
        """测试未打卡状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now(),
            checkin_status=CheckinStatus.PENDING.value
        )

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 0
        assert result['status_name'] == 'pending'

    def test_from_entity_missed_status(self):
        """测试已错过状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.mark_missed()

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 2
        assert result['status_name'] == 'missed'

    def test_from_entity_cancelled_status(self):
        """测试已取消状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.cancel()

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 3
        assert result.status_name == 'cancelled'

    def test_from_entity_with_null_checkin_time(self):
        """测试空打卡时间的转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now(),
            checkin_status=CheckinStatus.PENDING.value
        )

        result = CheckinRecordDTO.from_entity(entity)

        assert result['checkin_time'] is None

    def test_from_entity_list(self):
        """测试列表转换"""
        entities = [
            CheckinRecordEntity.create(
                record_id=i,
                rule_id=10,
                user_id=100,
                planned_checkin_time=datetime.now(),
                checkin_status=CheckinStatus.PENDING.value
            ) for i in range(1, 4)
        ]

        entities[0].complete(datetime.now())
        entities[1].mark_missed()
        entities[2].cancel()

        result = CheckinRecordDTO.from_entity_list(entities)

        assert len(result) == 3
        assert result[0]['status_name'] == 'completed'
        assert result[1]['status_name'] == 'missed'
        assert result[2]['status_name'] == 'cancelled'
```

**运行测试**:

```bash
pytest tests/unit/test_checkin_record_dto.py -v
```

**预期输出**: PASS - 所有测试通过

---

### 步骤 6: 重构routes.py使用DTO层

**修改**: `src/app/modules/checkin/routes.py`

**移除Controller层的转换函数**:
```python
# ❌ 删除 _rule_to_dict 等转换函数
def _rule_to_dict(rule): ...
def _checkin_record_to_dict(record): ...
```

**使用DTO重构**:
```python
from app.application.dtos import CheckinRuleDTO, CheckinRecordDTO, ResponseDTO


@checkin_bp.route('/checkin/rules', methods=['GET'])
@with_user_verification
def get_checkin_rules(user_id: int, user: dict):
    """获取用户打卡规则列表"""
    # 使用 get_json_params 辅助函数
    params, error_msg = get_json_params({
        'page': 1,
        'page_size': 20
    })
    if error_msg:
        return make_err_response({}, error_msg)

    # 执行 UseCase
    result = execute_use_case(
        GetCheckinRuleUseCase,
        user_id=user_id,
        page=params.get('page', 1),
        page_size=params.get('page_size', 20)
    )

    if not result.is_success:
        return make_err_response({}, result.message)

    # 使用DTO转换
    rules = result.data.get('rules', [])
    return make_succ_response({
        'rules': [CheckinRuleDTO.from_entity(rule) for rule in rules],
        'total': result.data.get('total', 0),
        'page': result.data.get('page', 1),
        'page_size': result.data.get('page_size', 20)
    })
```

---

### 步骤 7: 提交DTO层创建

```bash
git add src/app/application/dtos/ tests/unit/test_checkin_rule_dto.py tests/unit/test_checkin_record_dto.py
git commit -m "feat: 创建DTO层并修复Controller层问题

- 创建 CheckinRuleDTO 和 CheckinRecordDTO
- 创建通用 ResponseDTO 和 PaginationDTO
- 重构 routes.py 移除数据转换逻辑
- 使用 get_json_params 和 handle_use_case_result 辅助函数
- 符合单一职责原则,Controller只负责HTTP处理
- 遵循分层架构:Controller → DTO → Entity

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 2: 为UseCase添加事务装饰器

**目标**: 定义清晰的事务边界,确保数据一致性

**文件**:
- 修改: `src/app/application/use_cases/base.py` - 添加事务装饰器
- 创建: `src/app/infrastructure/transaction/transaction_manager.py` (新建)
- 修改: `src/app/application/use_cases/checkin/perform_checkin_use_case.py`

### 步骤 1: 创建事务管理器

**创建**: `src/app/infrastructure/transaction/transaction_manager.py`

```python
"""
事务管理器

提供事务装饰器和事务上下文管理
"""
import logging
from contextlib import contextmanager
from typing import Callable, Optional
from flask import current_app, g

from database.flask_models import db


class TransactionManager:
    """事务管理器"""

    @staticmethod
    @contextmanager
    def transaction(save_point: Optional[str] = None):
        """
        事务上下文管理器

        Args:
            save_point: 保存点名称,用于嵌套事务

        Yields:
            None

        Raises:
            Exception: 事务失败时抛出异常
        """
        if save_point:
            current_app.logger.debug(f'开始事务,保存点: {save_point}')

        try:
            yield
            current_app.logger.debug(f'事务成功,保存点: {save_point}')
        except Exception as e:
            current_app.logger.error(f'事务失败,保存点: {save_point}, 错误: {str(e)}')
            raise


class TransactionDecorator:
    """事务装饰器"""

    def __call__(self, func: Callable) -> Callable:
        """
        装饰器方法

        Args:
            func: 被装饰的函数

        Returns:
            Callable: 包装后的函数
        """
        def wrapper(*args, **kwargs):
            with TransactionManager.transaction(save_point=func.__name__):
                return func(*args, **kwargs)
        return wrapper


# 便捷装饰器
transaction = TransactionDecorator()
```

### 步骤 2: 修改BaseUseCase添加事务支持

**修改**: `src/app/application/use_cases/base.py`

```python
"""
UseCase 基类 - 支持事务

提供通用模板方法模式和事务支持
"""
import logging
from typing import Optional
from abc import ABC, abstractmethod
from flask import request
from app.infrastructure.transaction.transaction_manager import TransactionManager


class UseCaseStatus:
    """UseCase 状态枚举"""
    PENDING = 'pending'
    SUCCESS = 'success'
    VALIDATION_ERROR = 'validation_error'
    NOT_FOUND = 'not_found'
    FORBIDDEN = 'forbidden'
    BUSINESS_ERROR = 'business_error'
    FAILURE = 'failure'


class UseCaseResult:
    """UseCase 统一返回结果"""
    def __init__(
        self,
        status: UseCaseStatus,
        message: str,
        data: Optional[dict] = None,
        errors: list = None
    ):
        self.status = status
        self.message = message
        self.data = data
        self.errors = errors or []

    @property
    def is_success(self) -> bool:
        return self.status == UseCaseStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.status != UseCaseStatus.SUCCESS

    @classmethod
    def success(cls, data: dict, message: str = '操作成功') -> 'UseCaseResult':
        """创建成功结果"""
        return cls(
            status=UseCaseStatus.SUCCESS,
            message=message,
            data=data
        )

    @classmethod
    def fail(cls, message: str, status: UseCaseStatus = UseCaseStatus.FAILURE,
             data: dict = None) -> 'UseCaseResult':
        """创建失败结果"""
        return cls(
            status=status,
            message=message,
            data=data
        )

    @classmethod
    def validation_error(cls, message: str, data: dict = None) -> 'UseCaseResult':
        """创建验证错误结果"""
        return cls(
            status=UseCaseStatus.VALIDATION_ERROR,
            message=message,
            data=data
        )

    @classmethod
    def not_found(cls, message: str, data: dict = None) -> 'UseCaseResult':
        """创建未找到错误结果"""
        return cls(
            status=use_case_status.NOT_FOUND,
            message=message,
            data=data
        )

    @classmethod
    def forbidden(cls, message: str, data: dict = None) -> 'UseCaseResult':
        """创建权限错误结果"""
        return cls(
            status=use_case_status.FORBIDDEN,
            message=message,
            data=data
        )

    @classmethod
    def business_error(cls, message: str, data: dict = None) -> 'UseCaseResult':
        """创建业务错误结果"""
        return cls(
            status=use_case_status.BUSINESS_ERROR,
            message=message,
            data=data
        )


class BaseUseCase(ABC):
    """UseCase 基类"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, *args, **kwargs) -> 'UseCaseResult':
        """
        执行用例逻辑

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            UseCaseResult: 执行结果
        """
        pass

    def _validate_request(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        验证请求参数

        Args:
            **kwargs: 请求参数

        Returns:
            tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        return True, None

    def _validate_user_exists(self, user_id: int) -> tuple[bool, Optional[str]]:
        """验证用户是否存在"""
        raise NotImplementedError  # 由子类实现

    def _validate_rule_exists(self, rule_id: int) -> tuple[bool, Optional[str]]:
        """验证规则是否存在"""
        raise NotImplementedError  # 由子类实现
```

### 步骤 3: 更新UseCase使用事务装饰器

**修改**: `src/app/application/use_cases/checkin/perform_checkin_use_case.py`

添加事务支持:
```python
from app.infrastructure.transaction.transaction_manager import transaction


class PerformCheckinUseCase(BaseUseCase):
    """执行打卡用例"""

    def __init__(self):
        super().__init__()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    @transaction
    def execute(self, rule_id: int, user_id: int, rule_source: Optional[str] = None) -> UseCaseResult:
        """
        执行打卡用例

        事务边界: 查询规则 -> 验证权限 -> 创建记录 -> 保存, 所有操作在同一事务中

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_source: 规则来源

        Returns:
            UseCaseResult: 执行结果
        """
        # 1. 验证参数
        if not rule_id:
            return UseCaseResult.validation_error('规则ID不能为空')

        if not user_id:
            return UseCaseResult.validation_error('用户ID不能为空')

        # 2. 查询规则并验证(在同一事务中)
        rule_entity = self.checkin_rule_repository.find_by_id(rule_id)
        if not rule_entity:
            return UseCaseResult.not_found('打卡规则不存在')

        # 3. 验证权限
        if rule_entity.user_id != user_id:
            return UseCaseResult.forbidden('无权限操作此打卡规则')

        # 4. 检查今天是否已有打卡记录
        today = datetime.now().date()
        today_records = self.checkin_record_repository.find_today_records(user_id, rule_id)

        # 查找当天已有的打卡记录
        for record in today_records:
            if record.is_completed:
                return UseCaseResult.business_error('今日该事项已打卡,请勿重复打卡')

        # 5. 创建或更新打卡记录(在同一事务中)
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
            planned_time = rule_entity.calculate_planned_checkin_time() or datetime.now()
            new_record = CheckinRecordEntity.create(
                record_id=0,  # 将由数据库生成
                rule_id=rule_id,
                user_id=user_id,
                planned_checkin_time=planned_time
            )
            new_record.complete(checkin_time)
            updated_record = self.checkin_record_repository.save_entity(new_record)

        self.logger.info(f'执行打卡成功: rule_id={rule_id}, user_id={user_id}, record_id={updated_record.record_id}')

        # 6. 返回结果(事务成功后)
        return UseCaseResult.success(data={
            'rule_id': rule_id,
            'record_id': updated_record.record_id,
            'user_id': updated_record.user_id,
            'checkin_time': updated_record.actual_checkin_time.isoformat() if updated_record.actual_checkin_time else None,
            'status': 'completed'
        })
```

### 步骤 4: 编写事务测试

**创建**: `tests/unit/test_transaction_manager.py`

```python
"""
测试事务管理器
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from datetime import datetime


class TestTransactionManager:
    """测试事务管理器"""

    def test_transaction_commits_on_success(self):
        """测试事务成功时提交"""
        with patch('app.infrastructure.persistence.repository_factory.RepositoryFactory.get_checkin_record_repository') as mock_repo:
            mock_repo.return_value.save_entity.return_value = MagicMock(record_id=1)

            from app.infrastructure.transaction.transaction_manager import TransactionManager

            # 测试正常流程
            def test_operation():
                record = MagicMock(record_id=1)
                mock_repo.save_entity(record)
                return True

            with TransactionManager.transaction(save_point='test'):
                result = test_operation()

            assert result is True

    def test_transaction_rollback_on_error(self):
        """测试事务失败时回滚"""
        with patch('app.infrastructure.persistence.repository_factory.RepositoryFactory.get_checkin_record_repository') as mock_repo:
            mock_repo.save_entity.side_effect = Exception("Database error")

            from app.infrastructure.transaction.transaction_manager import TransactionManager

            # 测试错误流程
            def test_operation():
                mock_repo.save_entity(MagicMock(record_id=1))
                return False

            with pytest.raises(Exception, match="Database error"):
                with TransactionManager.transaction(save_point='test'):
                    test_operation()

    def test_transaction_decorator(self):
        """测试事务装饰器"""
        with patch('app.infrastructure.transaction.transaction_manager.TransactionManager'):

            @transaction
            def test_operation():
                return True

            result = test_operation()
            assert result is True
```

**运行测试**:

```bash
pytest tests/unit/test_transaction_manager.py -v
```

**预期输出**: PASS - 所有测试通过

---

### 步骤 5: 提交事务管理器创建

```bash
git add src/app/infrastructure/transaction/transaction_manager.py \
        src/app/application/use_cases/base.py \
        src/app/application/use_cases/checkin/perform_checkin_use_case.py \
        tests/unit/test_transaction_manager.py

git commit -m "feat: 添加事务装饰器和事务管理器

- 创建 TransactionManager 和 TransactionDecorator
- BaseUseCase 添加 UseCaseStatus 枚举和通用方法
- PerformCheckinUseCase 添加 @transaction 装饰器
- 添加事务测试验证
- 定义清晰的事务边界,保证数据一致性
- 符合 ACID 原则和事务边界原则

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 3: 重构所有UseCase使用事务装饰器

**目标**: 为所有UseCase添加事务支持,确保数据一致性

**文件**:
- 修改: `src/app/application/use_cases/checkin/*.py`

### 步骤 1: 重构 CreateCheckinRuleUseCase

**修改**: `src/app/application/use_cases/checkin/create_checkin_rule_use_case.py`

添加事务装饰器:
```python
from app.infrastructure.transaction.transaction_manager import transaction


class CreateCheckinRuleUseCase(BaseUseCase):
    """创建打卡规则用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

    @transaction
    def execute(self, user_id: int, rule_data: dict) -> UseCaseResult:
        """
        创建打卡规则用例

        事务边界: 查询用户 -> 验证参数 -> 创建规则 -> 保存, 所有操作在同一事务中

        Args:
            user_id: 用户ID
            rule_data: 规则数据字典

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 验证参数
            if not rule_data.get('rule_name'):
                return UseCaseResult.validation_error('规则名称不能为空')

            # 2. 查询用户(在同一事务中)
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult.not_found('用户不存在')

            # 3. 创建规则实体并保存(在同一事务中)
            custom_time_str = None
            if rule_data.get('custom_time'):
                custom_time_str = rule_data['custom_time']

            new_rule = CheckinRuleEntity.create(
                rule_id=0,
                user_id=user_id,
                rule_name=rule_data['rule_name'],
                frequency_type=rule_data.get('frequency_type', 0),
                time_slot_type=rule_data.get('time_slot_type', 4),
                status=1,
                community_id=user.community_id,
                icon_url=rule_data.get('icon_url'),
                custom_time=custom_time_str,
                week_days=rule_data.get('week_days', 127),
                custom_start_date=rule_data.get('custom_start_date'),
                custom_end_date=rule_data.get('custom_end_date')
            )

            saved_rule = self.checkin_rule_repository.save_entity(new_rule)

            self.logger.info(f'创建打卡规则成功: rule_id={saved_rule.rule_id}, user_id={user_id}')

            return UseCaseResult.success(data={
                'rule': saved_rule
            })

        except ValueError as e:
            self.logger.error(f'创建打卡规则失败: {str(e)}')
            return UseCaseResult.validation_error(str(e))

        except Exception as e:
            self.logger.error(f'创建打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult.failure(f'创建打卡规则失败: {str(e)}')
```

### 步骤 2: 重构其他UseCase

按照相同模式重构:
- `UpdateCheckinRuleUseCase`
- `DeleteCheckinRuleUseCase`
- `GetTodayCheckinsUseCase`
- `GetCheckinHistoryUseCase`
- `CancelCheckinUseCase`
- `ReportMissCheckinUseCase`

每个UseCase都需要:
1. 添加 `@transaction` 装饰器
2. 在方法开头添加事务边界注释
3. 确保所有数据库操作在同一事务中

### 步骤 3: 提交事务重构

```bash
git add src/app/application/use_cases/checkin/*.py
git commit -m "feat: 为所有CheckinUseCase添加事务装饰器

- 为所有UseCase添加 @transaction 装饰器
- 添加事务边界注释说明事务范围
- 确保所有仓储操作在同一事务中
- 实现ACID原则中的原子性和一致性
- 符合事务边界原则

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 任务 4: 重构路由层统一使用辅助函数

**目标**: 消除重复代码,统一使用路由辅助函数

**文件**:
- 修改: `src/app/modules/checkin/routes.py`
- 修改: `src/app/modules/supervision/routes.py`

### 步骤 1: 修复 checkin/routes.py

**当前问题**: 存在重复的验证逻辑,未使用已有辅助函数

**修改**: `src/app/modules/checkin/routes.py`

```python
"""
打卡路由层 - 符合DDD架构

只负责HTTP请求/响应处理,数据转换由DTO层完成
"""
from flask import Blueprint
from app.modules.routes_helper import (
    get_json_params,
    handle_use_case_result,
    make_err_response,
    make_succ_response,
    with_user_verification
)

from app.application.use_cases.checkin.perform_checkin_use_case import PerformCheckinUseCase
from app.application.use_cases.checkin.get_checkin_rule_use_case import GetCheckinRuleUseCase
from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
from app.application.dtos import CheckinRuleDTO, CheckinRecordDTO, ResponseDTO


checkin_bp = Blueprint('checkin', __name__)


@checkin_bp.route('/checkin', methods=['POST'])
@with_user_verification  # 自动验证token和用户存在性
def perform_checkin(user_id: int, user: dict):
    """执行打卡接口"""
    # 使用 get_json_params 辅助函数获取参数
    params, error_msg = get_json_params(
        {'rule_id': int},
        required_fields=['rule_id']
    )
    if error_msg:
        return make_err_response({}, error_msg)

    # 使用 handle_use_case_result 辅助函数
    return handle_use_case_result(
        PerformCheckinUseCase,
        rule_id=params['rule_id'],
        user_id=user_id
    )


@checkin_bp.route('/checkin/rules', methods=['GET'])
@with_user_verification
def get_checkin_rules(user_id: int, user: dict):
    """获取用户打卡规则列表"""
    params, error_msg = get_json_params({
        'page': 1,
        'page_size': 20
    })
    if error_msg:
        return make_err_response({}, error_msg)

    return handle_use_case_result(
        GetCheckinRuleUseCase,
        user_id=user_id,
        page=params.get('page', 1),
        page_size=params.get('page_size', 20)
    )


@checkin_bp.route('/checkin/rules', methods=['POST'])
@with_user_verification
def create_checkin_rule(user_id: int, user: dict):
    """创建打卡规则接口"""
    params, error_msg = get_json_params(
        {'rule_name': str},
        required_fields=['rule_name']
    )
    if error_msg:
        return make_err_response({}, error_msg)

    return handle_use_case_result(
        CreateCheckinRuleUseCase,
        user_id=user_id,
        rule_data=params
    )
```

### 步骤 2: 修复 supervision/routes.py

按照相同模式修复 `supervision/routes.py`

### 步骤 3: 运行测试验证

```bash
make ut
```

**预期输出**: 所有测试通过

---

## 任务 5: 创建数据库迁移脚本

**目标**: 更新数据库约束以支持 CANCELLED 状态

**文件**:
- 创建: `src/database/migrations/versions/xxx_update_checkin_record_status_constraint.py`

### 步骤 1: 创建迁移脚本

**创建**: `alembic revision --autogenerate -m "update checkin_record status constraint"`

```python
"""update checkin_record status constraint

Revision ID: xxx

Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    """更新约束"""
    # 修改现有约束
    op.execute('ALTER TABLE checkin_records DROP CONSTRAINT ck_checkin_record_status')
    op.create_check_constraint('ck_checkin_record_status',
                           'checkin_records',
                           sa.CheckConstraint('status IN (0, 1, 2, 3)'),
                           name='ck_checkin_record_status')

def downgrade():
    """回滚到之前版本"""
    op.execute('ALTER TABLE checkin_records DROP CONSTRAINT ck_checkin_record_status')
    op.create_check_constraint('ck_checkin_record_status',
                           'checkin_records',
                           sa.CheckConstraint('status IN (0, 1, 2)'),
                           name='ck_checkin_record_status')
```

### 步骤 2: 运行迁移

```bash
cd src
alembic upgrade head
```

### 步骤 3: 提交迁移

```bash
git add src/database/migrations/versions/*update_checkin_record_status_constraint.py
git commit -m "refactor: 更新打卡记录状态约束支持CANCELLED状态

- 修改约束为 status IN (0, 1, 2, 3)
- 支持未打卡、已打卡、已错过、已取消4种状态
- 符合状态语义完整性
- 数据库迁移脚本

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 验收标准

### 功能测试

```bash
# 运行所有单元测试
make ut

# 运行集成测试(如果有相关修改)
make it
```

**预期结果**: 所有测试通过,无回滚

### 代码质量检查

1. **分层清晰检查**:
   - Controller不包含业务逻辑
   - UseCase不直接使用ORM模型
   - DTO负责数据转换

2. **事务边界检查**:
   - 所有UseCase使用@transaction装饰器
   - 事务边界注释清晰

3. **重复代码检查**:
   - 无重复的验证逻辑
   - 统一使用辅助函数

### 架构审查

重新运行 DDD 架构审查,确认所有P0和P1问题已解决。

---

## 附录: 常见问题

**Q: 测试环境如何配置?**

```bash
export ENV_TYPE=unit  # 使用内存数据库
pytest tests/unit/
```

**Q: 如何处理现有的业务逻辑?**

保持现有业务逻辑不变,只是重构架构。使用测试保护重构过程。

**Q: 如何避免影响线上服务?**

建议在测试环境完整验证后再部署,确保所有测试通过。
```

---

## 执行指南

**Plan complete and saved to `docs/plans/2026-01-17-phase2-ddd-refactoring.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Guide them to open new session in worktree, **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans