"""
领域聚合根

聚合根是领域模型的核心，它是访问聚合内其他对象的唯一入口。
每个聚合都有自己的边界，确保了业务不变性和一致性。
"""
from .community_aggregate import CommunityAggregate
from .user_aggregate import UserAggregate
from .checkin_rule_aggregate import CheckinRuleAggregate
from .community_event_aggregate import CommunityEventAggregate

__all__ = [
    'CommunityAggregate',
    'UserAggregate',
    'CheckinRuleAggregate',
    'CommunityEventAggregate',
]