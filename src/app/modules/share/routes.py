"""
分享功能视图模块
包含分享链接创建、解析和分享页面渲染功能
"""

import logging
from datetime import datetime, timedelta
from flask import request, Response, current_app
from . import share_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from wxcloudrun.user_service import UserService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from database.flask_models import db, ShareLink, ShareLinkAccessLog, SupervisionRuleRelation
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
        user = UserService.query_user_by_openid(openid)
        if not user:
            return make_err_response({}, '用户不存在')

        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        expire_hours = int(params.get('expire_hours', 168))
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        rule = CheckinRuleService.query_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        link = ShareLink(
            token=token,
            solo_user_id=user.user_id,
            rule_id=rule.rule_id,
            expires_at=expires_at
        )
        db.session.add(link)
        db.session.commit()

        # 构建分享链接
        base_url = request.host_url.rstrip('/')
        full_url = f"{base_url}/share/check-in?token={token}"
        mini_path = f"/share/check-in?token={token}"

        current_app.logger.info(f'用户 {user.user_id} 创建分享链接成功，token: {token}')
        return make_succ_response({
            'token': token,
            'url': full_url,
            'mini_path': mini_path,
            'expire_at': expires_at.isoformat()
        })

    except Exception as e:
        current_app.logger.error(f'创建分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, '创建分享链接失败')


@share_bp.route('/checkin/resolve', methods=['GET'])
def resolve_share_checkin_link():
    """
    解析分享链接，返回打卡规则信息（无需登录）
    参数：token
    返回：{ rule_info, share_info }
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        link = ShareLink.query.filter_by(token=token).first()
        if not link or link.expires_at < datetime.now():
            return make_err_response({}, '分享链接无效或已过期')

        # 记录访问日志
        access_log = ShareLinkAccessLog(
            share_link_id=link.share_link_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            accessed_at=datetime.now()
        )
        db.session.add(access_log)
        db.session.commit()

        # 获取规则信息
        rule = CheckinRuleService.query_rule_by_id(link.rule_id)
        if not rule:
            return make_err_response({}, '关联的打卡规则不存在')

        # 获取用户信息
        user = UserService.query_user_by_id(link.solo_user_id)
        if not user:
            return make_err_response({}, '分享用户不存在')

        rule_info = {
            'rule_id': rule.rule_id,
            'title': rule.title,
            'description': rule.description,
            'checkin_time': rule.checkin_time,
            'repeat_days': rule.repeat_days,
            'is_enabled': rule.is_enabled
        }

        share_info = {
            'share_user_id': user.user_id,
            'share_user_nickname': user.nickname,
            'share_user_avatar': user.avatar_url,
            'created_at': link.created_at.isoformat(),
            'expires_at': link.expires_at.isoformat(),
            'access_count': link.access_count
        }

        current_app.logger.info(f'解析分享链接成功，token: {token}')
        return make_succ_response({
            'rule_info': rule_info,
            'share_info': share_info
        })

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

        link = ShareLink.query.filter_by(token=token).first()
        if not link or link.expires_at < datetime.now():
            return "分享链接无效或已过期", 400

        # 记录访问日志
        access_log = ShareLinkAccessLog(
            share_link_id=link.share_link_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            accessed_at=datetime.now()
        )
        db.session.add(access_log)
        db.session.commit()

        # 获取规则和用户信息
        rule = CheckinRuleService.query_rule_by_id(link.rule_id)
        user = UserService.query_user_by_id(link.solo_user_id)

        if not rule or not user:
            return "分享内容不存在", 404

        # 渲染HTML页面
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{rule.title} - 打卡分享</title>
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
                    <div class="title">{rule.title}</div>
                    <div class="description">{rule.description or '暂无描述'}</div>
                </div>
                
                <div class="info">
                    <div class="info-item">
                        <span class="info-label">打卡时间：</span>
                        <span class="info-value">{rule.checkin_time}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">重复周期：</span>
                        <span class="info-value">{rule.repeat_days}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">分享者：</span>
                        <span class="info-value">{user.nickname}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">状态：</span>
                        <span class="info-value">{'启用' if rule.is_enabled else '禁用'}</span>
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