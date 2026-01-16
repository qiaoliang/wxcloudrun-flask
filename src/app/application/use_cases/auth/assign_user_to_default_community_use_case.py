"""
分配用户到默认社区用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class AssignUserToDefaultCommunityUseCase(BaseUseCase):
    """分配用户到默认社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(self, user) -> UseCaseResult:
        """
        执行分配用户到默认社区用例

        Args:
            user: 用户对象

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            from const_default import DEFAULT_COMMUNITY_NAME

            # 查找默认社区
            community = self.community_repository.find_by_name(DEFAULT_COMMUNITY_NAME)

            if community:
                # 分配用户到默认社区
                user.community_id = community.community_id
                self.logger.info(f'新用户已自动分配到默认社区，用户ID: {user.user_id}, 社区ID: {community.community_id}')

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='已分配到默认社区',
                    data={'community_id': community.community_id, 'community_name': community.name}
                )
            else:
                self.logger.warning(f'默认社区不存在: {DEFAULT_COMMUNITY_NAME}')
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='默认社区不存在',
                    data={'community_name': DEFAULT_COMMUNITY_NAME}
                )

        except Exception as e:
            self.logger.error(f'自动分配社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'自动分配社区失败: {str(e)}'
            )