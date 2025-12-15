"""
打卡功能视图模块
包含打卡操作、打卡规则管理、打卡历史等功能
"""

import logging
from datetime import datetime, date, time, timedelta
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.dao import (
    query_user_by_openid, 
    query_checkin_rules_by_user_id,
    query_checkin_rule_by_id,
    query_checkin_records_by_rule_id_and_date,
    query_checkin_record_by_id,
    insert_checkin_record,
    update_checkin_record_by_id,
    insert_checkin_rule,
    update_checkin_rule_by_id,
    delete_checkin_rule_by_id,
    query_checkin_records_by_user_and_date_range
)
from database.models import CheckinRule, CheckinRecord
from wxcloudrun.decorators import login_required

app_logger = logging.getLogger('log')


@app.route('/api/checkin/today', methods=['GET'])
@login_required
def get_today_checkin_items(decoded):
    """
    获取用户今日打卡事项列表
    """
    app.logger.info('=== 开始执行获取今日打卡事项接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    # 提取user_id以避免会话问题
    user_id = user.user_id

    try:
        # 获取用户的打卡规则
        checkin_rules = query_checkin_rules_by_user_id(user_id)

        # 生成今天的打卡计划
        today = date.today()
        checkin_items = []
        for rule in checkin_rules:
            # 根据规则频率类型判断今天是否需要打卡
            should_checkin_today = True

            if rule.frequency_type == 1:  # 每周
                # 根据week_days位掩码判断今天是否需要打卡
                today_weekday = today.weekday()  # 0是周一，6是周日
                if not (rule.week_days & (1 << today_weekday)):
                    should_checkin_today = False
            elif rule.frequency_type == 2:  # 工作日
                if today.weekday() >= 5:  # 周六日
                    should_checkin_today = False

            if should_checkin_today:
                # 查询今天该规则的打卡记录
                today_records = query_checkin_records_by_rule_id_and_date(
                    rule.rule_id, today)

                # 计算计划打卡时间
                if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                    planned_time = datetime.combine(today, rule.custom_time)
                elif rule.time_slot_type == 1:  # 上午
                    planned_time = datetime.combine(
                        today, time(9, 0))  # 默认上午9点
                elif rule.time_slot_type == 2:  # 下午
                    planned_time = datetime.combine(
                        today, time(14, 0))  # 默认下午2点
                else:  # 晚上，默认晚上8点
                    planned_time = datetime.combine(today, time(20, 0))

                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None
                record_id = None

                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime(
                            '%H:%M:%S') if record.checkin_time else None
                        record_id = record.record_id
                        break
                    elif record.status == 2:  # 已撤销
                        checkin_status = 'unchecked'
                        checkin_time = None
                        record_id = record.record_id
                        break

                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'record_id': record_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.strftime('%H:%M:%S'),
                    'status': checkin_status,  # unchecked, checked
                    'checkin_time': checkin_time
                })

        response_data = {
            'date': today.strftime('%Y-%m-%d'),
            'checkin_items': checkin_items
        }

        app.logger.info(
            f'成功获取今日打卡事项，用户ID: {user_id}, 事项数量: {len(checkin_items)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')


@app.route('/api/checkin', methods=['POST'])
@login_required
def perform_checkin(decoded):
    """
    执行打卡操作
    """
    app.logger.info('=== 开始执行打卡接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        rule_id = params.get('rule_id')

        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')

        # 验证打卡规则是否存在且属于当前用户
        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        # 检查今天是否已有打卡记录（防止重复打卡）
        today = date.today()
        existing_records = query_checkin_records_by_rule_id_and_date(
            rule_id, today)

        # 查找当天已有的打卡记录（状态为已打卡）
        existing_checkin = None
        for record in existing_records:
            if record.status == 1:  # 已打卡
                # 不允许重复打卡
                return make_err_response({}, '今日该事项已打卡，请勿重复打卡')
            elif record.status == 0:  # 未打卡状态的记录，可以更新为已打卡
                existing_checkin = record
                break
            elif record.status == 2:  # 已撤销的记录，可以重新打卡
                # 创建新的打卡记录
                existing_checkin = None
                break

        # 记录打卡时间
        checkin_time = datetime.now()

        if existing_checkin:
            # 更新已有记录的打卡时间和状态
            existing_checkin.checkin_time = checkin_time
            existing_checkin.status = 1  # 已打卡
            update_checkin_record_by_id(existing_checkin)
            record_id = existing_checkin.record_id
        else:
            # 计算计划打卡时间
            if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                planned_time = datetime.combine(today, rule.custom_time)
            elif rule.time_slot_type == 1:  # 上午
                planned_time = datetime.combine(today, time(9, 0))  # 默认上午9点
            elif rule.time_slot_type == 2:  # 下午
                planned_time = datetime.combine(today, time(14, 0))  # 默认下午2点
            else:  # 晚上，默认晚上8点
                planned_time = datetime.combine(today, time(20, 0))

            # 创建新的打卡记录
            new_record = CheckinRecord(
                rule_id=rule_id,
                solo_user_id=user.user_id,
                checkin_time=checkin_time,
                status=1,  # 已打卡
                planned_time=planned_time
            )
            insert_checkin_record(new_record)
            record_id = new_record.record_id

        response_data = {
            'rule_id': rule_id,
            'record_id': record_id,
            'checkin_time': checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
            'message': '打卡成功'
        }

        app.logger.info(f'用户 {user.user_id} 打卡成功，规则ID: {rule_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡失败: {str(e)}')


@app.route('/api/checkin/miss', methods=['POST'])
@login_required
def mark_missed(decoded):
    """
    标记当天规则为missed（超过宽限期）
    """
    app.logger.info('=== 开始执行标记miss接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        params = request.get_json() or {}
        rule_id = params.get('rule_id')
        if not rule_id:
            return make_err_response({}, '缺少rule_id参数')
        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user.user_id:
            return make_err_response({}, '打卡规则不存在或无权限')

        today = date.today()
        records = query_checkin_records_by_rule_id_and_date(rule_id, today)
        for r in records:
            if r.status == 1:
                return make_err_response({}, '今日该事项已打卡，无需标记miss')

        if rule.time_slot_type == 4 and rule.custom_time:
            planned_time = datetime.combine(today, rule.custom_time)
        elif rule.time_slot_type == 1:
            planned_time = datetime.combine(today, time(9, 0))
        elif rule.time_slot_type == 2:
            planned_time = datetime.combine(today, time(14, 0))
        else:
            planned_time = datetime.combine(today, time(20, 0))

        new_record = CheckinRecord(
            rule_id=rule_id,
            solo_user_id=user.user_id,
            checkin_time=None,
            status=0,
            planned_time=planned_time
        )
        insert_checkin_record(new_record)

        return make_succ_response({'record_id': new_record.record_id, 'message': '已标记为miss'})
    except Exception as e:
        app.logger.error(f'标记miss时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'标记miss失败: {str(e)}')


@app.route('/api/checkin/cancel', methods=['POST'])
@login_required
def cancel_checkin(decoded):
    """
    撤销打卡操作（仅限30分钟内）
    """
    app.logger.info('=== 开始执行撤销打卡接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        params = request.get_json()
        record_id = params.get('record_id')

        if not record_id:
            return make_err_response({}, '缺少record_id参数')

        # 验证打卡记录是否存在且属于当前用户
        record = query_checkin_record_by_id(record_id)
        if not record or record.solo_user_id != user.user_id:
            return make_err_response({}, '打卡记录不存在或无权限')

        # 检查打卡时间是否在30分钟内（防止撤销过期打卡）
        if record.checkin_time:
            time_diff = datetime.now() - record.checkin_time
            if time_diff.total_seconds() > 30 * 60:  # 30分钟
                return make_err_response({}, '只能撤销30分钟内的打卡记录')

        # 更新记录状态为已撤销
        record.status = 2  # 已撤销
        record.checkin_time = None  # 清除打卡时间
        update_checkin_record_by_id(record)

        response_data = {
            'record_id': record_id,
            'message': '撤销打卡成功'
        }

        app.logger.info(f'用户 {user.user_id} 撤销打卡成功，记录ID: {record_id}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'撤销打卡时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'撤销打卡失败: {str(e)}')


@app.route('/api/checkin/history', methods=['GET'])
@login_required
def get_checkin_history(decoded):
    """
    获取打卡历史记录
    """
    app.logger.info('=== 开始执行获取打卡历史接口 ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        # 获取查询参数
        params = request.args
        start_date_str = params.get(
            'start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date_str = params.get(
            'end_date', date.today().strftime('%Y-%m-%d'))

        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 获取打卡记录
        records = query_checkin_records_by_user_and_date_range(
            user.user_id, start_date, end_date)

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
            f'成功获取打卡历史，用户ID: {user.user_id}, 记录数量: {len(history_data)}')
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f'获取打卡历史时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取打卡历史失败: {str(e)}')


@app.route('/api/checkin/rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_checkin_rules(decoded):
    """
    打卡规则管理接口
    GET: 获取打卡规则列表
    POST: 创建打卡规则
    PUT: 更新打卡规则
    DELETE: 删除打卡规则
    """
    app.logger.info(f'=== 开始执行打卡规则管理接口: {request.method} ===')

    openid = decoded.get('openid')
    user = query_user_by_openid(openid)
    if not user:
        app.logger.error(f'数据库中未找到openid为 {openid} 的用户')
        return make_err_response({}, '用户不存在')

    try:
        def parse_time(v):
            if not v:
                return None
            try:
                return datetime.strptime(v, '%H:%M:%S').time()
            except Exception:
                return datetime.strptime(v, '%H:%M').time()

        def format_time(t):
            return t.strftime('%H:%M') if t else None

        def parse_date(v):
            if not v:
                return None
            return datetime.strptime(v, '%Y-%m-%d').date()
            
        if request.method == 'GET':
            # 获取用户的所有打卡规则
            rules = query_checkin_rules_by_user_id(user.user_id)

            rules_data = []
            for rule in rules:
                rules_data.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'frequency_type': rule.frequency_type,
                    'time_slot_type': rule.time_slot_type,
                    'custom_time': format_time(rule.custom_time),
                    'week_days': rule.week_days,
                    'custom_start_date': rule.custom_start_date.strftime('%Y-%m-%d') if rule.custom_start_date else None,
                    'custom_end_date': rule.custom_end_date.strftime('%Y-%m-%d') if rule.custom_end_date else None,
                    'status': rule.status,
                    'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            response_data = {
                'rules': rules_data
            }

            app.logger.info(
                f'成功获取打卡规则列表，用户ID: {user.user_id}, 规则数量: {len(rules_data)}')
            return make_succ_response(response_data)

        elif request.method == 'POST':
            params = request.get_json()

            rule_name = params.get('rule_name')
            if not rule_name:
                app.logger.error('❌ Layer 4验证失败: 缺少rule_name参数')
                return make_err_response({}, '缺少rule_name参数')

            # 创建新的打卡规则
            freq = params.get('frequency_type', 0)
            start_date = parse_date(params.get('custom_start_date'))
            end_date = parse_date(params.get('custom_end_date'))
            if int(freq) == 3:
                if not start_date or not end_date:
                    return make_err_response({}, '自定义频率必须提供起止日期')
                if end_date < start_date:
                    return make_err_response({}, '结束日期不能早于开始日期')

            new_rule = CheckinRule(
                solo_user_id=user.user_id,
                rule_name=rule_name,
                icon_url=params.get('icon_url', ''),
                frequency_type=freq,  # 默认每天
                time_slot_type=params.get('time_slot_type', 4),  # 默认自定义时间
                custom_time=parse_time(params.get('custom_time')),
                week_days=params.get('week_days', 127),  # 默认周一到周日
                custom_start_date=start_date,
                custom_end_date=end_date,
                status=params.get('status', 1)  # 默认启用
            )

            try:
                insert_checkin_rule(new_rule)
            except Exception as db_error:
                import traceback
                app.logger.error(f'数据库错误堆栈: {traceback.format_exc()}')
                return make_err_response({}, f'数据库保存失败: {str(db_error)}')

            response_data = {
                'rule_id': new_rule.rule_id,
                'message': '创建打卡规则成功'
            }

            app.logger.info(
                f'成功创建打卡规则，用户ID: {user.user_id}, 规则ID: {new_rule.rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'PUT':
            # 更新打卡规则
            params = request.get_json()

            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 验证规则是否存在且属于当前用户
            rule = query_checkin_rule_by_id(rule_id)
            if not rule or rule.solo_user_id != user.user_id:
                return make_err_response({}, '打卡规则不存在或无权限')

            # 更新规则信息
            if 'rule_name' in params:
                rule.rule_name = params['rule_name']
            if 'icon_url' in params:
                rule.icon_url = params['icon_url']
            if 'frequency_type' in params:
                rule.frequency_type = params['frequency_type']
            if 'time_slot_type' in params:
                rule.time_slot_type = params['time_slot_type']
            if 'custom_time' in params:
                rule.custom_time = parse_time(
                    params['custom_time']) if params['custom_time'] else None
            if 'week_days' in params:
                rule.week_days = params['week_days']
            if 'status' in params:
                rule.status = params['status']
            if 'custom_start_date' in params:
                rule.custom_start_date = parse_date(
                    params['custom_start_date']) if params['custom_start_date'] else None
            if 'custom_end_date' in params:
                rule.custom_end_date = parse_date(
                    params['custom_end_date']) if params['custom_end_date'] else None

            # 校验自定义频率的日期范围
            final_freq = params.get('frequency_type', rule.frequency_type)
            if int(final_freq) == 3:
                if not rule.custom_start_date or not rule.custom_end_date:
                    return make_err_response({}, '自定义频率必须提供起止日期')
                if rule.custom_end_date < rule.custom_start_date:
                    return make_err_response({}, '结束日期不能早于开始日期')

            update_checkin_rule_by_id(rule)

            response_data = {
                'rule_id': rule.rule_id,
                'message': '更新打卡规则成功'
            }

            app.logger.info(
                f'成功更新打卡规则，用户ID: {user.user_id}, 规则ID: {rule.rule_id}')
            return make_succ_response(response_data)

        elif request.method == 'DELETE':
            # 删除打卡规则
            params = request.get_json()

            rule_id = params.get('rule_id')
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')

            # 验证规则是否存在且属于当前用户
            rule = query_checkin_rule_by_id(rule_id)
            if not rule or rule.solo_user_id != user.user_id:
                return make_err_response({}, '打卡规则不存在或无权限')

            try:
                delete_checkin_rule_by_id(rule_id)

                response_data = {
                    'rule_id': rule_id,
                    'message': '删除打卡规则成功'
                }

                app.logger.info(
                    f'成功删除打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
                return make_succ_response(response_data)
            except ValueError as e:
                # 处理规则不存在的异常
                app.logger.warning(f'删除打卡规则失败: {str(e)}, 用户ID: {user.user_id}')
                return make_err_response({}, str(e))
            except Exception as e:
                app.logger.error(
                    f'删除打卡规则时发生错误: {str(e)}, 用户ID: {user.user_id}')
                return make_err_response({}, f'删除打卡规则失败: {str(e)}')

    except Exception as e:
        app.logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
        return make_err_response({}, f'打卡规则管理失败: {str(e)}')