"""
删除打卡规则用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CheckinRule


class DeleteCheckinRuleUseCase(BaseUseCase):
    """删除打卡规则用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        执行删除打卡规则用例

        Args:
            rule_id: 规则ID
            user_id: 用户ID（用于权限验证）

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

            # 3. 验证权限（只有规则创建者或管理员可以删除）
            if rule.user_id != user_id:
                user = self.user_repository.find_by_id(user_id)
                if not user or user.role not in [3, 4]:  # 不是社区主管或超级管理员
                    return UseCaseResult(
                        status=UseCaseStatus.UNAUTHORIZED,
                        message='无权删除此打卡规则'
                    )

            # 4. 软删除打卡规则
            self.checkin_rule_repository.soft_delete(rule_id)

            self.logger.info(f'删除打卡规则成功: rule_id={rule_id}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡规则删除成功',
                data={
                    'rule_id': rule_id
                }
            )

        except Exception as e:
            self.logger.error(f'删除打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'删除打卡规则失败: {str(e)}'
            )