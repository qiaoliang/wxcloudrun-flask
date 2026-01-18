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
