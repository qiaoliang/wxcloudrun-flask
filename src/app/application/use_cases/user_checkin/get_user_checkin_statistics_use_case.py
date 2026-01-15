"""
获取用户打卡统计信息用例
"""
from flask import has_app_context
import logging

app_logger = logging.getLogger('log')


def _get_logger():
    """获取logger，避免在模块级别访问current_app"""
    if has_app_context():
        from flask import current_app
        return current_app.logger
    return app_logger
from datetime import datetime, date, timedelta
from sqlalchemy import select, func
from database.flask_models import db, CheckinRule, CheckinRecord
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserCheckinStatisticsUseCase(BaseUseCase):
    """获取用户打卡统计信息用例"""

    def _validate(self, user_id: int, period: str = 'week',
                  start_date: str = None, end_date: str = None) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            period: 统计周期（week/month）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        if period not in ['week', 'month']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='统计周期无效，必须是 week 或 month'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, period: str = 'week',
                 start_date: str = None, end_date: str = None) -> UseCaseResult:
        """
        执行获取用户打卡统计信息操作

        Args:
            user_id: 用户ID
            period: 统计周期（week/month）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            UseCaseResult: 执行结果
        """
        # 解析日期范围
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = date.today()

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            if period == 'week':
                end_date = start_date + timedelta(days=6)
            else:  # month
                # 计算到月底
                if start_date.month == 12:
                    end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)

        # 计算总天数
        total_days = (end_date - start_date).days + 1

        # 获取用户的打卡规则
        checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
        personal_rules = checkin_rule_repo.find_active_by_user_id(user_id)
        total_rules = len(personal_rules)

        # 获取用户信息
        user_repo = RepositoryFactory.get_user_repository()
        user = user_repo.find_by_id(user_id)
        if user and user.community_id:
            community_checkin_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
            user_community_rule_repo = RepositoryFactory.get_user_community_rule_repository()

            active_mappings = user_community_rule_repo.find_by_user_id(user_id, include_inactive=False)
            active_rule_ids = [m.community_rule_id for m in active_mappings if m.is_active]

            if active_rule_ids:
                community_rules = community_checkin_rule_repo.find_by_community_id_and_status(
                    user.community_id, 1
                )
                community_rules = [r for r in community_rules if r.community_rule_id in active_rule_ids]
                total_rules += len(community_rules)

        # 统计打卡记录
        stmt = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id,
            func.date(CheckinRecord.planned_time) >= start_date,
            func.date(CheckinRecord.planned_time) <= end_date
        )
        records = list(db.session.execute(stmt).scalars().all())

        completed_checkins = len([r for r in records if r.status == 1])
        missed_checkins = len([r for r in records if r.status == 0])

        # 计算打卡天数
        checkin_dates = set()
        for record in records:
            if record.status == 1 and record.checkin_time:
                checkin_dates.add(record.checkin_time.date())

        checkin_days = len(checkin_dates)
        checkin_rate = round((checkin_days / total_days * 100), 1) if total_days > 0 else 0

        # 生成每日统计
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_records = [r for r in records if r.planned_time.date() == current_date]
            day_completed = len([r for r in day_records if r.status == 1])
            day_missed = len([r for r in day_records if r.status == 0])

            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total_rules': total_rules,
                'completed_rules': day_completed,
                'missed_rules': day_missed,
                'checkin_rate': round((day_completed / total_rules * 100), 1) if total_rules > 0 else 0
            })

            current_date += timedelta(days=1)

        stats = {
            'period': period,
            'total_days': total_days,
            'checkin_days': checkin_days,
            'checkin_rate': checkin_rate,
            'total_rules': total_rules,
            'completed_checkins': completed_checkins,
            'missed_checkins': missed_checkins,
            'daily_stats': daily_stats
        }

        _get_logger().info(f'成功获取用户 {user_id} 的打卡统计信息')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取统计信息成功',
            data=stats
        )