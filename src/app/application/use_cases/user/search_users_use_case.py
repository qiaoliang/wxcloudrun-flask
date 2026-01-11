"""
搜索用户用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class SearchUsersUseCase(BaseUseCase):
    """搜索用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        keyword: str,
        community_id: Optional[int] = None,
        role: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行搜索用户用例

        Args:
            keyword: 搜索关键词（昵称、手机号、姓名）
            community_id: 社区ID（可选）
            role: 角色筛选（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not keyword or not keyword.strip():
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='搜索关键词不能为空'
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

            # 2. 搜索用户
            users = self.user_repository.search_users(keyword.strip(), community_id)

            # 3. 筛选角色
            if role is not None:
                users = [user for user in users if user.role == role]

            # 4. 分页处理
            total = len(users)
            start = (page - 1) * page_size
            end = start + page_size
            paged_users = users[start:end]

            # 5. 构造响应数据
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
                    'community_name': user.community.name if user.community else None,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })

            response_data = {
                'users': user_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

            self.logger.info(f'搜索用户成功: keyword={keyword}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='搜索用户成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'搜索用户失败: {str(e)}'
            )