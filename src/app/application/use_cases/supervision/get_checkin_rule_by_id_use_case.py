"""
通过ID查询打卡规则用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCheckinRuleByIdUseCase(BaseUseCase):
    """通过ID查询打卡规则用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

    def _validate(self, rule_id: int) -> UseCaseResult:
        """验证参数"""
        if not rule_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID不能为空'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, rule_id: int) -> UseCaseResult:
        """
        执行查询打卡规则逻辑

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果，包含规则对象
        """
        try:
            rule = self.checkin_rule_repository.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            self.logger.info(f'查询打卡规则成功: rule_id={rule_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='查询成功',
                data=rule
            )

        except Exception as e:
            self.logger.error(f'查询打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'查询失败: {str(e)}'
            )