"""
仓储层（Repository Layer）

仓储层负责：
1. 定义数据访问接口
2. 抽象数据存储细节
3. 提供领域对象的持久化

仓储遵循依赖倒置原则，领域层定义接口，基础设施层实现。
"""

from .community_application_repository import CommunityApplicationRepository
from .audit_log_repository import AuditLogRepository
from .checkin_rule_repository import CheckinRuleRepository
from .checkin_record_repository import CheckinRecordRepository

__all__ = [
    'CommunityApplicationRepository',
    'AuditLogRepository',
    'CheckinRuleRepository',
    'CheckinRecordRepository',
]