"""
仓储工厂

提供仓储实例的创建和获取。
"""
from typing import Optional

from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.community_repository import CommunityRepository
from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.persistence.sqlalchemy_community_repository import SQLAlchemyCommunityRepository


class RepositoryFactory:
    """仓储工厂"""

    _user_repository: Optional[UserRepository] = None
    _community_repository: Optional[CommunityRepository] = None

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
    def reset(cls):
        """重置仓储实例（主要用于测试）"""
        cls._user_repository = None
        cls._community_repository = None