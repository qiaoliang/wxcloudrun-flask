"""
SQLAlchemy 用户仓储实现

使用 SQLAlchemy 实现用户仓储接口。
"""
from typing import List, Optional

from sqlalchemy import select, or_

from app.domain.repositories.user_repository import UserRepository
from database.flask_models import db, User


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy 用户仓储实现"""

    def save(self, entity: User) -> User:
        """
        保存用户

        Args:
            entity: 要保存的用户

        Returns:
            User: 保存后的用户
        """
        db.session.add(entity)
        db.session.flush()
        db.session.commit()
        return entity

    def delete(self, entity: User) -> None:
        """
        删除用户

        Args:
            entity: 要删除的用户
        """
        db.session.delete(entity)

    def find_by_id(self, entity_id: int) -> Optional[User]:
        """
        根据ID查找用户

        Args:
            entity_id: 用户ID

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        return db.session.get(User, entity_id)

    def find_all(self) -> List[User]:
        """
        查找所有用户

        Returns:
            List[User]: 用户列表
        """
        stmt = select(User)
        return db.session.execute(stmt).scalars().all()

    def exists(self, entity_id: int) -> bool:
        """
        检查用户是否存在

        Args:
            entity_id: 用户ID

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        return self.find_by_id(entity_id) is not None

    def find_by_openid(self, openid: str) -> Optional[User]:
        """
        根据微信openid查找用户

        Args:
            openid: 微信openid

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        stmt = select(User).options(
            db.joinedload(User.community)
        ).where(User.wechat_openid == openid)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_phone_hash(self, phone_hash: str) -> Optional[User]:
        """
        根据手机号哈希查找用户

        Args:
            phone_hash: 手机号哈希

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        stmt = select(User).options(
            db.joinedload(User.community)
        ).where(User.phone_hash == phone_hash)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_refresh_token(self, refresh_token: str) -> Optional[User]:
        """
        根据refresh token查找用户

        Args:
            refresh_token: 刷新令牌

        Returns:
            Optional[User]: 用户对象，如果不存在则返回 None
        """
        stmt = select(User).where(User.refresh_token == refresh_token)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_community_id(self, community_id: int) -> List[User]:
        """
        根据社区ID查找用户列表

        Args:
            community_id: 社区ID

        Returns:
            List[User]: 用户列表
        """
        stmt = select(User).where(User.community_id == community_id)
        return db.session.execute(stmt).scalars().all()

    def find_by_role(self, role: int) -> List[User]:
        """
        根据角色查找用户列表

        Args:
            role: 角色ID

        Returns:
            List[User]: 用户列表
        """
        stmt = select(User).where(User.role == role)
        return db.session.execute(stmt).scalars().all()

    def search_users(self, keyword: str, community_id: Optional[int] = None) -> List[User]:
        """
        搜索用户

        Args:
            keyword: 搜索关键词（昵称、手机号、姓名）
            community_id: 社区ID（可选）

        Returns:
            List[User]: 用户列表
        """
        stmt = select(User).where(
            or_(
                User.nickname.like(f'%{keyword}%'),
                User.phone_number.like(f'%{keyword}%'),
                User.name.like(f'%{keyword}%')
            )
        )

        if community_id:
            stmt = stmt.where(User.community_id == community_id)

        return db.session.execute(stmt).scalars().all()

    def exists_by_openid(self, openid: str) -> bool:
        """
        检查微信openid是否存在

        Args:
            openid: 微信openid

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        return self.find_by_openid(openid) is not None

    def exists_by_phone_hash(self, phone_hash: str) -> bool:
        """
        检查手机号哈希是否存在

        Args:
            phone_hash: 手机号哈希

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        return self.find_by_phone_hash(phone_hash) is not None

    def search_users_paginated(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> tuple[List[dict], int]:
        """
        分页搜索用户

        Args:
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量
            search_type: 搜索类型 (all, phone, nickname)
            exclude_blackroom: 是否排除黑名单房间

        Returns:
            tuple[List[dict], int]: (用户数据列表, 总数)
        """
        from sqlalchemy import func, and_
        from database.flask_models import Community

        # 构建查询条件
        conditions = []

        if search_type == 'phone':
            conditions.append(User.phone_number.like(f'%{keyword}%'))
        elif search_type == 'nickname':
            conditions.append(User.nickname.like(f'%{keyword}%'))
        else:  # all
            conditions.append(
                or_(
                    User.nickname.like(f'%{keyword}%'),
                    User.phone_number.like(f'%{keyword}%'),
                    User.name.like(f'%{keyword}%')
                )
            )

        # 排除黑房间
        if exclude_blackroom:
            stmt = select(Community).where(Community.is_blackhouse == True)
            blackroom_communities = db.session.execute(stmt).scalars().all()
            blackroom_ids = [c.community_id for c in blackroom_communities]
            if blackroom_ids:
                conditions.append(User.community_id.notin_(blackroom_ids))

        # 构建查询
        stmt = select(User).where(and_(*conditions))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.session.execute(count_stmt).scalar() or 0

        # 分页
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        # 执行查询
        users = db.session.execute(stmt).scalars().all()

        # 转换为字典列表
        users_data = []
        for user in users:
            users_data.append({
                'user_id': user.user_id,
                'nickname': user.nickname,
                'name': user.name,
                'phone_number': user.phone_number,
                'avatar_url': user.avatar_url,
                'community_id': user.community_id,
                'role': user.role,
                'status': user.status
            })

        return users_data, total