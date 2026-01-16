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
from app.domain.repositories.share_link_repository import ShareLinkRepository
from app.domain.repositories.share_link_access_log_repository import ShareLinkAccessLogRepository
from app.domain.repositories.supervision_relation_repository import SupervisionRelationRepository
from app.domain.repositories.community_checkin_rule_repository import CommunityCheckinRuleRepository
from app.domain.repositories.user_community_rule_repository import UserCommunityRuleRepository
from app.domain.repositories.user_daily_abnormality_repository import UserDailyAbnormalityRepository
from app.domain.repositories.profile_view_log_repository import ProfileViewLogRepository
from app.domain.repositories.counters_repository import CountersRepository
from app.domain.repositories.verification_code_repository import VerificationCodeRepository
from app.domain.repositories.community_dashboard_repository import CommunityDashboardRepository

from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.persistence.sqlalchemy_community_repository import SQLAlchemyCommunityRepository
from app.infrastructure.persistence.sqlalchemy_checkin_rule_repository import SQLAlchemyCheckinRuleRepository
from app.infrastructure.persistence.sqlalchemy_checkin_record_repository import SQLAlchemyCheckinRecordRepository
from app.infrastructure.persistence.sqlalchemy_community_event_repository import SQLAlchemyCommunityEventRepository
from app.infrastructure.persistence.sqlalchemy_event_message_repository import SQLAlchemyEventMessageRepository
from app.infrastructure.persistence.sqlalchemy_community_staff_repository import SQLAlchemyCommunityStaffRepository
from app.infrastructure.persistence.sqlalchemy_share_link_repository import SQLAlchemyShareLinkRepository
from app.infrastructure.persistence.sqlalchemy_share_link_access_log_repository import SQLAlchemyShareLinkAccessLogRepository
from app.infrastructure.persistence.sqlalchemy_supervision_relation_repository import SQLAlchemySupervisionRelationRepository
from app.infrastructure.persistence.sqlalchemy_community_checkin_rule_repository import SQLAlchemyCommunityCheckinRuleRepository
from app.infrastructure.persistence.sqlalchemy_user_community_rule_repository import SQLAlchemyUserCommunityRuleRepository
from app.infrastructure.persistence.sqlalchemy_user_daily_abnormality_repository import SQLAlchemyUserDailyAbnormalityRepository
from app.infrastructure.persistence.sqlalchemy_profile_view_log_repository import SQLAlchemyProfileViewLogRepository
from app.infrastructure.persistence.sqlalchemy_counters_repository import SQLAlchemyCountersRepository
from app.infrastructure.persistence.sqlalchemy_verification_code_repository import SQLAlchemyVerificationCodeRepository
from app.infrastructure.persistence.sqlalchemy_community_dashboard_repository import SQLAlchemyCommunityDashboardRepository


class RepositoryFactory:
    """仓储工厂"""

    _user_repository: Optional[UserRepository] = None
    _community_repository: Optional[CommunityRepository] = None
    _checkin_rule_repository: Optional[CheckinRuleRepository] = None
    _checkin_record_repository: Optional[CheckinRecordRepository] = None
    _community_event_repository: Optional[CommunityEventRepository] = None
    _event_message_repository: Optional[EventMessageRepository] = None
    _community_staff_repository: Optional[CommunityStaffRepository] = None
    _share_link_repository: Optional[ShareLinkRepository] = None
    _share_link_access_log_repository: Optional[ShareLinkAccessLogRepository] = None
    _supervision_relation_repository: Optional[SupervisionRelationRepository] = None
    _community_checkin_rule_repository: Optional[CommunityCheckinRuleRepository] = None
    _user_community_rule_repository: Optional[UserCommunityRuleRepository] = None
    _user_daily_abnormality_repository: Optional[UserDailyAbnormalityRepository] = None
    _profile_view_log_repository: Optional[ProfileViewLogRepository] = None
    _counters_repository: Optional[CountersRepository] = None
    _verification_code_repository: Optional[VerificationCodeRepository] = None
    _community_dashboard_repository: Optional[CommunityDashboardRepository] = None

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
    def get_share_link_repository(cls) -> ShareLinkRepository:
        """
        获取分享链接仓储实例

        Returns:
            ShareLinkRepository: 分享链接仓储实例
        """
        if cls._share_link_repository is None:
            cls._share_link_repository = SQLAlchemyShareLinkRepository()
        return cls._share_link_repository

    @classmethod
    def get_share_link_access_log_repository(cls) -> ShareLinkAccessLogRepository:
        """
        获取分享链接访问日志仓储实例

        Returns:
            ShareLinkAccessLogRepository: 分享链接访问日志仓储实例
        """
        if cls._share_link_access_log_repository is None:
            cls._share_link_access_log_repository = SQLAlchemyShareLinkAccessLogRepository()
        return cls._share_link_access_log_repository

    @classmethod
    def get_supervision_relation_repository(cls) -> SupervisionRelationRepository:
        """
        获取监督关系仓储实例

        Returns:
            SupervisionRelationRepository: 监督关系仓储实例
        """
        if cls._supervision_relation_repository is None:
            cls._supervision_relation_repository = SQLAlchemySupervisionRelationRepository()
        return cls._supervision_relation_repository

    @classmethod
    def get_community_checkin_rule_repository(cls) -> CommunityCheckinRuleRepository:
        """
        获取社区打卡规则仓储实例

        Returns:
            CommunityCheckinRuleRepository: 社区打卡规则仓储实例
        """
        if cls._community_checkin_rule_repository is None:
            cls._community_checkin_rule_repository = SQLAlchemyCommunityCheckinRuleRepository()
        return cls._community_checkin_rule_repository

    @classmethod
    def get_user_community_rule_repository(cls) -> UserCommunityRuleRepository:
        """
        获取用户社区规则仓储实例

        Returns:
            UserCommunityRuleRepository: 用户社区规则仓储实例
        """
        if cls._user_community_rule_repository is None:
            cls._user_community_rule_repository = SQLAlchemyUserCommunityRuleRepository()
        return cls._user_community_rule_repository

    @classmethod
    def get_user_daily_abnormality_repository(cls) -> UserDailyAbnormalityRepository:
        """
        获取用户每日异常仓储实例

        Returns:
            UserDailyAbnormalityRepository: 用户每日异常仓储实例
        """
        if cls._user_daily_abnormality_repository is None:
            cls._user_daily_abnormality_repository = SQLAlchemyUserDailyAbnormalityRepository()
        return cls._user_daily_abnormality_repository

    @classmethod
    def get_profile_view_log_repository(cls) -> ProfileViewLogRepository:
        """
        获取个人资料查看日志仓储实例

        Returns:
            ProfileViewLogRepository: 个人资料查看日志仓储实例
        """
        if cls._profile_view_log_repository is None:
            cls._profile_view_log_repository = SQLAlchemyProfileViewLogRepository()
        return cls._profile_view_log_repository

    @classmethod
    def get_counters_repository(cls) -> CountersRepository:
        """
        获取计数器仓储实例

        Returns:
            CountersRepository: 计数器仓储实例
        """
        if cls._counters_repository is None:
            cls._counters_repository = SQLAlchemyCountersRepository()
        return cls._counters_repository

    @classmethod
    def get_verification_code_repository(cls) -> VerificationCodeRepository:
        """
        获取验证码仓储实例

        Returns:
            VerificationCodeRepository: 验证码仓储实例
        """
        if cls._verification_code_repository is None:
            cls._verification_code_repository = SQLAlchemyVerificationCodeRepository()
        return cls._verification_code_repository

    @classmethod
    def get_community_dashboard_repository(cls) -> CommunityDashboardRepository:
        """
        获取社区仪表板仓储实例

        Returns:
            CommunityDashboardRepository: 社区仪表板仓储实例
        """
        if cls._community_dashboard_repository is None:
            cls._community_dashboard_repository = SQLAlchemyCommunityDashboardRepository()
        return cls._community_dashboard_repository

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
        cls._share_link_repository = None
        cls._share_link_access_log_repository = None
        cls._supervision_relation_repository = None
        cls._community_checkin_rule_repository = None
        cls._user_community_rule_repository = None
        cls._user_daily_abnormality_repository = None
        cls._profile_view_log_repository = None
        cls._counters_repository = None
        cls._verification_code_repository = None
        cls._community_dashboard_repository = None