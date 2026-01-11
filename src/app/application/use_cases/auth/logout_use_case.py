"""
登出用例

负责编排登出的完整流程：
1. 验证 token
2. 查询用户信息
3. 清除 refresh token
4. 返回登出结果
"""
import logging
from typing import Optional

from .base import BaseUseCase, UseCaseResult, UseCaseError, UseCaseStatus
from wxcloudrun.user_service import UserService


class LogoutUseCase(BaseUseCase):
    """登出用例"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _validate(self, openid: Optional[str]) -> UseCaseResult:
        """
        验证登出参数

        Args:
            openid: 微信openid

        Returns:
            UseCaseResult: 验证结果
        """
        if not openid:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="token无效"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, openid: str) -> UseCaseResult:
        """
        执行登出

        Args:
            openid: 微信openid

        Returns:
            UseCaseResult: 登出结果
        """
        self.logger.info('开始执行登出用例')

        # 1. 查询用户
        user = UserService.query_user_by_openid(openid)

        if user:
            # 2. 清除 refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            UserService.update_user_by_id(user)
            self.logger.info(f'成功清除用户ID: {user.user_id} 的refresh token')
        else:
            self.logger.warning(f'未找到用户，openid: {openid}')

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='登出成功'
        )