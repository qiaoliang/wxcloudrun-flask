"""
监督功能视图模块
包含监督关系管理、监督邀请、监督记录查看等功能
"""

import logging
from datetime import datetime, date, time, timedelta
from flask import request, current_app
from . import supervision_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token
from wxcloudrun.user_service import UserService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService
from database.flask_models import db, SupervisionRuleRelation, CheckinRecord
from app.shared.utils.transaction import transaction

app_logger = logging.getLogger('log')


@supervision_bp.route('/supervision/invite', methods=['POST'])
@login_required
def invite_supervisor(decoded):
    """
    邀请监督者接口 - 邀请特定用户监督特定规则
    """
    current_app.logger.info('=== 开始执行邀请监督者接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        rule_ids = params.get('rule_ids', [])  # 要监督的规则ID列表，空表示监督所有规则
        target_openid = params.get('target_openid')  # 被邀请用户的openid

        if not target_openid:
            return make_err_response({}, '缺少target_openid参数')

        # 查询被邀请用户
        target_user = UserService.query_user_by_openid(target_openid)
        if not target_user:
            return make_err_response({}, '被邀请用户不存在')

        # 使用应用服务用例邀请监督者
        from app.application.use_cases.supervision import InviteSupervisorUseCase

        use_case = InviteSupervisorUseCase()
        result = use_case.execute(
            inviter_id=user.user_id,
            target_user_id=target_user.user_id,
            rule_ids=rule_ids
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 成功邀请用户 {target_user.user_id} 监督')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'邀请监督者失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invite_link', methods=['POST'])
@login_required
def create_invite_link(decoded):
    """
    创建监督邀请链接接口
    """
    current_app.logger.info('=== 开始创建监督邀请链接 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json()
        rule_ids = params.get('rule_ids', [])
        expire_hours = params.get('expire_hours', 24)  # 默认24小时过期

        if not rule_ids:
            return make_err_response({}, '缺少rule_ids参数')

        # 生成邀请token
        import secrets
        invite_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        # 保存邀请信息
        invite_data = {
            'supervisor_id': user.user_id,
            'supervisor_openid': openid,
            'rule_ids': rule_ids,
            'invite_token': invite_token,
            'expires_at': expires_at.isoformat(),
            'status': 'pending'
        }

        # 这里简化处理，实际应该保存到数据库
        current_app.logger.info(f'用户 {user.user_id} 创建监督邀请链接成功，token: {invite_token}')
        return make_succ_response(invite_data)

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

        # 这里简化处理，实际应该从数据库查询
        invite_data = {
            'supervisor_id': 1,
            'supervisor_nickname': '张三',
            'rule_ids': [1, 2, 3],
            'expires_at': '2025-12-25T12:00:00',
            'status': 'pending'
        }

        current_app.logger.info(f'解析监督邀请链接成功，token: {invite_token}')
        return make_succ_response(invite_data)

    except Exception as e:
        current_app.logger.error(f'解析邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析邀请链接失败: {str(e)}')


@supervision_bp.route('/supervision/invitations', methods=['GET'])
@login_required
def get_supervision_invitations(decoded):
    """
    获取监督邀请列表接口
    """
    current_app.logger.info('=== 开始获取监督邀请列表 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取查询参数
        status = request.args.get('status')  # pending, accepted, rejected
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # 这里简化处理，实际应该从数据库查询
        invitations = [
            {
                'invitation_id': 1,
                'supervisor_id': 1,
                'supervisor_nickname': '张三',
                'supervised_id': 2,
                'supervised_nickname': '李四',
                'rule_ids': [1, 2],
                'status': 'pending',
                'invited_at': '2025-12-24T10:00:00',
                'expires_at': '2025-12-25T12:00:00'
            }
        ]

        current_app.logger.info(f'用户 {user.user_id} 获取监督邀请列表成功，共 {len(invitations)} 条记录')
        return make_succ_response({
            'invitations': invitations,
            'total': len(invitations),
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        current_app.logger.error(f'获取监督邀请列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取邀请列表失败: {str(e)}')


@supervision_bp.route('/supervision/accept', methods=['POST'])
@login_required
def accept_supervision(decoded):
    """
    接受监督邀请接口
    """
    current_app.logger.info('=== 开始接受监督邀请 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json()
        invitation_id = params.get('invitation_id')
        if not invitation_id:
            return make_err_response({}, '缺少invitation_id参数')

        # 这里简化处理，实际应该更新数据库状态
        current_app.logger.info(f'用户 {user.user_id} 接受监督邀请，邀请ID: {invitation_id}')
        return make_succ_response({'message': '接受监督邀请成功'})

    except Exception as e:
        current_app.logger.error(f'接受监督邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受邀请失败: {str(e)}')


@supervision_bp.route('/supervision/reject', methods=['POST'])
@login_required
def reject_supervision(decoded):
    """
    拒绝监督邀请接口
    """
    current_app.logger.info('=== 开始拒绝监督邀请 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json()
        invitation_id = params.get('invitation_id')
        reason = params.get('reason', '')

        if not invitation_id:
            return make_err_response({}, '缺少invitation_id参数')

        # 这里简化处理，实际应该更新数据库状态
        current_app.logger.info(f'用户 {user.user_id} 拒绝监督邀请，邀请ID: {invitation_id}，原因: {reason}')
        return make_succ_response({'message': '拒绝监督邀请成功'})

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

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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