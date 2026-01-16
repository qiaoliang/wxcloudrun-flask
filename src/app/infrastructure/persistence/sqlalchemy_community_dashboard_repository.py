"""
社区仪表板仓储 SQLAlchemy 实现
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from database.flask_models import (
    db, User, Community, CommunityCheckinRule, CheckinRecord,
    UserDailyAbnormality, CommunityEvent, UserCommunityRule
)
from app.shared.constants.roles import Role
from app.domain.repositories.community_dashboard_repository import CommunityDashboardRepository


class SQLAlchemyCommunityDashboardRepository(CommunityDashboardRepository):
    """社区仪表板仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def has_permission(self, user_id: int, community_id: int) -> bool:
        """检查用户是否有权限访问社区数据看板"""
        # 获取用户
        stmt = select(User).where(User.user_id == user_id)
        user = self.session.execute(stmt).scalar_one_or_none()

        if not user:
            return False

        # 超级管理员可以访问所有社区
        if user.role == Role.SUPER_ADMIN:
            return True

        # 社区主管和专员只能访问自己所属的社区
        if user.community_id == community_id and user.role in [Role.MANAGER, Role.STAFF]:
            return True

        return False

    def get_community_stats(self, community_id: int) -> Dict:
        """获取社区统计数据"""
        # 获取用户总数
        user_count_stmt = select(func.count(User.user_id)).where(
            and_(
                User.community_id == community_id,
                User.status == 1  # 正常状态
            )
        )
        total_users = self.session.execute(user_count_stmt).scalar() or 0

        # 获取启用的规则总数
        rule_count_stmt = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        total_rules = self.session.execute(rule_count_stmt).scalar() or 0

        # 计算今日打卡率
        today = date.today()

        if total_rules == 0 or total_users == 0:
            today_checkin_rate = 0.0
            unchecked_count = 0
        else:
            # 应打卡总数 = 用户数 × 规则数
            expected_checkins = total_users * total_rules

            # 实际打卡总数
            checkin_stmt = select(func.count(CheckinRecord.record_id)).join(
                CommunityCheckinRule,
                CheckinRecord.community_rule_id == CommunityCheckinRule.community_rule_id
            ).where(
                and_(
                    CommunityCheckinRule.community_id == community_id,
                    func.date(CheckinRecord.checkin_time) == today
                )
            )
            actual_checkins = self.session.execute(checkin_stmt).scalar() or 0

            today_checkin_rate = round((actual_checkins / expected_checkins * 100), 1) if expected_checkins > 0 else 0.0

            # 未打卡人数计算
            completed_users_stmt = select(CheckinRecord.user_id).join(
                CommunityCheckinRule,
                CheckinRecord.community_rule_id == CommunityCheckinRule.community_rule_id
            ).where(
                and_(
                    CommunityCheckinRule.community_id == community_id,
                    func.date(CheckinRecord.checkin_time) == today
                )
            ).group_by(CheckinRecord.user_id).having(
                func.count(CheckinRecord.record_id) >= total_rules
            )

            completed_count = self.session.execute(
                select(func.count()).select_from(completed_users_stmt)
            ).scalar() or 0

            unchecked_count = total_users - completed_count

        return {
            'total_users': total_users,
            'today_checkin_rate': today_checkin_rate,
            'unchecked_count': unchecked_count,
            'total_rules': total_rules
        }

    def get_abnormal_users(
        self,
        community_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """获取异常用户列表"""
        today = date.today()

        # 获取社区的规则总数
        rule_count_stmt = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        rule_count = self.session.execute(rule_count_stmt).scalar() or 0

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

        # 查询异常用户
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
        total = self.session.execute(total_stmt).scalar() or 0

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

        results = self.session.execute(stmt).unique().all()

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

            rule_abnormalities = self.session.execute(rule_abnormalities_stmt).all()

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

    def get_trend_data(self, community_id: int, days: int = 7) -> Dict:
        """获取历史趋势数据"""
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
        total_rules = self.session.execute(rule_count_stmt).scalar() or 0

        user_count_stmt = select(func.count(User.user_id)).where(
            and_(
                User.community_id == community_id,
                User.status == 1
            )
        )
        total_users = self.session.execute(user_count_stmt).scalar() or 0

        for target_date in date_range:
            date_obj = datetime.fromisoformat(target_date).date()

            if total_rules == 0 or total_users == 0:
                checkin_rates.append(0.0)
            else:
                expected_checkins = total_users * total_rules

                checkin_stmt = select(func.count(CheckinRecord.record_id)).join(
                    CommunityCheckinRule,
                    CheckinRecord.community_rule_id == CommunityCheckinRule.community_rule_id
                ).where(
                    and_(
                        CommunityCheckinRule.community_id == community_id,
                        func.date(CheckinRecord.checkin_time) == date_obj
                    )
                )
                actual_checkins = self.session.execute(checkin_stmt).scalar() or 0

                rate = round((actual_checkins / expected_checkins * 100), 1) if expected_checkins > 0 else 0.0
                checkin_rates.append(rate)

        # 获取各规则逾期情况
        rule_missed_stmt = select(
            CommunityCheckinRule.community_rule_id,
            CommunityCheckinRule.rule_name,
            CommunityCheckinRule.icon_url,
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
            CommunityCheckinRule.icon_url
        ).order_by(
            desc('missed_count')
        )

        rule_missed_results = self.session.execute(rule_missed_stmt).all()

        rule_missed_stats = []
        for row in rule_missed_results:
            rule_missed_stats.append({
                'rule_id': row.community_rule_id,
                'rule_name': row.rule_name,
                'rule_icon': row.icon_url or '📋',
                'missed_count': row.missed_count
            })

        return {
            'date_range': date_range,
            'checkin_rates': checkin_rates,
            'rule_missed_stats': rule_missed_stats
        }

    def get_pending_events(self, community_id: int, limit: int = 3) -> List[Dict]:
        """获取未处理的事件列表"""
        # 只返回未处理事件（status=1）
        stmt = select(CommunityEvent).where(
            and_(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1  # pending
            )
        ).order_by(
            desc(CommunityEvent.created_at)
        ).limit(limit)

        events = self.session.execute(stmt).scalars().all()

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

        return event_list

    def get_user_abnormality_detail(
        self,
        community_id: int,
        user_id: int
    ) -> Dict:
        """获取用户的异常值详情"""
        today = date.today()

        # 获取用户的所有规则异常值
        stmt = select(
            CommunityCheckinRule.rule_name,
            UserDailyAbnormality.total_abnormality,
            UserDailyAbnormality.last_checkin_time,
            UserDailyAbnormality.last_scheduled_time,
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

        results = self.session.execute(stmt).all()

        rule_details = []
        total_abnormality = 0

        for row in results:
            rule_details.append({
                'rule_name': row.rule_name,
                'scheduled_time': row.last_scheduled_time.strftime('%H:%M') if row.last_scheduled_time else None,
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
