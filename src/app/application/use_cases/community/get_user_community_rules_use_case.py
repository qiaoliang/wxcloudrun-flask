"""
获取用户社区规则用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserCommunityRulesUseCase(BaseUseCase):
    """获取用户社区规则用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_rule_repo = RepositoryFactory.get_user_community_rule_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取用户社区规则用例

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 获取用户的所有用户规则
            user_rules = self.user_rule_repo.find_by_user_id(user_id, include_inactive=True)

            # 3. 构建返回数据
            rules_data = [
                {
                    'user_rule_id': rule.user_rule_id,
                    'community_rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'rule_type': rule.rule_type,
                    'checkin_time': rule.checkin_time.isoformat() if rule.checkin_time else None,
                    'checkin_frequency': rule.checkin_frequency,
                    'status': rule.status,
                    'created_at': rule.created_at.isoformat() if rule.created_at else None,
                    'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
                }
                for rule in user_rules
            ]

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取用户社区规则成功',
                data=rules_data
            )

        except Exception as e:
            self.logger.error(f'获取用户社区规则失败: user_id={user_id}, error={str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取用户社区规则失败: {str(e)}'
            )