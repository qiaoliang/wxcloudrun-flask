"""
激活社区规则用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transactional
from database.flask_models import UserCommunityRule


class ActivateCommunityRulesUseCase(BaseUseCase):
    """激活社区规则用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
        self.user_rule_repo = RepositoryFactory.get_user_community_rule_repository()

    @transaction
    @transactional
    def execute(self, user_id: int, community_id: int) -> UseCaseResult:
        """
        执行激活社区规则用例

        为新加入社区的用户激活社区打卡规则

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id or not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 查询社区所有启用的打卡规则
            community_rules = self.community_rule_repo.get_all_enabled_by_community_id(community_id)

            if not community_rules:
                self.logger.info(f'社区 {community_id} 没有启用的打卡规则')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='社区没有启用的打卡规则',
                    data={'activated_count': 0}
                )

            # 3. 为用户创建对应的用户打卡规则
            activated_count = 0
            for community_rule in community_rules:
                # 检查是否已存在
                existing = self.user_rule_repo.find_by_user_and_rule(
                    user_id=user_id,
                    community_rule_id=community_rule.community_rule_id
                )

                if existing:
                    # 更新现有规则
                    existing.status = 1  # 启用
                    self.user_rule_repo.save(existing)
                else:
                    # 创建新规则
                    user_rule = UserCommunityRule(
                        user_id=user_id,
                        community_rule_id=community_rule.community_rule_id,
                        status=1,  # 启用
                        rule_name=community_rule.rule_name,
                        rule_type=community_rule.rule_type,
                        checkin_time=community_rule.checkin_time,
                        checkin_frequency=community_rule.checkin_frequency
                    )
                    self.user_rule_repo.save(user_rule)
                activated_count += 1

            self.logger.info(f'用户 {user_id} 已激活社区 {community_id} 的 {activated_count} 个打卡规则')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='社区规则激活成功',
                data={'activated_count': activated_count}
            )

        except Exception as e:
            self.logger.error(f'激活社区规则失败: user_id={user_id}, community_id={community_id}, error={str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'激活社区规则失败: {str(e)}'
            )
from app.shared.utils.transaction import transactional