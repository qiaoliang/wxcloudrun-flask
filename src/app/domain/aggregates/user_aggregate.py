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