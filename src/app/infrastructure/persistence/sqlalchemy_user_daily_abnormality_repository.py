"""
用户每日异常值仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import date, datetime, timedelta

from sqlalchemy import select, and_, func
from database.flask_models import db, UserDailyAbnormality
from app.domain.repositories.user_daily_abnormality_repository import UserDailyAbnormalityRepository


class SQLAlchemyUserDailyAbnormalityRepository(UserDailyAbnormalityRepository):
    """用户每日异常值仓储 SQLAlchemy 实现"""

    def find_by_id(self, abnormality_id: int) -> Optional[UserDailyAbnormality]:
        """
        根据ID查找异常记录

        Args:
            abnormality_id: 异常记录ID

        Returns:
            用户每日异常值对象，如果不存在则返回 None
        """
        return db.session.get(UserDailyAbnormality, abnormality_id)

    def find_by_user_id_and_date(self, user_id: int, date: date) -> List[UserDailyAbnormality]:
        """
        根据用户ID和日期查找异常记录

        Args:
            user_id: 用户ID
            date: 日期

        Returns:
            用户每日异常值列表
        """
        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.user_id == user_id,
            UserDailyAbnormality.date == date
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_user_id_and_date_range(self, user_id: int, start_date: date, end_date: date) -> List[UserDailyAbnormality]:
        """
        根据用户ID和日期范围查找异常记录

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            用户每日异常值列表
        """
        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.user_id == user_id,
            UserDailyAbnormality.date >= start_date,
            UserDailyAbnormality.date <= end_date
        ).order_by(UserDailyAbnormality.date)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_rule_id_and_date(self, rule_id: int, date: date) -> List[UserDailyAbnormality]:
        """
        根据规则ID和日期查找异常记录

        Args:
            rule_id: 规则ID
            date: 日期

        Returns:
            用户每日异常值列表
        """
        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.rule_id == rule_id,
            UserDailyAbnormality.date == date
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_user_rule_and_date(self, user_id: int, rule_id: int, date: date) -> Optional[UserDailyAbnormality]:
        """
        根据用户ID、规则ID和日期查找异常记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            date: 日期

        Returns:
            用户每日异常值对象，如果不存在则返回 None
        """
        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.user_id == user_id,
            UserDailyAbnormality.rule_id == rule_id,
            UserDailyAbnormality.date == date
        )

        result = db.session.execute(query)
        return result.scalar_one_or_none()

    def save(self, abnormality: UserDailyAbnormality) -> UserDailyAbnormality:
        """
        保存用户每日异常值

        Args:
            abnormality: 用户每日异常值对象

        Returns:
            保存后的用户每日异常值对象
        """
        db.session.add(abnormality)
        db.session.flush()
        return abnormality

    def update_abnormality(self, user_id: int, rule_id: int, date: date,
                          abnormality_delta: int, checkin_time: datetime = None,
                          scheduled_time: datetime = None, is_completed: bool = None) -> Optional[UserDailyAbnormality]:
        """
        更新用户每日异常值

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            date: 日期
            abnormality_delta: 异常值增量
            checkin_time: 打卡时间
            scheduled_time: 计划打卡时间
            is_completed: 是否已完成

        Returns:
            更新后的用户每日异常值对象，如果不存在则返回 None
        """
        abnormality = self.find_by_user_rule_and_date(user_id, rule_id, date)

        if abnormality:
            abnormality.total_abnormality += abnormality_delta
            if checkin_time:
                abnormality.last_checkin_time = checkin_time
            if scheduled_time:
                abnormality.last_scheduled_time = scheduled_time
            if is_completed is not None:
                abnormality.is_completed = is_completed
            abnormality.updated_at = datetime.now()
            db.session.flush()
            return abnormality

        return None

    def get_abnormal_users_by_date(self, community_id: int, date: date, threshold: int = 5) -> List[int]:
        """
        获取指定日期异常值超过阈值的用户ID列表

        Args:
            community_id: 社区ID
            date: 日期
            threshold: 异常值阈值

        Returns:
            用户ID列表
        """
        # 需要通过关联查询获取社区用户
        from database.flask_models import User, CommunityCheckinRule

        query = select(UserDailyAbnormality.user_id).join(
            CommunityCheckinRule, UserDailyAbnormality.rule_id == CommunityCheckinRule.community_rule_id
        ).join(
            User, UserDailyAbnormality.user_id == User.user_id
        ).where(
            CommunityCheckinRule.community_id == community_id,
            UserDailyAbnormality.date == date,
            UserDailyAbnormality.total_abnormality >= threshold,
            User.community_id == community_id
        ).distinct()

        result = db.session.execute(query)
        return [row[0] for row in result.all()]

    def get_user_abnormality_trend(self, user_id: int, days: int) -> List[dict]:
        """
        获取用户最近N天的异常值趋势

        Args:
            user_id: 用户ID
            days: 天数

        Returns:
            异常值趋势数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.user_id == user_id,
            UserDailyAbnormality.date >= start_date,
            UserDailyAbnormality.date <= end_date
        ).order_by(UserDailyAbnormality.date)

        result = db.session.execute(query)
        abnormalities = list(result.scalars().all())

        return [{
            'date': abn.date.isoformat(),
            'total_abnormality': abn.total_abnormality,
            'is_completed': abn.is_completed
        } for abn in abnormalities]

    def delete_by_user_id(self, user_id: int) -> bool:
        """
        删除用户的所有异常记录

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        query = select(UserDailyAbnormality).where(
            UserDailyAbnormality.user_id == user_id
        )

        result = db.session.execute(query)
        abnormalities = result.scalars().all()

        for abnormality in abnormalities:
            db.session.delete(abnormality)

        db.session.flush()
        return len(abnormalities) > 0