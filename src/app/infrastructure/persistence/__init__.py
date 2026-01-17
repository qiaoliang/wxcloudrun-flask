"""
持久化层（Persistence Layer）

持久化层负责：
1. 实现仓储接口
2. 封装数据库访问细节
3. 提供事务管理
"""

from .sqlalchemy_community_application_repository import SQLAlchemyCommunityApplicationRepository
from .sqlalchemy_audit_log_repository import SQLAlchemyAuditLogRepository

__all__ = [
    'SQLAlchemyCommunityApplicationRepository',
    'SQLAlchemyAuditLogRepository',
]