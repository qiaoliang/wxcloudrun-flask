"""
监督功能视图模块
包含监督关系管理、监督邀请、监督记录查看等功能
"""

import logging
from datetime import datetime, date, time, timedelta
from flask import request, current_app
from sqlalchemy import select
from . import supervision_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from app.shared.utils.route_helpers import execute_use_case, get_json_params
from app.application.use_cases.supervision import (
    GetUserByIdUseCase,
    GetUserByOpenIdUseCase,
    GetCheckinRuleByIdUseCase,
    SendInternalInvitationUseCase,
    InvitationManagementUseCase,
    GetSupervisedUsersUseCase,
    GetGuardiansUseCase,
    GetSupervisionRecordsUseCase,
    GetTodaySupervisionDataUseCase,
    CreateSupervisionInviteLinkUseCase,
    ResolveSupervisionInviteLinkUseCase,
    AcceptSupervisionUseCase,
    RejectSupervisionUseCase,
    SendReminderUseCase
)
# 移除 db 直接访问，改用 UseCase
# from database.flask_models import db, SupervisionRuleRelation, CheckinRecord, CheckinRule
from app.shared.utils.transaction import transaction

app_logger = logging.getLogger('log')


@supervision_bp.route('/supervision/invite/internal', methods=['POST'])
@login_required
def invite_supervisor_internal(decoded):
    """
    站内邀请监督者接口 - 通过搜索用户并直接发送邀请
    请求体：{ rule_id, receiver_ids: [], message: '' }
    返回：{ sender_id, receiver_ids, rule_id, relation_ids, invitation_type, status, expires_at }
    """
    current_app.logger.info('=== 开始执行站内邀请监督者接口 ===')

    user_id = decoded.get('user_id')

    try:
        # 使用辅助函数获取并验证请求参数
        params, error_msg = get_json_params(required_fields=['rule_id'])
        if error_msg:
            return make_err_response({}, error_msg)

        rule_id = params.get('rule_id')
        receiver_ids = params.get('receiver_ids', [])
        message = params.get('message', '')

        if not receiver_ids or len(receiver_ids) == 0:
            return make_err_response({}, '缺少receiver_ids参数')

        # 使用辅助函数执行 UseCase
        result = execute_use_case(
            SendInternalInvitationUseCase,
            sender_id=user_id,
            rule_id=rule_id,
            receiver_ids=receiver_ids,
            message=message
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user_id} 成功向 {len(receiver_ids)} 个用户发送站内邀请')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'站内邀请监督者失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'站内邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invite_link', methods=['POST'])
@login_required
def create_invite_link(decoded):
    """
    创建监督邀请链接接口
    """
    current_app.logger.info('=== 开始创建监督邀请链接 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        params = request.get_json()
        rule_ids = params.get('rule_ids', [])
        expire_hours = params.get('expire_hours', 24)  # 默认24小时过期

        if not rule_ids:
            return make_err_response({}, '缺少rule_ids参数')

        # 使用 CreateSupervisionInviteLinkUseCase 创建邀请链接
        use_case = CreateSupervisionInviteLinkUseCase()
        result = use_case.execute(
            user_id=user.user_id,
            rule_ids=rule_ids,
            expire_hours=expire_hours
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'用户 {user.user_id} 创建监督邀请链接成功，token: {result.data.get("token")}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'创建邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建邀请链接失败: {str(e)}')


@supervision_bp.route('/supervision/invite/resolve', methods=['GET'])
def resolve_invite_link():
    """
    解析监督邀请链接接口
    """
    current_app.logger.info('=== 开始解析监督邀请链接 ===')

    try:
        invite_token = request.args.get('token')
        if not invite_token:
            return make_err_response({}, '缺少token参数')

        # 使用 ResolveSupervisionInviteLinkUseCase 解析邀请链接
        use_case = ResolveSupervisionInviteLinkUseCase()
        result = use_case.execute(invite_token=invite_token)

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'解析监督邀请链接成功，token: {invite_token}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'解析邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析邀请链接失败: {str(e)}')


@supervision_bp.route('/supervision/invitations', methods=['GET'])
@login_required
def get_supervision_invitations(decoded):
    """
    获取邀请列表接口
    查询参数：page（默认1）, limit（默认10）, status（可选）
    返回：{ invitations, total, page, limit, total_pages }
    """
    current_app.logger.info('=== 开始获取邀请列表 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status')

        # 转换状态参数
        status_value = None
        if status:
            try:
                status_value = int(status)
            except ValueError:
                return make_err_response({}, 'status参数格式错误')

        # 使用邀请管理用例获取邀请列表
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementUseCase()
        result = service.get_invitations(
            user_id=user.user_id,
            page=page,
            limit=limit,
            status=status_value
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取邀请列表成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取邀请列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取邀请列表失败: {str(e)}')


@supervision_bp.route('/supervision/sent-invitations', methods=['GET'])
@login_required
def get_sent_invitations(decoded):
    """
    获取用户发起的邀请列表接口（作为被监督人）
    查询参数：page（默认1）, limit（默认10）, status（可选）
    返回：{ invitations, total, page, limit, total_pages }
    """
    current_app.logger.info('=== 开始获取发起的邀请列表 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status')

        # 转换状态参数
        status_value = None
        if status:
            try:
                status_value = int(status)
            except ValueError:
                return make_err_response({}, 'status参数格式错误')

        # 使用邀请管理用例获取发起的邀请列表
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementUseCase()
        result = service.get_sent_invitations(
            user_id=user.user_id,
            page=page,
            limit=limit,
            status=status_value
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取发起的邀请列表成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取发起的邀请列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取发起的邀请列表失败: {str(e)}')


@supervision_bp.route('/supervision/accept', methods=['POST'])
@login_required
def accept_supervision(decoded):
    """
    接受监督邀请接口（已废弃，弃用日期: 2026-01-20）- 请使用 POST /api/supervision/invitations/<id>/accept
    请求体：{ relation_id }
    返回：{ relation_id, status }
    """
    from datetime import datetime

    current_app.logger.info('=== 开始接受监督邀请（已废弃） ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        params = request.get_json()
        relation_id = params.get('relation_id')
        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 使用 AcceptSupervisionUseCase 接受监督邀请
        use_case = AcceptSupervisionUseCase()
        result = use_case.execute(
            relation_id=relation_id,
            user_id=user.user_id
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'用户 {user.user_id} 接受监督邀请成功，关系ID: {relation_id}')

        # 添加 deprecation 警告
        response = make_succ_response(result.data)
        response.headers['Deprecation'] = 'Use POST /api/supervision/invitations/<id>/accept instead'
        response.headers['Warning'] = f'299 - "Deprecated API (since 2026-01-20): Use POST /api/supervision/invitations/{relation_id}/accept instead"'
        response.headers['X-Deprecated-Since'] = '2026-01-20'

        return response

    except Exception as e:
        current_app.logger.error(f'接受监督邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受监督邀请失败: {str(e)}')


@supervision_bp.route('/supervision/reject', methods=['POST'])
@login_required
def reject_supervision(decoded):
    """
    拒绝监督邀请接口（已废弃，弃用日期: 2026-01-20）- 请使用 POST /api/supervision/invitations/<id>/reject
    请求体：{ relation_id, reason }
    返回：{ message }
    """
    from datetime import datetime

    current_app.logger.info('=== 开始拒绝监督邀请（已废弃） ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        params = request.get_json()
        relation_id = params.get('relation_id')
        reason = params.get('reason', '')

        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 使用 RejectSupervisionUseCase 拒绝监督邀请
        use_case = RejectSupervisionUseCase()
        result = use_case.execute(
            relation_id=relation_id,
            user_id=user.user_id,
            reason=reason
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'用户 {user.user_id} 拒绝监督邀请，关系ID: {relation_id}，原因: {reason}')

        # 添加 deprecation 警告
        response = make_succ_response(result.data)
        response.headers['Deprecation'] = 'Use POST /api/supervision/invitations/<id>/reject instead'
        response.headers['Warning'] = f'299 - "Deprecated API (since 2026-01-20): Use POST /api/supervision/invitations/{relation_id}/reject instead"'
        response.headers['X-Deprecated-Since'] = '2026-01-20'

        return response

    except Exception as e:
        current_app.logger.error(f'拒绝监督邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'拒绝邀请失败: {str(e)}')


@supervision_bp.route('/supervision/my_supervised', methods=['GET'])
@login_required
def get_my_supervised_users(decoded):
    """
    获取我监督的用户列表接口
    """
    current_app.logger.info('=== 开始获取我监督的用户列表 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 使用应用服务用例获取被监督用户列表
        from app.application.use_cases.supervision import GetSupervisedUsersUseCase

        use_case = GetSupervisedUsersUseCase()
        result = use_case.execute(
            supervisor_id=user.user_id,
            page=page,
            page_size=per_page
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取监督用户列表成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取监督用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督用户列表失败: {str(e)}')


@supervision_bp.route('/supervision/my_guardians', methods=['GET'])
@login_required
def get_my_guardians(decoded):
    """
    获取监督我的用户列表接口
    """
    current_app.logger.info('=== 开始获取监督我的用户列表 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 使用应用服务用例获取监督者列表
        from app.application.use_cases.supervision import GetGuardiansUseCase

        use_case = GetGuardiansUseCase()
        result = use_case.execute(
            supervised_id=user.user_id,
            page=page,
            page_size=per_page
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取监督者列表成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取监督者列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督者列表失败: {str(e)}')


@supervision_bp.route('/supervision/records', methods=['GET'])
@login_required
def get_supervision_records(decoded):
    """
    获取监督记录接口
    """
    current_app.logger.info('=== 开始获取监督记录 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 使用应用服务用例获取监督记录
        from app.application.use_cases.supervision import GetSupervisionRecordsUseCase

        use_case = GetSupervisionRecordsUseCase()
        result = use_case.execute(
            user_id=user.user_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=per_page
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取监督记录成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取监督记录失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督记录失败: {str(e)}')


@supervision_bp.route('/supervision/today', methods=['GET'])
@login_required
def get_today_supervision_data(decoded):
    """
    获取今日监护数据接口
    参数：date（可选，格式：YYYY-MM-DD，默认为今天）
    返回：{ supervised_users: [...], date: "2026-01-13", pending_invitations_count }
    """
    current_app.logger.info('=== 开始获取今日监护数据 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取查询参数
        date_str = request.args.get('date')
        target_date = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return make_err_response({}, '日期格式错误，应为YYYY-MM-DD')

        # 使用应用服务用例获取今日监护数据
        from app.application.use_cases.supervision import GetTodaySupervisionDataUseCase

        use_case = GetTodaySupervisionDataUseCase()
        result = use_case.execute(
            supervisor_id=user.user_id,
            target_date=target_date
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 获取待处理邀请数量
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        invitation_service = InvitationManagementUseCase()
        pending_invitations_result = invitation_service.get_invitations(
            user_id=user.user_id,
            page=1,
            limit=1,  # 只需要获取总数，不需要具体数据
            status=1  # 1=待处理
        )

        # 获取待处理邀请总数
        pending_invitations_count = 0
        if pending_invitations_result.is_success:
            pending_invitations_count = pending_invitations_result.data.get('total', 0)

        # 在返回数据中添加待处理邀请数量
        result.data['pending_invitations_count'] = pending_invitations_count

        current_app.logger.info(f'用户 {user.user_id} 获取今日监护数据成功')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'获取今日监护数据失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日监护数据失败: {str(e)}')


@supervision_bp.route('/supervision/send_reminder', methods=['POST'])
@login_required
def send_reminder(decoded):
    """
    发送提醒接口
    请求体：{ supervised_user_id, rule_id, template_type, template_content }
    返回：{ message_id, sent_at }
    """
    current_app.logger.info('=== 开始发送提醒 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        params = request.get_json()
        supervised_user_id = params.get('supervised_user_id')
        rule_id = params.get('rule_id')
        template_type = params.get('template_type', 'default')
        template_content = params.get('template_content', '')

        if not supervised_user_id or not rule_id:
            return make_err_response({}, '缺少必要参数：supervised_user_id 和 rule_id')

        # 使用 SendReminderUseCase 发送提醒
        use_case = SendReminderUseCase()
        result = use_case.execute(
            user_id=user.user_id,
            supervised_user_id=supervised_user_id,
            rule_id=rule_id,
            template_type=template_type,
            template_content=template_content
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'发送提醒失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'发送提醒失败: {str(e)}')


# ==================== 站内邀请相关接口 ====================

@supervision_bp.route('/supervision/invitations/<int:invitation_id>/accept', methods=['POST'])
@login_required
def accept_invitation(decoded, invitation_id):
    """
    接受邀请接口
    路径参数：invitation_id
    返回：{ relation_id, status }
    """
    current_app.logger.info('=== 开始接受邀请 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 使用邀请管理用例接受邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementUseCase()
        result = service.accept_invitation(
            invitation_id=invitation_id,
            user_id=user.user_id
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 接受邀请成功，邀请ID: {invitation_id}')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'接受邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invitations/<int:invitation_id>/reject', methods=['POST'])
@login_required
def reject_invitation(decoded, invitation_id):
    """
    拒绝邀请接口
    路径参数：invitation_id
    请求体：{ reason }
    返回：{ message }
    """
    current_app.logger.info('=== 开始拒绝邀请 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取请求参数
        params = request.get_json() or {}
        reason = params.get('reason', '')

        # 使用邀请管理用例拒绝邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementUseCase()
        result = service.reject_invitation(
            invitation_id=invitation_id,
            user_id=user.user_id,
            reason=reason if reason else None
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 拒绝邀请成功，邀请ID: {invitation_id}')
            return make_succ_response({'message': result.message})
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'拒绝邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'拒绝邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invitations/<int:invitation_id>', methods=['DELETE'])
@login_required
def ignore_invitation(decoded, invitation_id):
    """
    忽略邀请接口
    路径参数：invitation_id
    返回：{ message }
    """
    current_app.logger.info('=== 开始忽略邀请 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 使用邀请管理用例忽略邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementUseCase()
        result = service.ignore_invitation(
            invitation_id=invitation_id,
            user_id=user.user_id
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 忽略邀请成功，邀请ID: {invitation_id}')
            return make_succ_response({'message': result.message})
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'忽略邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'忽略邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invitations/batch-accept', methods=['POST'])
@login_required
def batch_accept_invitations(decoded):
    """
    批量接受邀请接口
    请求体：{ invitation_ids }
    返回：{ accepted_count, failed_count }
    """
    current_app.logger.info('=== 开始批量接受邀请 ===')

    user_id = decoded.get('user_id')
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取请求参数
        params = request.get_json()
        invitation_ids = params.get('invitation_ids', [])

        if not invitation_ids or len(invitation_ids) == 0:
            return make_err_response({}, '缺少invitation_ids参数')

        # 使用邀请管理用例批量接受邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        service = InvitationManagementService()
        result = service.batch_accept_invitations(
            invitation_ids=invitation_ids,
            user_id=user.user_id
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 批量接受邀请成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'批量接受邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'批量接受邀请失败: {str(e)}')

@supervision_bp.route('/supervision/invitations/<int:invitation_id>/withdraw', methods=['POST'])
@login_required
def withdraw_invitation(decoded, invitation_id):
    """
    撤回邀请接口
    路径参数：invitation_id - 邀请ID
    返回：{ invitation_id, status, withdrawn_at }
    """
    current_app.logger.info('=== 开始撤回邀请 ===')

    user_id = decoded.get('user_id')

    try:
        # 使用邀请管理用例撤回邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        use_case = InvitationManagementUseCase()
        result = use_case.withdraw_invitation(
            invitation_id=invitation_id,
            operator_id=user_id
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user_id} 撤回邀请成功: invitation_id={invitation_id}')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'撤回邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'撤回邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invitations/batch-reject', methods=['POST'])
@login_required
def batch_reject_invitations(decoded):
    """
    批量拒绝邀请接口
    请求体：{ invitation_ids }
    返回：{ rejected_count, failed_count, failed_ids }
    """
    current_app.logger.info('=== 开始批量拒绝邀请 ===')

    user_id = decoded.get('user_id')

    try:
        # 获取请求参数
        params = request.get_json()
        invitation_ids = params.get('invitation_ids', [])

        if not invitation_ids or len(invitation_ids) == 0:
            return make_err_response({}, '缺少invitation_ids参数')

        # 使用邀请管理用例批量拒绝邀请
        from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase

        use_case = InvitationManagementUseCase()
        result = use_case.batch_reject_invitations(
            invitation_ids=invitation_ids,
            user_id=user_id
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user_id} 批量拒绝邀请成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'批量拒绝邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'批量拒绝邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invitations/pending-count', methods=['GET'])
@login_required
def get_pending_invitations_count(decoded):
    """
    获取待处理邀请数量接口
    返回：{ pending_count }
    """
    current_app.logger.info('=== 开始获取待处理邀请数量 ===')

    user_id = decoded.get('user_id')

    try:
        # 使用获取待处理邀请数量用例
        from app.application.use_cases.supervision.get_pending_invitations_count_use_case import GetPendingInvitationsCountUseCase

        use_case = GetPendingInvitationsCountUseCase()
        result = use_case.execute(user_id=user_id)

        if result.is_success:
            current_app.logger.info(f'用户 {user_id} 获取待处理邀请数量成功: count={result.data.get("pending_count", 0)}')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'获取待处理邀请数量失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取待处理邀请数量失败: {str(e)}')
