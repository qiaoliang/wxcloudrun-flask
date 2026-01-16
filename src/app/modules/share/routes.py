"""
分享功能视图模块
包含分享链接创建、解析和分享页面渲染功能
"""

import logging
from datetime import datetime, timedelta
from flask import request, Response, current_app
from sqlalchemy import select
from . import share_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from database.flask_models import db, ShareLink, ShareLinkAccessLog, SupervisionRuleRelation
from app.shared.utils.transaction import transaction
from app.infrastructure.persistence.repository_factory import RepositoryFactory
import secrets

app_logger = logging.getLogger('log')


@share_bp.route('/checkin/create', methods=['POST'])
def create_share_checkin_link():
    """
    创建可分享的打卡邀请链接（opaque token，避免暴露敏感参数）
    请求体：{ rule_id, expire_hours? 默认 168(7天) }
    返回：{ token, url, mini_path, expire_at }
    """
    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        openid = decoded.get('openid')
        # 使用UseCase获取用户
        from app.application.use_cases.user import GetUserByOpenidUseCase
        get_user_use_case = GetUserByOpenidUseCase()
        user_result = get_user_use_case.execute(openid)

        if not user_result.is_success:
            return make_err_response({}, '用户不存在')

        user_id = user_result.data.get('user_id')

        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        expire_hours = int(params.get('expire_hours', 168))
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        # 使用应用服务用例创建分享链接
        from app.application.use_cases.share import CreateShareLinkUseCase

        use_case = CreateShareLinkUseCase()
        result = use_case.execute(
            user_id=user_id,
            rule_id=rule_id,
            expire_hours=expire_hours
        )

        if result.is_success:
            # 构建分享链接
            base_url = request.host_url.rstrip('/')
            token = result.data.get('token')
            full_url = f"{base_url}/share/check-in?token={token}"
            mini_path = f"/share/check-in?token={token}"
            qrcode_url = result.data.get('qrcode_url')

            current_app.logger.info(f'用户 {user_id} 创建分享链接成功，token: {token}')
            return make_succ_response({
                'token': token,
                'url': full_url,
                'mini_path': mini_path,
                'qrcode_url': qrcode_url,
                'expire_at': result.data.get('expires_at')
            })
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'创建分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, '创建分享链接失败')


@share_bp.route('/checkin/resolve', methods=['GET'])
def resolve_share_checkin_link():
    """
    解析分享链接，返回打卡规则信息（无需登录）
    参数：token
    返回：{ rule_info, inviter_info, is_expired, is_already_supervisor }
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        # 获取当前用户ID（如果已登录）
        current_user_id = None
        decoded, error_response = verify_token()
        if not error_response and decoded:
            openid = decoded.get('openid')
            # 使用UseCase获取用户
            from app.application.use_cases.user import GetUserByOpenidUseCase
            get_user_use_case = GetUserByOpenidUseCase()
            user_result = get_user_use_case.execute(openid)
            if user_result.is_success:
                current_user_id = user_result.data.get('user_id')

        # 使用应用服务用例解析分享链接
        from app.application.use_cases.share import ResolveShareLinkUseCase

        use_case = ResolveShareLinkUseCase()
        result = use_case.execute(
            token=token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            current_user_id=current_user_id
        )

        if result.is_success:
            current_app.logger.info(f'解析分享链接成功，token: {token}')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'解析分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, '解析分享链接失败')


@share_bp.route('/check-in', methods=['GET'])
def share_checkin_page():
    """
    分享打卡页面（无需登录，用于小程序分享卡片）
    参数：token
    返回：HTML页面
    """
    try:
        token = request.args.get('token')
        if not token:
            return "缺少token参数", 400

        link = db.session.execute(select(ShareLink).filter_by(token=token)).scalar_one_or_none()
        if not link or link.expires_at < datetime.now():
            return "分享链接无效或已过期", 400

        # 记录访问日志（使用事务管理器）
        with transaction():
            access_log = ShareLinkAccessLog(
                token=link.token,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                accessed_at=datetime.now()
            )
            db.session.add(access_log)

        # 使用Repository获取规则和用户信息
        checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        user_repository = RepositoryFactory.get_user_repository()

        rule = checkin_rule_repository.find_by_id(link.rule_id)
        user = user_repository.find_by_id(link.solo_user_id)

        if not rule or not user:
            return "分享内容不存在", 404

        # 渲染HTML页面
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{rule.rule_name} - 打卡分享</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 24px;
                }}
                .avatar {{
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    margin-bottom: 12px;
                    object-fit: cover;
                }}
                .title {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #1a1a1a;
                }}
                .description {{
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 20px;
                    line-height: 1.5;
                }}
                .info {{
                    background: #f8f9fa;
                    padding: 16px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                }}
                .info-item {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-size: 14px;
                }}
                .info-label {{
                    color: #666;
                }}
                .info-value {{
                    font-weight: 500;
                    color: #333;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                    margin-top: 24px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{user.avatar_url}" alt="头像" class="avatar">
                    <div class="title">{rule.rule_name}</div>
                    <div class="description">暂无描述</div>
                </div>

                <div class="info">
                    <div class="info-item">
                        <span class="info-label">打卡时间：</span>
                        <span class="info-value">{rule.custom_time.strftime('%H:%M') if rule.custom_time else '未设置'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">重复周期：</span>
                        <span class="info-value">每天</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">分享者：</span>
                        <span class="info-value">{user.nickname}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">状态：</span>
                        <span class="info-value">{'启用' if rule.status == 1 else '禁用'}</span>
                    </div>
                </div>

                <div class="footer">
                    <p>此分享链接由 SafeGuard 提供</p>
                    <p>有效期至：{link.expires_at.strftime('%Y-%m-%d %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return Response(html_content, mimetype='text/html')

    except Exception as e:
        current_app.logger.error(f'渲染分享页面失败: {str(e)}', exc_info=True)
        return "页面渲染失败", 500