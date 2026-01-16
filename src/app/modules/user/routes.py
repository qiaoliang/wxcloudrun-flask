"""
用户模块路由
包含用户信息管理、用户搜索、账号绑定等功能
"""

import logging
import os
import datetime
import jwt
import json
from flask import request, current_app
from sqlalchemy import select, delete
from . import user_bp
from app.shared import make_succ_response, make_err_response
from database.flask_models import db, User, SupervisionRuleRelation, UserMedicalHistory
from app.shared.utils.auth import verify_token
from app.shared.utils.transaction import transaction
from wxcloudrun.utils.validators import _verify_sms_code, _audit, _hash_code, normalize_phone_number
from app.shared.decorators import login_required
from config import get_config
from error_code import INVALID_CAPTCHA

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





@user_bp.route('/user/profile', methods=['GET', 'POST'])
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
        current_app.logger.error(f'Token验证失败: {error_response}')
        return error_response

    user_id = decoded.get('user_id')
    openid = decoded.get('openid')
    current_app.logger.info(f'用户ID: {user_id}, OpenID: {openid}')
    current_app.logger.info(f'解码后的完整token信息: {decoded}')

    if request.method == 'GET':
        # 获取用户信息 - 使用 GetUserDetailsUseCase
        try:
            from app.application.use_cases.user import GetUserDetailsUseCase

            use_case = GetUserDetailsUseCase()
            result = use_case.execute(user_id)

            if result.is_success:
                current_app.logger.info(f'获取用户信息成功: user_id={user_id}')
                return make_succ_response(result.data)
            else:
                current_app.logger.error(f'获取用户信息失败: {result.message}')
                return make_err_response({}, result.message)

        except Exception as e:
            current_app.logger.error(f'获取用户信息失败: {str(e)}', exc_info=True)
            return make_err_response({}, '获取用户信息失败')

    elif request.method == 'POST':
        # 更新用户信息 - 使用 UpdateProfileUseCase
        try:
            params = request.get_json()
            if not params:
                return make_err_response({}, '缺少请求参数')

            # 使用应用服务用例更新用户信息
            from app.application.use_cases.user import UpdateProfileUseCase

            use_case = UpdateProfileUseCase()
            result = use_case.execute(
                user_id=user_id,
                nickname=params.get('nickname'),
                name=params.get('name'),
                avatar_url=params.get('avatar_url')
            )

            if result.is_success:
                return make_succ_response({'message': result.message})
            else:
                return make_err_response({}, result.message)

        except Exception as e:
            current_app.logger.error(f'更新用户信息失败: {str(e)}', exc_info=True)
            return make_err_response({}, '更新用户信息失败')


@user_bp.route('/user/upload-avatar', methods=['POST'])
@login_required
def upload_avatar(decoded):
    """
    上传用户头像
    """
    current_app.logger.info('=== 开始执行上传头像接口 ===')

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 检查是否有文件上传
        if 'avatar' not in request.files:
            return make_err_response({}, '未上传文件')

        file = request.files['avatar']
        if file.filename == '':
            return make_err_response({}, '未选择文件')

        # 验证文件类型
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not ('.' in file.filename and
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return make_err_response({}, '不支持的文件格式')

        # 验证文件大小（最大 5MB）
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > 5 * 1024 * 1024:
            return make_err_response({}, '文件大小超过限制（最大 5MB）')

        # 读取文件数据
        file_data = file.read()

        # 确定内容类型
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif'
        }
        content_type = content_type_map.get(file_extension, 'image/jpeg')

        # 使用应用服务用例上传头像
        from app.application.use_cases.user import UploadAvatarUseCase

        use_case = UploadAvatarUseCase()
        result = use_case.execute(
            user_id=user_id,
            file_data=file_data,
            file_name=file.filename,
            content_type=content_type
        )

        if result.is_success:
            return make_succ_response({
                'avatar_url': result.data.get('avatar_url'),
                'message': result.message
            })
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'上传头像失败: {str(e)}', exc_info=True)
        return make_err_response({}, '上传头像失败')


@user_bp.route('/user/change-password', methods=['POST'])
@login_required
def change_password(decoded):
    """
    修改用户密码
    """
    current_app.logger.info('=== 开始执行修改密码接口 ===')

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        old_password = params.get('old_password')
        new_password = params.get('new_password')

        # 使用应用服务用例修改密码
        from app.application.use_cases.user import ChangePasswordUseCase

        use_case = ChangePasswordUseCase()
        result = use_case.execute(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password
        )

        if result.is_success:
            return make_succ_response({'message': result.message})
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'修改密码失败: {str(e)}', exc_info=True)
        return make_err_response({}, '修改密码失败')


@user_bp.route('/user/search', methods=['GET'])
@login_required
def search_users(decoded):
    """
    用户搜索接口
    支持按手机号、昵称搜索用户
    支持社区过滤，用于添加专员时排除当前社区工作人员
    """
    current_app.logger.info('=== 开始执行用户搜索接口 ===')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # 限制最大100条
        community_id = request.args.get('community_id')  # 社区ID过滤参数
        role = request.args.get('role')  # 角色筛选参数

        if community_id:
            try:
                community_id = int(community_id)
            except ValueError:
                return make_err_response({}, '社区ID格式错误')

        if role:
            try:
                role = int(role)
            except ValueError:
                return make_err_response({}, '角色格式错误')

        # 使用应用服务用例搜索用户
        from app.application.use_cases.user import SearchUsersUseCase

        use_case = SearchUsersUseCase()
        result = use_case.execute(
            keyword=keyword,
            community_id=community_id,
            role=role,
            page=page,
            page_size=per_page
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'用户搜索失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@user_bp.route('/user/bind_phone', methods=['POST'])
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
            return make_err_response({}, 'INVALID_CAPTCHA')

        user_id = decoded.get('user_id')
        from app.application.use_cases.user import GetUserByIdUseCase
        get_user_use_case = GetUserByIdUseCase()
        get_user_result = get_user_use_case.execute(user_id)
        if not get_user_result.is_success:
            return make_err_response({}, '用户不存在')
        user = get_user_result.data

        # 检查手机号是否已被绑定
        phone_hash = _calculate_phone_hash(normalized_phone)
        from app.application.use_cases.user import GetUserByPhoneHashUseCase
        get_by_phone_use_case = GetUserByPhoneHashUseCase()
        existing_user_result = get_by_phone_use_case.execute(phone_hash)
        existing_user = existing_user_result.data if existing_user_result.is_success else None

        if existing_user and existing_user.user_id != user_id:
            # 检查是否是同一用户的不同账号（微信账号和手机号账号）
            if existing_user.wechat_openid and user.wechat_openid:
                # 两个账号都有openid，不能合并
                return make_err_response({}, '该手机号已被其他用户绑定')
            else:
                # 合并账号
                current_app.logger.info(f'检测到同一用户的不同账号，开始合并: {user_id} 和 {existing_user.user_id}')
                from app.application.use_cases.user import MergeAccountsUseCase
                merge_use_case = MergeAccountsUseCase()
                merge_result = merge_use_case.execute(user, existing_user)

                if not merge_result.is_success:
                    current_app.logger.error(f'合并账号失败: {merge_result.message}')
                    return make_err_response({}, f'合并账号失败: {merge_result.message}')

                merged_user_id = merge_result.data.get('primary_user_id')

                # 记录审计日志
                _audit(merged_user_id, 'bind_phone_merge', {
                    'phone': normalized_phone,
                    'merged_user_id': existing_user.user_id,
                    'primary_user_id': user_id
                })

                return make_succ_response({
                    'message': '手机号绑定成功，已合并账号',
                    'user_id': merged_user_id
                })

        # 绑定手机号
        user.phone_number = normalized_phone
        from app.application.use_cases.user import UpdateUserUseCase
        update_use_case = UpdateUserUseCase()
        update_result = update_use_case.execute(user)
        if not update_result.is_success:
            current_app.logger.warning(f'更新用户信息失败: {update_result.message}')

        # 记录审计日志
        _audit(user_id, 'bind_phone', {'phone': normalized_phone})

        current_app.logger.info(f'手机号绑定成功: user_id={user_id}, phone={normalized_phone}')
        return make_succ_response({'message': '绑定成功'})

    except Exception as e:
        current_app.logger.error(f'绑定手机号失败: {str(e)}', exc_info=True)
        return make_err_response({}, '绑定失败')


@user_bp.route('/user/bind_wechat', methods=['POST'])
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
        from app.application.use_cases.user import GetUserByIdUseCase
        get_user_use_case = GetUserByIdUseCase()
        get_user_result = get_user_use_case.execute(user_id)
        if not get_user_result.is_success:
            return make_err_response({}, '用户不存在')
        user = get_user_result.data

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
        from app.application.use_cases.user import GetUserByOpenidUseCase
        get_by_openid_use_case = GetUserByOpenidUseCase()
        existing_user_result = get_by_openid_use_case.execute(openid)
        existing_user = existing_user_result.data if existing_user_result.is_success else None

        if existing_user and existing_user.user_id != user_id:
            # 检查是否是同一用户的不同账号（微信账号和手机号账号）
            if existing_user.phone_number and user.phone_number:
                # 两个账号都有手机号，不能合并
                return make_err_response({}, '该微信账号已被其他用户绑定')
            else:
                # 合并账号
                current_app.logger.info(f'检测到同一用户的不同账号，开始合并: {user_id} 和 {existing_user.user_id}')
                from app.application.use_cases.user import MergeAccountsUseCase
                merge_use_case = MergeAccountsUseCase()
                merge_result = merge_use_case.execute(user, existing_user)

                if not merge_result.is_success:
                    current_app.logger.error(f'合并账号失败: {merge_result.message}')
                    return make_err_response({}, f'合并账号失败: {merge_result.message}')

                merged_user_id = merge_result.data.get('primary_user_id')

                # 记录审计日志
                _audit(merged_user_id, 'bind_wechat_merge', {
                    'openid': openid,
                    'merged_user_id': existing_user.user_id,
                    'primary_user_id': user_id
                })

                return make_succ_response({
                    'message': '微信账号绑定成功，已合并账号',
                    'user_id': merged_user_id
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

        from app.application.use_cases.user import UpdateUserUseCase
        update_use_case = UpdateUserUseCase()
        update_result = update_use_case.execute(user)
        if not update_result.is_success:
            current_app.logger.warning(f'更新用户信息失败: {update_result.message}')

        # 记录审计日志
        _audit(user_id, 'bind_wechat', {'openid': openid})

        current_app.logger.info(f'微信账号绑定成功: user_id={user_id}, openid={openid[:20]}...')
        return make_succ_response({'message': '绑定成功'})

    except Exception as e:
        current_app.logger.error(f'绑定微信账号失败: {str(e)}', exc_info=True)
        return make_err_response({}, '绑定失败')


@user_bp.route('/user/community/verify', methods=['POST'])
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
        from app.application.use_cases.user import GetUserByIdUseCase
        get_user_use_case = GetUserByIdUseCase()
        get_user_result = get_user_use_case.execute(user_id)
        if not get_user_result.is_success:
            return make_err_response({}, '用户不存在')
        user = get_user_result.data

        # 验证社区成员关系
        from app.application.use_cases.community import CheckCommunityPermissionUseCase
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        is_member = permission_result.data.get('has_permission', False) if permission_result.is_success else False

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


# ==================== 用户事件相关 API ====================

@user_bp.route('/user/my-active-event', methods=['GET'])
@login_required
def get_my_active_event(decoded):
    """获取用户当前进行中的事件"""
    try:
        user_id = decoded.get('user_id')

        from app.application.use_cases.events import GetUserActiveEventUseCase
        get_event_use_case = GetUserActiveEventUseCase()
        result = get_event_use_case.execute(user_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.message)

    except Exception as e:
        current_app.logger.error(f"获取用户进行中事件API异常: {str(e)}", exc_info=True)
        return make_err_response('服务器内部错误')


@user_bp.route('/user/events/<int:event_id>/messages', methods=['POST'])
@login_required
def add_event_message(decoded, event_id):
    """添加事件消息（支持文字/语音/图片）"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response('请求数据不能为空')

        user_id = decoded.get('user_id')
        message_type = data.get('message_type', 'text')
        content = data.get('content', '')
        media_url = data.get('media_url')
        media_duration = data.get('media_duration')

        # 验证消息类型
        if message_type not in ['text', 'voice', 'image']:
            return make_err_response('无效的消息类型')

        # 文字消息必须有内容
        if message_type == 'text' and not content.strip():
            return make_err_response('消息内容不能为空')

        # 语音和图片必须有媒体URL
        if message_type in ['voice', 'image'] and not media_url:
            return make_err_response('缺少媒体文件')

        from app.application.use_cases.events import AddEventMessageUseCase
        add_message_use_case = AddEventMessageUseCase()
        result = add_message_use_case.execute(
            event_id=event_id,
            user_id=user_id,
            message_type=message_type,
            content=content,
            media_url=media_url,
            media_duration=media_duration
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.message)

    except Exception as e:
        current_app.logger.error(f"添加事件消息API异常: {str(e)}", exc_info=True)
        return make_err_response('服务器内部错误')


@user_bp.route('/user/events/<int:event_id>/history', methods=['GET'])
@login_required
def get_event_history(decoded, event_id):
    """获取事件历史记录"""
    try:
        from app.application.use_cases.events import GetEventHistoryUseCase
        get_history_use_case = GetEventHistoryUseCase()
        result = get_history_use_case.execute(event_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response(result.message)

    except Exception as e:
        current_app.logger.error(f"获取事件历史API异常: {str(e)}", exc_info=True)
        return make_err_response('服务器内部错误')


# ==================== 病史管理相关 API ====================

@user_bp.route('/user/<int:user_id>/medical-history', methods=['GET'])
@login_required
def get_user_medical_history(decoded, user_id):
    """获取用户病史列表"""
    try:
        viewer_id = decoded.get('user_id')

        # 常见病史标签
        COMMON_CONDITIONS = [
            "高血压", "糖尿病", "心脏病", "冠心病", "脑卒中",
            "骨质疏松", "阿尔茨海默病", "帕金森病", "抑郁症",
            "失眠症", "关节炎", "白内障", "青光眼"
        ]

        # 获取病史记录
        stmt = select(UserMedicalHistory).where(
            UserMedicalHistory.user_id == user_id
        ).order_by(UserMedicalHistory.created_at.desc())

        histories = db.session.execute(stmt).scalars().all()

        # 权限过滤
        result = []
        for history in histories:
            history_dict = history.to_dict()

            # 检查权限
            can_view = False
            # 查看自己的病史
            if viewer_id == user_id:
                can_view = True
            elif history_dict['visibility'] == 1:
                # visibility=1: 仅工作人员可见
                # TODO: 检查 viewer_id 是否是工作人员
                can_view = True  # 暂时返回 True
            elif history_dict['visibility'] == 2:
                # visibility=2: 工作人员和监护人可见
                # TODO: 检查 viewer_id 是否是工作人员或监护人
                can_view = True  # 暂时返回 True

            if can_view:
                result.append(history_dict)

        return make_succ_response(result)
    except Exception as e:
        current_app.logger.error(f"获取用户病史列表失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取病史列表失败: {str(e)}')


@user_bp.route('/user/medical-history', methods=['POST'])
@login_required
def add_medical_history(decoded):
    """添加病史记录"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response({}, '缺少请求参数')

        user_id = data.get('user_id')
        condition_name = data.get('condition_name')
        treatment_plan = data.get('treatment_plan')
        visibility = data.get('visibility', 1)

        if not user_id or not condition_name:
            return make_err_response({}, '缺少必要参数')

        # 验证用户存在
        user = db.session.get(User, user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        # 创建病史记录
        history = UserMedicalHistory(
            user_id=user_id,
            condition_name=condition_name,
            treatment_plan=json.dumps(treatment_plan, ensure_ascii=False) if treatment_plan else None,
            visibility=visibility
        )

        db.session.add(history)
        db.session.flush()

        return make_succ_response(history.to_dict())
    except Exception as e:
        current_app.logger.error(f"添加病史记录失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'添加病史记录失败: {str(e)}')


@user_bp.route('/user/medical-history/<int:history_id>', methods=['PUT'])
@login_required
def update_medical_history(decoded, history_id):
    """更新病史记录"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response({}, '缺少请求参数')

        user_id = data.get('user_id')
        if not user_id:
            return make_err_response({}, '缺少用户ID')

        # 查询病史记录
        history = db.session.execute(
            select(UserMedicalHistory).where(
                UserMedicalHistory.id == history_id,
                UserMedicalHistory.user_id == user_id
            )
        ).scalar_one_or_none()

        if not history:
            return make_err_response({}, '病史记录不存在')

        # 更新字段
        if data.get('condition_name'):
            history.condition_name = data.get('condition_name')
        if data.get('treatment_plan') is not None:
            history.treatment_plan = json.dumps(data.get('treatment_plan'), ensure_ascii=False)
        if data.get('visibility') is not None:
            history.visibility = data.get('visibility')

        history.updated_at = datetime.datetime.now()
        db.session.flush()

        return make_succ_response(history.to_dict())
    except Exception as e:
        current_app.logger.error(f"更新病史记录失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'更新病史记录失败: {str(e)}')


@user_bp.route('/user/medical-history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_medical_history(decoded, history_id):
    """删除病史记录"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response({}, '缺少请求参数')

        user_id = data.get('user_id')
        if not user_id:
            return make_err_response({}, '缺少用户ID')

        # 查询病史记录
        history = db.session.execute(
            select(UserMedicalHistory).where(
                UserMedicalHistory.id == history_id,
                UserMedicalHistory.user_id == user_id
            )
        ).scalar_one_or_none()

        if not history:
            return make_err_response({}, '病史记录不存在')

        db.session.delete(history)
        db.session.flush()

        return make_succ_response({'success': True})
    except Exception as e:
        current_app.logger.error(f"删除病史记录失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'删除病史记录失败: {str(e)}')


@user_bp.route('/user/medical-history/common-conditions', methods=['GET'])
@login_required
def get_common_conditions(decoded):
    """获取常见病史标签"""
    try:
        # 常见病史标签
        COMMON_CONDITIONS = [
            "高血压", "糖尿病", "心脏病", "冠心病", "脑卒中",
            "骨质疏松", "阿尔茨海默病", "帕金森病", "抑郁症",
            "失眠症", "关节炎", "白内障", "青光眼"
        ]
        return make_succ_response({'conditions': COMMON_CONDITIONS})
    except Exception as e:
        current_app.logger.error(f"获取常见病史标签失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取常见病史标签失败: {str(e)}')


# ==================== 浏览记录相关 API ====================

@user_bp.route('/user/log-profile-view', methods=['POST'])
@login_required
def log_profile_view(decoded):
    """记录查看成员信息"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response({}, '缺少请求参数')

        viewer_id = decoded.get('user_id')
        viewed_user_id = data.get('viewed_user_id')
        community_id = data.get('community_id')

        if not viewed_user_id or not community_id:
            return make_err_response({}, '缺少必要参数')

        from app.application.use_cases.user import LogProfileViewUseCase
        log_view_use_case = LogProfileViewUseCase()
        log_result = log_view_use_case.execute(viewer_id, viewed_user_id, community_id)
        if not log_result.is_success:
            current_app.logger.warning(f'记录浏览信息失败: {log_result.message}')
        return make_succ_response({'message': '记录成功'})
    except Exception as e:
        current_app.logger.error(f"记录浏览信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'记录浏览信息失败: {str(e)}')


@user_bp.route('/user/log-view-guardian', methods=['POST'])
@login_required
def log_view_guardian(decoded):
    """记录查看监护人信息"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response({}, '缺少请求参数')

        viewer_id = decoded.get('user_id')
        guardian_id = data.get('guardian_id')
        ward_user_id = data.get('ward_user_id')
        community_id = data.get('community_id')

        if not guardian_id or not ward_user_id or not community_id:
            return make_err_response({}, '缺少必要参数')

        from app.application.use_cases.user import LogViewGuardianInfoUseCase
        log_guardian_use_case = LogViewGuardianInfoUseCase()
        log_result = log_guardian_use_case.execute(viewer_id, guardian_id, ward_user_id, community_id)
        if not log_result.is_success:
            current_app.logger.warning(f'记录查看监护人信息失败: {log_result.message}')
        return make_succ_response({'message': '记录成功'})
    except Exception as e:
        current_app.logger.error(f"记录查看监护人信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'记录查看监护人信息失败: {str(e)}')


@user_bp.route('/user/profile-view-logs', methods=['GET'])
@login_required
def get_profile_view_logs(decoded):
    """获取浏览记录列表"""
    try:
        community_id = request.args.get('community_id', type=int)
        viewer_id = request.args.get('viewer_id', type=int)
        limit = request.args.get('limit', 100, type=int)

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        from app.application.use_cases.user import GetProfileViewLogsUseCase
        get_logs_use_case = GetProfileViewLogsUseCase()
        logs_result = get_logs_use_case.execute(community_id, viewer_id, limit)
        if logs_result.is_success:
            return make_succ_response(logs_result.data)
        else:
            return make_err_response(logs_result.message)
    except Exception as e:
        current_app.logger.error(f"获取浏览记录列表失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取浏览记录列表失败: {str(e)}')