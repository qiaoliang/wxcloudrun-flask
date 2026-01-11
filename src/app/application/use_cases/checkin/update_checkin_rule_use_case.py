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
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        rule_id: int,
        user_id: int,
        rule_type: Optional[str] = None,
        frequency_type: Optional[str] = None,
        planned_time: Optional[str] = None,
        planned_dates: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UseCaseResult:
        """
        执行更新打卡规则用例

        Args:
            rule_id: 规则ID
            user_id: 用户ID（用于权限验证）
            rule_type: 规则类型
            frequency_type: 频率类型
            planned_time: 计划时间
            planned_dates: 计划日期
            is_active: 是否激活

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

            # 2. 查询打卡规则
            rule = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 3. 验证权限（只有规则创建者或管理员可以修改）
            if rule.user_id != user_id:
                user = self.user_repository.find_by_id(user_id)
                if not user or user.role not in [3, 4]:  # 不是社区主管或超级管理员
                    return UseCaseResult(
                        status=UseCaseStatus.UNAUTHORIZED,
                        message='无权修改此打卡规则'
                    )

            # 4. 更新规则信息
            if rule_type is not None:
                if rule_type not in ['personal', 'community']:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='规则类型无效'
                    )
                rule.rule_type = rule_type

            if frequency_type is not None:
                if frequency_type not in ['daily', 'weekly', 'workdays', 'custom']:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='频率类型无效'
                    )
                rule.frequency_type = frequency_type

            if planned_time is not None:
                # 验证时间格式
                try:
                    import datetime
                    datetime.datetime.strptime(planned_time, '%H:%M')
                    rule.planned_time = planned_time
                except ValueError:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='时间格式无效，应为 HH:MM'
                    )

            if planned_dates is not None:
                # 验证日期格式
                if frequency_type == 'custom':
                    try:
                        import json
                        dates = json.loads(planned_dates)
                        if not isinstance(dates, list):
                            return UseCaseResult(
                                status=UseCaseStatus.VALIDATION_ERROR,
                                message='计划日期格式无效'
                            )
                        rule.planned_dates = planned_dates
                    except json.JSONDecodeError:
                        return UseCaseResult(
                            status=UseCaseStatus.VALIDATION_ERROR,
                            message='计划日期格式无效'
                        )

            if is_active is not None:
                rule.is_active = is_active

            # 5. 保存更新
            updated_rule = self.checkin_rule_repository.save(rule)

            self.logger.info(f'更新打卡规则成功: rule_id={rule_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡规则更新成功',
                data={
                    'rule_id': updated_rule.rule_id,
                    'user_id': updated_rule.user_id,
                    'rule_type': updated_rule.rule_type,
                    'frequency_type': updated_rule.frequency_type,
                    'planned_time': updated_rule.planned_time,
                    'planned_dates': updated_rule.planned_dates,
                    'is_active': updated_rule.is_active
                }
            )

        except Exception as e:
            self.logger.error(f'更新打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新打卡规则失败: {str(e)}'
            )