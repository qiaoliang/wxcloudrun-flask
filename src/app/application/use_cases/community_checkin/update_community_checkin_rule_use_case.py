"""
更新社区打卡规则用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class UpdateCommunityCheckinRuleUseCase(BaseUseCase):
    """更新社区打卡规则用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, rule_id: int, params: dict, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID
            params: 请求参数
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
            )

        if not params:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数不能为空'
            )

        if not isinstance(params, dict):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数格式错误'
            )

        if not isinstance(user_id, int) or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    @transactional


    def _execute(self, rule_id: int, params: dict, user_id: int) -> UseCaseResult:
        """
        执行更新社区打卡规则操作

        Args:
            rule_id: 规则ID
            params: 请求参数
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
from app.shared.utils.transaction import transactional
            # 获取现有规则
            rule = self.checkin_rule_repository.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'规则 {rule_id} 不存在'
                )

            # 更新规则属性
            if 'rule_name' in params:
                rule.rule_name = params['rule_name']
            if 'custom_time' in params:
                rule.custom_time = params['custom_time']
            if 'frequency_type' in params:
                rule.frequency_type = params['frequency_type']
            if 'time_slot_type' in params:
                rule.time_slot_type = params['time_slot_type']
            if 'icon_url' in params:
                rule.icon_url = params['icon_url']

            # 保存更新
            updated_rule = self.checkin_rule_repository.save(rule)

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'成功更新社区打卡规则，规则ID: {updated_rule.community_rule_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='更新成功',
                data={
                    'rule_id': updated_rule.community_rule_id,
                    'rule_name': updated_rule.rule_name
                }
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'更新社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新规则失败: {str(e)}'
            )
