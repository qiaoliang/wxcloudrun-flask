"""
接受监督邀请用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transactional

app_logger = logging.getLogger('log')


class AcceptSupervisionUseCase(BaseUseCase):
    """接受监督邀请用例"""

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    @transactional

    def execute(self, relation_id: int, user_id: int) -> UseCaseResult:
        """
        执行接受监督邀请

        Args:
            relation_id: 监督关系ID
            user_id: 用户ID（监督人）

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

            # 更新监督关系状态为已激活
            success = self.supervision_relation_repository.update_status(relation_id, 2)  # 2 = 已激活

            if not success:
                return UseCaseResult.fail('更新监督关系状态失败')

            app_logger.info(f'用户 {user_id} 接受监督邀请成功，关系ID: {relation_id}')
            return UseCaseResult.success(data={
                'relation_id': relation_id,
                'status': 2  # 2 = 已激活
            })

        except Exception as e:
            app_logger.error(f'接受监督邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'接受监督邀请失败: {str(e)}')
