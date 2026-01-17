"""
微信登录用例

负责编排微信登录的完整流程：
1. 通过微信 code 获取 openid
2. 查询或创建用户
3. 生成 JWT token 和 refresh token
4. 返回登录结果
"""
import datetime
import logging
from typing import Dict, Optional

from ..base import BaseUseCase, UseCaseResult, UseCaseError, UseCaseStatus
from wxcloudrun.wxchat_api import get_user_info_by_code
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from const_default import DEFAULT_COMMUNITY_NAME
from app.domain.repositories.user_repository import UserRepository
from database.flask_models import User


class LoginWeChatUseCase(BaseUseCase):
    """微信登录用例"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def _validate(self, code: str, nickname: Optional[str] = None, 
                  avatar_url: Optional[str] = None) -> UseCaseResult:
        """
        验证登录参数

        Args:
            code: 微信授权码
            nickname: 用户昵称（可选）
            avatar_url: 用户头像（可选）

        Returns:
            UseCaseResult: 验证结果
        """
        if not code:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="缺少code参数"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, code: str, nickname: Optional[str] = None,
                 avatar_url: Optional[str] = None) -> UseCaseResult:
        """
        执行微信登录

        Args:
            code: 微信授权码
            nickname: 用户昵称（可选）
            avatar_url: 用户头像（可选）

        Returns:
            UseCaseResult: 登录结果
        """
        self.logger.info('开始执行微信登录用例')

        # 1. 调用微信API获取用户信息
        wx_data = get_user_info_by_code(code)

        if 'errcode' in wx_data:
            error_msg = wx_data.get('errmsg', '未知错误')
            self.logger.error(f'微信API返回错误: {error_msg}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=f'微信API错误: {error_msg}'
            )

        openid = wx_data.get('openid')
        session_key = wx_data.get('session_key')

        if not openid or not session_key:
            self.logger.error('微信API返回数据不完整')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message='微信API返回数据不完整'
            )

        self.logger.info(f'成功获取openid: {openid}')

        # 2. 清理和验证用户信息
        cleaned_nickname, cleaned_avatar = self._clean_user_info(nickname, avatar_url)

        # 3. 查询或创建用户
        user, is_new = self._get_or_create_user(openid, cleaned_nickname, cleaned_avatar)

        # 4. 生成 token
        token, error_response = generate_jwt_token(user, expires_hours=2)
        if error_response:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message='生成token失败'
            )

        refresh_token = generate_refresh_token(user, expires_days=7)
        self.user_repository.save(user)

        self.logger.info(f'微信登录成功 - 用户ID: {user.user_id}, 新用户: {is_new}')

        # 5. 构造响应数据
        response_data = self._build_response_data(user, token, refresh_token, is_new)

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='登录成功',
            data=response_data
        )

    def _clean_user_info(self, nickname: Optional[str], avatar_url: Optional[str]) -> tuple:
        """
        清理和验证用户信息

        Args:
            nickname: 原始昵称
            avatar_url: 原始头像URL

        Returns:
            tuple: (清理后的昵称, 清理后的头像URL)
        """
        # 处理昵称
        if not nickname or len(nickname.strip()) == 0:
            cleaned_nickname = f"微信用户_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        else:
            cleaned_nickname = nickname.strip()
            if len(cleaned_nickname) > 50:
                cleaned_nickname = cleaned_nickname[:50] + "..."

        # 处理头像
        if not avatar_url or not avatar_url.startswith(('http://', 'https://')):
            cleaned_avatar = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"
        else:
            cleaned_avatar = avatar_url.strip()

        return cleaned_nickname, cleaned_avatar

    def _get_or_create_user(self, openid: str, nickname: str, avatar_url: str) -> tuple:
        """
        查询或创建用户

        Args:
            openid: 微信openid
            nickname: 用户昵称
            avatar_url: 用户头像

        Returns:
            tuple: (用户对象, 是否为新用户)
        """
        # 查询现有用户
        existing_user = self.user_repository.find_by_openid(openid)

        if existing_user:
            # 更新现有用户信息
            user = existing_user
            updated = False

            if nickname and user.nickname != nickname:
                if len(nickname.strip()) > 0:
                    original_nickname = nickname.strip()
                    if len(original_nickname) > 50:
                        user.nickname = original_nickname[:50] + "..."
                    else:
                        user.nickname = original_nickname
                    updated = True

            if avatar_url and user.avatar_url != avatar_url:
                if avatar_url.startswith(('http://', 'https://')) and len(avatar_url) <= 500:
                    user.avatar_url = avatar_url.strip()
                    updated = True

            # 检查并补充社区信息
            if not user.community_id:
                try:
                    # 查找默认社区
                    community = self.community_repository.find_by_name(DEFAULT_COMMUNITY_NAME)
                    if community:
                        user.community_id = community.community_id
                        updated = True
                        self.logger.info(f'用户已分配到默认社区: {DEFAULT_COMMUNITY_NAME}')
                    else:
                        self.logger.warning(f'默认社区不存在: {DEFAULT_COMMUNITY_NAME}')
                except Exception as e:
                    self.logger.error(f'分配用户到默认社区失败: {str(e)}')

            if updated:
                self.user_repository.save(user)

            return user, False

        # 创建新用户
        user_data = User(
            wechat_openid=openid,
            nickname=nickname,
            avatar_url=avatar_url,
            role=1,  # 默认为独居者角色
            status=1  # 默认为正常状态
        )

        try:
            created_user = self.user_repository.save(user_data)
            self.logger.info(f'新用户创建成功，用户ID: {created_user.user_id}')
            return created_user, True
        except Exception as e:
            self.logger.error(f'创建用户失败: {str(e)}')
            # 使用最小可用信息重试
            fallback_nickname = f"用户_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            fallback_avatar = "https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0"

            user_data = User(
                wechat_openid=openid,
                nickname=fallback_nickname,
                avatar_url=fallback_avatar,
                role=1,
                status=1
            )
            created_user = self.user_repository.save(user_data)
            self.logger.warning(f'使用fallback信息创建用户成功，用户ID: {created_user.user_id}')
            return created_user, True

    def _build_response_data(self, user: User, token: str, refresh_token: str, is_new: bool) -> Dict:
        """
        构造响应数据

        Args:
            user: 用户对象
            token: JWT token
            refresh_token: 刷新token
            is_new: 是否为新用户

        Returns:
            Dict: 响应数据
        """
        # 获取社区名称
        community_name = None
        try:
            if user.community_id and hasattr(user, 'community') and user.community:
                community_name = user.community.name
        except Exception as e:
            self.logger.warning(f'无法获取社区名称: {e}')

        return {
            'token': token,
            'refresh_token': refresh_token,
            'user_id': user.user_id,
            'wechat_openid': user.wechat_openid,
            'phone_number': user.phone_number,
            'nickname': user.nickname,
            'name': user.name,
            'avatar_url': user.avatar_url,
            'role': user.role,
            'role_name': user.role_name,
            'community_id': user.community_id,
            'community_name': community_name,
            'login_type': 'new_user' if is_new else 'existing_user'
        }