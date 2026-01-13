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
from database.flask_models import db, SupervisionRuleRelation, CheckinRecord, CheckinRule
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
        for rule_id in rule_ids:
            # 检查规则是否存在且属于当前用户
            rule = CheckinRuleService.query_rule_by_id(rule_id)
            if not rule or rule.user_id != user.user_id:
                current_app.logger.warning(f'规则 {rule_id} 不存在或不属于用户 {user.user_id}')
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
            'supervisor_id': user.user_id,
            'supervisor_openid': openid,
            'rule_ids': rule_ids,
            'invite_token': invite_token,
            'expires_at': expires_at.isoformat(),
            'status': 'pending',
            'mini_path': mini_path,
            'qrcode_url': qrcode_url
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
        solo_user = UserService.query_user_by_id(relations[0].solo_user_id)
        if not solo_user:
            return make_err_response({}, '被监督人不存在')

        # 获取规则信息
        rule_ids = [r.rule_id for r in relations]
        rules = db.session.query(CheckinRule).filter(
            CheckinRule.rule_id.in_(rule_ids)
        ).all()

        # 构建返回数据
        invite_data = {
            'supervisor_id': solo_user.user_id,
            'supervisor_nickname': solo_user.nickname or '未知用户',
            'supervisor_phone': solo_user.phone_number,
            'rule_ids': rule_ids,
            'rule_names': [r.rule_name for r in rules],
            'expires_at': relations[0].invite_expires_at.isoformat() if relations[0].invite_expires_at else None,
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
    请求体：{ relation_id }
    返回：{ relation_id, status }
    """
    current_app.logger.info('=== 开始接受监督邀请 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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


@supervision_bp.route('/supervision/today', methods=['GET'])
@login_required
def get_today_supervision_data(decoded):
    """
    获取今日监护数据接口
    参数：date（可选，格式：YYYY-MM-DD，默认为今天）
    返回：{ supervised_users: [...], date: "2026-01-13" }
    """
    current_app.logger.info('=== 开始获取今日监护数据 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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

        if result.is_success:
            current_app.logger.info(f'用户 {user.user_id} 获取今日监护数据成功')
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

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

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        current_app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

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
        supervised_user = UserService.query_user_by_id(supervised_user_id)
        if not supervised_user or not supervised_user.wechat_openid:
            return make_err_response({}, '被监护人不存在或未绑定微信')

        # 获取规则信息
        rule = CheckinRuleService.query_rule_by_id(rule_id)
        if not rule:
            return make_err_response({}, '打卡规则不存在')

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