"""
搜索用户用例
支持按手机号和昵称搜索用户
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.domain.repositories.user_repository import UserRepository


class SearchUsersUseCase(BaseUseCase):
    """搜索用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repo = UserRepository()

    def _validate(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> UseCaseResult:
        """验证参数"""
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

        if per_page < 1 or per_page > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> UseCaseResult:
        """
        执行搜索用户逻辑

        Args:
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量
            search_type: 搜索类型 (all, phone, nickname)
            exclude_blackroom: 是否排除黑名单房间

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 使用Repository进行搜索
            users_data, total = self.user_repo.search_users_paginated(
                keyword=keyword,
                page=page,
                per_page=per_page,
                search_type=search_type,
                exclude_blackroom=exclude_blackroom
            )

            self.logger.info(f'搜索用户成功: keyword={keyword}, type={search_type}, count={len(users_data)}, total={total}')

            # 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='搜索成功',
                data={
                    'users': users_data,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'has_next': len(users_data) == per_page
                }
            )

        except Exception as e:
            self.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'搜索失败: {str(e)}'
            )