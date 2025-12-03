from typing import Optional
from datetime import datetime
from wxcloudrun.model import User


class AuthService:
    """
    认证服务类
    """

    def refresh_token(self, refresh_token_str: str):
        """
        刷新token
        """
        from wxcloudrun.dao import query_user_by_refresh_token, update_user_by_id
        import os
        import jwt
        import secrets
        import datetime as dt_module

        # 从数据库中查找用户信息
        user = query_user_by_refresh_token(refresh_token_str)
        if not user or not user.refresh_token or user.refresh_token != refresh_token_str:
            raise ValueError('无效的refresh_token')

        # 检查refresh token是否过期
        if user.refresh_token_expire and user.refresh_token_expire < datetime.now():
            # 清除过期的refresh token
            user.refresh_token = None
            user.refresh_token_expire = None
            update_user_by_id(user)
            raise ValueError('refresh_token已过期')

        # 生成新的JWT token（access token）
        token_payload = {
            'openid': user.wechat_openid,
            'user_id': user.user_id,
            'exp': dt_module.datetime.now(timezone.utc) + dt_module.timedelta(hours=2)  # 设置2小时过期时间
        }
        token_secret = os.environ.get('TOKEN_SECRET', 'your-secret-key')
        new_token = jwt.encode(token_payload, token_secret, algorithm='HS256')

        # 生成新的refresh token
        new_refresh_token = secrets.token_urlsafe(32)
        # 设置新的refresh token过期时间（7天）
        new_refresh_token_expire = datetime.now() + dt_module.timedelta(days=7)

        # 更新数据库中的refresh token
        user.refresh_token = new_refresh_token
        user.refresh_token_expire = new_refresh_token_expire
        update_user_by_id(user)

        return {
            'token': new_token,
            'refresh_token': new_refresh_token,
            'expires_in': 7200  # 2小时（秒）
        }

    def logout(self, openid: str):
        """
        用户登出，清除refresh token
        """
        from wxcloudrun.dao import query_user_by_openid, update_user_by_id

        # 根据openid查找用户并清除refresh token
        user = query_user_by_openid(openid)
        if user:
            user.refresh_token = None
            user.refresh_token_expire = None
            update_user_by_id(user)

        return {'message': '登出成功'}