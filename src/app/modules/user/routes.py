"""
用户模块路由
包含用户信息管理、用户搜索、账号绑定等功能
"""

import logging
import os
import datetime
import jwt
from flask import request, current_app
from . import user_bp
from app.shared import make_succ_response, make_err_response
from wxcloudrun.user_service import UserService
from database.flask_models import db, User, SupervisionRuleRelation
from app.shared.utils.auth import verify_token
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _hash_code
from app.shared.decorators import login_required
from config_manager import get_token_secret

app_logger = logging.getLogger('log')


def _calculate_phone_hash(phone):
    """
    计算手机号的hash值

    Args:
        phone (str): 手机号

    Returns:
        str: 手机号的hash值
    """
    from hashlib import sha256
    phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
    return sha256(
        f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()


def _merge_accounts_by_time(account1, account2):
    """按注册时间合并账号，保留较早的账号"""
    import time
    current_app.logger.info(f'开始合并账号: {account1.user_id} 和 {account2.user_id}')

    if account1.created_at < account2.created_at:
        primary, secondary = account1, account2
        current_app.logger.info(f'保留主账号: {primary.user_id} (创建时间: {primary.created_at})')
    else:
        primary, secondary = account2, account1
        current_app.logger.info(f'保留主账号: {primary.user_id} (创建时间: {primary.created_at})')

    # 先保存需要迁移的信息
    migrate_info = {
        'wechat_openid': secondary.wechat_openid,
        'phone_number': secondary.phone_number,
        'nickname': secondary.nickname if secondary.nickname and len(secondary.nickname.strip()) > 0 else primary.nickname,
        'avatar_url': secondary.avatar_url if secondary.avatar_url else primary.avatar_url,
        'name': secondary.name if secondary.name else primary.name,
    }

    # 更新主账号信息
    if migrate_info['wechat_openid'] and not primary.wechat_openid:
        primary.wechat_openid = migrate_info['wechat_openid']
        current_app.logger.info(f'迁移微信openid到主账号: {migrate_info["wechat_openid"][:20]}...')
    
    if migrate_info['phone_number'] and not primary.phone_number:
        primary.phone_number = migrate_info['phone_number']
        current_app.logger.info(f'迁移手机号到主账号: {migrate_info["phone_number"]}')
    
    if migrate_info['nickname'] and migrate_info['nickname'] != primary.nickname:
        primary.nickname = migrate_info['nickname']
        current_app.logger.info(f'更新昵称: {migrate_info["nickname"]}')
    
    if migrate_info['avatar_url'] and migrate_info['avatar_url'] != primary.avatar_url:
        primary.avatar_url = migrate_info['avatar_url']
        current_app.logger.info(f'更新头像: {migrate_info["avatar_url"][:30]}...')
    
    if migrate_info['name'] and migrate_info['name'] != primary.name:
        primary.name = migrate_info['name']
        current_app.logger.info(f'更新姓名: {migrate_info["name"]}')

    # 迁移监督关系
    supervision_relations = SupervisionRuleRelation.query.filter_by(supervised_user_id=secondary.user_id).all()
    for relation in supervision_relations:
        # 检查是否已存在相同的监督关系
        existing = SupervisionRuleRelation.query.filter_by(
            supervisor_user_id=relation.supervisor_user_id,
            supervised_user_id=primary.user_id,
            rule_id=relation.rule_id
        ).first()
        
        if not existing:
            relation.supervised_user_id = primary.user_id
            current_app.logger.info(f'迁移监督关系: {relation.supervisor_user_id} -> {primary.user_id}')
        else:
            db.session.delete(relation)
            current_app.logger.info(f'删除重复的监督关系')

    # 删除次要账号
    db.session.delete(secondary)
    
    # 保存主账号更改
    db.session.commit()
    
    current_app.logger.info(f'账号合并完成，保留账号ID: {primary.user_id}')
    return primary


@user_bp.route('/profile', methods=['GET', 'POST'])
def user_profile():
    """
    用户信息获取和更新接口
    GET: 获取用户信息
    POST: 更新用户信息
    """
    current_app.logger.info('=== 开始执行用户信息接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    if request.method == 'GET':
        # 获取用户信息
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return make_err_response({}, '用户不存在')

            # 构造返回数据
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status
            }

            current_app.logger.info(f'获取用户信息成功: {user_id}')
            return make_succ_response(user_data)

        except Exception as e:
            current_app.logger.error(f'获取用户信息失败: {str(e)}', exc_info=True)
            return make_err_response({}, '获取用户信息失败')

    elif request.method == 'POST':
        # 更新用户信息
        try:
            params = request.get_json()
            if not params:
                return make_err_response({}, '缺少请求参数')

            user = UserService.get_user_by_id(user_id)
            if not user:
                return make_err_response({}, '用户不存在')

            # 更新允许的字段
            update_fields = ['nickname', 'name', 'avatar_url']
            updated = False

            for field in update_fields:
                if field in params and params[field] is not None:
                    if field == 'nickname' and params[field].strip():
                        # 昵称长度限制
                        nickname = params[field].strip()
                        if len(nickname) > 50:
                            nickname = nickname[:50] + "..."
                            current_app.logger.warning(f'昵称过长，截断处理: {params[field][:30]}... -> {nickname[:30]}...')
                        setattr(user, field, nickname)
                        updated = True
                    elif field in ['name', 'avatar_url']:
                        setattr(user, field, params[field])
                        updated = True

            if updated:
                UserService.update_user_by_id(user)
                current_app.logger.info(f'用户信息更新成功: {user_id}')
                return make_succ_response({'message': '更新成功'})
            else:
                current_app.logger.info('用户信息无变化')
                return make_succ_response({'message': '无需更新'})

        except Exception as e:
            current_app.logger.error(f'更新用户信息失败: {str(e)}', exc_info=True)
            return make_err_response({}, '更新用户信息失败')


@user_bp.route('/search', methods=['GET'])
@login_required
def search_users():
    """
    用户搜索接口
    支持按手机号、昵称搜索用户
    """
    current_app.logger.info('=== 开始执行用户搜索接口 ===')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        search_type = request.args.get('type', 'all')  # all, phone, nickname
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # 限制最大100条

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'搜索参数: keyword={keyword}, type={search_type}, page={page}, per_page={per_page}')

        # 执行搜索
        if search_type == 'phone':
            # 标准化手机号格式
            normalized_phone = keyword
            if len(normalized_phone) >= 7:
                normalized_phone = normalized_phone[:3] + '****' + normalized_phone[-4:]
            
            result = UserService.search_users_by_phone(normalized_phone, page, per_page)
        elif search_type == 'nickname':
            result = UserService.search_users_by_nickname(keyword, page, per_page)
        else:
            # 全局搜索
            result = UserService.search_users(keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["total"]} 条记录')

        # 构造返回数据
        users = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users.append(user_data)

        response_data = {
            'users': users,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'用户搜索失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@user_bp.route('/bind_phone', methods=['POST'])
def bind_phone():
    """
    绑定手机号接口
    """
    current_app.logger.info('=== 开始执行绑定手机号接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        phone = params.get('phone')
        code = params.get('code')

        if not phone or not code:
            return make_err_response({}, '缺少手机号或验证码')

        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        # 验证短信验证码
        if not _verify_sms_code(normalized_phone, 'bind_phone', code):
            return make_err_response({}, '验证码无效或已过期')

        user_id = decoded.get('user_id')
        user = UserService.get_user_by_id(user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        # 检查手机号是否已被绑定
        phone_hash = _calculate_phone_hash(normalized_phone)
        existing_user = UserService.query_user_by_phone_hash(phone_hash)
        
        if existing_user and existing_user.user_id != user_id:
            # 检查是否是同一用户的不同账号（微信账号和手机号账号）
            if existing_user.wechat_openid and user.wechat_openid:
                # 两个账号都有openid，不能合并
                return make_err_response({}, '该手机号已被其他用户绑定')
            else:
                # 合并账号
                current_app.logger.info(f'检测到同一用户的不同账号，开始合并: {user_id} 和 {existing_user.user_id}')
                merged_user = _merge_accounts_by_time(user, existing_user)
                
                # 记录审计日志
                _audit(merged_user.user_id, 'bind_phone_merge', {
                    'phone': normalized_phone,
                    'merged_user_id': existing_user.user_id,
                    'primary_user_id': user_id
                })
                
                return make_succ_response({
                    'message': '手机号绑定成功，已合并账号',
                    'user_id': merged_user.user_id
                })

        # 绑定手机号
        user.phone_number = normalized_phone
        UserService.update_user_by_id(user)

        # 记录审计日志
        _audit(user_id, 'bind_phone', {'phone': normalized_phone})

        current_app.logger.info(f'手机号绑定成功: user_id={user_id}, phone={normalized_phone}')
        return make_succ_response({'message': '绑定成功'})

    except Exception as e:
        current_app.logger.error(f'绑定手机号失败: {str(e)}', exc_info=True)
        return make_err_response({}, '绑定失败')


@user_bp.route('/bind_wechat', methods=['POST'])
def bind_wechat():
    """
    绑定微信账号接口
    """
    current_app.logger.info('=== 开始执行绑定微信账号接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        code = params.get('code')
        if not code:
            return make_err_response({}, '缺少code参数')

        user_id = decoded.get('user_id')
        user = UserService.get_user_by_id(user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        # 调用微信API获取用户信息
        from wxcloudrun.wxchat_api import get_user_info_by_code
        wx_data = get_user_info_by_code(code)

        if 'errcode' in wx_data:
            current_app.logger.error(f'微信API返回错误: {wx_data}')
            return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

        openid = wx_data.get('openid')
        if not openid:
            return make_err_response({}, '微信API返回数据不完整')

        # 检查openid是否已被绑定
        existing_user = UserService.query_user_by_openid(openid)
        
        if existing_user and existing_user.user_id != user_id:
            # 检查是否是同一用户的不同账号（微信账号和手机号账号）
            if existing_user.phone_number and user.phone_number:
                # 两个账号都有手机号，不能合并
                return make_err_response({}, '该微信账号已被其他用户绑定')
            else:
                # 合并账号
                current_app.logger.info(f'检测到同一用户的不同账号，开始合并: {user_id} 和 {existing_user.user_id}')
                merged_user = _merge_accounts_by_time(user, existing_user)
                
                # 记录审计日志
                _audit(merged_user.user_id, 'bind_wechat_merge', {
                    'openid': openid,
                    'merged_user_id': existing_user.user_id,
                    'primary_user_id': user_id
                })
                
                return make_succ_response({
                    'message': '微信账号绑定成功，已合并账号',
                    'user_id': merged_user.user_id
                })

        # 绑定微信账号
        user.wechat_openid = openid
        
        # 更新用户信息（如果提供了新的头像或昵称）
        nickname = params.get('nickname')
        avatar_url = params.get('avatar_url')
        
        if nickname and nickname.strip():
            user.nickname = nickname.strip()[:50]  # 限制长度
        if avatar_url and avatar_url.startswith(('http://', 'https://')):
            user.avatar_url = avatar_url
            
        UserService.update_user_by_id(user)

        # 记录审计日志
        _audit(user_id, 'bind_wechat', {'openid': openid})

        current_app.logger.info(f'微信账号绑定成功: user_id={user_id}, openid={openid[:20]}...')
        return make_succ_response({'message': '绑定成功'})

    except Exception as e:
        current_app.logger.error(f'绑定微信账号失败: {str(e)}', exc_info=True)
        return make_err_response({}, '绑定失败')


@user_bp.route('/community/verify', methods=['POST'])
def verify_community():
    """
    验证用户是否属于指定社区
    """
    current_app.logger.info('=== 开始执行社区验证接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        user_id = decoded.get('user_id')
        user = UserService.get_user_by_id(user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        # 验证社区成员关系
        from wxcloudrun.community_service import CommunityService
        is_member = CommunityService.verify_user_community_access(user_id, community_id)

        if is_member:
            response_data = {
                'is_member': True,
                'community_id': community_id,
                'user_role': user.role_name
            }
        else:
            response_data = {
                'is_member': False,
                'community_id': community_id
            }

        current_app.logger.info(f'社区验证结果: user_id={user_id}, community_id={community_id}, is_member={is_member}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'社区验证失败: {str(e)}', exc_info=True)
        return make_err_response({}, '验证失败')