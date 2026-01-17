"""
拒绝监督邀请用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory

app_logger = logging.getLogger('log')


class RejectSupervisionUseCase(BaseUseCase):
    """拒绝监督邀请用例"""

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(self, relation_id: int, user_id: int, reason: str = '') -> UseCaseResult:
        """
        执行拒绝监督邀请

        Args:
            relation_id: 监督关系ID
            user_id: 用户ID（监督人）
            reason: 拒绝原因

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 查询监督关系
            relation = self.supervision_relation_repository.find_by_id(relation_id)

            if not relation:
                return UseCaseResult.fail('监督关系不存在', status=UseCaseStatus.NOT_FOUND)

            # 验证当前用户是监督人
            if relation.supervisor_user_id != user_id:
                return UseCaseResult.fail('无权限操作此监督关系', status=UseCaseStatus.FORBIDDEN)

            # 删除监督关系（拒绝）
            success = self.supervision_relation_repository.delete_entity(relation)

            if not success:
                return UseCaseResult.fail('删除监督关系失败')

            app_logger.info(f'用户 {user_id} 拒绝监督邀请，关系ID: {relation_id}，原因: {reason}')
            return UseCaseResult.success(data={'message': '拒绝监督邀请成功'})

        except Exception as e:
            app_logger.error(f'拒绝监督邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'拒绝邀请失败: {str(e)}')
