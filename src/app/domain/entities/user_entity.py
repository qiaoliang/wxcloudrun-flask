"""
用户领域实体

封装用户相关的业务逻辑。
"""
import hashlib
import secrets
from typing import Optional

from database.flask_models import User
from app.domain.value_objects.role import Role


class UserEntity:
    """用户领域实体"""

    def __init__(self, user: User):
        """
        初始化用户领域实体

        Args:
            user: SQLAlchemy User 模型实例
        """
        self._user = user

    @property
    def user(self) -> User:
        """获取底层的 SQLAlchemy User 模型"""
        return self._user

    @property
    def role(self) -> Role:
        """获取角色值对象"""
        return Role.from_int(self._user.role)

    def set_password(self, password: str) -> None:
        """
        设置密码

        Args:
            password: 明文密码
        """
        password_salt = hashlib.md5(str(hash(secrets.token_hex(8))).encode()).hexdigest()[:32]
        salted_password = f"{password}:{password_salt}"
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()

        self._user.password_salt = password_salt
        self._user.password_hash = password_hash

    def verify_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码

        Returns:
            bool: 密码是否正确
        """
        if not self._user.password_hash or not self._user.password_salt:
            return False

        salted_password = f"{password}:{self._user.password_salt}"
        return self._user.password_hash == hashlib.sha256(salted_password.encode()).hexdigest()

    def is_admin(self) -> bool:
        """
        是否为管理员

        Returns:
            bool: 是否为管理员
        """
        return self.role.is_admin()

    def is_super_admin(self) -> bool:
        """
        是否为超级管理员

        Returns:
            bool: 是否为超级管理员
        """
        return self.role.is_super_admin()

    def is_staff(self) -> bool:
        """
        是否为工作人员

        Returns:
            bool: 是否为工作人员
        """
        return self.role.is_staff()

    def can_manage_community(self, community_id: int) -> bool:
        """
        是否可以管理指定社区

        Args:
            community_id: 社区ID

        Returns:
            bool: 是否可以管理
        """
        # 超级管理员可以管理所有社区
        if self.is_super_admin():
            return True

        # 社区主管可以管理自己的社区
        if self.role.can_manage_community() and self._user.community_id == community_id:
            return True

        return False

    def update_profile(self, nickname: Optional[str] = None, avatar_url: Optional[str] = None,
                      name: Optional[str] = None, address: Optional[str] = None,
                      motto: Optional[str] = None) -> None:
        """
        更新用户资料

        Args:
            nickname: 昵称
            avatar_url: 头像URL
            name: 真实姓名
            address: 地址
            motto: 座右铭
        """
        if nickname is not None:
            if len(nickname.strip()) > 0:
                self._user.nickname = nickname.strip()[:50]

        if avatar_url is not None:
            if avatar_url.startswith(('http://', 'https://')) and len(avatar_url) <= 500:
                self._user.avatar_url = avatar_url.strip()

        if name is not None:
            self._user.name = name[:100] if name else None

        if address is not None:
            self._user.address = address[:200] if address else None

        if motto is not None:
            self._user.motto = motto[:100] if motto else None

    def join_community(self, community_id: int) -> None:
        """
        加入社区

        Args:
            community_id: 社区ID
        """
        self._user.community_id = community_id
        self._user.community_joined_at = datetime.now()

    def leave_community(self) -> None:
        """离开社区"""
        self._user.community_id = None
        self._user.community_joined_at = None

    def is_active(self) -> bool:
        """
        用户是否活跃

        Returns:
            bool: 是否活跃
        """
        return self._user.status == 1

    def activate(self) -> None:
        """激活用户"""
        self._user.status = 1

    def deactivate(self) -> None:
        """停用用户"""
        self._user.status = 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, UserEntity):
            return False
        return self._user.user_id == other._user.user_id

    def __hash__(self) -> int:
        return hash(self._user.user_id)