# 领域事件机制实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 checkin 模块建立完善的领域事件机制，使用 Outbox 模式确保事件可靠投递

**Architecture:** 使用混合投递策略 - 同步发布优先，失败后降级到 Outbox，后台任务重试

**Tech Stack:** Python 3.12, Flask 3.1.2, SQLAlchemy 2.0.16, 内存队列 + 数据库队列

---

## Phase 1: 基础架构 - Outbox 枚举和实体

### Task 1: 创建 Outbox 状态枚举

**Files:**
- Create: `src/app/domain/enums/__init__.py`
- Create: `src/app/domain/enums/outbox_status.py`

**Step 1: 创建枚举包初始化文件**

```bash
mkdir -p src/app/domain/enums
touch src/app/domain/enums/__init__.py
```

**Step 2: 创建 OutboxStatus 枚举**

```python
# src/app/domain/enums/outbox_status.py
from enum import Enum

class OutboxStatus(Enum):
    """Outbox 事件状态枚举"""
    PENDING = 'pending'      # 待处理
    PUBLISHED = 'published'  # 已发布
    FAILED = 'failed'        # 发布失败
```

**Step 3: 运行测试验证枚举**

```python
# tests/unit/test_outbox_status.py
import pytest
from app.domain.enums.outbox_status import OutboxStatus

def test_outbox_status_enum():
    """测试 OutboxStatus 枚举"""
    assert OutboxStatus.PENDING.value == 'pending'
    assert OutboxStatus.PUBLISHED.value == 'published'
    assert OutboxStatus.FAILED.value == 'failed'
```

Run: `pytest tests/unit/test_outbox_status.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/domain/enums/
git commit -m "feat: 添加 OutboxStatus 枚举"
```

---

### Task 2: 创建 OutboxEvent 领域实体

**Files:**
- Create: `src/app/domain/entities/outbox_event_entity.py`
- Test: `tests/unit/test_outbox_event_entity.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_outbox_event_entity.py
import pytest
from datetime import datetime, timedelta
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

def test_outbox_event_creation():
    """测试 OutboxEvent 实体创建"""
    entity = OutboxEventEntity('TestEvent', {'key': 'value'})

    assert entity.event_type == 'TestEvent'
    assert entity.payload == {'key': 'value'}
    assert entity.status == OutboxStatus.PENDING
    assert entity.retry_count == 0
    assert entity.created_at is not None
    assert entity.next_retry_at is not None

def test_mark_as_published():
    """测试标记为已发布"""
    entity = OutboxEventEntity('TestEvent', {})
    entity.mark_as_published()

    assert entity.status == OutboxStatus.PUBLISHED
    assert entity.published_at is not None

def test_calculate_next_retry():
    """测试计算下次重试时间（指数退避）"""
    entity = OutboxEventEntity('TestEvent', {})

    # 第一次重试：1秒
    entity.calculate_next_retry()
    assert entity.retry_count == 1
    expected_time = datetime.now() + timedelta(seconds=1)
    assert abs((entity.next_retry_at - expected_time).total_seconds()) < 1

    # 第五次重试：最多60秒
    entity.retry_count = 4
    entity.calculate_next_retry()
    assert entity.retry_count == 5
    expected_time = datetime.now() + timedelta(seconds=16)  # 2^4 = 16
    assert abs((entity.next_retry_at - expected_time).total_seconds()) < 1

def test_should_retry():
    """测试是否应该重试"""
    entity = OutboxEventEntity('TestEvent', {})

    assert entity.should_retry() is True

    entity.retry_count = 4
    assert entity.should_retry() is True

    entity.retry_count = 5
    assert entity.should_retry() is False
```

Run: `pytest tests/unit/test_outbox_event_entity.py -v`
Expected: FAIL with "No module named 'app.domain.entities.outbox_event_entity'"

**Step 2: Write minimal implementation**

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

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_outbox_event_entity.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/domain/entities/outbox_event_entity.py tests/unit/test_outbox_event_entity.py
git commit -m "feat: 添加 OutboxEventEntity 领域实体"
```

---

### Task 3: 创建 OutboxEvent ORM 模型

**Files:**
- Modify: `src/database/flask_models.py`

**Step 1: Find where to add the model**

查看 `src/database/flask_models.py`，在文件末尾添加 OutboxEvent 模型（在最后一个模型类之后）

**Step 2: Add OutboxEvent model to flask_models.py**

在 `src/database/flask_models.py` 末尾添加：

```python
class OutboxEvent(db.Model):
    """Outbox 事件 ORM 模型"""
    __tablename__ = 'outbox_events'

    id = db.Column(db.Integer, primary_key=True, comment='事件ID')
    event_type = db.Column(db.String(100), nullable=False, comment='事件类型', index=True)
    payload = db.Column(db.JSON, nullable=False, comment='事件数据')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='状态', index=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0, comment='重试次数')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间', index=True)
    published_at = db.Column(db.DateTime, nullable=True, comment='发布时间')
    next_retry_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='下次重试时间', index=True)

    # 索引优化
    __table_args__ = (
        db.Index('idx_outbox_event_type', 'event_type'),
        db.Index('idx_outbox_status', 'status'),
        db.Index('idx_outbox_status_next_retry', 'status', 'next_retry_at'),
        db.Index('idx_outbox_created_at', 'created_at'),
    )
```

**Step 3: Verify model creation**

```python
# tests/unit/test_outbox_model.py
from src.database.flask_models import OutboxEvent
from datetime import datetime

def test_outbox_model_creation():
    """测试 OutboxEvent ORM 模型创建"""
    event = OutboxEvent(
        event_type='TestEvent',
        payload={'key': 'value'},
        status='pending',
        retry_count=0,
        created_at=datetime.now(),
        next_retry_at=datetime.now()
    )

    assert event.event_type == 'TestEvent'
    assert event.payload == {'key': 'value'}
    assert event.status == 'pending'
    assert event.retry_count == 0
```

**Step 4: Commit**

```bash
git add src/database/flask_models.py
git commit -m "feat: 添加 OutboxEvent ORM 模型"
```

---

## Phase 2: 仓储层实现

### Task 4: 创建 Outbox 仓储接口

**Files:**
- Create: `src/app/domain/repositories/outbox_repository.py`
- Test: `tests/unit/test_outbox_repository.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_outbox_repository.py
import pytest
from abc import ABC
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.entities.outbox_event_entity import OutboxEventEntity

def test_outbox_repository_is_abstract():
    """测试 OutboxRepository 是抽象类"""
    assert issubclass(OutboxRepository, ABC)

def test_outbox_repository_has_required_methods():
    """测试 OutboxRepository 有必需的方法"""
    assert hasattr(OutboxRepository, 'save')
    assert hasattr(OutboxRepository, 'find_pending_events')
    assert hasattr(OutboxRepository, 'update_status')
```

Run: `pytest tests/unit/test_outbox_repository.py -v`
Expected: FAIL with "No module named 'app.domain.repositories.outbox_repository'"

**Step 2: Write minimal implementation**

```python
# src/app/domain/repositories/outbox_repository.py
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

class OutboxRepository(ABC):
    """Outbox 仓储接口"""

    @abstractmethod
    def save(self, event: OutboxEventEntity) -> OutboxEventEntity:
        """
        保存事件到 Outbox

        Args:
            event: Outbox 事件实体

        Returns:
            OutboxEventEntity: 保存后的实体（带 ID）
        """
        pass

    @abstractmethod
    def find_pending_events(self, limit: int = 100) -> List[OutboxEventEntity]:
        """
        查找待处理事件

        Args:
            limit: 最大返回数量

        Returns:
            List[OutboxEventEntity]: 待处理事件列表
        """
        pass

    @abstractmethod
    def update_status(self, event_id: int, status: OutboxStatus) -> None:
        """
        更新事件状态

        Args:
            event_id: 事件 ID
            status: 新状态
        """
        pass
```

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_outbox_repository.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/domain/repositories/outbox_repository.py tests/unit/test_outbox_repository.py
git commit -m "feat: 添加 OutboxRepository 仓储接口"
```

---

### Task 5: 实现 SQLAlchemy Outbox 仓储

**Files:**
- Create: `src/app/infrastructure/persistence/sqlalchemy_outbox_repository.py`
- Test: `tests/unit/test_sqlalchemy_outbox_repository.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_sqlalchemy_outbox_repository.py
import pytest
from datetime import datetime
from app.infrastructure.persistence.sqlalchemy_outbox_repository import SQLAlchemyOutboxRepository
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

@pytest.fixture
def outbox_repository():
    """创建 Outbox 仓储实例"""
    return SQLAlchemyOutboxRepository()

def test_save_outbox_event(outbox_repository):
    """测试保存 Outbox 事件"""
    entity = OutboxEventEntity('TestEvent', {'key': 'value'})

    saved = outbox_repository.save(entity)

    assert saved.id is not None
    assert saved.event_type == 'TestEvent'
    assert saved.status == OutboxStatus.PENDING

def test_find_pending_events(outbox_repository):
    """测试查找待处理事件"""
    # 创建一个待处理事件
    entity = OutboxEventEntity('TestEvent', {})
    outbox_repository.save(entity)

    # 查找待处理事件
    pending = outbox_repository.find_pending_events(limit=10)

    assert len(pending) > 0
    assert any(e.id == entity.id for e in pending)

def test_update_status(outbox_repository):
    """测试更新事件状态"""
    entity = OutboxEventEntity('TestEvent', {})
    saved = outbox_repository.save(entity)

    # 更新状态
    outbox_repository.update_status(saved.id, OutboxStatus.PUBLISHED)

    # 验证状态已更新
    updated_events = outbox_repository.find_pending_events()
    assert not any(e.id == saved.id for e in updated_events)
```

Run: `pytest tests/unit/test_sqlalchemy_outbox_repository.py -v`
Expected: FAIL with "No module named 'app.infrastructure.persistence.sqlalchemy_outbox_repository'"

**Step 2: Write minimal implementation**

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

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_sqlalchemy_outbox_repository.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/infrastructure/persistence/sqlalchemy_outbox_repository.py tests/unit/test_sqlalchemy_outbox_repository.py
git commit -m "feat: 实现 SQLAlchemyOutboxRepository"
```

---

### Task 6: 更新 RepositoryFactory

**Files:**
- Modify: `src/app/infrastructure/persistence/repository_factory.py`

**Step 1: Add Outbox 仓储到 RepositoryFactory**

在 `src/app/infrastructure/persistence/repository_factory.py` 中添加：

1. 在文件顶部导入：
```python
from app.domain.repositories.outbox_repository import OutboxRepository
from app.infrastructure.persistence.sqlalchemy_outbox_repository import SQLAlchemyOutboxRepository
```

2. 在 RepositoryFactory 类中添加类变量：
```python
_outbox_repository: Optional[OutboxRepository] = None
```

3. 在 RepositoryFactory 类中添加方法：
```python
@classmethod
def get_outbox_repository(cls) -> OutboxRepository:
    """
    获取 Outbox 仓储实例

    Returns:
        OutboxRepository: Outbox 仓储实例
    """
    if cls._outbox_repository is None:
        cls._outbox_repository = SQLAlchemyOutboxRepository()
    return cls._outbox_repository
```

4. 在 `reset` 方法中添加：
```python
cls._outbox_repository = None
```

**Step 2: Test the factory**

```python
# tests/unit/test_repository_factory.py
from app.infrastructure.persistence.repository_factory import RepositoryFactory

def test_get_outbox_repository():
    """测试获取 Outbox 仓储"""
    repo1 = RepositoryFactory.get_outbox_repository()
    repo2 = RepositoryFactory.get_outbox_repository()

    # 验证单例模式
    assert repo1 is repo2
    assert repo1 is not None

def test_reset_repository_factory():
    """测试重置仓储工厂"""
    repo1 = RepositoryFactory.get_outbox_repository()
    RepositoryFactory.reset()
    repo2 = RepositoryFactory.get_outbox_repository()

    # 验证重置后创建新实例
    assert repo1 is not repo2
```

Run: `pytest tests/unit/test_repository_factory.py::test_get_outbox_repository -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/app/infrastructure/persistence/repository_factory.py tests/unit/test_repository_factory.py
git commit -m "feat: 添加 Outbox 仓储到 RepositoryFactory"
```

---

## Phase 3: 增强事件总线

### Task 7: 创建增强的事件总线（支持 Outbox 降级）

**Files:**
- Create: `src/app/infrastructure/events/enhanced_event_bus.py`
- Test: `tests/unit/test_enhanced_event_bus.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_enhanced_event_bus.py
import pytest
from unittest.mock import Mock, MagicMock
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.domain.events.checkin_events import CheckinCompletedEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity

def test_subscribe_and_publish_sync():
    """测试订阅和同步发布"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    handler = Mock()
    event_bus.subscribe('CheckinCompletedEvent', handler)

    event = CheckinCompletedEvent(1, 100, 10)
    event_bus.publish_with_fallback(event)

    # 验证处理器被调用
    handler.assert_called_once()
    # 验证没有写入 Outbox（因为同步成功）
    mock_outbox_repo.save.assert_not_called()

def test_publish_fallback_to_outbox():
    """测试发布失败时降级到 Outbox"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    # 创建一个会失败的处理器
    handler = Mock(side_effect=Exception('Handler failed'))
    event_bus.subscribe('CheckinCompletedEvent', handler)

    event = CheckinCompletedEvent(1, 100, 10)
    event_bus.publish_with_fallback(event)

    # 验证写入了 Outbox
    mock_outbox_repo.save.assert_called_once()
    saved_event = mock_outbox_repo.save.call_args[0][0]
    assert saved_event.event_type == 'CheckinCompletedEvent'

def test_publish_from_outbox():
    """测试从 Outbox 发布事件"""
    mock_outbox_repo = Mock()
    event_bus = EnhancedEventBus(mock_outbox_repo)

    handler = Mock()
    event_bus.subscribe('CheckinCompletedEvent', handler)

    # 创建一个模拟的 OutboxEvent
    outbox_event = OutboxEventEntity('CheckinCompletedEvent', {
        'record_id': 1,
        'user_id': 100,
        'rule_id': 10
    })

    success = event_bus.publish_from_outbox(outbox_event)

    assert success is True
    handler.assert_called_once()
```

Run: `pytest tests/unit/test_enhanced_event_bus.py -v`
Expected: FAIL with "No module named 'app.infrastructure.events.enhanced_event_bus'"

**Step 2: Write minimal implementation**

```python
# src/app/infrastructure/events/enhanced_event_bus.py
from typing import Callable, Dict, List
from threading import Lock
import logging
from app.domain.events.domain_event import DomainEvent
from app.domain.events.checkin_events import CheckinCompletedEvent, CheckinMissedEvent
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.repositories.outbox_repository import OutboxRepository
from datetime import datetime

class EnhancedEventBus:
    """增强的事件总线（支持 Outbox 降级）"""

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

    def publish_with_fallback(self, event: DomainEvent) -> None:
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
                payload={
                    'event_id': event.event_id,
                    'aggregate_id': event.aggregate_id,
                    'data': event.data,
                    'occurred_on': event.occurred_on.isoformat()
                }
            )
            self._outbox_repository.save(outbox_event)

    def _publish_sync(self, event: DomainEvent) -> None:
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

    def _deserialize_event(self, outbox_event: OutboxEventEntity) -> DomainEvent:
        """从 Outbox 事件反序列化领域事件"""
        event_type = outbox_event.event_type
        payload = outbox_event.payload

        if event_type == 'CheckinCompletedEvent':
            return CheckinCompletedEvent(
                record_id=payload['aggregate_id'],
                user_id=payload['data']['user_id'],
                rule_id=payload['data']['rule_id'],
                checkin_time=datetime.fromisoformat(payload['data']['checkin_time'])
            )
        elif event_type == 'CheckinMissedEvent':
            return CheckinMissedEvent(
                record_id=payload['aggregate_id'],
                user_id=payload['data']['user_id'],
                rule_id=payload['data']['rule_id'],
                scheduled_time=datetime.fromisoformat(payload['data']['scheduled_time'])
            )

        raise ValueError(f'未知事件类型: {event_type}')
```

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_enhanced_event_bus.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/infrastructure/events/enhanced_event_bus.py tests/unit/test_enhanced_event_bus.py
git commit -m "feat: 添加增强的事件总线（支持 Outbox 降级）"
```

---

## Phase 4: 后台任务实现

### Task 8: 创建 Outbox 后台处理器

**Files:**
- Create: `src/app/infrastructure/events/outbox_processor.py`
- Test: `tests/unit/test_outbox_processor.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_outbox_processor.py
import pytest
import time
from unittest.mock import Mock, MagicMock
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.enums.outbox_status import OutboxStatus

def test_outbox_processor_start_stop():
    """测试处理器启动和停止"""
    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = []
    mock_event_bus = Mock()

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    processor.start()
    assert processor._running is True
    assert processor._thread is not None

    processor.stop()
    assert processor._running is False

def test_outbox_processor_processes_events():
    """测试处理器处理事件"""
    # 创建模拟事件
    event1 = OutboxEventEntity('TestEvent', {'id': 1})
    event1.id = 1
    event2 = OutboxEventEntity('TestEvent', {'id': 2})
    event2.id = 2

    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = [event1, event2]

    mock_event_bus = Mock()
    mock_event_bus.publish_from_outbox.return_value = True

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    # 手动触发一次处理
    processor._process_batch()

    # 验证处理了两个事件
    assert mock_event_bus.publish_from_outbox.call_count == 2
    assert mock_outbox_repo.update_status.call_count == 2

def test_outbox_processor_retry_logic():
    """测试重试逻辑"""
    event = OutboxEventEntity('TestEvent', {})
    event.id = 1

    mock_outbox_repo = Mock()
    mock_outbox_repo.find_pending_events.return_value = [event]

    mock_event_bus = Mock()
    mock_event_bus.publish_from_outbox.return_value = False  # 发布失败

    processor = OutboxProcessor(
        mock_outbox_repo,
        mock_event_bus,
        interval_seconds=1
    )

    processor._process_batch()

    # 验证计算了下一次重试时间
    assert event.retry_count > 0
    # 验证没有标记为已发布
    mock_outbox_repo.update_status.assert_not_called()
```

Run: `pytest tests/unit/test_outbox_processor.py -v`
Expected: FAIL with "No module named 'app.infrastructure.events.outbox_processor'"

**Step 2: Write minimal implementation**

```python
# src/app/infrastructure/events/outbox_processor.py
import threading
import time
from typing import Optional
import logging
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.enums.outbox_status import OutboxStatus
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus

class OutboxProcessor:
    """Outbox 后台处理器"""

    def __init__(
        self,
        outbox_repository: OutboxRepository,
        event_bus: EnhancedEventBus,
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

**Step 3: Run test to verify it passes**

Run: `pytest tests/unit/test_outbox_processor.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/infrastructure/events/outbox_processor.py tests/unit/test_outbox_processor.py
git commit -m "feat: 添加 Outbox 后台处理器"
```

---

## Phase 5: 应用集成

### Task 9: 集成事件总线到应用启动

**Files:**
- Modify: `src/app/__init__.py`
- Test: `tests/integration/test_event_bus_integration.py`

**Step 1: 在应用初始化时集成事件总线**

在 `src/app/__init__.py` 中的 `create_app()` 函数中添加事件总线初始化代码：

1. 在导入部分添加：
```python
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.infrastructure.persistence.repository_factory import RepositoryFactory
```

2. 在 `create_app()` 函数中，在配置数据库之后添加：

```python
def create_app(config_class=Config):
    """应用工厂"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ... 现有初始化代码 ...

    # 初始化事件总线
    outbox_repository = RepositoryFactory.get_outbox_repository()
    app.event_bus = EnhancedEventBus(outbox_repository)

    # 初始化 Outbox 处理器
    app.outbox_processor = OutboxProcessor(
        outbox_repository=outbox_repository,
        event_bus=app.event_bus,
        interval_seconds=app.config.get('OUTBOX_PROCESSOR_INTERVAL_SECONDS', 5)
    )

    # 启动后台处理线程
    @app.before_first_request
    def start_outbox_processor():
        if not app.outbox_processor._running:
            app.outbox_processor.start()

    # 注册应用关闭时的清理
    import atexit
    atexit.register(app.outbox_processor.stop)

    return app
```

**Step 2: Test the integration**

```python
# tests/integration/test_event_bus_integration.py
import pytest
from app import create_app
from app.infrastructure.persistence.repository_factory import RepositoryFactory

def test_event_bus_initialized():
    """测试事件总线已初始化"""
    app = create_app()

    with app.app_context():
        assert hasattr(app, 'event_bus')
        assert hasattr(app, 'outbox_processor')
        assert app.event_bus is not None
        assert app.outbox_processor is not None

def test_outbox_processor_running():
    """测试 Outbox 处理器正在运行"""
    app = create_app()

    with app.app_context():
        # 触发 before_first_request
        with app.test_client() as client:
            client.get('/')  # 任何请求触发 before_first_request

        assert app.outbox_processor._running is True
```

Run: `pytest tests/integration/test_event_bus_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/app/__init__.py tests/integration/test_event_bus_integration.py
git commit -m "feat: 集成事件总线到应用启动"
```

---

### Task 10: 重构 PerformCheckinUseCase 使用增强事件总线

**Files:**
- Modify: `src/app/application/use_cases/checkin/perform_checkin_use_case.py`

**Step 1: 查看现有代码**

首先读取 `src/app/application/use_cases/checkin/perform_checkin_use_case.py`，找到旧的事件发布代码（大约在 121-143 行）。

**Step 2: 修改 UseCase 使用增强事件总线**

在 `PerformCheckinUseCase` 类中：

1. 在 `__init__` 方法中注入事件总线：
```python
def __init__(self):
    super().__init__()
    # ... 现有仓储初始化 ...
    from flask import current_app
    self.event_bus = current_app.event_bus
```

2. 找到旧的事件发布代码（121-143 行），将其替换为：
```python
# 发布领域事件（事务成功后）
event = CheckinCompletedEvent(
    record_id=updated_record.record_id,
    user_id=user_id,
    rule_id=rule_id,
    checkin_time=checkin_time
)
self.event_bus.publish_with_fallback(event)
```

3. 删除旧的事件发布代码（try-except 块中的聚合根创建逻辑）

**Step 3: Test the refactored UseCase**

```python
# tests/integration/test_perform_checkin_use_case_refactored.py
import pytest
from app.application.use_cases.checkin.perform_checkin_use_case import PerformCheckinUseCase
from app.infrastructure.persistence.repository_factory import RepositoryFactory

def test_use_case_publishes_event():
    """测试 UseCase 发布事件"""
    use_case = PerformCheckinUseCase()

    # 执行打卡
    result = use_case.execute(rule_id=1, user_id=100)

    # 验证打卡成功
    assert result.is_success is True

    # 验证事件已发布（检查 Outbox 应该为空，因为同步发布成功）
    outbox_repo = RepositoryFactory.get_outbox_repository()
    pending_events = outbox_repo.find_pending_events()
    assert len(pending_events) == 0
```

Run: `pytest tests/integration/test_perform_checkin_use_case_refactored.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/app/application/use_cases/checkin/perform_checkin_use_case.py tests/integration/test_perform_checkin_use_case_refactored.py
git commit -m "refactor: 重构 PerformCheckinUseCase 使用增强事件总线"
```

---

## Phase 6: 最终测试和验证

### Task 11: 端到端测试

**Files:**
- Test: `tests/integration/test_event_bus_e2e.py`

**Step 1: Write comprehensive E2E test**

```python
# tests/integration/test_event_bus_e2e.py
import pytest
import time
from app import create_app
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.outbox_event_entity import OutboxEventEntity

def test_full_event_flow():
    """测试完整的事件流程"""
    app = create_app()

    with app.app_context():
        # 1. 创建一个失败的处理器，强制事件写入 Outbox
        def failing_handler(event):
            raise Exception('Simulated handler failure')

        app.event_bus.subscribe('TestEvent', failing_handler)

        # 2. 手动创建一个领域事件并发布
        from app.domain.events.checkin_events import CheckinCompletedEvent
        from datetime import datetime

        event = CheckinCompletedEvent(1, 100, 10, datetime.now())
        app.event_bus.publish_with_fallback(event)

        # 3. 验证事件写入 Outbox
        outbox_repo = RepositoryFactory.get_outbox_repository()
        pending_events = outbox_repo.find_pending_events()
        assert len(pending_events) > 0

        # 4. 移除失败的处理器，添加成功的处理器
        app.event_bus._subscribers['TestEvent'] = []
        success_handler_called = False

        def success_handler(event):
            nonlocal success_handler_called
            success_handler_called = True

        app.event_bus.subscribe('TestEvent', success_handler)

        # 5. 手动触发 Outbox 处理器
        app.outbox_processor._process_batch()

        # 6. 验证事件被处理
        pending_events = outbox_repo.find_pending_events()
        assert len(pending_events) == 0  # 所有事件已处理
```

Run: `pytest tests/integration/test_event_bus_e2e.py -v`
Expected: PASS

**Step 2: Commit**

```bash
git add tests/integration/test_event_bus_e2e.py
git commit -m "test: 添加事件总线端到端测试"
```

### Task 12: 运行所有测试

**Step 1: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: All PASS

**Step 2: Run all integration tests**

```bash
pytest tests/integration/ -v
```

Expected: All PASS

**Step 3: Run with coverage**

```bash
pytest --cov=app.infrastructure.events --cov=app.domain.entities.outbox_event_entity --cov=app.domain.repositories.outbox_repository --cov-report=html
```

Expected: Coverage > 80%

---

## 验收检查清单

**功能验收**：
- [ ] OutboxEvent ORM 模型定义正确，系统自动建表成功
- [ ] EventBus 能同步发布事件
- [ ] 同步发布失败时写入 Outbox
- [ ] OutboxProcessor 能处理待发布事件
- [ ] 重试机制工作正常（指数退避）
- [ ] 打卡流程集成事件发布

**测试验收**：
- [ ] 单元测试覆盖率 > 80%
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 端到端测试通过

---

## 故障排查

**问题 1: Outbox 表未自动创建**
- 检查 `src/database/flask_models.py` 中 `OutboxEvent` 模型定义
- 确认应用启动时调用了 `db.create_all()`

**问题 2: 事件总线处理器未收到事件**
- 检查事件类型名称是否匹配（`event.event_type` vs 订阅的类型）
- 检查处理器是否已正确订阅

**问题 3: Outbox 处理器未运行**
- 检查 `before_first_request` 是否触发
- 检查 `app.outbox_processor._running` 状态

---

## 实施完成后的清理

1. **删除临时测试文件**（如果有）
2. **更新文档**：
   - 更新 `docs/plans/2026-01-18-ddd-phase3-event-bus-implementation.md` 标记为已完成
   - 创建 `docs/domain-events-guide.md` 使用指南
3. **创建 Pull Request** 并请求代码审查

---

**计划完成时间**: 约 8-10 个工作日
**下一步**: 选择执行方式（Subagent-Driven 或 Parallel Session）
