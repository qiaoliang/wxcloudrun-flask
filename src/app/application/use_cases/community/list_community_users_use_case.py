"""
列出社区用户用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import User


class ListCommunityUsersUseCase(BaseUseCase):
    """列出社区用户用例"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        community_id: int,
        role: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行列出社区用户用例

        Args:
            community_id: 社区ID
            role: 角色筛选（可选）
            keyword: 搜索关键词（昵称、手机号、姓名）
            page: 页码
            page_size: 每页数量

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区ID不能为空'
                )

            if page < 1:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='页码必须大于0'
                )

            if page_size < 1 or page_size > 100:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='每页数量必须在1-100之间'
                )

            # 2. 验证社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 查询社区用户
            users = self.user_repository.find_by_community_id(community_id)

            # 4. 筛选角色
            if role is not None:
                users = [user for user in users if user.role == role]

            # 5. 搜索关键词
            if keyword:
                keyword_lower = keyword.lower()
                users = [
                    user for user in users
                    if (user.nickname and keyword_lower in user.nickname.lower()) or
                       (user.phone_number and keyword_lower in user.phone_number.lower()) or
                       (user.name and keyword_lower in user.name.lower())
                ]

            # 6. 分页处理
            total = len(users)
            start = (page - 1) * page_size
            end = start + page_size
            paged_users = users[start:end]

            # 7. 构造响应数据
            user_list = []
            for user in paged_users:
                user_list.append({
                    'user_id': user.user_id,
                    'nickname': user.nickname,
                    'name': user.name,
                    'phone_number': user.phone_number,
                    'role': user.role,
                    'role_name': user.role_name,
                    'avatar_url': user.avatar_url,
                    'community_id': user.community_id,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })

            response_data = {
                'users': user_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

            self.logger.info(f'列出社区用户成功: community_id={community_id}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='列出社区用户成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'列出社区用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'列出社区用户失败: {str(e)}'
            )