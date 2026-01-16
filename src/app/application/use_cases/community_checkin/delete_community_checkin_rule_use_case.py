"""
删除社区打卡规则用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class DeleteCommunityCheckinRuleUseCase(BaseUseCase):
    """删除社区打卡规则用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
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

    def _execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        执行删除社区打卡规则操作

        Args:
            rule_id: 规则ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 检查规则是否存在
            rule = self.checkin_rule_repository.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'规则 {rule_id} 不存在'
                )

            # 删除规则（软删除，设置status=2）
            result = self.checkin_rule_repository.delete(rule_id)

            if not result:
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='删除失败'
                )

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'成功删除社区打卡规则，规则ID: {rule_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='删除成功',
                data={'rule_id': rule_id}
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'删除社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'删除规则失败: {str(e)}'
            )
