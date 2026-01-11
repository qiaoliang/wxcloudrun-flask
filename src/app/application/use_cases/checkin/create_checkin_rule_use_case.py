"""
创建打卡规则用例
"""
import logging
from datetime import datetime, time, date
from typing import Optional, Dict, Any

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CheckinRule


class CreateCheckinRuleUseCase(BaseUseCase):
    """创建打卡规则用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

    def execute(
        self,
        user_id: int,
        rule_data: Dict[str, Any]
    ) -> UseCaseResult:
        """
        执行创建打卡规则用例

        Args:
            user_id: 用户ID
            rule_data: 规则数据字典

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not rule_data.get('rule_name'):
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则名称不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 解析时间字段
            custom_time = None
            if rule_data.get('custom_time'):
                custom_time_str = rule_data['custom_time']
                custom_time = self._parse_time_only(custom_time_str)

            # 4. 解析日期字段
            custom_start_date = None
            custom_end_date = None
            if rule_data.get('custom_start_date'):
                custom_start_date_str = rule_data['custom_start_date']
                custom_start_date = self._parse_date_only(custom_start_date_str)

            if rule_data.get('custom_end_date'):
                custom_end_date_str = rule_data['custom_end_date']
                custom_end_date = self._parse_date_only(custom_end_date_str)

            # 5. 验证自定义频率的日期范围
            if rule_data.get('frequency_type') == 3:  # 自定义频率
                if not custom_start_date or not custom_end_date:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='自定义频率必须提供起止日期'
                    )
                if custom_end_date < custom_start_date:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='结束日期不能早于开始日期'
                    )

            # 6. 创建打卡规则
            new_rule = CheckinRule(
                user_id=user_id,
                community_id=user.community_id,
                rule_name=rule_data['rule_name'],
                icon_url=rule_data.get('icon_url'),
                frequency_type=rule_data.get('frequency_type', 0),
                time_slot_type=rule_data.get('time_slot_type', 4),
                custom_time=custom_time,
                custom_start_date=custom_start_date,
                custom_end_date=custom_end_date,
                week_days=rule_data.get('week_days', 127),
                status=1,
                created_at=datetime.now()
            )

            saved_rule = self.checkin_rule_repository.save(new_rule)

            self.logger.info(f'创建打卡规则成功: rule_id={saved_rule.rule_id}, user_id={user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡规则创建成功',
                data={
                    'rule_id': saved_rule.rule_id,
                    'rule_name': saved_rule.rule_name,
                    'user_id': saved_rule.user_id,
                    'community_id': saved_rule.community_id,
                    'frequency_type': saved_rule.frequency_type,
                    'time_slot_type': saved_rule.time_slot_type,
                    'status': saved_rule.status
                }
            )

        except ValueError as e:
            self.logger.error(f'创建打卡规则失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'创建打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建打卡规则失败: {str(e)}'
            )

    def _parse_time_only(self, time_str: str) -> Optional[time]:
        """解析时间字符串"""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            try:
                return datetime.strptime(time_str, '%H:%M:%S').time()
            except ValueError:
                raise ValueError(f'无效的时间格式: {time_str}')

    def _parse_date_only(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f'无效的日期格式: {date_str}')