"""
监督功能视图模块
包含监督关系管理、监督邀请、监督记录查看等功能
"""

import logging
from datetime import datetime, date, time, timedelta
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.user_service import UserService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService
from database import get_database
from database.flask_models import SupervisionRuleRelation, CheckinRecord
from wxcloudrun.decorators import login_required

app_logger = logging.getLogger('log')

# 获取数据库实例
db = get_database()


@app.route('/api/rules/supervision/invite', methods=['POST'])
@login_required
def invite_supervisor(decoded):
    """
    邀请监督者接口 - 邀请特定用户监督特定规则
    """
    app.logger.info('=== 开始执行邀请监督者接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        invite_type = params.get(
            'invite_type', 'wechat')  # 邀请类型：wechat, phone等
        rule_ids = params.get('rule_ids', [])  # 要监督的规则ID列表，空表示监督所有规则
        target_openid = params.get('target_openid')  # 被邀请用户的openid

        if not target_openid:
            return make_err_response({}, '缺少target_openid参数')

        # 查询被邀请用户
        target_user = UserService.query_user_by_openid(target_openid)
        if not target_user:
            return make_err_response({}, '被邀请用户不存在')

        # 检查规则是否都属于当前用户
        if rule_ids:
            for rule_id in rule_ids:
                rule = CheckinRuleService.query_rule_by_id(rule_id)
                if not rule or rule.solo_user_id != user.user_id:
                    return make_err_response({}, f'规则ID {rule_id} 不存在或不属于当前用户')

        # 创建监督关系 - 为每个规则创建一条记录，如果rule_ids为空则创建一条规则ID为null的记录
        if not rule_ids:  # 监督所有规则
            # 检查是否已存在监督关系
            existing_relation = SupervisionRuleRelation.query.filter_by(
                solo_user_id=user.user_id,
                supervisor_user_id=target_user.user_id,
                rule_id=None,
                status=1  # 待同意
            ).first()

            if not existing_relation:
                with db.get_session() as session:
                    new_relation = SupervisionRuleRelation(
                        solo_user_id=user.user_id,
                        supervisor_user_id=target_user.user_id,
                        rule_id=None,  # 表示监督所有规则
                        status=1  # 待同意
                    )
                    session.add(new_relation)
                    session.commit()
        else:  # 监督特定规则
            for rule_id in rule_ids:
                # 检查是否已存在监督关系
                existing_relation = SupervisionRuleRelation.query.filter_by(
                    solo_user_id=user.user_id,
                    supervisor_user_id=target_user.user_id,
                    rule_id=rule_id,
                    status=1  # 待同意
                ).first()

                if not existing_relation:
                    new_relation = SupervisionRuleRelation(
                        solo_user_id=user.user_id,
                        supervisor_user_id=target_user.user_id,
                        rule_id=rule_id,
                        status=1  # 待同意
                    )
                    session.add(new_relation)

        session.commit()

        response_data = {
            'message': '邀请发送成功'
        }

        app.logger.info(f'用户 {user.user_id} 邀请用户 {target_user.user_id} 监督规则成功')
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'邀请监督者时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'邀请监督者失败: {str(e)}')


@app.route('/api/rules/supervision/invite_link', methods=['POST'])
@login_required
def invite_supervisor_link(decoded):
    """
    生成监督邀请链接（无需目标openid）
    """
    app.logger.info('=== 开始执行生成监督邀请链接接口 ===')
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json() or {}
        rule_ids = params.get('rule_ids', [])
        expire_hours = int(params.get('expire_hours', 72))
        import secrets
        token = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(hours=expire_hours)

        created_relations = []
        if rule_ids:
            for rid in rule_ids:
                rel = SupervisionRuleRelation(
                    solo_user_id=user.user_id,
                    supervisor_user_id=None,
                    rule_id=rid,
                    status=1,
                    invite_token=token,
                    invite_expires_at=expires_at
                )
                session.add(rel)
                created_relations.append(rel)
        else:
            rel = SupervisionRuleRelation(
                solo_user_id=user.user_id,
                supervisor_user_id=None,
                rule_id=None,
                status=1,
                invite_token=token,
                invite_expires_at=expires_at
            )
            session.add(rel)
            created_relations.append(rel)

        session.commit()

        response_data = {
            'invite_token': token,
            'mini_path': f"/pages/supervisor-invite/supervisor-invite?token={token}",
            'expire_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'生成监督邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'生成监督邀请链接失败: {str(e)}')


@app.route('/api/rules/supervision/invite/resolve', methods=['GET'])
@login_required
def resolve_invite_link(decoded):
    """
    解析邀请链接，将当前登录用户绑定为supervisor
    """
    app.logger.info('=== 开始执行解析邀请链接接口 ===')
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        token = request.args.get('token')
        if not token:
            return make_err_response({}, '缺少token参数')

        relation = SupervisionRuleRelation.query.filter_by(
            invite_token=token).first()
        if not relation:
            return make_err_response({}, '邀请链接无效或已失效')

        if relation.invite_expires_at and relation.invite_expires_at < datetime.now():
            return make_err_response({}, '邀请链接已过期')

        if relation.supervisor_user_id and relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请已被其他用户处理')

        relation.supervisor_user_id = user.user_id
        relation.updated_at = datetime.now()
        session.commit()

        response_data = {
            'relation_id': relation.relation_id,
            'status': relation.status_name,
            'solo_user_id': relation.solo_user_id,
            'rule_id': relation.rule_id
        }
        return make_succ_response(response_data)
    except Exception as e:
        app.logger.error(f'解析邀请链接失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'解析邀请链接失败: {str(e)}')


@app.route('/api/rules/supervision/invitations', methods=['GET'])
@login_required
def get_supervision_invitations(decoded):
    """
    获取监督邀请列表接口 - 获取当前用户收到的监督邀请
    """
    app.logger.info('=== 开始执行获取监督邀请列表接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        inv_type = request.args.get('type', 'received')
        if inv_type == 'sent':
            invitations = SupervisionRuleRelation.query.filter_by(
                solo_user_id=user.user_id,
                status=1
            ).all()
        else:
            invitations = SupervisionRuleRelation.query.filter_by(
                supervisor_user_id=user.user_id,
                status=1
            ).all()

        invitations_data = []
        for inv in invitations:
            solo_user = UserService.query_user_by_id(inv.solo_user_id)
            rule_info = None
            if inv.rule_id:
                rule = CheckinRuleService.query_rule_by_id(inv.rule_id)
                if rule:
                    rule_info = {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name
                    }

            invitations_data.append({
                'relation_id': inv.relation_id,
                'solo_user': {
                    'user_id': solo_user.user_id,
                    'nickname': solo_user.nickname,
                    'avatar_url': solo_user.avatar_url
                },
                'rule': rule_info,
                'status': inv.status_name,
                'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        response_data = {
            'type': inv_type,
            'invitations': invitations_data
        }

        app.logger.info(
            f'成功获取监督邀请列表，用户ID: {user.user_id}, 邀请数量: {len(invitations_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取监督邀请列表时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督邀请列表失败: {str(e)}')


@app.route('/api/rules/supervision/accept', methods=['POST'])
@login_required
def accept_supervision_invitation(decoded):
    """
    接受监督邀请接口
    """
    app.logger.info('=== 开始执行接受监督邀请接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        relation_id = params.get('relation_id')

        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 查找邀请关系
        relation = SupervisionRuleRelation.query.get(relation_id)
        if not relation or relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请关系不存在或无权限')

        # 检查是否已经是已同意状态
        if relation.status == 2:  # 已同意
            return make_err_response({}, '邀请已接受')

        # 更新状态为已同意
        relation.status = 2  # 已同意
        relation.updated_at = datetime.now()
        session.commit()

        response_data = {
            'message': '接受邀请成功'
        }

        app.logger.info(f'用户 {user.user_id} 接受监督邀请成功，关系ID: {relation_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'接受监督邀请时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'接受监督邀请失败: {str(e)}')


@app.route('/api/rules/supervision/reject', methods=['POST'])
@login_required
def reject_supervision_invitation(decoded):
    """
    拒绝监督邀请接口
    """
    app.logger.info('=== 开始执行拒绝监督邀请接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        relation_id = params.get('relation_id')

        if not relation_id:
            return make_err_response({}, '缺少relation_id参数')

        # 查找邀请关系
        relation = SupervisionRuleRelation.query.get(relation_id)
        if not relation or relation.supervisor_user_id != user.user_id:
            return make_err_response({}, '邀请关系不存在或无权限')

        # 更新状态为已拒绝
        relation.status = 3  # 已拒绝
        relation.updated_at = datetime.now()
        session.commit()

        response_data = {
            'message': '拒绝邀请成功'
        }

        app.logger.info(f'用户 {user.user_id} 拒绝监督邀请成功，关系ID: {relation_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'拒绝监督邀请时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'拒绝监督邀请失败: {str(e)}')


@app.route('/api/rules/supervision/my_supervised', methods=['GET'])
@login_required
def get_my_supervised_users(decoded):
    """
    获取我监督的用户列表接口
    """
    app.logger.info('=== 开始执行获取我监督的用户列表接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取当前用户监督的用户列表
        supervised_users = user.get_supervised_users()

        supervised_data = []
        for solo_user in supervised_users:
            # 获取被监督用户的规则列表
            rules = user.get_supervised_rules(solo_user.user_id)
            rule_list = [{
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'icon_url': rule.icon_url
            } for rule in rules]

            # 获取被监督用户今天的打卡状态
            today = date.today()
            checkin_items = []
            for rule in rules:
                # 查询今天该规则的打卡记录
                today_records = CheckinRecordService._query_records_by_rule_and_date(
                    rule.rule_id, today)

                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None

                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime(
                            '%H:%M:%S') if record.checkin_time else None
                        break
                    elif record.status == 2:  # 已撤销
                        checkin_status = 'unchecked'
                        checkin_time = None
                        break

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'status': checkin_status,
                    'checkin_time': checkin_time
                })

            supervised_data.append({
                'user_id': solo_user.user_id,
                'nickname': solo_user.nickname,
                'avatar_url': solo_user.avatar_url,
                'rules': rule_list,
                'today_checkin_status': checkin_items
            })

        response_data = {
            'supervised_users': supervised_data
        }

        app.logger.info(
            f'成功获取监督的用户列表，用户ID: {user.user_id}, 监督数量: {len(supervised_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取监督的用户列表时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取监督的用户列表失败: {str(e)}')


@app.route('/api/rules/supervision/my_guardians', methods=['GET'])
@login_required
def get_my_guardians(decoded):
    app.logger.info('=== 开始执行获取我的监护人列表接口 ===')
    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        return make_err_response({}, '用户不存在')

    try:
        relations = SupervisionRuleRelation.query.filter(
            SupervisionRuleRelation.solo_user_id == user.user_id,
            SupervisionRuleRelation.status == 2
        ).distinct(SupervisionRuleRelation.supervisor_user_id).all()

        guardians = []
        for rel in relations:
            sup = UserService.query_user_by_id(rel.supervisor_user_id)
            guardians.append({
                'user_id': sup.user_id,
                'nickname': sup.nickname,
                'avatar_url': sup.avatar_url
            })

        return make_succ_response({'guardians': guardians})
    except Exception as e:
        app.logger.error(f'获取我的监护人列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取我的监护人列表失败: {str(e)}')


@app.route('/api/rules/supervision/records', methods=['GET'])
@login_required
def get_supervised_checkin_records(decoded):
    """
    获取被监督用户的打卡记录接口
    """
    app.logger.info('=== 开始执行获取被监督用户打卡记录接口 ===')

    openid = decoded.get('openid')
    user = UserService.query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取查询参数
        params = request.args
        solo_user_id = params.get('solo_user_id')
        rule_id = params.get('rule_id')  # 可选：特定规则ID
        start_date_str = params.get(
            'start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get(
            'end_date', date.today().strftime('%Y-%m-%d'))

        if not solo_user_id:
            return make_err_response({}, '缺少solo_user_id参数')

        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 检查是否有权限监督该用户或规则
        if rule_id:
            if not user.can_supervise_rule(int(rule_id)):
                return make_err_response({}, '无权限监督该规则')
        else:
            if not user.can_supervise_user(int(solo_user_id)):
                return make_err_response({}, '无权限监督该用户')

        # 根据是否有特定规则ID来查询打卡记录
        if rule_id:
            # 查询特定规则的打卡记录
            records = CheckinRecord.query.filter(
                CheckinRecord.solo_user_id == int(solo_user_id),
                CheckinRecord.rule_id == int(rule_id),
                CheckinRecord.planned_time >= datetime.combine(
                    start_date, time.min),
                CheckinRecord.planned_time <= datetime.combine(
                    end_date, time.max)
            ).order_by(CheckinRecord.planned_time.desc()).all()
        else:
            # 查询特定用户的所有可监督规则的打卡记录
            supervised_rules = user.get_supervised_rules(int(solo_user_id))
            rule_ids = [rule.rule_id for rule in supervised_rules]
            if not rule_ids:
                records = []
            else:
                records = CheckinRecord.query.filter(
                    CheckinRecord.solo_user_id == int(solo_user_id),
                    CheckinRecord.rule_id.in_(rule_ids),
                    CheckinRecord.planned_time >= datetime.combine(
                        start_date, time.min),
                    CheckinRecord.planned_time <= datetime.combine(
                        end_date, time.max)
                ).order_by(CheckinRecord.planned_time.desc()).all()

        # 转换为响应格式
        history_data = []
        for record in records:
            history_data.append({
                'record_id': record.record_id,
                'rule_id': record.rule_id,
                'rule_name': record.rule.rule_name,
                'icon_url': record.rule.icon_url,
                'planned_time': record.planned_time.strftime('%Y-%m-%d %H:%M:%S'),
                'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                'status': record.status_name,  # 使用模型中的状态名称
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        response_data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'history': history_data
        }

        app.logger.info(
            f'成功获取被监督用户打卡记录，监督者ID: {user.user_id}, 被监督者ID: {solo_user_id}, 记录数量: {len(history_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取被监督用户打卡记录时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取被监督用户打卡记录失败: {str(e)}')