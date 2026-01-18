"""
检查缺失打卡UseCase
用于定时任务检查并标记未打卡的记录
"""
import logging
import os
from datetime import datetime, time, timedelta
from typing import Dict
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transactional, transaction

logger = logging.getLogger(__name__)


class CheckMissedCheckinUseCase(BaseUseCase):
    """检查缺失打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()

    def execute(self, check_time: datetime = None) -> UseCaseResult:
        """执行缺失打卡检查

        Args:
            check_time: 检查时间，默认为当前时间

        Returns:
            UseCaseResult: 包含统计信息
        """
        if check_time is None:
            check_time = datetime.now()

        try:
            stats = {
                'personal_rules_checked': 0,
                'personal_missed_created': 0,
                'community_rules_checked': 0,
                'community_missed_created': 0,
                'errors': 0
            }

            # 检查个人打卡规则
            personal_stats = self._check_personal_rules(check_time)
            stats.update(personal_stats)

            # 检查社区打卡规则
            community_stats = self._check_community_rules(check_time)
            stats.update(community_stats)

            self.logger.info(f"缺失打卡检查完成: {stats}")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='缺失打卡检查完成',
                data=stats
            )

        except Exception as e:
            self.logger.error(f"缺失打卡检查失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'缺失打卡检查失败: {str(e)}',
                data={'errors': 1}
            )

    def _check_personal_rules(self, check_time: datetime) -> Dict:
        """检查个人打卡规则

        Args:
            check_time: 检查时间

        Returns:
            统计信息
        """
        stats = {'personal_rules_checked': 0, 'personal_missed_created': 0, 'errors': 0}
        today = check_time.date()

        try:
            # 获取宽限期
            grace_minutes = int(os.getenv('MISS_GRACE_MINUTES', '0'))
            grace_delta = timedelta(minutes=grace_minutes)

            # 获取所有启用的个人打卡规则（排除已删除）
            rules = self.checkin_rule_repository.find_active_rules()
            stats['personal_rules_checked'] = len(rules)

            for rule in rules:
                try:
                    # 跳过全天规则，全天规则由每日任务处理
                    if rule.time_slot_type == 5:
                        continue

                    # 跳过今天创建的规则
                    if rule.created_at and rule.created_at.date() == today:
                        continue

                    # 检查规则今天是否应该打卡
                    if not self._should_check_today(rule, today):
                        continue

                    # 计算计划打卡时间
                    planned_time = self._planned_time_for_rule(rule, today)

                    # 检查是否还在宽限期内
                    if check_time < planned_time + grace_delta:
                        continue

                    # 查询今天的打卡记录
                    records = self.checkin_record_repository.find_by_rule_and_date(
                        rule_id=rule.rule_id,
                        check_date=today,
                        rule_source='personal'
                    )

                    # 检查是否已经有记录
                    has_checked = any(r.status == 1 for r in records)
                    has_missed = any(r.status == 0 for r in records)

                    if has_checked or has_missed:
                        continue

                    # 创建缺失打卡记录
                    with transaction():
                        self.checkin_record_repository.create(
                            rule_id=rule.rule_id,
                            user_id=rule.user_id,
                            checkin_time=None,
                            planned_time=planned_time,
                            status=0,
                            rule_source='personal'
                        )

                    stats['personal_missed_created'] += 1
                    self.logger.info(
                        f"用户 {rule.user_id} 规则 {rule.rule_id} 标记为miss，计划时间 {planned_time}"
                    )

                except Exception as e:
                    self.logger.error(f"处理规则 {rule.rule_id} 时出错: {str(e)}", exc_info=True)
                    stats['errors'] += 1

        except Exception as e:
            self.logger.error(f"检查个人规则失败: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats

    def _check_community_rules(self, check_time: datetime) -> Dict:
        """检查社区打卡规则

        Args:
            check_time: 检查时间

        Returns:
            统计信息
        """
        stats = {'community_rules_checked': 0, 'community_missed_created': 0, 'errors': 0}
        today = check_time.date()

        try:
            # 获取宽限期
            grace_minutes = int(os.getenv('MISS_GRACE_MINUTES', '0'))
            grace_delta = timedelta(minutes=grace_minutes)

            # 获取所有启用的社区打卡规则
            rules = self.community_checkin_rule_repository.find_active_rules()
            stats['community_rules_checked'] = len(rules)

            for rule in rules:
                try:
                    # 跳过全天规则，全天规则由每日任务处理
                    if rule.time_slot_type == 5:
                        continue

                    # 跳过今天创建的规则
                    if rule.created_at and rule.created_at.date() == today:
                        continue

                    # 检查规则今天是否应该打卡
                    if not self._should_check_today(rule, today):
                        continue

                    # 计算计划打卡时间
                    planned_time = self._planned_time_for_rule(rule, today)

                    # 检查是否还在宽限期内
                    if check_time < planned_time + grace_delta:
                        continue

                    # 获取该社区的工作人员
                    staff_list = self.community_staff_repository.find_by_community_id(
                        community_id=rule.community_id,
                        include_removed=False
                    )
                    staff_user_ids = [s.user_id for s in staff_list]

                    # 获取该社区的普通用户（排除工作人员）
                    all_users = self.user_repository.find_by_community_id(rule.community_id)
                    regular_users = [u for u in all_users if u.user_id not in staff_user_ids]

                    if not regular_users:
                        continue

                    # 获取该规则的激活用户
                    active_user_ids = []
                    for user in regular_users:
                        mapping = self.user_community_rule_repository.find_by_user_and_rule(
                            user_id=user.user_id,
                            community_rule_id=rule.community_rule_id
                        )
                        if mapping and mapping.is_active:
                            active_user_ids.append(user.user_id)

                    if not active_user_ids:
                        continue

                    # 查询今天的打卡记录
                    records = self.checkin_record_repository.find_by_community_rule_and_users(
                        community_rule_id=rule.community_rule_id,
                        user_ids=active_user_ids,
                        planned_time=planned_time
                    )

                    # 按用户分组检查
                    checked_user_ids = {r.user_id for r in records if r.status == 1}
                    missed_user_ids = {r.user_id for r in records if r.status == 0}

                    # 为未打卡的用户创建记录
                    for user_id in active_user_ids:
                        if user_id not in checked_user_ids and user_id not in missed_user_ids:
                            with transaction():
                                self.checkin_record_repository.create(
                                    rule_id=rule.community_rule_id,
                                    user_id=user_id,
                                    checkin_time=None,
                                    planned_time=planned_time,
                                    status=0,
                                    rule_source='community'
                                )

                            stats['community_missed_created'] += 1
                            self.logger.info(
                                f"用户 {user_id} 社区规则 {rule.community_rule_id} 标记为miss，计划时间 {planned_time}"
                            )

                except Exception as e:
                    self.logger.error(f"处理社区规则 {rule.community_rule_id} 时出错: {str(e)}", exc_info=True)
                    stats['errors'] += 1

        except Exception as e:
            self.logger.error(f"检查社区规则失败: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats

    def _should_check_today(self, rule, today: datetime.date) -> bool:
        """检查规则今天是否应该打卡

        Args:
            rule: 打卡规则
            today: 今天的日期

        Returns:
            是否应该打卡
        """
        if rule.frequency_type == 1:  # 自定义星期
            weekday = today.weekday()
            return bool(rule.week_days & (1 << weekday))
        elif rule.frequency_type == 2:  # 工作日
            return today.weekday() < 5
        elif rule.frequency_type == 3:  # 自定义日期范围
            if rule.custom_start_date and rule.custom_end_date:
                return rule.custom_start_date <= today <= rule.custom_end_date
            return False
        return True

    def _planned_time_for_rule(self, rule, today: datetime.date) -> datetime:
        """计算规则的计划打卡时间

        Args:
            rule: 打卡规则
            today: 今天的日期

        Returns:
            计划打卡时间
        """
        if rule.time_slot_type == 5:  # 全天有效
            return datetime.combine(today, time(0, 0))
        elif rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
            return datetime.combine(today, rule.custom_time)
        elif rule.time_slot_type == 1:  # 上午
            return datetime.combine(today, time(9, 0))
        elif rule.time_slot_type == 2:  # 下午
            return datetime.combine(today, time(14, 0))
        else:  # 晚上
            return datetime.combine(today, time(20, 0))