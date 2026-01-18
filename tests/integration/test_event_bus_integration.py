"""
事件总线集成测试

测试事件总线在应用启动时的正确初始化和功能。
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock

from app import create_app
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class TestEventBusIntegration:
    """事件总线集成测试类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 设置环境变量为单元测试
        self.test_env = {'ENV_TYPE': 'unit'}

        # 创建简单的测试事件类
        from app.domain.events.domain_event import DomainEvent

        class TestEvent(DomainEvent):
            def __init__(self, aggregate_id, data):
                super().__init__(aggregate_id, data)

        self.TestEvent = TestEvent

    def test_event_bus_initialization(self):
        """测试事件总线的初始化"""
        # 创建应用实例
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 验证事件总线已正确初始化
            assert hasattr(app, 'event_bus'), "应用应该有 event_bus 属性"
            assert isinstance(app.event_bus, EnhancedEventBus), "event_bus 应该是 EnhancedEventBus 实例"

            # 验证 Outbox 处理器已正确初始化
            assert hasattr(app, 'outbox_processor'), "应用应该有 outbox_processor 属性"
            assert isinstance(app.outbox_processor, OutboxProcessor), "outbox_processor 应该是 OutboxProcessor 实例"

    def test_outbox_processor_running_state(self):
        """测试 Outbox 处理器的运行状态"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 验证处理器初始状态
            assert not app.outbox_processor._running, "Outbox 处理器初始状态应该为未运行"

            # 模拟第一个请求启动处理器
            with app.test_client() as client:
                # 发送一个请求来触发 before_first_request
                client.get('/api/health')

                # 等待一小段时间让处理器启动
                time.sleep(0.1)

                # 验证处理器已启动
                assert app.outbox_processor._running, "Outbox 处理器应该已经启动"

    def test_event_bus_with_repository_factory(self):
        """测试事件总线与仓储工厂的集成"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 验证使用的是同一个 outbox repository
            outbox_repo_from_factory = RepositoryFactory.get_outbox_repository()
            outbox_repo_from_event_bus = app.event_bus._outbox_repo

            # 由于是单例模式，应该返回同一个实例
            assert outbox_repo_from_factory is outbox_repo_from_event_bus, \
                "事件总线和工厂应该使用同一个 outbox repository 实例"

    def test_event_bus_publish_subscribe(self):
        """测试事件的发布和订阅功能"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 测试事件处理器
            events_received = []

            def test_handler(event):
                events_received.append((event.event_type, event.data))

            # 订阅事件
            app.event_bus.subscribe('TestEvent', test_handler)

            # 创建并发布事件
            test_event = self.TestEvent(aggregate_id=1, data={'message': 'Hello, EventBus!'})
            app.event_bus.publish_with_fallback(test_event)

            # 等待事件被处理
            time.sleep(0.1)

            # 验证事件被正确接收
            assert len(events_received) == 1, "应该接收到1个事件"
            assert events_received[0][0] == 'TestEvent', "事件名称应该匹配"
            assert events_received[0][1] == test_event.data, "事件载荷应该匹配"

    def test_atexit_cleanup(self):
        """测试应用退出时的清理功能"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 启动处理器
            with app.test_client() as client:
                client.get('/api/health')
                time.sleep(0.1)

            # 验证处理器正在运行
            assert app.outbox_processor._running, "处理器应该正在运行"

            # 手动触发清理
            app.outbox_processor.stop()

            # 验证处理器已停止
            assert not app.outbox_processor._running, "处理器应该已停止"

    def test_event_bus_error_handling(self):
        """测试事件总线的错误处理"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            # 测试订阅不存在的处理器
            def failing_handler(event):
                raise Exception("Handler error")

            # 订阅事件
            app.event_bus.subscribe('TestEvent', failing_handler)

            # 创建并发布事件，应该不会抛出异常，而是降级到 outbox
            test_event = self.TestEvent(aggregate_id=1, data={'data': 'test'})
            with app.app_context():
                try:
                    app.event_bus.publish_with_fallback(test_event)
                    time.sleep(0.1)
                    # 如果没有抛出异常，说明错误处理正确
                    assert True
                except Exception:
                    pytest.fail("事件处理器错误不应该影响应用")

    def test_multiple_event_types(self):
        """测试多种事件类型的处理"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            events_received = []

            def multi_handler(event):
                events_received.append((event.event_type, event.data))

            # 订阅多种事件
            app.event_bus.subscribe('TestEvent', multi_handler)

            # 发布各种事件
            app.event_bus.publish_with_fallback(self.TestEvent(1, {'id': 1, 'name': 'Alice'}))
            app.event_bus.publish_with_fallback(self.TestEvent(2, {'id': 1, 'name': 'Alice Smith'}))
            app.event_bus.publish_with_fallback(self.TestEvent(3, {'id': 1}))

            # 等待事件处理
            time.sleep(0.1)

            # 验证接收到所有事件
            assert len(events_received) == 3, "应该接收到3个事件"
            assert events_received[0][0] == 'TestEvent'
            assert events_received[1][0] == 'TestEvent'
            assert events_received[2][0] == 'TestEvent'

    def test_concurrent_events(self):
        """测试并发事件的处理"""
        with patch.dict('os.environ', self.test_env):
            app = create_app()

            events_received = []
            lock = threading.Lock()

            def concurrent_handler(event):
                with lock:
                    events_received.append((event.event_type, event.data))
                    # 模拟一些处理时间
                    time.sleep(0.01)

            # 订阅事件
            app.event_bus.subscribe('TestEvent', concurrent_handler)

            # 创建多个线程并发发布事件
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=app.event_bus.publish_with_fallback,
                    args=(self.TestEvent(aggregate_id=i, data={'thread_id': i}),)
                )
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 等待事件处理
            time.sleep(0.1)

            # 验证所有事件都被处理
            assert len(events_received) == 5, "应该处理完所有并发事件"

    def test_outbox_batch_processing(self):
        """测试 Outbox 的批量处理功能"""
        from app.domain.entities.outbox_event_entity import OutboxEventEntity
        from app.domain.enums.outbox_status import OutboxStatus

        with patch.dict('os.environ', self.test_env):
            app = create_app()

            with app.app_context():
                # 获取 outbox repository
                outbox_repo = RepositoryFactory.get_outbox_repository()

                # 创建 outbox 事件实体
                outbox_event = OutboxEventEntity(
                    event_type='BatchTestEvent',
                    payload={'data': 'batch test'}
                )

                # 保存 outbox 记录
                saved_event = outbox_repo.save(outbox_event)

                # 查找待处理事件
                pending_events = outbox_repo.find_pending_events(limit=10)

                # 验证找到待处理事件
                assert len(pending_events) > 0, "应该找到待处理事件"

                # 更新事件状态为已发布
                outbox_repo.update_status(pending_events[0].id, OutboxStatus.PUBLISHED)

                # 验证处理完成
                updated_events = outbox_repo.find_pending_events(limit=10)
                assert len(updated_events) == 0, "不应该再有待处理事件"