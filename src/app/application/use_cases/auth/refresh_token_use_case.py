"""
刷新 Token 用例

负责编排刷新 token 的完整流程：
1. 验证 refresh token
2. 查询用户信息
3. 检查 token 是否过期
4. 生成新的 JWT token 和 refresh token
5. 返回新的 token
"""
import datetime
import logging
from typing import Dict

from .base import BaseUseCase, UseCaseResult, UseCaseError, UseCaseStatus
from wxcloudrun.user_service import UserService
from app.shared.utils.auth import generate_auth_tokens


class RefreshTokenUseCase(BaseUseCase):
    """刷新 Token 用例"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _validate(self, refresh_token: str) -> UseCaseResult:
        """
        验证刷新 token 参数

        Args:
            refresh_token: 刷新令牌

        Returns:
            UseCaseResult: 验证结果
        """
        if not refresh_token:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="缺少refresh_token参数"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, refresh_token: str) -> UseCaseResult:
        """
        执行刷新 token

        Args:
            refresh_token: 刷新令牌

        Returns:
            UseCaseResult: 刷新结果
        """
        self.logger.info('开始执行刷新 Token 用例')

        # 1. 查询用户信息
        user = UserService.query_user_by_refresh_token(refresh_token)

        if not user:
            self.logger.warning(f'未找到用户，refresh_token: {refresh_token[:20]}...')
            return UseCaseResult(
                status=UseCaseStatus.UNAUTHORIZED,
                message='无效的refresh_token'
            )

        # 2. 验证 refresh token
        if not user.refresh_token or user.refresh_token != refresh_token:
            self.logger.warning(f'无效的refresh_token: {refresh_token[:20]}...')
            return UseCaseResult(
                status=UseCaseStatus.UNAUTHORIZED,
                message='无效的refresh_token'
            )

        # 3. 检查 refresh token 是否过期
        if user.refresh_token_expire and user.refresh_token_expire < datetime.datetime.now():
            self.logger.warning(f'refresh_token已过期，用户ID: {user.user_id}')
            # 清除过期的 refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            UserService.update_user_by_id(user)
            return UseCaseResult(
                status=UseCaseStatus.UNAUTHORIZED,
                message='refresh_token已过期'
            )

        self.logger.info(f'找到用户，正在为用户ID: {user.user_id} 生成新token')

        # 4. 生成新的 token
        new_token, new_refresh_token, error_response = generate_auth_tokens(user, self.logger)
        if error_response:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message='生成token失败'
            )

        self.logger.info(f'成功为用户ID: {user.user_id} 刷新token')

        # 5. 构造响应数据
        response_data = {
            'token': new_token,
            'refresh_token': new_refresh_token,
            'expires_in': 7200  # 2小时（秒）
        }

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='刷新成功',
            data=response_data
        )