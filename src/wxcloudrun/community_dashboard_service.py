"""
社区数字看板服务模块
处理社区数据看板相关的核心业务逻辑
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from flask import current_app
from sqlalchemy import select, func, and_, or_, desc
from database.flask_models import (
    db, User, Community, CommunityCheckinRule, CheckinRecord,
    UserDailyAbnormality, CommunityEvent, UserCommunityRule
)
from app.shared.utils.abnormality_calculator import AbnormalityCalculator
from app.shared.utils.transaction import transactional

logger = logging.getLogger('CommunityDashboardService')


class CommunityDashboardService:
    """社区数字看板服务类"""

    @staticmethod
    def has_permission(user_id: int, community_id: int) -> bool:
        """
        检查用户是否有权限访问社区数据看板

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            是否有权限
        """
        # 获取用户
        stmt = select(User).where(User.user_id == user_id)
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user:
            return False

        # 超级管理员可以访问所有社区
        from app.shared.constants.roles import Role
        if user.role == Role.SUPER_ADMIN:
            return True

        # 社区主管和专员只能访问自己所属的社区
        if user.community_id == community_id and user.role in [Role.MANAGER, Role.STAFF]:
            return True

        return False

    @staticmethod
    def get_community_stats(community_id: int) -> Dict:
        """
        获取社区统计数据

        Args:
            community_id: 社区ID

        Returns:
            统计数据字典
        """
        # 获取用户总数
        user_count_stmt = select(func.count(User.user_id)).where(
            and_(
                User.community_id == community_id,
                User.status == 1  # 正常状态
            )
        )
        total_users = db.session.execute(user_count_stmt).scalar() or 0

        # 获取启用的规则总数
        rule_count_stmt = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        total_rules = db.session.execute(rule_count_stmt).scalar() or 0

        # 计算今日打卡率
        today = date.today()

        if total_rules == 0 or total_users == 0:
            today_checkin_rate = 0.0
            unchecked_count = 0
        else:
            # 应打卡总数 = 用户数 × 规则数
            expected_checkins = total_users * total_rules

            # 实际打卡总数
            checkin_stmt = select(func.count(CheckinRecord.record_id)).where(
                and_(
                    CheckinRecord.community_id == community_id,
                    func.date(CheckinRecord.checkin_time) == today
                )
            )
            actual_checkins = db.session.execute(checkin_stmt).scalar() or 0

            today_checkin_rate = round((actual_checkins / expected_checkins * 100), 1) if expected_checkins > 0 else 0.0

            # 未打卡人数 = 至少有一个规则未打卡的用户数
            # 使用子查询找出已完成所有规则打卡的用户
            completed_users_stmt = select(CheckinRecord.user_id).where(
                and_(
                    CheckinRecord.community_id == community_id,
                    func.date(CheckinRecord.checkin_time) == today
                )
            ).group_by(CheckinRecord.user_id).having(
                func.count(CheckinRecord.record_id) >= total_rules
            )

            completed_count = db.session.execute(
                select(func.count()).select_from(completed_users_stmt)
            ).scalar() or 0

            unchecked_count = total_users - completed_count

        return {
            'total_users': total_users,
            'today_checkin_rate': today_checkin_rate,
            'unchecked_count': unchecked_count,
            'total_rules': total_rules
        }

    @staticmethod
    def get_abnormal_users(
        community_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取异常用户列表

        Args:
            community_id: 社区ID
            page: 页码
            page_size: 每页数量

        Returns:
            异常用户列表字典
        """
        today = date.today()

        # 获取社区的规则总数
        rule_count_stmt = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        rule_count = db.session.execute(rule_count_stmt).scalar() or 0

        if rule_count == 0:
            return {
                'users': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'has_next': False
            }

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询异常用户（总异常值 >= 规则数）
        # 使用子查询计算每个用户的总异常值
        user_abnormality_stmt = select(
            UserDailyAbnormality.user_id,
            func.sum(UserDailyAbnormality.total_abnormality).label('total_abnormality')
        ).where(
            and_(
                UserDailyAbnormality.date == today,
                UserDailyAbnormality.is_completed == False
            )
        ).group_by(
            UserDailyAbnormality.user_id
        ).having(
            func.sum(UserDailyAbnormality.total_abnormality) >= rule_count
        )

        # 获取总数
        total_stmt = select(func.count()).select_from(user_abnormality_stmt)
        total = db.session.execute(total_stmt).scalar() or 0

        # 获取分页数据
        abnormality_subquery = user_abnormality_stmt.add_columns(
            func.row_number().over(
                order_by=desc(func.sum(UserDailyAbnormality.total_abnormality))
            ).label('rn')
        ).subquery()

        # 关联用户信息
        stmt = select(
            User.user_id,
            User.nickname,
            User.avatar_url,
            abnormality_subquery.c.total_abnormality
        ).join(
            abnormality_subquery, User.user_id == abnormality_subquery.c.user_id
        ).join(
            UserDailyAbnormality, User.user_id == UserDailyAbnormality.user_id
        ).where(
            and_(
                User.community_id == community_id,
                User.status == 1,
                UserDailyAbnormality.date == today,
                UserDailyAbnormality.is_completed == False
            )
        ).group_by(
            User.user_id, User.nickname, User.avatar_url, abnormality_subquery.c.total_abnormality
        ).order_by(
            desc(abnormality_subquery.c.total_abnormality)
        ).limit(page_size).offset(offset)

        results = db.session.execute(stmt).unique().all()

        users = []
        for row in results:
            # 获取该用户每个未完成规则的异常值详情
            rule_abnormalities_stmt = select(
                CommunityCheckinRule.rule_name,
                UserDailyAbnormality.total_abnormality
            ).join(
                UserDailyAbnormality,
                CommunityCheckinRule.community_rule_id == UserDailyAbnormality.rule_id
            ).where(
                and_(
                    UserDailyAbnormality.user_id == row.user_id,
                    UserDailyAbnormality.date == today,
                    UserDailyAbnormality.is_completed == False
                )
            )

            rule_abnormalities = db.session.execute(rule_abnormalities_stmt).all()

            # 计算异常值等级
            total_abn = int(row.total_abnormality)
            if total_abn <= 3:
                abnormality_level = 'low'
            elif total_abn <= 6:
                abnormality_level = 'medium'
            else:
                abnormality_level = 'high'

            users.append({
                'user_id': row.user_id,
                'nickname': row.nickname or '未知用户',
                'avatar_url': row.avatar_url or '',
                'total_abnormality': total_abn,
                'unfinished_rules_count': len(rule_abnormalities),
                'rule_abnormalities': [
                    {
                        'rule_name': ra[0],
                        'abnormality': int(ra[1])
                    }
                    for ra in rule_abnormalities
                ],
                'abnormality_level': abnormality_level
            })

        return {
            'users': users,
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_next': offset + page_size < total
        }

    @staticmethod
    def get_trend_data(community_id: int, days: int = 7) -> Dict:
        """
        获取历史趋势数据

        Args:
            community_id: 社区ID
            days: 天数（7或30）

        Returns:
            趋势数据字典
        """
        if days not in [7, 30]:
            days = 7

        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        # 生成日期范围
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current.isoformat())
            current += timedelta(days=1)

        # 获取打卡率趋势
        checkin_rates = []
        rule_count_stmt = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        total_rules = db.session.execute(rule_count_stmt).scalar() or 0

        user_count_stmt = select(func.count(User.user_id)).where(
            and_(
                User.community_id == community_id,
                User.status == 1
            )
        )
        total_users = db.session.execute(user_count_stmt).scalar() or 0

        for target_date in date_range:
            date_obj = datetime.fromisoformat(target_date).date()

            if total_rules == 0 or total_users == 0:
                checkin_rates.append(0.0)
            else:
                expected_checkins = total_users * total_rules

                checkin_stmt = select(func.count(CheckinRecord.record_id)).where(
                    and_(
                        CheckinRecord.community_id == community_id,
                        func.date(CheckinRecord.checkin_time) == date_obj
                    )
                )
                actual_checkins = db.session.execute(checkin_stmt).scalar() or 0

                rate = round((actual_checkins / expected_checkins * 100), 1) if expected_checkins > 0 else 0.0
                checkin_rates.append(rate)

        # 获取各规则逾期情况
        # 统计在指定时间范围内，每个规则的逾期人次
        # 逾期 = 未打卡或打卡时间晚于计划时间
        rule_missed_stmt = select(
            CommunityCheckinRule.community_rule_id,
            CommunityCheckinRule.rule_name,
            CommunityCheckinRule.rule_icon,
            func.count().label('missed_count')
        ).outerjoin(
            UserCommunityRule,
            CommunityCheckinRule.community_rule_id == UserCommunityRule.community_rule_id
        ).outerjoin(
            CheckinRecord,
            and_(
                CheckinRecord.community_rule_id == CommunityCheckinRule.community_rule_id,
                CheckinRecord.checkin_time >= start_date,
                CheckinRecord.checkin_time < end_date + timedelta(days=1)
            )
        ).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1,
                UserCommunityRule.is_active == True
            )
        ).group_by(
            CommunityCheckinRule.community_rule_id,
            CommunityCheckinRule.rule_name,
            CommunityCheckinRule.rule_icon
        ).order_by(
            desc('missed_count')
        )

        rule_missed_results = db.session.execute(rule_missed_stmt).all()

        rule_missed_stats = []
        for row in rule_missed_results:
            rule_missed_stats.append({
                'rule_id': row.community_rule_id,
                'rule_name': row.rule_name,
                'rule_icon': row.rule_icon or '📋',
                'missed_count': row.missed_count
            })

        return {
            'date_range': date_range,
            'checkin_rates': checkin_rates,
            'rule_missed_stats': rule_missed_stats
        }

    @staticmethod
    def get_pending_events(community_id: int, limit: int = 3) -> Dict:
        """
        获取未处理的事件列表

        Args:
            community_id: 社区ID
            limit: 最大返回数量

        Returns:
            未处理事件列表字典
        """
        # 只返回未处理事件（status=1）
        stmt = select(CommunityEvent).where(
            and_(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1  # pending
            )
        ).order_by(
            desc(CommunityEvent.created_at)
        ).limit(limit)

        events = db.session.execute(stmt).scalars().all()

        event_list = []
        for event in events:
            # 计算相对时间
            created_at = event.created_at
            now = datetime.now()
            time_diff = now - created_at

            if time_diff.seconds < 60:
                relative_time = f"{time_diff.seconds}秒前"
            elif time_diff.seconds < 3600:
                relative_time = f"{time_diff.seconds // 60}分钟前"
            elif time_diff.seconds < 86400:
                relative_time = f"{time_diff.seconds // 3600}小时前"
            else:
                relative_time = f"{time_diff.days}天前"

            # 确定事件标题
            if event.event_type == 'call_for_help':
                title = '用户求助'
                description = event.event_message or '需要帮助'
            elif event.event_type == 'supporting':
                title = '用户支持'
                description = event.event_message or '需要支持'
            else:
                title = '社区事件'
                description = event.event_message or ''

            event_list.append({
                'event_id': event.event_id,
                'type': event.event_type,
                'title': title,
                'description': description,
                'created_at': created_at.isoformat() if created_at else None,
                'relative_time': relative_time
            })

        return {
            'events': event_list,
            'total': len(event_list)
        }

    @staticmethod
    def get_user_abnormality_detail(community_id: int, user_id: int) -> Dict:
        """
        获取用户的异常值详情

        Args:
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            用户异常值详情字典
        """
        today = date.today()

        # 获取用户的所有规则异常值
        stmt = select(
            CommunityCheckinRule.rule_name,
            CommunityCheckinRule.scheduled_time,
            UserDailyAbnormality.total_abnormality,
            UserDailyAbnormality.last_checkin_time,
            UserDailyAbnormality.is_completed
        ).join(
            UserDailyAbnormality,
            CommunityCheckinRule.community_rule_id == UserDailyAbnormality.rule_id
        ).where(
            and_(
                UserDailyAbnormality.user_id == user_id,
                UserDailyAbnormality.date == today
            )
        ).order_by(
            desc(UserDailyAbnormality.total_abnormality)
        )

        results = db.session.execute(stmt).all()

        rule_details = []
        total_abnormality = 0

        for row in results:
            rule_details.append({
                'rule_name': row.rule_name,
                'scheduled_time': row.scheduled_time.strftime('%H:%M') if row.scheduled_time else None,
                'abnormality': int(row.total_abnormality),
                'last_checkin_time': row.last_checkin_time.isoformat() if row.last_checkin_time else None,
                'is_completed': row.is_completed
            })

            if not row.is_completed:
                total_abnormality += row.total_abnormality

        return {
            'user_id': user_id,
            'date': today.isoformat(),
            'total_abnormality': total_abnormality,
            'rule_details': rule_details
        }
