"""
用户聚合根

用户聚合是用户相关的核心业务概念，包含用户本身及其关联的打卡规则、打卡记录等。
"""
from typing import List, Optional
from datetime import datetime

from app.domain.entities.user_entity import UserEntity
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.domain.entities.checkin_record_entity import CheckinRecordEntity
from app.domain.value_objects.role import Role
from app.domain.events.user_events import (
    UserProfileUpdatedEvent,
    UserPasswordChangedEvent,
    UserAvatarUpdatedEvent,
    UserStatusChangedEvent,
    UserRoleChangedEvent
)


class UserAggregate:
    """
    用户聚合根

    聚合边界：
    - UserEntity（用户实体）
    - CheckinRuleEntity（用户的打卡规则）
    - CheckinRecordEntity（用户的打卡记录）

    业务不变性：
    - 用户必须至少有一个有效的联系方式（手机号或微信）
    - 用户只能属于一个社区
    - 用户的打卡规则必须符合其角色权限
    """

    def __init__(self, user_entity: UserEntity):
        """
        初始化用户聚合根

        Args:
            user_entity: 用户实体
        """
        self._user = user_entity
        self._checkin_rules: List[CheckinRuleEntity] = []
        self._checkin_records: List[CheckinRecordEntity] = []
        self._domain_events: List = []  # 存储领域事件

    @property
    def user(self) -> UserEntity:
        """获取用户实体"""
        return self._user

    @property
    def checkin_rules(self) -> List[CheckinRuleEntity]:
        """获取用户的打卡规则列表"""
        return self._checkin_rules

    @property
    def checkin_records(self) -> List[CheckinRecordEntity]:
        """获取用户的打卡记录列表"""
        return self._checkin_records

    @property
    def domain_events(self) -> List:
        """获取领域事件列表"""
        return self._domain_events

    def clear_domain_events(self) -> None:
        """清除领域事件列表"""
        self._domain_events.clear()

    def _add_domain_event(self, event) -> None:
        """
        添加领域事件

        Args:
            event: 领域事件
        """
        self._domain_events.append(event)

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
        updated_fields = {}

        if nickname is not None:
            old_nickname = self._user.user.nickname
            self._user.update_profile(nickname=nickname)
            if old_nickname != self._user.user.nickname:
                updated_fields['nickname'] = {'old': old_nickname, 'new': self._user.user.nickname}

        if avatar_url is not None:
            old_avatar = self._user.user.avatar_url
            self._user.update_profile(avatar_url=avatar_url)
            if old_avatar != self._user.user.avatar_url:
                updated_fields['avatar_url'] = {'old': old_avatar, 'new': self._user.user.avatar_url}

        if name is not None:
            old_name = self._user.user.name
            self._user.update_profile(name=name)
            if old_name != self._user.user.name:
                updated_fields['name'] = {'old': old_name, 'new': self._user.user.name}

        if address is not None:
            old_address = self._user.user.address
            self._user.update_profile(address=address)
            if old_address != self._user.user.address:
                updated_fields['address'] = {'old': old_address, 'new': self._user.user.address}

        if motto is not None:
            old_motto = self._user.user.motto
            self._user.update_profile(motto=motto)
            if old_motto != self._user.user.motto:
                updated_fields['motto'] = {'old': old_motto, 'new': self._user.user.motto}

        # 如果有字段更新，发布领域事件
        if updated_fields:
            self._add_domain_event(UserProfileUpdatedEvent(
                user_id=self._user.user.user_id,
                updated_fields=updated_fields
            ))

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否修改成功

        Raises:
            ValueError: 如果旧密码不正确
        """
        if not self._user.verify_password(old_password):
            raise ValueError("旧密码不正确")

        self._user.set_password(new_password)
        self._add_domain_event(UserPasswordChangedEvent(
            user_id=self._user.user.user_id
        ))
        return True

    def update_avatar(self, avatar_url: str) -> None:
        """
        更新头像

        Args:
            avatar_url: 新头像URL
        """
        old_avatar = self._user.user.avatar_url
        self._user.update_profile(avatar_url=avatar_url)

        if old_avatar != self._user.user.avatar_url:
            self._add_domain_event(UserAvatarUpdatedEvent(
                user_id=self._user.user.user_id,
                avatar_url=self._user.user.avatar_url
            ))

    def change_status(self, new_status: int) -> None:
        """
        修改用户状态

        Args:
            new_status: 新状态
        """
        old_status = self._user.user.status
        if new_status == 1:
            self._user.activate()
        else:
            self._user.deactivate()

        if old_status != self._user.user.status:
            self._add_domain_event(UserStatusChangedEvent(
                user_id=self._user.user.user_id,
                old_status=old_status,
                new_status=self._user.user.status
            ))

    def change_role(self, new_role: int) -> None:
        """
        修改用户角色

        Args:
            new_role: 新角色
        """
        old_role = self._user.user.role
        self._user.user.role = new_role

        if old_role != self._user.user.role:
            self._add_domain_event(UserRoleChangedEvent(
                user_id=self._user.user.user_id,
                old_role=old_role,
                new_role=self._user.user.role
            ))

    def add_checkin_rule(self, rule: CheckinRuleEntity) -> None:
        """
        添加打卡规则

        Args:
            rule: 打卡规则实体

        Raises:
            ValueError: 如果用户没有权限创建规则
        """
        # 检查用户权限
        if not self._user.is_staff():
            raise ValueError("用户没有权限创建打卡规则")

        # 添加规则
        self._checkin_rules.append(rule)

    def remove_checkin_rule(self, rule_id: int) -> bool:
        """
        移除打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            是否移除成功
        """
        for i, rule in enumerate(self._checkin_rules):
            if rule.rule_id == rule_id:
                self._checkin_rules.pop(i)
                return True
        return False

    def add_checkin_record(self, record: CheckinRecordEntity) -> None:
        """
        添加打卡记录

        Args:
            record: 打卡记录实体
        """
        self._checkin_records.append(record)

    def get_active_rules(self) -> List[CheckinRuleEntity]:
        """
        获取当前启用的打卡规则

        Returns:
            启用的打卡规则列表
        """
        return [rule for rule in self._checkin_rules if rule.is_enabled()]

    def get_today_checkin_records(self, date: datetime) -> List[CheckinRecordEntity]:
        """
        获取指定日期的打卡记录

        Args:
            date: 日期

        Returns:
            打卡记录列表
        """
        return [
            record for record in self._checkin_records
            if record.checkin_date.date() == date.date()
        ]

    def can_join_community(self, community_id: int) -> bool:
        """
        检查用户是否可以加入社区

        Args:
            community_id: 社区ID

        Returns:
            是否可以加入
        """
        # 用户不能同时属于多个社区
        if self._user.community_id is not None and self._user.community_id != community_id:
            return False

        # 普通用户可以加入社区
        return self._user.role.value.value in [1, 2, 3]  # SOLO, STAFF, MANAGER

    def join_community(self, community_id: int) -> None:
        """
        加入社区

        Args:
            community_id: 社区ID

        Raises:
            ValueError: 如果用户不能加入社区
        """
        if not self.can_join_community(community_id):
            raise ValueError("用户不能加入该社区")

        self._user.join_community(community_id)

    def leave_community(self) -> None:
        """
        离开社区
        """
        self._user.leave_community()

    def __eq__(self, other) -> bool:
        if not isinstance(other, UserAggregate):
            return False
        return self._user == other._user

    def __hash__(self) -> int:
        return hash(self._user)