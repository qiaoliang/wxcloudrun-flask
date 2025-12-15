"""
用户管理视图模块
包含用户信息管理、用户搜索、账号绑定等功能
"""

import logging
import os
import datetime
import jwt
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.user_service import UserService
from database import get_database
from database.models import User, SupervisionRuleRelation
from wxcloudrun.utils.auth import verify_token
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _hash_code

# 获取数据库实例
db = get_database()


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
from wxcloudrun.decorators import login_required
from config_manager import get_token_secret

app_logger = logging.getLogger('log')


def _merge_accounts_by_time(account1, account2):
    """按注册时间合并账号，保留较早的账号"""
    import time
    app.logger.info(f'开始合并账号: {account1.user_id} 和 {account2.user_id}')
    
    if account1.created_at < account2.created_at:
        primary, secondary = account1, account2
        app.logger.info(f'保留主账号: {primary.user_id} (创建时间: {primary.created_at})')
    else:
        primary, secondary = account2, account1
        app.logger.info(f'保留主账号: {primary.user_id} (创建时间: {primary.created_at})')
    
    # 先保存需要迁移的信息
    migrate_wechat_openid = secondary.wechat_openid if not primary.wechat_openid else None
    migrate_phone_hash = secondary.phone_hash if not primary.phone_hash else None
    migrate_phone_number = secondary.phone_number if not primary.phone_hash else None
    
    app.logger.info(f'准备迁移信息 - wechat_openid: {migrate_wechat_openid}, phone_hash: {migrate_phone_hash}')
    
    with db.get_session() as session:
        # 清空次要账号的唯一字段
        secondary.wechat_openid = f"disabled_{secondary.user_id}_{int(time.time())}"
        secondary.phone_hash = f"disabled_{secondary.user_id}_{int(time.time())}"
        secondary.phone_number = None
        session.flush()  # 刷新到数据库但不提交
        
        # 更新主账号信息
        if migrate_wechat_openid:
            primary.wechat_openid = migrate_wechat_openid
            app.logger.info(f'主账号已更新wechat_openid')
        if migrate_phone_hash:
            primary.phone_hash = migrate_phone_hash
            primary.phone_number = migrate_phone_number
            app.logger.info(f'主账号已更新phone_hash和phone_number')
        
        # 迁移数据
        _migrate_user_data(secondary.user_id, primary.user_id)
        app.logger.info(f'数据迁移完成')
        
        # 禁用次要账号
        secondary.status = 2
        session.commit()
    
    app.logger.info(f'账号合并完成: 主账号 {primary.user_id}, 次账号 {secondary.user_id} 已禁用')
    return primary


def _migrate_user_data(src_user_id, dst_user_id):
    """改进的数据迁移函数，增加事务处理和冲突解决"""
    try:
        from database.models import CheckinRule, CheckinRecord
        
        # 迁移打卡规则（排除已删除的）
        rules = CheckinRule.query.filter(
            CheckinRule.solo_user_id == src_user_id,
            CheckinRule.status != 2
        ).all()
        for r in rules:
            # 检查是否已存在同名规则
            existing_rule = CheckinRule.query.filter(
                CheckinRule.solo_user_id == dst_user_id,
                CheckinRule.rule_name == r.rule_name,
                CheckinRule.status != 2
            ).first()
            if not existing_rule:
                r.solo_user_id = dst_user_id
        
        # 迁移打卡记录
        records = CheckinRecord.query.filter(
            CheckinRecord.solo_user_id == src_user_id
        ).all()
        for rec in records:
            rec.solo_user_id = dst_user_id
        
        # 迁移监护关系（作为被监护人）
        rels = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == src_user_id
        ).all()
        for rel in rels:
            # 检查是否已存在相同关系
            existing_rel = SupervisionRuleRelation.query.filter(
                SupervisionRuleRelation.solo_user_id == dst_user_id,
                SupervisionRuleRelation.supervisor_user_id == rel.supervisor_user_id,
                SupervisionRuleRelation.status != 2
            ).first()
            if not existing_rel:
                rel.solo_user_id = dst_user_id
        
        # 迁移监护关系（作为监护人）
        rels2 = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.supervisor_user_id == src_user_id
        ).all()
        for rel in rels2:
            # 检查是否已存在相同关系
            existing_rel = SupervisionRuleRelation.query.filter(
                SupervisionRuleRelation.solo_user_id == rel.solo_user_id,
                SupervisionRuleRelation.supervisor_user_id == dst_user_id,
                SupervisionRuleRelation.status != 2
            ).first()
            if not existing_rel:
                rel.supervisor_user_id = dst_user_id
        
        # 移除commit调用，由调用方控制事务
    except Exception as e:
        app.logger.error(f'数据迁移失败: {str(e)}', exc_info=True)
        raise e


@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    """
    用户信息接口，支持获取和更新用户信息
    GET: 获取用户信息
    POST: 更新用户信息
    """
    app.logger.info('=== 开始执行用户信息接口 ===')
    app.logger.info(f'请求方法: {request.method}')
    app.logger.info(f'请求头信息: {dict(request.headers)}')
    app.logger.info('准备获取请求体参数...')

    # 获取请求体参数 - 对于GET请求，通常没有请求体
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:  # 只对有请求体的方法获取JSON
            params = request.get_json() if request.is_json else {}
        else:
            params = {}  # GET请求通常没有请求体
    except Exception as e:
        app.logger.warning(f'解析请求JSON失败: {str(e)}')
        params = {}
    app.logger.info(f'请求体参数: {params}')

    # 验证token
    auth_header = request.headers.get('Authorization', '')
    app.logger.info(f'原始Authorization头: {auth_header}')
    if auth_header.startswith('Bearer '):
        header_token = auth_header[7:]  # 去掉 'Bearer ' 前缀
        app.logger.info(f'去掉Bearer前缀后的token: {header_token}')
    else:
        header_token = auth_header
        app.logger.info(f'未找到Bearer前缀，直接使用Authorization头: {header_token}')
    token = params.get('token') or header_token

    app.logger.info(f'最终使用的token: {token}')

    # 打印传入的token用于调试
    app.logger.info(f'从请求中获取的token: {token}')
    app.logger.info(f'Authorization header完整内容: {auth_header}')

    if not token:
        app.logger.warning('请求中缺少token参数')
        return make_err_response({}, '缺少token参数')

    try:
        app.logger.info(f'开始处理token解码，原始token: {token}')
        # 解码token
        # 检查token是否包含额外的引号并去除
        if token and token.startswith('"') and token.endswith('"'):
            app.logger.info('检测到token包含额外引号，正在去除...')
            token = token[1:-1]  # 去除首尾的引号
            app.logger.info(f'去除引号后的token: {token[:50]}...')
        else:
            app.logger.info(f'token不包含额外引号或为空，无需处理')

        # 从配置管理器获取TOKEN_SECRET确保编码和解码使用相同的密钥
        try:
            token_secret = get_token_secret()
        except ValueError as e:
            app.logger.error(f'获取TOKEN_SECRET失败: {str(e)}')
            return make_err_response({}, '服务器配置错误')

        app.logger.info(
            f'用于解码的TOKEN_SECRET: {token_secret[:20]}...')  # 只显示前20个字符
        app.logger.info(f'准备解码token: {token[:50]}...')

        # 解码token，启用过期验证
        decoded = jwt.decode(
            token,
            token_secret,
            algorithms=['HS256']
        )
        app.logger.info(f'JWT解码成功，解码后的payload: {decoded}')
        openid = decoded.get('openid')
        app.logger.info(f'从解码结果中获取的openid: {openid}')

        if not openid:
            app.logger.error('解码后的token中未找到openid')
            return make_err_response({}, 'token无效')

        # 根据HTTP方法决定操作
        if request.method == 'GET':
            app.logger.info(f'处理GET请求 - 查询用户信息，openid: {openid}')
            # 查询用户信息
            user = UserService.query_user_by_openid(openid)
            app.logger.info(f'查询到的用户: {user}')
            if not user:
                app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
                return make_err_response({}, '用户不存在')

            # 返回用户信息
            app.logger.info(f'用户数据库信息 - user_id: {user.user_id}, nickname: {user.nickname}, avatar_url: {user.avatar_url}')
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'role': user.role_name,  # 返回字符串形式的角色名
                'community_id': user.community_id,
                'status': user.status_name,  # 返回字符串形式的状态名
                'is_community_worker': getattr(user, 'is_community_worker', False)
            }
            app.logger.info(f'返回的用户数据: {user_data}')

            app.logger.info(f'成功查询到用户信息，用户ID: {user.user_id}，准备返回响应')
            return make_succ_response(user_data)

        elif request.method == 'POST':
            app.logger.info(f'POST请求 - 更新用户信息，openid: {openid}')
            # 查询用户
            user = UserService.query_user_by_openid(openid)
            if not user:
                app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
                return make_err_response({}, '用户不存在')

            # 获取可更新的用户信息（只更新非空字段）
            nickname = params.get('nickname')
            avatar_url = params.get('avatar_url')
            phone_number = params.get('phone_number')
            role = params.get('role')
            community_id = params.get('community_id')
            status = params.get('status')
            # 权限组合字段
            is_community_worker = params.get('is_community_worker')

            app.logger.info(
                f'待更新的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}, phone_number: {phone_number}, role: {role}')

            # 更新用户信息到数据库
            if nickname is not None:
                app.logger.info(f'更新nickname: {user.nickname} -> {nickname}')
                user.nickname = nickname
            if avatar_url is not None:
                app.logger.info(
                    f'更新avatar_url: {user.avatar_url} -> {avatar_url}')
                user.avatar_url = avatar_url
            if phone_number is not None:
                app.logger.info(
                    f'更新phone_number: {user.phone_number} -> {phone_number}')
                user.phone_number = phone_number
            if role is not None:
                app.logger.info(f'更新role: {user.role} -> {role}')
                # 如果传入的是字符串，转换为对应的整数值
                if isinstance(role, str):
                    role_value = User.get_role_value(role)
                    if role_value is not None:
                        user.role = role_value
                elif isinstance(role, int):
                    user.role = role
            # 更新权限组合字段
            if is_community_worker is not None:
                app.logger.info(
                    f'更新is_community_worker: {user.is_community_worker} -> {is_community_worker}')
                user.is_community_worker = bool(is_community_worker)
            if community_id is not None:
                app.logger.info(
                    f'更新community_id: {user.community_id} -> {community_id}')
                user.community_id = community_id
            if status is not None:
                app.logger.info(f'更新status: {user.status} -> {status}')
                # 如果传入的是字符串，转换为对应的整数值
                if isinstance(status, str):
                    status_value = User.get_status_value(status)
                    if status_value is not None:
                        user.status = status_value
                elif isinstance(status, int):
                    user.status = status
            user.updated_at = datetime.datetime.now()

            # 保存到数据库
            UserService.update_user_by_id(user)

            app.logger.info(f'用户 {openid} 信息更新成功')

            return make_succ_response({'message': '用户信息更新成功'})
        else:
            # 处理不支持的HTTP方法
            app.logger.warning(f'不支持的HTTP方法: {request.method}')
            return make_err_response({}, f'不支持的HTTP方法: {request.method}')

    except jwt.ExpiredSignatureError as e:
        app.logger.error(f'token已过期: {str(e)}')
        return make_err_response({}, 'token已过期')
    except jwt.InvalidSignatureError as e:
        error_subclass = type(e).__name__
        app.logger.error(f"❌  InvalidSignatureError 实际异常子类：{error_subclass}")
        app.logger.error(f"InvalidSignatureError 详细描述：{str(e)}")
        app.logger.error(f'token签名验证失败: {str(e)}')
        app.logger.error('可能原因：TOKEN_SECRET配置不一致、token被篡改或格式错误')
        return make_err_response({}, 'token签名无效')
    except jwt.DecodeError as e:
        # 捕获更详细的 DecodeError 的子类错误，打印详细信息
        # 关键代码：获取实际子类名称
        error_subclass = type(e).__name__
        app.logger.error(f"❌ 实际异常子类：{error_subclass}")
        app.logger.error(f"详细描述：{str(e)}")

        app.logger.error(f'token解码失败: {str(e)}')
        app.logger.error('可能原因：token格式错误（非标准JWT格式）、token被截断或包含非法字符')
        # 额外调试信息
        app.logger.info(f'尝试解析的token长度: {len(token) if token else 0}')
        if token:
            token_parts = token.split('.')
            app.logger.info(f'token段数: {len(token_parts)}')
            if len(token_parts) >= 2:
                import base64
                try:
                    # 尝试解码header部分查看格式
                    header_part = token_parts[0]
                    # 补齐Base64 padding
                    missing_padding = len(header_part) % 4
                    if missing_padding:
                        header_part += '=' * (4 - missing_padding)
                    header_decoded = base64.urlsafe_b64decode(header_part)
                    app.logger.info(
                        f'token header解码成功: {header_decoded.decode("utf-8")}')
                except Exception as decode_err:
                    app.logger.error(f'token header解码失败: {str(decode_err)}')
        return make_err_response({}, 'token格式错误')
    except jwt.InvalidTokenError as e:
        app.logger.error(f'token无效: {str(e)}')
        return make_err_response({}, 'token无效')
    except Exception as e:
        app.logger.error(f'处理用户信息时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'处理用户信息失败: {str(e)}')

    app.logger.info('=== 用户信息接口执行完成 ===')


@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users(decoded):
    """
    根据关键词搜索用户（支持昵称和手机号），支持scope参数
    参数：keyword（关键词），scope（搜索范围：all/community），community_id（社区ID，scope=community时必需），limit（可选，默认10）
    """
    try:
        params = request.args
        keyword = params.get('keyword', '').strip()
        # 兼容旧的nickname参数
        if not keyword:
            keyword = params.get('nickname', '').strip()
        
        scope = params.get('scope', 'all')
        community_id = params.get('community_id')
        limit = int(params.get('limit', 10))

        if not keyword or len(keyword) < 1:
            return make_succ_response({'users': []})

        # 验证scope参数
        if scope not in ['all', 'community']:
            return make_err_response({}, 'Invalid scope parameter')

        # 验证community scope的community_id参数
        if scope == 'community' and not community_id:
            return make_err_response({}, 'Community ID required for community scope')

        # 当前用户
        openid = decoded.get('openid')
        # 使用当前会话查询用户，避免会话问题
        current_user = User.query.filter(User.wechat_openid == openid).first()
        if not current_user:
            return make_err_response({}, '用户不存在')

        # 权限验证
        if scope == 'all' and current_user.role != 4:
            return make_err_response({}, 'Only super admin can search all users')

        if scope == 'community':
            # 检查用户是否有该社区的管理权限
            if not current_user.can_manage_community(int(community_id)):
                return make_err_response({}, 'No permission for this community')

        # 构建查询条件
        # 检查是否是完整手机号（11位数字）
        import re
        is_full_phone = re.match(r'^1[3-9]\d{9}$', keyword)
        
        if is_full_phone:
            # 如果是完整手机号，使用phone_hash进行精确匹配
            phone_hash = _calculate_phone_hash(keyword)
            
            # 只使用phone_hash进行搜索，不再搜索昵称
            # 因为完整手机号搜索应该精确匹配
            query = User.query.filter(
                User.phone_hash == phone_hash,
                User.user_id != current_user.user_id
            )
        else:
            # 只搜索昵称，不搜索部分手机号
            # 因为部分手机号会导致错误匹配
            query = User.query.filter(
                User.nickname.ilike(f'%{keyword}%'),
                User.user_id != current_user.user_id
            )

        # 根据scope限制搜索范围
        if scope == 'community':
            from database.models import CommunityStaff
            query = query.join(CommunityStaff, User.user_id == CommunityStaff.user_id).filter(
                CommunityStaff.community_id == int(community_id)
            )

        # 执行搜索
        users = query.order_by(User.updated_at.desc()).limit(limit).all()

        result = []
        for u in users:
            # 计算是否具备监护能力（已有任意已批准监督关系）
            is_supervisor_flag = False
            # 检查是否有已批准的监督关系
            rel_exists = SupervisionRuleRelation.query.filter(
                SupervisionRuleRelation.supervisor_user_id == u.user_id,
                SupervisionRuleRelation.status == 2
            ).first()
            is_supervisor_flag = rel_exists is not None

            result.append({
                'user_id': u.user_id,
                'nickname': u.nickname,
                'phone_number': u.phone_number,
                'avatar_url': u.avatar_url,
                'is_supervisor': is_supervisor_flag
            })

        return make_succ_response({'users': result})
    except Exception as e:
        app.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'搜索用户失败: {str(e)}')


@app.route('/api/user/bind_phone', methods=['POST'])
@login_required
def bind_phone(decoded):
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        code = params.get('code')
        if not phone or not code:
            return make_err_response({}, '缺少phone或code参数')
        if not _verify_sms_code(phone, 'bind_phone', code):
            return make_err_response({}, '验证码无效或已过期')
        current_user = UserService.query_user_by_openid(decoded.get('openid'))
        if not current_user:
            return make_err_response({}, '用户不存在')
        
        from hashlib import sha256
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        target = User.query.filter_by(phone_hash=phone_hash).first()
        if target and target.user_id != current_user.user_id:
            primary = _merge_accounts_by_time(current_user, target)
            _audit(current_user.user_id, 'bind_phone', {'phone': phone})
            return make_succ_response({'message': '绑定手机号成功，账号已合并'})
        
        # 直接更新用户信息，避免嵌套事务问题
        current_user.phone_hash = phone_hash
        current_user.phone_number = phone[:3] + '****' + \
            phone[-4:] if len(phone) >= 7 else phone
        current_user.updated_at = datetime.datetime.now()
        
        with db.get_session() as session:
            session.commit()
        _audit(current_user.user_id, 'bind_phone', {'phone': phone})
        return make_succ_response({'message': '绑定手机号成功'})
    except Exception as e:
        with db.get_session() as session:
            session.rollback()
        app.logger.error(f'绑定手机号失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'绑定手机号失败: {str(e)}')


@app.route('/api/user/bind_wechat', methods=['POST'])
@login_required
def bind_wechat(decoded):
    try:
        with db.get_session() as session:
            with session.begin_nested():
                params = request.get_json() or {}
                wx_code = params.get('code')
                phone_code = params.get('phone_code')
                phone = params.get('phone')
            if not wx_code:
                return make_err_response({}, '缺少code参数')
            if phone and not _verify_sms_code(phone, 'bind_wechat', phone_code or ''):
                return make_err_response({}, '手机号验证码无效或已过期')
            from .wxchat_api import get_user_info_by_code
            wx_data = get_user_info_by_code(wx_code)
            if 'errcode' in wx_data:
                return make_err_response({}, f"微信API错误: {wx_data.get('errmsg', '未知错误')}")
            openid = wx_data.get('openid')
            if not openid:
                return make_err_response({}, '微信返回数据不完整')
            current_user = UserService.query_user_by_openid(decoded.get('openid'))
            if not current_user:
                return make_err_response({}, '用户不存在')
            existing_wechat = UserService.query_user_by_openid(openid)
            if existing_wechat and existing_wechat.user_id != current_user.user_id:
                primary = _merge_accounts_by_time(current_user, existing_wechat)
                _audit(existing_wechat.user_id, 'bind_wechat_merge', {'from_user_id': current_user.user_id})
                return make_succ_response({'message': '绑定微信成功，账号已合并'})
            current_user.wechat_openid = openid
            UserService.update_user_by_id(current_user)
            _audit(current_user.user_id, 'bind_wechat', {'openid': openid})
            return make_succ_response({'message': '绑定微信成功'})
    except Exception as e:
        with db.get_session() as session:
            session.rollback()
        app.logger.error(f'绑定微信失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'绑定微信失败: {str(e)}')


@app.route('/api/community/verify', methods=['POST'])
def community_verify():
    """
    社区工作人员身份验证接口
    """
    app.logger.info('=== 开始执行社区工作人员身份验证接口 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        name = params.get('name')
        work_id = params.get('workId')  # 注意：前端使用驼峰命名
        work_proof = params.get('workProof')  # 工作证明照片URL或base64

        if not name or not work_id or not work_proof:
            return make_err_response({}, '缺少必要参数：姓名、工号或工作证明')

        # 这里应该实现身份验证逻辑
        # 1. 保存验证信息到数据库
        # 2. 设置用户验证状态
        # 3. 模拟验证过程

        # 更新用户信息，设置验证状态
        user.name = name  # 添加姓名字段（如果模型中没有需要扩展）
        user.work_id = work_id  # 添加工号字段（如果模型中没有需要扩展）
        user.verification_status = 1  # 设置为待审核状态
        user.verification_materials = work_proof  # 保存验证材料
        user.updated_at = datetime.datetime.now()

        UserService.update_user_by_id(user)

        response_data = {
            'message': '身份验证申请已提交，请耐心等待审核',
            'verification_status': 'pending'
        }

        app.logger.info(f'用户 {user.user_id} 身份验证申请已提交')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'身份验证时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'身份验证失败: {str(e)}')


# 扩展User模型以支持身份验证相关字段
# 注意：由于无法直接修改已导入的模型，我们在数据库层面处理


def add_verification_fields():
    """
    为用户表添加身份验证相关字段
    """
    try:
        # 检查并添加必要的字段
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # 检查是否已存在验证相关字段
            # 添加姓名字段
            try:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN name VARCHAR(100) COMMENT '真实姓名'"))
            except:
                pass  # 字段可能已存在

            # 添加工号字段
            try:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN work_id VARCHAR(50) COMMENT '工号或身份证号'"))
            except:
                pass  # 字段可能已存在

            # 添加验证状态字段
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN verification_status INTEGER DEFAULT 0 COMMENT '验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝'"))
            except:
                pass  # 字段可能已存在

            # 添加验证材料字段
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN verification_materials TEXT COMMENT '验证材料URL'"))
            except:
                pass  # 字段可能已存在

            conn.commit()
    except Exception as e:
        app.logger.error(f'添加验证字段时发生错误: {str(e)}')

# 在应用启动后初始化验证字段
# with app.app_context():
#     init_verification_fields()
