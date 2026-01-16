"""
获取社区规则详情用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityRuleDetailUseCase(BaseUseCase):
    """获取社区规则详情用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()

    def execute(self, rule_id: int) -> UseCaseResult:
        """
        执行获取社区规则详情用例

        Args:
            rule_id: 规则ID

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

            # 2. 查询规则
            rule = self.community_rule_repo.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='规则不存在'
                )

            # 3. 构建返回数据
            rule_data = {
                'community_rule_id': rule.community_rule_id,
                'community_id': rule.community_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'checkin_time': rule.checkin_time.isoformat() if rule.checkin_time else None,
                'checkin_frequency': rule.checkin_frequency,
                'status': rule.status,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
            }

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data=rule_data
            )

        except Exception as e:
            self.logger.error(f'获取规则详情失败: rule_id={rule_id}, error={str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则详情失败: {str(e)}'
            )