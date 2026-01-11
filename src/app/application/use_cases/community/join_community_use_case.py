"""
加入社区用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import User, Community


class JoinCommunityUseCase(BaseUseCase):
    """加入社区用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(self, user_id: int, community_name: str) -> UseCaseResult:
        """
        执行加入社区用例

        Args:
            user_id: 用户ID
            community_name: 社区名称

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_name or not community_name.strip():
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区名称不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找社区
            community = self.community_repository.find_by_name(community_name)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'社区不存在: {community_name}'
                )

            # 4. 检查用户是否已在社区
            if user.community_id == community.community_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='用户已在社区'
                )

            # 5. 更新用户的社区ID
            user.community_id = community.community_id
            updated_user = self.user_repository.update(user)

            self.logger.info(f'用户 {user_id} 已加入社区 {community.community_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='加入社区成功',
                data={
                    'user_id': updated_user.user_id,
                    'community_id': updated_user.community_id,
                    'community_name': community.name
                }
            )

        except ValueError as e:
            self.logger.error(f'加入社区失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'加入社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'加入社区失败: {str(e)}'
            )