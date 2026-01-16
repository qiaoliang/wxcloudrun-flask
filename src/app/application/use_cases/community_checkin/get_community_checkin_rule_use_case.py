"""
获取单个社区打卡规则详情用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityCheckinRuleUseCase(BaseUseCase):
    """获取单个社区打卡规则详情用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, rule_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, rule_id: int) -> UseCaseResult:
        """
        执行获取单个社区打卡规则详情操作

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用Repository获取规则详情
            rule = self.checkin_rule_repository.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'规则 {rule_id} 不存在'
                )

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'成功获取社区打卡规则详情，规则ID: {rule.community_rule_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data={
                    'rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'custom_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                    'frequency_type': rule.frequency_type,
                    'time_slot_type': rule.time_slot_type,
                    'icon_url': rule.icon_url,
                    'status': rule.status
                }
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'获取社区打卡规则详情失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则详情失败: {str(e)}'
            )
