import os
import threading
import time as time_module
from datetime import datetime, time, timedelta

from flask import current_app
from database.flask_models import CheckinRule, CheckinRecord, User
from wxcloudrun.checkin_record_service import CheckinRecordService


def _should_check_today(rule, today):
    if rule.frequency_type == 1:
        weekday = today.weekday()
        return bool(rule.week_days & (1 << weekday))
    if rule.frequency_type == 2:
        return today.weekday() < 5
    if rule.frequency_type == 3:
        if rule.custom_start_date and rule.custom_end_date:
            return rule.custom_start_date <= today <= rule.custom_end_date
        return False
    return True


def _planned_time_for_rule(rule, today):
    if rule.time_slot_type == 4 and rule.custom_time:
        return datetime.combine(today, rule.custom_time)
    if rule.time_slot_type == 1:
        return datetime.combine(today, time(9, 0))
    if rule.time_slot_type == 2:
        return datetime.combine(today, time(14, 0))
    return datetime.combine(today, time(20, 0))


def _process_missed_for_today(now):
    today = now.date()
    grace_minutes = int(os.getenv('MISS_GRACE_MINUTES', '0'))
    grace_delta = timedelta(minutes=grace_minutes)

    try:
        rules = CheckinRule.query.filter(CheckinRule.status != 2).all()  # 排除已删除的规则
    except Exception as e:
        # 如果数据库表不存在，跳过本次检查
        if "no such table" in str(e).lower():
            current_app.logger.warning(f"[missing-mark] 数据库表尚未创建，跳过检查。如果此日志仅出现一次，属于正常状态。")
            return
        else:
            # 其他错误继续抛出
            raise e
    for rule in rules:
        try:
            user = db.session.get(User, rule.user_id)  # 更新字段名
            if not user:
                continue
            # 所有用户都可以有打卡规则，不需要特殊检查

            if not _should_check_today(rule, today):
                continue

            planned_dt = _planned_time_for_rule(rule, today)
            if now < planned_dt + grace_delta:
                continue

            today_records = CheckinRecordService._query_records_by_rule_and_date(rule.rule_id, today)

            has_checked = any(r.status == 1 for r in today_records)
            has_missed = any(r.status == 0 for r in today_records)
            if has_checked or has_missed:
                continue

            # 使用 service 方法创建记录
            CheckinRecordService._create_record(
                rule_id=rule.rule_id,
                user_id=rule.user_id,  # 更新字段名
                checkin_time=None,
                planned_time=planned_dt,
                status=0
            )
            current_app.logger.info(
                f"[missing-mark] 用户 {rule.user_id} 规则 {rule.rule_id} 标记为miss，计划时间 {planned_dt}"  # 更新字段名
            )
        except Exception as e:
            current_app.logger.error(
                f"[missing-mark] 处理规则 {rule.rule_id} 时出错: {str(e)}", exc_info=True
            )


def _run_loop():
    interval_minutes = int(os.getenv('MISS_CHECK_INTERVAL_MINUTES', '5'))
    interval_seconds = max(1, interval_minutes * 60)
    current_app.logger.info(
        f"[missing-mark] 后台服务启动，检查间隔 {interval_minutes} 分钟"
    )

    while True:
        try:
            with current_app.app_context():
                now = datetime.now()
                _process_missed_for_today(now)
        except Exception as e:
            current_app.logger.error(f"[missing-mark] 后台服务循环错误: {str(e)}", exc_info=True)
        finally:
            time_module.sleep(interval_seconds)


def start_missing_check_service(app):
    """启动缺失检查服务"""
    try:
        # 创建后台线程
        t = threading.Thread(target=_run_loop_with_context, daemon=True, args=(app,))
        t.start()
        app.logger.info("[missing-mark] 后台服务线程已启动")
    except Exception as e:
        app.logger.error(f"[missing-mark] 启动后台服务失败: {str(e)}")


def _run_loop_with_context(app):
    """在线程中运行循环，保持应用上下文"""
    with app.app_context():
        _run_loop()

