"""
获取用户今日打卡计划用例
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
from datetime import datetime, date, time
from sqlalchemy import select, func
from sqlalchemy.orm import noload
from database.flask_models import db, CheckinRule, CommunityCheckinRule, UserCommunityRule, CheckinRecord
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserTodayPlanUseCase(BaseUseCase):
    """获取用户今日打卡计划用例"""

    def _validate(self, user_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取用户今日打卡计划操作

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        today_plan = []
        today = date.today()

        # 获取个人规则的今日计划
        checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
        personal_rules = checkin_rule_repo.find_active_by_user_id(user_id)

        for rule in personal_rules:
            # 判断今天是否需要打卡
            if not self._should_checkin_today(rule, today):
                continue

            # 查询今天该规则的打卡记录
            today_records = self._query_today_records(rule.rule_id, today, 'personal')

            # 计算计划打卡时间
            planned_time = self._calculate_planned_time(rule, today)

            # 确定打卡状态
            status_info = self._determine_checkin_status(today_records)

            today_plan.append({
                'rule_id': rule.rule_id,
                'record_id': status_info['record_id'],
                'rule_name': rule.rule_name,
                'icon_url': rule.icon_url,
                'planned_time': planned_time.strftime('%H:%M:%S') if planned_time else None,
                'status': status_info['status'],
                'checkin_time': status_info['checkin_time'],
                'rule_source': 'personal',
                'is_editable': True,
                'time_slot_type': rule.time_slot_type
            })

        # 获取激活的社区规则的今日计划
        user_repo = RepositoryFactory.get_user_repository()
        user = user_repo.find_by_id(user_id)
        if user and user.community_id:
            user_community_rule_repo = RepositoryFactory.get_user_community_rule_repository()
            active_mappings = user_community_rule_repo.find_by_user_id(user_id, include_inactive=False)
            active_rule_ids = [m.community_rule_id for m in active_mappings if m.is_active]

            if active_rule_ids:
                community_checkin_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
                community_rules = community_checkin_rule_repo.find_by_community_id_and_status(
                    user.community_id, 1  # 1=启用
                )

                for rule in community_rules:
                    if rule.community_rule_id not in active_rule_ids:
                        continue

                    # 检查今天是否需要打卡
                    if not self._should_checkin_today(rule, today):
                        continue

                    # 获取今日打卡记录
                    today_records = self._query_today_records(rule.community_rule_id, today, 'community')

                    # 计算计划时间
                    planned_time = self._calculate_planned_time(rule, today)

                    # 确定打卡状态
                    status_info = self._determine_checkin_status(today_records)

                    plan_item = {
                        'rule_id': rule.community_rule_id,
                        'rule_name': rule.rule_name,
                        'icon_url': rule.icon_url,
                        'planned_time': planned_time.isoformat() if planned_time else None,
                        'status': status_info['status'],
                        'checkin_time': status_info['checkin_time'],
                        'rule_source': 'community',
                        'is_editable': False,
                        'community_name': rule.community.name if rule.community else None,
                        'time_slot_type': rule.time_slot_type
                    }

                    today_plan.append(plan_item)

        # 按计划时间排序
        today_plan.sort(key=lambda x: x['planned_time'] or '')

        result = {
            'date': today.strftime('%Y-%m-%d'),
            'total_items': len(today_plan),
            'completed_items': len([item for item in today_plan if item.get('status') == 'checked']),
            'pending_items': len([item for item in today_plan if item.get('status') != 'checked']),
            'items': today_plan
        }

        _get_logger().info(f'成功获取用户 {user_id} 的今日打卡计划，共 {result["total_items"]} 项')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取今日计划成功',
            data=result
        )

    def _should_checkin_today(self, rule, today: date) -> bool:
        """判断今天是否需要打卡"""
        frequency_type = rule.frequency_type
        week_days = rule.week_days
        custom_start_date = rule.custom_start_date
        custom_end_date = rule.custom_end_date

        if frequency_type == 1:  # 每周
            today_weekday = today.weekday()  # 0是周一，6是周日
            return bool(week_days & (1 << today_weekday))
        elif frequency_type == 2:  # 工作日
            return today.weekday() < 5  # 周一到周五
        elif frequency_type == 3:  # 自定义日期范围
            if custom_start_date and custom_end_date:
                return custom_start_date <= today <= custom_end_date
            return False
        else:  # 每天 (frequency_type == 0)
            return True

    def _query_today_records(self, rule_id: int, today: date, rule_source: str = 'personal'):
        """查询今天该规则的打卡记录"""
        stmt = select(CheckinRecord).options(
            noload(CheckinRecord.user),
            noload(CheckinRecord.solo_user),
            noload(CheckinRecord.rule)
        ).where(func.date(CheckinRecord.planned_time) == today)

        if rule_source == 'community':
            stmt = stmt.where(CheckinRecord.community_rule_id == rule_id)
        else:
            stmt = stmt.where(CheckinRecord.rule_id == rule_id)

        return list(db.session.execute(stmt).scalars().all())

    def _calculate_planned_time(self, rule, today: date) -> datetime:
        """计算计划打卡时间"""
        time_slot_type = rule.time_slot_type
        custom_time = rule.custom_time

        if time_slot_type == 5:  # 全天有效
            return datetime.combine(today, time(0, 0))
        elif time_slot_type == 4 and custom_time:  # 自定义时间
            if isinstance(custom_time, str):
                from wxcloudrun.utils.timeutil import parse_time_only
                try:
                    custom_time = parse_time_only(custom_time)
                except ValueError:
                    return datetime.combine(today, time(20, 0))

            if not isinstance(custom_time, time):
                return datetime.combine(today, time(20, 0))

            return datetime.combine(today, custom_time)
        elif time_slot_type == 1:  # 上午
            return datetime.combine(today, time(9, 0))
        elif time_slot_type == 2:  # 下午
            return datetime.combine(today, time(14, 0))
        else:  # 晚上
            return datetime.combine(today, time(20, 0))

    def _determine_checkin_status(self, today_records):
        """确定打卡状态"""
        status_info = {
            'status': 'pending',
            'checkin_time': None,
            'record_id': None
        }

        for record in today_records:
            if record.status == 1:  # 已打卡
                status_info['status'] = 'checked'
                status_info['checkin_time'] = record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else None
                status_info['record_id'] = record.record_id
                break
            elif record.status == 2:  # 已撤销
                status_info['status'] = 'unchecked'
                status_info['checkin_time'] = None
                status_info['record_id'] = record.record_id
                break

        return status_info