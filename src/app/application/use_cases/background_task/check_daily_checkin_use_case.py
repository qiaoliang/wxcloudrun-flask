"""
检查全天打卡UseCase
用于定时任务检查并标记全天规则的未打卡记录（每天执行一次）
"""
import logging
from datetime import datetime, time, date, timedelta
from typing import Dict
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class CheckDailyCheckinUseCase(BaseUseCase):
    """检查全天打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()

    def execute(self, check_date: date = None) -> UseCaseResult:
        """执行全天规则检查

        Args:
            check_date: 检查日期，默认为昨天

        Returns:
            UseCaseResult: 包含统计信息
        """
        if check_date is None:
            check_date = (datetime.now() - timedelta(days=1)).date()

        try:
            stats = {
                'personal_all_day_rules_checked': 0,
                'personal_missed_created': 0,
                'community_all_day_rules_checked': 0,
                'community_missed_created': 0,
                'errors': 0
            }

            # 检查个人全天规则
            personal_stats = self._check_personal_all_day_rules(check_date)
            stats.update(personal_stats)

            # 检查社区全天规则
            community_stats = self._check_community_all_day_rules(check_date)
            stats.update(community_stats)

            self.logger.info(f"全天规则检查完成: {stats}")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='全天规则检查完成',
                data=stats
            )

        except Exception as e:
            self.logger.error(f"全天规则检查失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'全天规则检查失败: {str(e)}',
                data={'errors': 1}
            )

    def _check_personal_all_day_rules(self, check_date: date) -> Dict:
        """检查个人全天规则

        Args:
            check_date: 检查日期

        Returns:
            统计信息
        """
        stats = {'personal_all_day_rules_checked': 0, 'personal_missed_created': 0, 'errors': 0}
        today = datetime.now().date()

        try:
            # 获取所有启用的全天个人打卡规则
            rules = self.checkin_rule_repository.find_all_day_rules()
            stats['personal_all_day_rules_checked'] = len(rules)

            for rule in rules:
                try:
                    # 检查创建时间
                    if rule.created_at is None:
                        continue

                    if rule.created_at.date() == today:
                        continue  # 今天创建，跳过

                    if rule.created_at.date() > check_date:
                        continue  # 创建时间在检查日期之后，跳过

                    # 查询检查日期的打卡记录
                    records = self.checkin_record_repository.find_by_rule_and_date(
                        rule_id=rule.rule_id,
                        check_date=check_date,
                        rule_source='personal'
                    )

                    # 检查是否已经有记录
                    has_checked = any(r.status == 1 for r in records)
                    has_missed = any(r.status == 0 for r in records)

                    if not has_checked and not has_missed:
                        # 创建缺失打卡记录
                        with transaction():
                            self.checkin_record_repository.create(
                                rule_id=rule.rule_id,
                                user_id=rule.user_id,
                                checkin_time=None,
                                planned_time=datetime.combine(check_date, time(0, 0)),
                                status=0,
                                rule_source='personal'
                            )

                        stats['personal_missed_created'] += 1
                        self.logger.info(
                            f"用户 {rule.user_id} 全天规则 {rule.rule_id} 标记为miss，计划时间 {datetime.combine(check_date, time(0, 0))}"
                        )

                except Exception as e:
                    self.logger.error(f"处理全天规则 {rule.rule_id} 时出错: {str(e)}", exc_info=True)
                    stats['errors'] += 1

        except Exception as e:
            self.logger.error(f"检查个人全天规则失败: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats

    def _check_community_all_day_rules(self, check_date: date) -> Dict:
        """检查社区全天规则

        Args:
            check_date: 检查日期

        Returns:
            统计信息
        """
        stats = {'community_all_day_rules_checked': 0, 'community_missed_created': 0, 'errors': 0}
        today = datetime.now().date()

        try:
            # 获取所有启用的全天社区打卡规则
            rules = self.community_checkin_rule_repository.find_all_day_rules()
            stats['community_all_day_rules_checked'] = len(rules)

            for rule in rules:
                try:
                    # 检查创建时间
                    if rule.created_at is None:
                        continue

                    if rule.created_at.date() == today:
                        continue  # 今天创建，跳过

                    if rule.created_at.date() > check_date:
                        continue  # 创建时间在检查日期之后，跳过

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

                    # 查询检查日期的打卡记录
                    records = self.checkin_record_repository.find_by_community_rule_and_users(
                        community_rule_id=rule.community_rule_id,
                        user_ids=active_user_ids,
                        planned_time=datetime.combine(check_date, time(0, 0))
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
                                    planned_time=datetime.combine(check_date, time(0, 0)),
                                    status=0,
                                    rule_source='community'
                                )

                            stats['community_missed_created'] += 1
                            self.logger.info(
                                f"用户 {user_id} 社区全天规则 {rule.community_rule_id} 标记为miss，计划时间 {datetime.combine(check_date, time(0, 0))}"
                            )

                except Exception as e:
                    self.logger.error(f"处理社区全天规则 {rule.community_rule_id} 时出错: {str(e)}", exc_info=True)
                    stats['errors'] += 1

        except Exception as e:
            self.logger.error(f"检查社区全天规则失败: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats