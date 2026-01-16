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
from app.application.use_cases.supervision import (
    GetUserByIdUseCase,
    GetUserByOpenIdUseCase,
    GetCheckinRuleByIdUseCase,
    SendInternalInvitationUseCase,
    InviteSupervisorUseCase,
    InvitationManagementService,
    GetSupervisedUsersUseCase,
    GetGuardiansUseCase,
    GetSupervisionRecordsUseCase,
    GetTodaySupervisionDataUseCase
)
from database.flask_models import db, SupervisionRuleRelation, CheckinRecord, CheckinRule
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
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    if not user_result.is_success:
        current_app.logger.error(f'数据库中未找到user_id为 {user_id} 的用户')
        return make_err_response({}, '用户不存在')
    user = user_result.data

    try:
        # 获取请求参数
        params = request.get_json()
        rule_id = params.get('rule_id')
        receiver_ids = params.get('receiver_ids', [])
        message = params.get('message', '')

        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        if not receiver_ids or len(receiver_ids) == 0:
            return make_err_response({}, '缺少receiver_ids参数')

        # 使用应用服务用例发送站内邀请
        from app.application.use_cases.supervision import SendInternalInvitationUseCase

        use_case = SendInternalInvitationUseCase()
        result = use_case.execute(
            sender_id=user.user_id,
            rule_id=rule_id,
            receiver_ids=receiver_ids,
            message=message
        )

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 成功向 {len(receiver_ids)} 个用户发送站内邀请')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'站内邀请监督者失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'站内邀请失败: {str(e)}')


@supervision_bp.route('/supervision/invite', methods=['POST'])
@login_required
def invite_supervisor(decoded):
    """
    邀请监督者接口 - 邀请特定用户监督特定规则（已弃用，请使用invite_supervisor_internal）
    """
    current_app.logger.info('=== 开始执行邀请监督者接口 ===')

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
        rule_ids = params.get('rule_ids', [])  # 要监督的规则ID列表，空表示监督所有规则
        target_openid = params.get('target_openid')  # 被邀请用户的openid（可选）
        target_user_id = params.get('target_user_id')  # 被邀请用户的user_id（可选）

        # 支持使用 target_user_id 或 target_openid 查询被邀请用户
        if target_user_id:
            get_target_user_use_case = GetUserByIdUseCase()
            target_user_result = get_target_user_use_case.execute(user_id=target_user_id)
        elif target_openid:
            get_target_user_use_case = GetUserByOpenIdUseCase()
            target_user_result = get_target_user_use_case.execute(openid=target_openid)
        else:
            return make_err_response({}, '缺少target_user_id或target_openid参数')

        if not target_user_result.is_success:
            return make_err_response({}, '被邀请用户不存在')
        target_user = target_user_result.data

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

        # 生成邀请token
        import secrets
        import qrcode
        import os
        invite_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        # 生成二维码
        qrcode_dir = 'static/supervision_qrcodes'
        os.makedirs(qrcode_dir, exist_ok=True)

        # 构建小程序路径
        mini_path = f"/pages/supervisor-invite/supervisor-invite?token={invite_token}"

        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(mini_path)
        qr.make(fit=True)

        # 生成图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 保存到文件
        filename = f"{invite_token}.png"
        filepath = os.path.join(qrcode_dir, filename)
        img.save(filepath)

        # 构建二维码URL
        qrcode_url = f"/static/supervision_qrcodes/{filename}"

        # 保存邀请信息到数据库
        # 为每个规则创建监督关系记录
        get_rule_use_case = GetCheckinRuleByIdUseCase()
        for rule_id in rule_ids:
            # 检查规则是否存在且属于当前用户
            rule_result = get_rule_use_case.execute(rule_id=rule_id)
            if not rule_result.is_success:
                current_app.logger.warning(f'规则 {rule_id} 不存在')
                continue
            rule = rule_result.data
            if rule.user_id != user.user_id:
                current_app.logger.warning(f'规则 {rule_id} 不属于用户 {user.user_id}')
                continue

            # 创建监督关系记录（状态为1=待确认）
            relation = SupervisionRuleRelation(
                solo_user_id=user.user_id,
                supervisor_user_id=user.user_id,  # 暂时设置为发起人，等待监督人接受后更新
                rule_id=rule_id,
                status=1,  # 1=待确认
                invite_token=invite_token,
                invite_expires_at=expires_at
            )
            db.session.add(relation)

        db.session.commit()

        invite_data = {
            'token': invite_token,
            'url': qrcode_url,
            'mini_path': mini_path,
            'expire_at': expires_at.isoformat()
        }

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

        # 从数据库查询邀请信息
        relations = db.session.query(SupervisionRuleRelation).filter_by(
            invite_token=invite_token,
            status=1  # 1=待确认
        ).all()

        if not relations:
            return make_err_response({}, '邀请链接不存在或已过期')

        # 检查邀请是否过期
        now = datetime.now()
        if relations[0].invite_expires_at and relations[0].invite_expires_at < now:
            return make_err_response({}, '邀请链接已过期')

        # 获取被监督人信息
        get_user_use_case = GetUserByIdUseCase()
        solo_user_result = get_user_use_case.execute(user_id=relations[0].solo_user_id)
        if not solo_user_result.is_success:
            return make_err_response({}, '被监督人不存在')
        solo_user = solo_user_result.data

        # 获取规则信息
        rule_ids = [r.rule_id for r in relations]
        rules = db.session.query(CheckinRule).filter(
            CheckinRule.rule_id.in_(rule_ids)
        ).all()

        # 构建规则信息（返回第一个规则的详细信息）
        rule_info = None
        if rules:
            rule = rules[0]
            rule_info = {
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'checkin_time': rule.custom_time.strftime('%H:%M:%S') if rule.custom_time else '灵活时间',
                'frequency': 'daily' if rule.frequency_type == 0 else 'weekly'
            }

        # 构建邀请人信息
        inviter_info = {
            'user_id': solo_user.user_id,
            'nickname': solo_user.nickname or '未知用户',
            'phone_number': solo_user.phone_number,
            'avatar_url': solo_user.avatar_url or ''
        }

        # 构建返回数据
        invite_data = {
            'relation_id': relations[0].relation_id,
            'rule_info': rule_info,
            'inviter_info': inviter_info,
            'expires_at': relations[0].invite_expires_at.isoformat() if relations[0].invite_expires_at else None,
            'is_expired': relations[0].invite_expires_at and relations[0].invite_expires_at < now,
            'is_already_supervisor': False  # 需要在实际应用中检查当前用户是否已经是监督人
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

        # 使用邀请管理服务获取邀请列表
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

        service = InvitationManagementService()
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


@supervision_bp.route('/supervision/accept', methods=['POST'])
@login_required
def accept_supervision(decoded):
    """
    接受监督邀请接口
    请求体：{ relation_id }
    返回：{ relation_id, status }
    """
    current_app.logger.info('=== 开始接受监督邀请 ===')

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

        # 查询监督关系
        relation = db.session.query(SupervisionRuleRelation).filter_by(
            relation_id=relation_id
        ).first()

        if not relation:
            return make_err_response({}, '监督关系不存在')

        # 验证当前用户是监督人
        if relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '无权限操作此监督关系')

        # 更新监督关系状态为已激活
        relation.status = 2  # 2 = 已激活
        db.session.commit()

        current_app.logger.info(f'用户 {user.user_id} 接受监督邀请成功，关系ID: {relation_id}')
        return make_succ_response({
            'relation_id': relation_id,
            'status': 2  # 2 = 已激活
        })

    except Exception as e:
        current_app.logger.error(f'接受监督邀请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受监督邀请失败: {str(e)}')


@supervision_bp.route('/supervision/reject', methods=['POST'])
@login_required
def reject_supervision(decoded):
    """
    拒绝监督邀请接口
    请求体：{ relation_id, reason }
    返回：{ message }
    """
    current_app.logger.info('=== 开始拒绝监督邀请 ===')

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

        # 查询监督关系
        relation = db.session.query(SupervisionRuleRelation).filter_by(
            relation_id=relation_id
        ).first()

        if not relation:
            return make_err_response({}, '监督关系不存在')

        # 验证当前用户是监督人
        if relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '无权限操作此监督关系')

        # 删除监督关系（拒绝）
        db.session.delete(relation)
        db.session.commit()

        current_app.logger.info(f'用户 {user.user_id} 拒绝监督邀请，关系ID: {relation_id}，原因: {reason}')
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
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

        invitation_service = InvitationManagementService()
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

        # 验证监督关系
        relation = db.session.query(SupervisionRuleRelation).filter_by(
            supervisor_user_id=user.user_id,
            solo_user_id=supervised_user_id,
            rule_id=rule_id,
            status=2  # 2 = 已激活
        ).first()

        if not relation:
            return make_err_response({}, '监督关系不存在或未激活')

        # 获取被监护人信息
        get_supervised_user_use_case = GetUserByIdUseCase()
        supervised_user_result = get_supervised_user_use_case.execute(user_id=supervised_user_id)
        if not supervised_user_result.is_success:
            return make_err_response({}, '被监护人不存在')
        supervised_user = supervised_user_result.data
        if not supervised_user.wechat_openid:
            return make_err_response({}, '被监护人未绑定微信')

        # 获取规则信息
        get_rule_use_case = GetCheckinRuleByIdUseCase()
        rule_result = get_rule_use_case.execute(rule_id=rule_id)
        if not rule_result.is_success:
            return make_err_response({}, '打卡规则不存在')
        rule = rule_result.data

        # 获取模板内容
        if template_type == 'custom' and template_content:
            message_content = template_content
        else:
            # 使用默认模板
            default_templates = {
                'default': '该打卡了',
                'remember': '记得吃药',
                'wake_up': '该起床了',
                'sleep': '该睡觉了'
            }
            message_content = default_templates.get(template_type, '该打卡了')

        # TODO: 调用微信模板消息接口发送通知
        # 这里先返回成功，实际项目中需要集成微信 API
        current_app.logger.info(f'用户 {user.user_id} 向用户 {supervised_user_id} 发送提醒: {message_content}')

        # 记录提醒发送日志（可选）
        # 可以创建一个 ReminderLog 表来记录所有提醒发送记录

        return make_succ_response({
            'message_id': f'msg_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'sent_at': datetime.now().isoformat()
        })

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
        # 使用邀请管理服务接受邀请
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

        service = InvitationManagementService()
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

        # 使用邀请管理服务拒绝邀请
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

        service = InvitationManagementService()
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
        # 使用邀请管理服务忽略邀请
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

        service = InvitationManagementService()
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

        # 使用邀请管理服务批量接受邀请
        from app.application.use_cases.supervision.invitation_management_service import InvitationManagementService

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