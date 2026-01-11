"""
仓储工厂

提供仓储实例的创建和获取。
"""
from typing import Optional

from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.community_repository import CommunityRepository
from app.domain.repositories.checkin_rule_repository import CheckinRuleRepository
from app.domain.repositories.checkin_record_repository import CheckinRecordRepository
from app.domain.repositories.community_event_repository import CommunityEventRepository
from app.domain.repositories.event_message_repository import EventMessageRepository
from app.domain.repositories.community_staff_repository import CommunityStaffRepository

from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.persistence.sqlalchemy_community_repository import SQLAlchemyCommunityRepository
from app.infrastructure.persistence.sqlalchemy_checkin_rule_repository import SQLAlchemyCheckinRuleRepository
from app.infrastructure.persistence.sqlalchemy_checkin_record_repository import SQLAlchemyCheckinRecordRepository
from app.infrastructure.persistence.sqlalchemy_community_event_repository import SQLAlchemyCommunityEventRepository
from app.infrastructure.persistence.sqlalchemy_event_message_repository import SQLAlchemyEventMessageRepository
from app.infrastructure.persistence.sqlalchemy_community_staff_repository import SQLAlchemyCommunityStaffRepository


class RepositoryFactory:
    """仓储工厂"""

    _user_repository: Optional[UserRepository] = None
    _community_repository: Optional[CommunityRepository] = None
    _checkin_rule_repository: Optional[CheckinRuleRepository] = None
    _checkin_record_repository: Optional[CheckinRecordRepository] = None
    _community_event_repository: Optional[CommunityEventRepository] = None
    _event_message_repository: Optional[EventMessageRepository] = None
    _community_staff_repository: Optional[CommunityStaffRepository] = None

    @classmethod
    def get_user_repository(cls) -> UserRepository:
        """
        获取用户仓储实例

        Returns:
            UserRepository: 用户仓储实例
        """
        if cls._user_repository is None:
            cls._user_repository = SQLAlchemyUserRepository()
        return cls._user_repository

    @classmethod
    def get_community_repository(cls) -> CommunityRepository:
        """
        获取社区仓储实例

        Returns:
            CommunityRepository: 社区仓储实例
        """
        if cls._community_repository is None:
            cls._community_repository = SQLAlchemyCommunityRepository()
        return cls._community_repository

    @classmethod
    def get_checkin_rule_repository(cls) -> CheckinRuleRepository:
        """
        获取打卡规则仓储实例

        Returns:
            CheckinRuleRepository: 打卡规则仓储实例
        """
        if cls._checkin_rule_repository is None:
            cls._checkin_rule_repository = SQLAlchemyCheckinRuleRepository()
        return cls._checkin_rule_repository

    @classmethod
    def get_checkin_record_repository(cls) -> CheckinRecordRepository:
        """
        获取打卡记录仓储实例

        Returns:
            CheckinRecordRepository: 打卡记录仓储实例
        """
        if cls._checkin_record_repository is None:
            cls._checkin_record_repository = SQLAlchemyCheckinRecordRepository()
        return cls._checkin_record_repository

    @classmethod
    def get_community_event_repository(cls) -> CommunityEventRepository:
        """
        获取社区事件仓储实例

        Returns:
            CommunityEventRepository: 社区事件仓储实例
        """
        if cls._community_event_repository is None:
            cls._community_event_repository = SQLAlchemyCommunityEventRepository()
        return cls._community_event_repository

    @classmethod
    def get_event_message_repository(cls) -> EventMessageRepository:
        """
        获取事件消息仓储实例

        Returns:
            EventMessageRepository: 事件消息仓储实例
        """
        if cls._event_message_repository is None:
            cls._event_message_repository = SQLAlchemyEventMessageRepository()
        return cls._event_message_repository

    @classmethod
    def get_community_staff_repository(cls) -> CommunityStaffRepository:
        """
        获取社区工作人员仓储实例

        Returns:
            CommunityStaffRepository: 社区工作人员仓储实例
        """
        if cls._community_staff_repository is None:
            cls._community_staff_repository = SQLAlchemyCommunityStaffRepository()
        return cls._community_staff_repository

    @classmethod
    def reset(cls):
        """重置仓储实例（主要用于测试）"""
        cls._user_repository = None
        cls._community_repository = None
        cls._checkin_rule_repository = None
        cls._checkin_record_repository = None
        cls._community_event_repository = None
        cls._event_message_repository = None
        cls._community_staff_repository = None