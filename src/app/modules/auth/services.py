"""
认证模块业务逻辑服务
包含认证相关的业务逻辑函数
"""
import logging
from flask import current_app
from wxcloudrun.user_service import UserService
from database.flask_models import User
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _gen_phone_nickname, _hash_code, normalize_phone_number
from config_manager import get_token_secret
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token

app_logger = logging.getLogger('log')


def _format_user_login_response(user, token, refresh_token, is_new_user=False):
    """统一格式化登录响应"""
    # 获取社区名称 - 安全处理避免session问题
    community_name = None
    try:
        if user.community_id and hasattr(user, 'community') and user.community:
            community_name = user.community.name
    except Exception as e:
        current_app.logger.warning(f'无法获取社区名称，可能是session问题: {e}')
        # 不抛出错误，继续使用默认值
    
    # 调试：记录社区信息获取情况
    if user.community_id:
        if community_name:
            current_app.logger.info(f'用户社区信息获取成功: ID={user.community_id}, 名称={community_name}')
        else:
            current_app.logger.warning(f'用户有社区ID但无法获取社区名称: community_id={user.community_id}')
    else:
        current_app.logger.info(f'用户无社区信息: community_id={user.community_id}')
    
    return {
        'token': token,
        'refresh_token': refresh_token,
        'user_id': user.user_id,
        'wechat_openid': user.wechat_openid,
        'phone_number': user.phone_number,
        'nickname': user.nickname,
        'name': user.name,
        'avatar_url': user.avatar_url,
        'role': user.role_name,
        'community_id': user.community_id,
        'community_name': community_name,
        'login_type': 'new_user' if is_new_user else 'existing_user'
    }