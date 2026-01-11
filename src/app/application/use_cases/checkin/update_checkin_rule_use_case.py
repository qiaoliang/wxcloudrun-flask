"""
更新打卡规则用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CheckinRule


class UpdateCheckinRuleUseCase(BaseUseCase):
    """更新打卡规则用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        rule_id: int,
        user_id: int,
        rule_data: Optional[dict] = None
    ) -> UseCaseResult:
        """
        执行更新打卡规则用例

        Args:
            rule_id: 规则ID
            user_id: 用户ID（用于权限验证）
            rule_data: 规则数据字典

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if not rule_data:
                rule_data = {}

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找打卡规则
            rule = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 4. 验证权限
            if rule.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限修改此打卡规则'
                )

            # 5. 更新规则字段
            if 'rule_name' in rule_data:
                rule.rule_name = rule_data['rule_name']

            if 'icon_url' in rule_data:
                rule.icon_url = rule_data['icon_url']

            if 'frequency_type' in rule_data:
                rule.frequency_type = rule_data['frequency_type']

            if 'time_slot_type' in rule_data:
                rule.time_slot_type = rule_data['time_slot_type']

            if 'custom_time' in rule_data:
                from datetime import datetime, time
                custom_time_str = rule_data['custom_time']
                if custom_time_str:
                    try:
                        rule.custom_time = datetime.strptime(custom_time_str, '%H:%M').time()
                    except ValueError:
                        try:
                            rule.custom_time = datetime.strptime(custom_time_str, '%H:%M:%S').time()
                        except ValueError:
                            return UseCaseResult(
                                status=UseCaseStatus.VALIDATION_ERROR,
                                message=f'无效的时间格式: {custom_time_str}'
                            )

            if 'custom_start_date' in rule_data:
                from datetime import datetime, date
                custom_start_date_str = rule_data['custom_start_date']
                if custom_start_date_str:
                    try:
                        rule.custom_start_date = datetime.strptime(custom_start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return UseCaseResult(
                            status=UseCaseStatus.VALIDATION_ERROR,
                            message=f'无效的日期格式: {custom_start_date_str}'
                        )

            if 'custom_end_date' in rule_data:
                from datetime import datetime, date
                custom_end_date_str = rule_data['custom_end_date']
                if custom_end_date_str:
                    try:
                        rule.custom_end_date = datetime.strptime(custom_end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return UseCaseResult(
                            status=UseCaseStatus.VALIDATION_ERROR,
                            message=f'无效的日期格式: {custom_end_date_str}'
                        )

            if 'week_days' in rule_data:
                week_days = rule_data['week_days']
                if isinstance(week_days, list):
                    week_days = sum(1 << (day - 1) for day in week_days)
                rule.week_days = week_days

            if 'status' in rule_data:
                rule.status = rule_data['status']

            # 6. 保存更新
            updated_rule = self.checkin_rule_repository.update(rule)

            self.logger.info(f'更新打卡规则成功: rule_id={rule_id}, user_id={user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡规则更新成功',
                data={
                    'rule': updated_rule
                }
            )

        except ValueError as e:
            self.logger.error(f'更新打卡规则失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'更新打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新打卡规则失败: {str(e)}'
            )