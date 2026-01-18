# DDD 第三阶段实施文档：领域事件机制

> **文档日期**: 2026-01-18
> **阶段目标**: 完善领域事件机制，提升系统可靠性
> **预计工期**: 8-10 个工作日
> **文档类型**: 开发实施指南

---

## 目录

1. [架构概览](#1-架构概览)
2. [Outbox 模式实现](#2-outbox-模式实现)
3. [事件总线实现](#3-事件总线实现)
4. [后台任务实现](#4-后台任务实现)
5. [数据库和仓储实现](#5-数据库和仓储实现)
6. [集成测试和验收标准](#6-集成测试和验收标准)
7. [实施计划](#7-实施计划)
8. [附录和代码示例](#8-附录和代码示例)

---

## 1. 架构概览

### 1.1 目标与范围

**目标**：在 checkin 模块建立完善的领域事件机制，确保事件可靠投递，提升系统可靠性。

**范围**：
- **模块范围**：仅 checkin 模块（打卡规则和打卡记录）
- **事件类型**：打卡完成事件（CheckinCompletedEvent）、漏打卡事件（CheckinMissedEvent）
- **技术栈**：内存队列 + SQLAlchemy 数据库队列
- **投递策略**：混合模式（同步优先，失败后降级到 Outbox）

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        UseCase Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PerformCheckinUseCase                                 │ │
│  │  - 执行业务逻辑                                         │ │
│  │  - 保存聚合根                                           │ │
│  │  - 发布事件 (event_bus.publish_with_fallback)          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Event Bus Layer                         │
│  ┌──────────────────┐        ┌──────────────────────────┐  │
│  │  同步发布优先     │  ──▶   │  失败后写入 Outbox        │  │
│  │  - 订阅者通知     │        │  - 持久化事件            │  │
│  │  - 实时处理       │        │  - 等待后台任务处理      │  │
│  └──────────────────┘        └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌──────────────────┐              ┌──────────────────────────┐
│  Event Handlers  │              │  Outbox Processor        │
│  - 通知发送       │              │  - 后台轮询 (5s)         │
│  - 统计更新       │              │  - 重试发布              │
│  - 日志记录       │              │  - 状态更新              │
└──────────────────┘              └──────────────────────────┘
```

### 1.3 关键设计原则

1. **可靠性优先**：事件发布失败不应影响主业务流程
2. **最终一致性**：事件投递允许短暂延迟，但必须最终成功
3. **幂等性**：事件处理器必须支持重复消费
4. **可观测性**：完整记录事件生命周期，便于排查问题

---

## 2. Outbox 模式实现

### 2.1 数据模型设计

**Outbox 表结构** (`outbox_events`):

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键 |
| event_type | String(100) | 事件类型（如 CheckinCompletedEvent） |
| payload | JSON | 事件数据（JSON 格式） |
| status | String(20) | 状态：pending/published/failed |
| retry_count | Integer | 重试次数 |
| created_at | DateTime | 创建时间 |
| published_at | DateTime | 发布时间（可为空） |
| next_retry_at | DateTime | 下次重试时间 |

**索引设计**：
- `(status, next_retry_at)`：后台任务高效查询待处理事件
- `(event_type, created_at)`：按类型查询事件历史

### 2.2 混合投递策略

**同步优先路径**：
1. UseCase 事务提交成功后，立即尝试同步发布事件
2. 发布成功：直接返回，不写入 Outbox
3. 发布失败：写入 Outbox 表（status=pending）

**异步降级路径**：
1. 后台任务每 5 秒扫描一次 Outbox 表
2. 查询条件：`status='pending' AND next_retry_at <= NOW()`
3. 重试策略：指数退避（1s → 2s → 4s → 8s → 60s）
4. 重试 5 次仍失败：标记为 `status='failed'`，发送告警

### 2.3 核心类设计

**OutboxEvent 实体**：

```python
# src/app/domain/entities/outbox_event_entity.py
from datetime import datetime, timedelta
from app.domain.enums.outbox_status import OutboxStatus

class OutboxEventEntity:
    """Outbox 事件领域实体"""

    def __init__(self, event_type: str, payload: dict):
        self.id = None
        self.event_type = event_type
        self.payload = payload
        self.status = OutboxStatus.PENDING
        self.retry_count = 0
        self.created_at = datetime.now()
        self.published_at = None
        self.next_retry_at = datetime.now()

    def mark_as_published(self) -> None:
        """标记为已发布"""
        self.status = OutboxStatus.PUBLISHED
        self.published_at = datetime.now()

    def calculate_next_retry(self) -> None:
        """计算下次重试时间（指数退避）"""
        delay = min(2 ** self.retry_count, 60)  # 最多 60 秒
        self.next_retry_at = datetime.now() + timedelta(seconds=delay)
        self.retry_count += 1

    def should_retry(self) -> bool:
        """判断是否应该重试"""
        return self.retry_count < 5
```

**Outbox 仓储接口**：

```python
# src/app/domain/repositories/outbox_repository.py
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.outbox_event_entity import OutboxEventEntity

class OutboxRepository(ABC):
    """Outbox 仓储接口"""

    @abstractmethod
    def save(self, event: OutboxEventEntity) -> OutboxEventEntity:
        """保存事件到 Outbox"""
        pass

    @abstractmethod
    def find_pending_events(self, limit: int = 100) -> List[OutboxEventEntity]:
        """查找待处理事件"""
        pass

    @abstractmethod
    def update_status(self, event_id: int, status: OutboxStatus) -> None:
        """更新事件状态"""
        pass
```

### 2.4 使用示例

```python
# src/app/application/use_cases/checkin/perform_checkin_use_case.py
class PerformCheckinUseCase(BaseUseCase):

    @transaction
    def execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        # ... 业务逻辑 ...

        # 保存打卡记录（事务内）
        self.checkin_record_repository.save(record)

        # 事务提交后尝试同步发布事件
        event = CheckinCompletedEvent(
            record_id=record.record_id,
            user_id=user_id,
            rule_id=rule_id
        )

        # 混合投递：同步优先，失败后写入 Outbox
        self.event_bus.publish_with_fallback(event)

        return UseCaseResult.success(data={...})
```

---

## 3. 事件总线实现

### 3.1 EventBus 核心职责

1. 维护事件订阅者注册表
2. 同步分发事件到订阅者
3. 处理发布失败，降级到 Outbox
4. 提供事件发布接口

**技术选择**：
- 内存队列：Python `list` + `threading.Lock`（简单高效）
- 订阅者注册：字典 `{event_type: [handlers]}`
- 线程安全：使用锁保护订阅者注册表

### 3.2 领域事件设计

**基础事件类**：

```python
# src/app/domain/events/base_event.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

@dataclass
class BaseEvent:
    """领域事件基类"""
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload
        }
```

**具体事件类型**：

```python
# src/app/domain/events/checkin_events.py
from dataclasses import dataclass
from datetime import datetime
from app.domain.events.base_event import BaseEvent

@dataclass
class CheckinCompletedEvent(BaseEvent):
    """打卡完成事件"""
    record_id: int
    user_id: int
    rule_id: int

    def __init__(self, record_id: int, user_id: int, rule_id: int):
        super().__init__(
            event_type='CheckinCompletedEvent',
            timestamp=datetime.now(),
            payload={
                'record_id': record_id,
                'user_id': user_id,
                'rule_id': rule_id
            }
        )

@dataclass
class CheckinMissedEvent(BaseEvent):
    """漏打卡事件"""
    rule_id: int
    user_id: int
    planned_time: datetime

    def __init__(self, rule_id: int, user_id: int, planned_time: datetime):
        super().__init__(
            event_type='CheckinMissedEvent',
            timestamp=datetime.now(),
            payload={
                'rule_id': rule_id,
                'user_id': user_id,
                'planned_time': planned_time.isoformat()
            }
        )
```

### 3.3 EventBus 实现

```python
# src/app/infrastructure/events/event_bus.py
from typing import Callable, Dict, List
from threading import Lock
import logging
from app.domain.events.base_event import BaseEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.repositories.outbox_repository import OutboxRepository

class EventBus:
    """事件总线"""

    def __init__(self, outbox_repository: OutboxRepository):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = Lock()
        self._outbox_repository = outbox_repository
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def publish_with_fallback(self, event: BaseEvent) -> None:
        """
        发布事件（混合模式）

        策略：同步发布优先，失败后写入 Outbox
        """
        try:
            # 同步发布
            self._publish_sync(event)
            self.logger.info(f'事件同步发布成功: {event.event_type}')
        except Exception as e:
            # 发布失败，写入 Outbox
            self.logger.warning(f'同步发布失败，降级到 Outbox: {e}')
            outbox_event = OutboxEventEntity(
                event_type=event.event_type,
                payload=event.to_dict()
            )
            self._outbox_repository.save(outbox_event)

    def _publish_sync(self, event: BaseEvent) -> None:
        """同步发布事件"""
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            self.logger.warning(f'没有找到 {event.event_type} 的订阅者')
            return

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f'事件处理失败: {e}')
                raise  # 触发降级到 Outbox

    def publish_from_outbox(self, outbox_event: OutboxEventEntity) -> bool:
        """从 Outbox 发布事件（供后台任务使用）"""
        try:
            event = self._deserialize_event(outbox_event)
            self._publish_sync(event)
            return True
        except Exception as e:
            self.logger.error(f'Outbox 事件发布失败: {e}')
            return False

    def _deserialize_event(self, outbox_event: OutboxEventEntity) -> BaseEvent:
        """从 Outbox 事件反序列化领域事件"""
        # 根据事件类型创建对应的事件对象
        if outbox_event.event_type == 'CheckinCompletedEvent':
            payload = outbox_event.payload
            return CheckinCompletedEvent(
                record_id=payload['record_id'],
                user_id=payload['user_id'],
                rule_id=payload['rule_id']
            )
        elif outbox_event.event_type == 'CheckinMissedEvent':
            payload = outbox_event.payload
            return CheckinMissedEvent(
                rule_id=payload['rule_id'],
                user_id=payload['user_id'],
                planned_time=datetime.fromisoformat(payload['planned_time'])
            )
        raise ValueError(f'未知事件类型: {outbox_event.event_type}')
```

### 3.4 事件处理器示例

```python
# src/app/application/event_handlers/checkin_notification_handler.py
from app.domain.events.checkin_events import CheckinCompletedEvent

class CheckinNotificationHandler:
    """打卡通知处理器"""

    def handle(self, event: CheckinCompletedEvent) -> None:
        """处理打卡完成事件"""
        # 发送通知（可以是短信、推送等）
        message = f'您已完成打卡，规则ID: {event.rule_id}'
        # self.notification_service.send(user_id=event.user_id, message=message)
        print(f'发送通知: {message}')
```

**注册处理器**：

```python
# src/app/application/event_handlers/__init__.py
from app.infrastructure.events.event_bus import EventBus
from app.application.event_handlers.checkin_notification_handler import CheckinNotificationHandler

def register_event_handlers(event_bus: EventBus) -> None:
    """注册所有事件处理器"""
    notification_handler = CheckinNotificationHandler()

    event_bus.subscribe(
        event_type='CheckinCompletedEvent',
        handler=notification_handler.handle
    )
```

---

## 4. 后台任务实现

### 4.1 后台任务架构

**任务职责**：
1. 定期扫描 Outbox 表中的待处理事件
2. 尝试重新发布事件
3. 更新事件状态（已发布/失败）
4. 记录失败事件并告警

**运行方式**：
- 使用 Flask 的 `before_first_request` 启动后台线程
- 线程安全：使用数据库锁防止并发处理同一事件
- 优雅退出：响应应用关闭信号

### 4.2 OutboxProcessor 实现

```python
# src/app/infrastructure/events/outbox_processor.py
import threading
import time
from typing import Optional
import logging
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.enums.outbox_status import OutboxStatus
from app.infrastructure.events.event_bus import EventBus

class OutboxProcessor:
    """Outbox 后台处理器"""

    def __init__(
        self,
        outbox_repository: OutboxRepository,
        event_bus: EventBus,
        interval_seconds: int = 5,
        batch_size: int = 100
    ):
        self._outbox_repository = outbox_repository
        self._event_bus = event_bus
        self._interval = interval_seconds
        self._batch_size = batch_size
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """启动后台处理线程"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        self.logger.info('Outbox 后台处理线程已启动')

    def stop(self) -> None:
        """停止后台处理线程"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self.logger.info('Outbox 后台处理线程已停止')

    def _process_loop(self) -> None:
        """处理循环"""
        while self._running:
            try:
                self._process_batch()
            except Exception as e:
                self.logger.error(f'Outbox 处理异常: {e}')

            time.sleep(self._interval)

    def _process_batch(self) -> None:
        """处理一批事件"""
        # 1. 查找待处理事件
        pending_events = self._outbox_repository.find_pending_events(
            limit=self._batch_size
        )

        if not pending_events:
            return

        self.logger.info(f'找到 {len(pending_events)} 个待处理事件')

        published_count = 0
        failed_count = 0
        retry_count = 0

        # 2. 逐个处理
        for event in pending_events:
            try:
                # 尝试发布
                success = self._event_bus.publish_from_outbox(event)

                if success:
                    # 标记为已发布
                    event.mark_as_published()
                    self._outbox_repository.update_status(
                        event.id,
                        OutboxStatus.PUBLISHED
                    )
                    published_count += 1
                    self.logger.info(f'事件 {event.id} 发布成功')
                else:
                    # 发布失败，计算下次重试时间
                    event.calculate_next_retry()

                    if event.should_retry():
                        self._outbox_repository.update_status(
                            event.id,
                            OutboxStatus.PENDING
                        )
                        retry_count += 1
                        self.logger.warning(f'事件 {event.id} 发布失败，将在 {event.next_retry_at} 重试')
                    else:
                        # 超过最大重试次数
                        self._outbox_repository.update_status(
                            event.id,
                            OutboxStatus.FAILED
                        )
                        failed_count += 1
                        self.logger.error(f'事件 {event.id} 发布失败，已达最大重试次数')
                        # TODO: 发送告警

            except Exception as e:
                self.logger.error(f'处理事件 {event.id} 时发生异常: {e}')

        # 记录处理统计
        self.logger.info({
            'event': 'outbox_processed',
            'total': len(pending_events),
            'published': published_count,
            'failed': failed_count,
            'retry_later': retry_count
        })
```

### 4.3 应用集成

```python
# src/app/__init__.py
from app.infrastructure.events.event_bus import EventBus
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.application.event_handlers import register_event_handlers
from app.infrastructure.persistence.repository_factory import RepositoryFactory

def create_app():
    app = Flask(__name__)
    # ... 其他初始化 ...

    # 初始化事件总线
    outbox_repository = RepositoryFactory.get_outbox_repository()
    event_bus = EventBus(outbox_repository)
    register_event_handlers(event_bus)

    # 初始化 Outbox 处理器
    outbox_processor = OutboxProcessor(
        outbox_repository=outbox_repository,
        event_bus=event_bus,
        interval_seconds=5
    )

    # 启动后台处理线程
    @app.before_first_request
    def start_outbox_processor():
        outbox_processor.start()

    # 注册应用关闭时的清理
    import atexit
    atexit.register(outbox_processor.stop)

    return app
```

### 4.4 监控指标

**关键指标**：
- Outbox 中待处理事件数量
- 平均发布延迟
- 发布成功率
- 失败事件数量

**日志记录**：
```python
self.logger.info({
    'event': 'outbox_processed',
    'total': len(pending_events),
    'published': published_count,
    'failed': failed_count,
    'retry_later': retry_count
})
```

---

## 5. 数据库和仓储实现

### 5.1 ORM 模型定义

```python
# database/flask_models.py
from datetime import datetime

class OutboxEvent(db.Model):
    """Outbox 事件 ORM 模型"""
    __tablename__ = 'outbox_events'

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)
    next_retry_at = db.Column(db.DateTime, nullable=True)
```

**注意**：系统会根据 ORM 模型自动建表，无需手动创建迁移文件。

### 5.2 枚举定义

```python
# src/app/domain/enums/outbox_status.py
from enum import Enum

class OutboxStatus(Enum):
    """Outbox 事件状态"""
    PENDING = 'pending'      # 待处理
    PUBLISHED = 'published'  # 已发布
    FAILED = 'failed'        # 发布失败
```

### 5.3 Outbox 仓储实现

```python
# src/app/infrastructure/persistence/sqlalchemy_outbox_repository.py
from typing import List
from datetime import datetime
from sqlalchemy import select, and_
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.enums.outbox_status import OutboxStatus
from database.flask_models import OutboxEvent, db

class SQLAlchemyOutboxRepository(OutboxRepository):
    """Outbox 仓储的 SQLAlchemy 实现"""

    def save(self, event: OutboxEventEntity) -> OutboxEventEntity:
        """保存事件"""
        orm_model = OutboxEvent(
            event_type=event.event_type,
            payload=event.payload,
            status=event.status.value,
            retry_count=event.retry_count,
            created_at=event.created_at,
            next_retry_at=event.next_retry_at
        )

        with db.session.begin():
            db.session.add(orm_model)
            db.session.flush()  # 获取 ID

        # 转换回领域实体
        return self._to_entity(orm_model)

    def find_pending_events(self, limit: int = 100) -> List[OutboxEventEntity]:
        """查找待处理事件"""
        now = datetime.now()

        stmt = select(OutboxEvent).where(
            and_(
                OutboxEvent.status == OutboxStatus.PENDING.value,
                OutboxEvent.next_retry_at <= now
            )
        ).order_by(
            OutboxEvent.created_at
        ).limit(limit)

        with db.session.begin():
            orm_models = db.session.execute(stmt).scalars().all()

        return [self._to_entity(model) for model in orm_models]

    def update_status(self, event_id: int, status: OutboxStatus) -> None:
        """更新事件状态"""
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)

        with db.session.begin():
            orm_model = db.session.execute(stmt).scalar_one()
            orm_model.status = status.value

            if status == OutboxStatus.PUBLISHED:
                orm_model.published_at = datetime.now()

    def _to_entity(self, orm_model: OutboxEvent) -> OutboxEventEntity:
        """转换为领域实体"""
        entity = OutboxEventEntity(
            event_type=orm_model.event_type,
            payload=orm_model.payload
        )
        entity.id = orm_model.id
        entity.status = OutboxStatus(orm_model.status)
        entity.retry_count = orm_model.retry_count
        entity.created_at = orm_model.created_at
        entity.published_at = orm_model.published_at
        entity.next_retry_at = orm_model.next_retry_at
        return entity
```

### 5.4 RepositoryFactory 集成

```python
# src/app/infrastructure/persistence/repository_factory.py
class RepositoryFactory:
    """仓储工厂"""

    @staticmethod
    def get_outbox_repository() -> OutboxRepository:
        """获取 Outbox 仓储"""
        return SQLAlchemyOutboxRepository()
```

---

## 6. 集成测试和验收标准

### 6.1 测试策略

**测试范围**：
1. **单元测试**：EventBus、OutboxProcessor、领域实体
2. **集成测试**：完整的事件发布流程
3. **端到端测试**：从 API 调用到事件处理的完整流程

**测试环境**：
- 使用内存数据库（`ENV_TYPE=unit`）
- Mock 事件处理器避免副作用
- 使用 pytest fixtures 快速构建测试数据

### 6.2 单元测试示例

```python
# tests/unit/test_event_bus.py
import pytest
from unittest.mock import Mock
from app.infrastructure.events.event_bus import EventBus
from app.domain.events.checkin_events import CheckinCompletedEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity

def test_publish_sync_success(mock_outbox_repository):
    """测试同步发布成功"""
    # Arrange
    event_bus = EventBus(mock_outbox_repository)
    handler = Mock()
    event_bus.subscribe('CheckinCompletedEvent', handler)

    event = CheckinCompletedEvent(record_id=1, user_id=100, rule_id=10)

    # Act
    event_bus.publish_with_fallback(event)

    # Assert
    handler.assert_called_once_with(event)
    mock_outbox_repository.save.assert_not_called()

def test_publish_sync_fallback_to_outbox(mock_outbox_repository):
    """测试同步发布失败降级到 Outbox"""
    # Arrange
    event_bus = EventBus(mock_outbox_repository)
    handler = Mock(side_effect=Exception('Handler failed'))
    event_bus.subscribe('CheckinCompletedEvent', handler)

    event = CheckinCompletedEvent(record_id=1, user_id=100, rule_id=10)

    # Act
    event_bus.publish_with_fallback(event)

    # Assert
    mock_outbox_repository.save.assert_called_once()

def test_outbox_entity_retry_logic():
    """测试重试逻辑"""
    # Arrange
    from app.domain.entities.outbox_event_entity import OutboxEventEntity

    event = OutboxEventEntity('CheckinCompletedEvent', {})

    # Act & Assert
    assert event.should_retry()
    assert event.retry_count == 0

    event.calculate_next_retry()
    assert event.retry_count == 1
    assert event.should_retry()

    event.retry_count = 5
    assert not event.should_retry()
```

### 6.3 集成测试示例

```python
# tests/integration/test_event_publishing_integration.py
import pytest
from app import create_app
from app.infrastructure.events.event_bus import EventBus
from app.infrastructure.persistence.repository_factory import RepositoryFactory

@pytest.fixture
def app_with_events():
    """创建带事件总线的应用"""
    app = create_app()
    app.config['TESTING'] = True
    return app

def test_checkin_event_publishing_flow(app_with_events):
    """测试打卡事件发布完整流程"""
    # 1. 执行打卡
    with app_with_events.test_client() as client:
        response = client.post('/api/checkin', json={
            'rule_id': 1
        }, headers={'Authorization': 'Bearer valid_token'})

        assert response.status_code == 200

    # 2. 验证事件发布（同步）
    outbox_repo = RepositoryFactory.get_outbox_repository()
    pending_events = outbox_repo.find_pending_events()

    # 因为同步发布成功，Outbox 应该为空
    assert len(pending_events) == 0
```

### 6.4 验收标准

**功能验收**：

| 验收项 | 标准 | 验证方法 |
|--------|------|---------|
| **事件发布可靠性** | 发布成功率 ≥ 99.9% | 统计日志中的发布成功率 |
| **Outbox 降级** | 同步发布失败时 100% 写入 Outbox | 单元测试 + 集成测试 |
| **后台处理** | 后台任务每 5 秒扫描一次 Outbox | 日志验证 |
| **重试机制** | 失败事件自动重试最多 5 次 | 单元测试 |
| **幂等性** | 重复处理同一事件不产生副作用 | 集成测试 |

**性能验收**：

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| **发布延迟** | 同步发布 < 100ms | 性能测试 |
| **Outbox 清理** | 待处理事件 < 1000 条 | 监控指标 |
| **内存占用** | 后台线程 < 50MB | 资源监控 |

### 6.5 监控和告警

**关键监控指标**：
```python
# src/app/infrastructure/events/metrics.py
class EventMetrics:
    """事件指标收集"""

    def __init__(self):
        self.published_count = 0
        self.failed_count = 0
        self.outbox_fallback_count = 0

    def record_published(self, event_type: str) -> None:
        """记录发布成功"""
        self.published_count += 1

    def record_failed(self, event_type: str) -> None:
        """记录发布失败"""
        self.failed_count += 1

    def record_outbox_fallback(self, event_type: str) -> None:
        """记录 Outbox 降级"""
        self.outbox_fallback_count += 1

    def get_success_rate(self) -> float:
        """计算成功率"""
        total = self.published_count + self.failed_count
        if total == 0:
            return 1.0
        return self.published_count / total
```

**告警规则**：
- Outbox 待处理事件 > 1000 条
- 发布成功率 < 99%
- 失败事件（status=failed）数量 > 10

---

## 7. 实施计划

### 7.1 任务分解

**Phase 1：基础架构（1.5 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 定义领域事件基类和枚举 | `src/app/domain/events/base_event.py`, `src/app/domain/enums/outbox_status.py` | 0.5 天 |
| 定义具体事件类型 | `src/app/domain/events/checkin_events.py` | 0.5 天 |
| 定义 OutboxEvent 实体 | `src/app/domain/entities/outbox_event_entity.py` | 0.5 天 |
| 创建 Outbox ORM 模型 | `database/flask_models.py` | 0.5 天 |

**Phase 2：仓储层（1 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 定义 Outbox 仓储接口 | `src/app/domain/repositories/outbox_repository.py` | 0.5 天 |
| 实现 Outbox 仓储 | `src/app/infrastructure/persistence/sqlalchemy_outbox_repository.py` | 0.5 天 |
| 更新 RepositoryFactory | `src/app/infrastructure/persistence/repository_factory.py` | 0.5 天 |

**Phase 3：事件总线（2 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 实现 EventBus | `src/app/infrastructure/events/event_bus.py` | 1 天 |
| 创建事件处理器 | `src/app/application/event_handlers/checkin_notification_handler.py` | 0.5 天 |
| 注册事件处理器 | `src/app/application/event_handlers/__init__.py` | 0.5 天 |

**Phase 4：后台任务（1.5 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 实现 OutboxProcessor | `src/app/infrastructure/events/outbox_processor.py` | 1 天 |
| 集成到应用启动 | `src/app/__init__.py` | 0.5 天 |

**Phase 5：重构 UseCase（1 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 重构 PerformCheckinUseCase | `src/app/application/use_cases/checkin/perform_checkin_use_case.py` | 0.5 天 |
| 移除旧的事件发布代码 | 移除 `perform_checkin_use_case.py:121-143` 的旧逻辑 | 0.5 天 |

**Phase 6：测试（2 天）**

| 任务 | 文件 | 预计时间 |
|------|------|---------|
| 编写单元测试 | `tests/unit/test_event_bus.py`, `tests/unit/test_outbox_processor.py` | 1 天 |
| 编写集成测试 | `tests/integration/test_event_publishing_integration.py` | 1 天 |

### 7.2 实施顺序

```
Week 1:
├── Day 1: Phase 1 (基础架构)
│   └── 定义领域模型和 ORM 模型（系统自动建表）
│
├── Day 2: Phase 2 (仓储层)
│   └── 实现 Outbox 仓储
│
├── Day 3-4: Phase 3 (事件总线)
│   ├── 实现 EventBus
│   └── 创建事件处理器
│
└── Day 5: Phase 4 (后台任务)
    └── 实现 OutboxProcessor

Week 2:
├── Day 6: Phase 5 (重构 UseCase)
│   └── 集成事件总线到打卡流程
│
├── Day 7-8: Phase 6 (测试)
│   ├── 单元测试
│   └── 集成测试
│
└── Day 9-10: 验收
    ├── 运行所有测试
    ├── 性能测试
    └── 代码审查
```

### 7.3 风险管理

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **后台线程稳定性** | 高 | 中 | 异常捕获、健康检查、自动重启 |
| **Outbox 表膨胀** | 中 | 低 | 定期清理任务、表大小监控 |
| **事件处理器阻塞** | 高 | 中 | 处理器超时、异步处理、快速降级 |
| **并发冲突** | 低 | 低 | 数据库事务隔离、行级锁 |

### 7.4 验收检查清单

**功能验收**：
- [ ] Outbox ORM 模型定义正确，系统自动建表成功
- [ ] EventBus 能同步发布事件
- [ ] 同步发布失败时写入 Outbox
- [ ] OutboxProcessor 能处理待发布事件
- [ ] 重试机制工作正常
- [ ] 打卡流程集成事件发布

**测试验收**：
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 性能测试达标

---

## 8. 附录和代码示例

### 8.1 完整文件结构

```
src/app/
├── domain/
│   ├── events/
│   │   ├── base_event.py              # 领域事件基类
│   │   └── checkin_events.py          # 打卡相关事件
│   ├── entities/
│   │   └── outbox_event_entity.py     # Outbox 事件实体
│   ├── repositories/
│   │   └── outbox_repository.py       # Outbox 仓储接口
│   └── enums/
│       └── outbox_status.py           # Outbox 状态枚举
│
├── application/
│   ├── event_handlers/
│   │   ├── __init__.py                # 事件处理器注册
│   │   └── checkin_notification_handler.py  # 打卡通知处理器
│   └── use_cases/
│       └── checkin/
│           └── perform_checkin_use_case.py  # 重构后的打卡 UseCase
│
└── infrastructure/
    ├── events/
    │   ├── event_bus.py               # 事件总线
    │   └── outbox_processor.py        # Outbox 后台处理器
    └── persistence/
        ├── sqlalchemy_outbox_repository.py  # Outbox 仓储实现
        └── repository_factory.py      # 仓储工厂

database/
└── flask_models.py                    # ORM 模型（添加 OutboxEvent）

tests/
├── unit/
│   ├── test_event_bus.py              # EventBus 单元测试
│   └── test_outbox_processor.py       # OutboxProcessor 单元测试
└── integration/
    └── test_event_publishing_integration.py  # 事件发布集成测试
```

### 8.2 配置示例

```python
# src/config.py
class Config:
    # ... 其他配置 ...

    # 事件总线配置
    EVENT_BUS_ENABLED = True
    OUTBOX_PROCESSOR_INTERVAL_SECONDS = 5
    OUTBOX_PROCESSOR_BATCH_SIZE = 100
    OUTBOX_MAX_RETRY_COUNT = 5
    OUTBOX_CLEANUP_DAYS = 30
```

### 8.3 日志示例

**结构化日志格式**：
```json
{
    "timestamp": "2026-01-18T10:30:00Z",
    "level": "INFO",
    "event": "checkin_completed",
    "record_id": 123,
    "user_id": 456,
    "rule_id": 78,
    "publish_method": "sync",
    "status": "success"
}

{
    "timestamp": "2026-01-18T10:30:01Z",
    "level": "WARNING",
    "event": "event_publish_fallback",
    "event_type": "CheckinCompletedEvent",
    "reason": "handler_timeout",
    "outbox_id": 999
}

{
    "timestamp": "2026-01-18T10:30:10Z",
    "level": "INFO",
    "event": "outbox_processed",
    "total": 5,
    "published": 4,
    "failed": 1,
    "retry_later": 0
}
```

---

## 参考资料

### DDD 相关

- **《Domain-Driven Design》** by Eric Evans - 领域事件基础
- **《Implementing Domain-Driven Design》** by Vaughn Vernon - 事件驱动架构

### 设计模式

- **Outbox Pattern**: https://microservices.io/patterns/data/transactional-outbox.html
- **Event-Driven Architecture**: https://martinfowler.com/articles/microservices.html#EventDrivenArchitecture

### 项目文档

- DDD 架构审查报告: `docs/plans/2026-01-17-16-17-ddd-architecture-review.md`
- 代码风格指南: `docs/code-style-guide.md`
- 集成测试编写指南: `docs/integration-test-writing-guide.md`

---

**文档生成时间**: 2026-01-18
**预计完成时间**: 2026-01-31
**负责人**: 开发团队
