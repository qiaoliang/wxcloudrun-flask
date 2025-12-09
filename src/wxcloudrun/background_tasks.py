import os
import threading
import time as time_module
from datetime import datetime, date, time, timedelta

from wxcloudrun import app, db
from wxcloudrun.model import CheckinRule, CheckinRecord, User
from wxcloudrun.dao import (
    query_checkin_records_by_rule_id_and_date,
    insert_checkin_record,
)


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
            app.logger.warning(f"[missing-mark] 数据库表尚未创建，跳过检查。如果此日志仅出现一次，属于正常状态。")
            return
        else:
            # 其他错误继续抛出
            raise e
    for rule in rules:
        try:
            user = User.query.get(rule.solo_user_id)
            if not user:
                continue
            if hasattr(user, 'is_solo_user'):
                if not bool(user.is_solo_user):
                    continue
            else:
                if user.role != 1:
                    continue

            if not _should_check_today(rule, today):
                continue

            planned_dt = _planned_time_for_rule(rule, today)
            if now < planned_dt + grace_delta:
                continue

            today_records = query_checkin_records_by_rule_id_and_date(rule.rule_id, today)

            has_checked = any(r.status == 1 for r in today_records)
            has_missed = any(r.status == 0 for r in today_records)
            if has_checked or has_missed:
                continue

            new_record = CheckinRecord(
                rule_id=rule.rule_id,
                solo_user_id=rule.solo_user_id,
                checkin_time=None,
                status=0,
                planned_time=planned_dt,
            )
            insert_checkin_record(new_record)
            app.logger.info(
                f"[missing-mark] 用户 {rule.solo_user_id} 规则 {rule.rule_id} 标记为miss，计划时间 {planned_dt}"
            )
        except Exception as e:
            app.logger.error(
                f"[missing-mark] 处理规则 {rule.rule_id} 时出错: {str(e)}", exc_info=True
            )


def _run_loop():
    interval_minutes = int(os.getenv('MISS_CHECK_INTERVAL_MINUTES', '5'))
    interval_seconds = max(1, interval_minutes * 60)
    app.logger.info(
        f"[missing-mark] 后台服务启动，检查间隔 {interval_minutes} 分钟"
    )

    while True:
        try:
            with app.app_context():
                now = datetime.now()
                _process_missed_for_today(now)
        except Exception as e:
            app.logger.error(f"[missing-mark] 后台服务循环错误: {str(e)}", exc_info=True)
        finally:
            time_module.sleep(interval_seconds)


def start_missing_check_service():
    try:
        t = threading.Thread(target=_run_loop, daemon=True)
        t.start()
        app.logger.info("[missing-mark] 后台服务线程已启动")
    except Exception as e:
        app.logger.error(f"[missing-mark] 启动后台服务失败: {str(e)}")

