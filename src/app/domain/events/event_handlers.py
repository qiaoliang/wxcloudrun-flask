"""
事件处理器

处理领域事件的逻辑。
"""
import logging
from typing import Dict, Any

from app.domain.events.domain_event import DomainEvent
from app.domain.events.user_events import UserCreatedEvent, UserJoinedCommunityEvent, UserLeftCommunityEvent
from app.domain.events.community_events import CommunityCreatedEvent, CommunityMemberAddedEvent
from app.domain.events.checkin_events import CheckinCompletedEvent, CheckinMissedEvent

logger = logging.getLogger(__name__)


class UserEventHandler:
    """用户事件处理器"""

    @staticmethod
    def handle_user_created(event: UserCreatedEvent) -> None:
        """
        处理用户创建事件

        Args:
            event: 用户创建事件
        """
        logger.info(f"处理用户创建事件: 用户ID={event.aggregate_id}, 手机号={event.data.get('phone_number')}")
        # 这里可以添加发送欢迎短信、初始化用户数据等逻辑

    @staticmethod
    def handle_user_joined_community(event: UserJoinedCommunityEvent) -> None:
        """
        处理用户加入社区事件

        Args:
            event: 用户加入社区事件
        """
        logger.info(f"处理用户加入社区事件: 用户ID={event.data.get('user_id')}, 社区ID={event.data.get('community_id')}")
        # 这里可以添加发送欢迎消息、通知社区成员等逻辑

    @staticmethod
    def handle_user_left_community(event: UserLeftCommunityEvent) -> None:
        """
        处理用户离开社区事件

        Args:
            event: 用户离开社区事件
        """
        logger.info(f"处理用户离开社区事件: 用户ID={event.data.get('user_id')}, 社区ID={event.data.get('community_id')}")
        # 这里可以添加清理用户数据、通知社区成员等逻辑


class CommunityEventHandler:
    """社区事件处理器"""

    @staticmethod
    def handle_community_created(event: CommunityCreatedEvent) -> None:
        """
        处理社区创建事件

        Args:
            event: 社区创建事件
        """
        logger.info(f"处理社区创建事件: 社区ID={event.aggregate_id}, 社区名称={event.data.get('community_name')}, 创建者ID={event.data.get('creator_id')}")
        # 这里可以添加初始化社区数据、创建默认规则等逻辑

    @staticmethod
    def handle_community_member_added(event: CommunityMemberAddedEvent) -> None:
        """
        处理社区成员添加事件

        Args:
            event: 社区成员添加事件
        """
        logger.info(f"处理社区成员添加事件: 社区ID={event.data.get('community_id')}, 用户ID={event.data.get('user_id')}, 角色={event.data.get('role')}")
        # 这里可以添加发送欢迎消息、更新社区统计等逻辑


class CheckinEventHandler:
    """打卡事件处理器"""

    @staticmethod
    def handle_checkin_completed(event: CheckinCompletedEvent) -> None:
        """
        处理打卡完成事件

        Args:
            event: 打卡完成事件
        """
        logger.info(f"处理打卡完成事件: 记录ID={event.aggregate_id}, 用户ID={event.data.get('user_id')}, 规则ID={event.data.get('rule_id')}")
        # 这里可以添加更新用户统计、发送通知等逻辑

    @staticmethod
    def handle_checkin_missed(event: CheckinMissedEvent) -> None:
        """
        处理打卡错过事件

        Args:
            event: 打卡错过事件
        """
        logger.info(f"处理打卡错过事件: 记录ID={event.aggregate_id}, 用户ID={event.data.get('user_id')}, 规则ID={event.data.get('rule_id')}")
        # 这里可以添加更新异常值、通知监护人等逻辑


# 注册事件处理器
def register_event_handlers() -> None:
    """注册所有事件处理器"""
    from app.domain.events.event_bus import EventBus

    # 用户事件
    EventBus.subscribe(UserCreatedEvent, UserEventHandler.handle_user_created)
    EventBus.subscribe(UserJoinedCommunityEvent, UserEventHandler.handle_user_joined_community)
    EventBus.subscribe(UserLeftCommunityEvent, UserEventHandler.handle_user_left_community)

    # 社区事件
    EventBus.subscribe(CommunityCreatedEvent, CommunityEventHandler.handle_community_created)
    EventBus.subscribe(CommunityMemberAddedEvent, CommunityEventHandler.handle_community_member_added)

    # 打卡事件
    EventBus.subscribe(CheckinCompletedEvent, CheckinEventHandler.handle_checkin_completed)
    EventBus.subscribe(CheckinMissedEvent, CheckinEventHandler.handle_checkin_missed)

    logger.info("所有事件处理器已注册")