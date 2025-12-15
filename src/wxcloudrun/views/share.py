"""
分享功能视图模块
包含分享链接创建、解析和分享页面渲染功能
"""

import logging
from datetime import datetime, timedelta
from flask import request, Response
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.user_service import UserService
from wxcloudrun.dao import query_checkin_rule_by_id
from database import get_database
from database.models import ShareLink, ShareLinkAccessLog, SupervisionRuleRelation
from wxcloudrun.decorators import login_required
from wxcloudrun.utils.auth import verify_token
import secrets

app_logger = logging.getLogger('log')

# 获取数据库实例
db = get_database()


@app.route('/api/share/checkin/create', methods=['POST'])
@login_required
def create_share_checkin_link(decoded):
    """
    创建可分享的打卡邀请链接（opaque token，避免暴露敏感参数）
    请求体：{ rule_id, expire_hours? 默认 168(7天) }
    返回：{ token, url, mini_path, expire_at }
    """
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

        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        with db.get_session() as session:
            link = ShareLink(
                token=token,
                solo_user_id=user.user_id,
                rule_id=rule.rule_id,
                expires_at=expires_at
            )
            session.add(link)
            session.commit()

        # 构造URL（PC/移动端），以及小程序内路径
        base = request.host_url.rstrip('/')
        url = f"{base}/share/check-in?token={token}"
        mini_path = f"/pages/supervisor-detail/supervisor-detail?token={token}"

        return make_succ_response({
            'token': token,
            'url': url,
            'mini_path': mini_path,
            'expire_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        app.logger.error(f'创建分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建分享链接失败: {str(e)}')


@app.route('/api/share/checkin/resolve', methods=['GET'])
@login_required
def resolve_share_checkin_link(decoded):
    """
    解析分享链接并建立监督关系（已注册用户点击链接后）
    参数：token
    返回：完整规则信息
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        link = ShareLink.query.filter_by(token=token).first()
        if not link:
            return make_err_response({}, '链接无效或已失效')
        if link.expires_at and link.expires_at < datetime.now():
            return make_err_response({}, '链接已过期')

        # 访问日志记录
        try:
            with db.get_session() as session:
                lg = ShareLinkAccessLog(
                    token=token,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    supervisor_user_id=UserService.query_user_by_openid(
                        decoded.get('openid')).user_id
                )
                session.add(lg)
                session.commit()
        except Exception:
            pass

        # 建立监督关系，直接设为已同意
        relation = SupervisionRuleRelation.query.filter_by(
            solo_user_id=link.solo_user_id,
            supervisor_user_id=UserService.query_user_by_openid(
                decoded.get('openid')).user_id,
            rule_id=link.rule_id
        ).first()
        with db.get_session() as session:
            if not relation:
                relation = SupervisionRuleRelation(
                    solo_user_id=link.solo_user_id,
                    supervisor_user_id=UserService.query_user_by_openid(
                        decoded.get('openid')).user_id,
                    rule_id=link.rule_id,
                    status=2
                )
                session.add(relation)
            else:
                relation.status = 2
                relation.updated_at = datetime.now()
            session.commit()

        rule = query_checkin_rule_by_id(link.rule_id)
        rule_data = {
            'rule_id': rule.rule_id,
            'rule_name': rule.rule_name,
            'icon_url': rule.icon_url,
            'frequency_type': rule.frequency_type,
            'time_slot_type': rule.time_slot_type,
            'custom_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
            'week_days': rule.week_days,
            'custom_start_date': rule.custom_start_date.strftime('%Y-%m-%d') if rule.custom_start_date else None,
            'custom_end_date': rule.custom_end_date.strftime('%Y-%m-%d') if rule.custom_end_date else None,
            'status': rule.status
        }
        return make_succ_response({'rule': rule_data, 'solo_user_id': link.solo_user_id})
    except Exception as e:
        app.logger.error(f'解析分享链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析分享链接失败: {str(e)}')


@app.route('/share/check-in', methods=['GET'])
def share_checkin_page():
    """
    分享链接的Web入口：
    - 记录访问日志
    - 微信UA下提示小程序路径
    - 如果提供了Authorization则自动解析并返回JSON
    """
    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')
        link = ShareLink.query.filter_by(token=token).first()
        if not link:
            return make_err_response({}, '链接无效或已失效')
        if link.expires_at and link.expires_at < datetime.now():
            return make_err_response({}, '链接已过期')

        # 访问日志
        try:
            with db.get_session() as session:
                lg = ShareLinkAccessLog(
                    token=token,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                session.add(lg)
                session.commit()
        except Exception:
            pass

        ua = request.headers.get('User-Agent', '')
        is_wechat = 'MicroMessenger' in ua

        # 如果携带了Authorization，可以直接走解析逻辑
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            decoded, err = verify_token()
            if not err:
                # 复用解析逻辑
                with app.app_context():
                    # 建立监督关系
                    supervisor_user = UserService.query_user_by_openid(
                        decoded.get('openid'))
                    with db.get_session() as session:
                        relation = session.query(SupervisionRuleRelation).filter_by(
                            solo_user_id=link.solo_user_id,
                            supervisor_user_id=supervisor_user.user_id,
                            rule_id=link.rule_id
                        ).first()
                        if not relation:
                            relation = SupervisionRuleRelation(
                                solo_user_id=link.solo_user_id,
                                supervisor_user_id=supervisor_user.user_id,
                                rule_id=link.rule_id,
                                status=2
                            )
                            session.add(relation)
                        else:
                            relation.status = 2
                            relation.updated_at = datetime.now()
                        session.commit()
                rule = query_checkin_rule_by_id(link.rule_id)
                return make_succ_response({
                    'message': '解析成功',
                    'rule': {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'icon_url': rule.icon_url
                    },
                    'solo_user_id': link.solo_user_id
                })

        # 微信环境返回提示页面
        if is_wechat:
            mini_path = f"/pages/supervisor-detail/supervisor-detail?token={token}"
            html = f"""
            <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>打开打卡规则</title></head>
            <body>
            <p>请在微信小程序中打开以下路径：</p>
            <pre>{mini_path}</pre>
            </body></html>
            """
            return html

        # 非微信环境返回基础提示
        base = request.host_url.rstrip('/')
        front_url = f"{base}/#/supervisor-detail?token={token}"
        html = f"""
        <html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>打开打卡规则</title></head>
        <body>
        <p>请在前端页面打开规则详情：</p>
        <a href='{front_url}'>{front_url}</a>
        </body></html>
        """
        return html
    except Exception as e:
        app.logger.error(f'分享页面处理失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'分享页面处理失败: {str(e)}')