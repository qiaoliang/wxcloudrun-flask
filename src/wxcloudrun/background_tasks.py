import os
import threading
import time as time_module
from datetime import datetime, time, timedelta

from flask import current_app
from sqlalchemy import select
from app.extensions import db
from database.flask_models import CheckinRule, CheckinRecord, User, CommunityCheckinRule, UserCommunityRule, CommunityStaff
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
    """计算个人规则的计划打卡时间"""
    if rule.time_slot_type == 5:  # 全天有效
        return datetime.combine(today, time(0, 0))
    if rule.time_slot_type == 4 and rule.custom_time:
        return datetime.combine(today, rule.custom_time)
    if rule.time_slot_type == 1:
        return datetime.combine(today, time(9, 0))
    if rule.time_slot_type == 2:
        return datetime.combine(today, time(14, 0))
    return datetime.combine(today, time(20, 0))


def _should_check_community_rule_today(rule, today):
    """检查社区规则今天是否应该打卡"""
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


def _planned_time_for_community_rule(rule, today):
    """计算社区规则的计划打卡时间"""
    if rule.time_slot_type == 5:  # 全天有效
        return datetime.combine(today, time(0, 0))
    if rule.time_slot_type == 4 and rule.custom_time:
        return datetime.combine(today, rule.custom_time)
    if rule.time_slot_type == 1:
        return datetime.combine(today, time(9, 0))
    if rule.time_slot_type == 2:
        return datetime.combine(today, time(14, 0))
    return datetime.combine(today, time(20, 0))


def _process_missed_for_today(now):
    """处理个人打卡规则的未打卡标记（跳过全天规则）"""
    today = now.date()
    grace_minutes = int(os.getenv('MISS_GRACE_MINUTES', '0'))
    grace_delta = timedelta(minutes=grace_minutes)

    try:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        stmt = select(CheckinRule).where(CheckinRule.status != 2)  # 排除已删除的规则
        rules = db.session.execute(stmt).scalars().all()
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

            # 跳过全天规则，全天规则由每日任务处理
            if rule.time_slot_type == 5:
                continue

            # 跳过今天创建的规则，给用户时间打卡
            if rule.created_at and rule.created_at.date() == today:
                continue

            if not _should_check_today(rule, today):
                continue

# 计算计划打卡时间
            planned_dt = _planned_time_for_rule(rule, today)
            
            # 对于其他规则，使用宽限期逻辑
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


def _process_community_missed_for_today(now):
    """处理社区打卡规则的未打卡标记（跳过全天规则）"""
    today = now.date()
    grace_minutes = int(os.getenv('MISS_GRACE_MINUTES', '0'))
    grace_delta = timedelta(minutes=grace_minutes)

    try:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        # 查询所有启用的社区规则
        stmt = select(CommunityCheckinRule).where(CommunityCheckinRule.status == 1)
        community_rules = db.session.execute(stmt).scalars().all()
    except Exception as e:
        if "no such table" in str(e).lower():
            current_app.logger.warning(f"[community-missing-mark] 数据库表尚未创建，跳过检查。")
            return
        else:
            raise e

    for rule in community_rules:
        try:
            # 跳过全天规则，全天规则由每日任务处理
            if rule.time_slot_type == 5:
                continue

            # 跳过今天创建的规则，给用户时间打卡
            if rule.created_at and rule.created_at.date() == today:
                continue

            # 检查规则今天是否应该打卡
            if not _should_check_community_rule_today(rule, today):
                continue

            # 计算计划打卡时间
            planned_dt = _planned_time_for_community_rule(rule, today)
            
            # 对于其他规则，使用宽限期逻辑
            # 检查是否还在宽限期内
            if now < planned_dt + grace_delta:
                continue

            # 获取该社区的所有工作人员（排除）
            stmt_staff = select(CommunityStaff).where(
                CommunityStaff.community_id == rule.community_id,
                CommunityStaff.removed_at.is_(None)
            )
            staff_user_ids = [s.user_id for s in db.session.execute(stmt_staff).scalars().all()]

            # 获取该社区所有普通用户（排除工作人员）
            stmt_users = select(User).where(User.community_id == rule.community_id)
            if staff_user_ids:
                from sqlalchemy import not_
                stmt_users = stmt_users.where(not_(User.user_id.in_(staff_user_ids)))
            all_users = db.session.execute(stmt_users).scalars().all()

            if not all_users:
                continue

            # 获取该规则的激活用户映射
            active_user_ids = []
            for u in all_users:
                stmt_mapping = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == u.user_id,
                    UserCommunityRule.community_rule_id == rule.community_rule_id,
                    UserCommunityRule.is_active == True
                )
                mapping = db.session.execute(stmt_mapping).scalar_one_or_none()
                if mapping:
                    active_user_ids.append(u.user_id)

            if not active_user_ids:
                continue

            # 查询今天的打卡记录
            stmt_records = select(CheckinRecord).where(
                CheckinRecord.community_rule_id == rule.community_rule_id,
                CheckinRecord.user_id.in_(active_user_ids),
                CheckinRecord.planned_time >= planned_dt,
                CheckinRecord.planned_time < planned_dt + timedelta(days=1)
            )
            today_records = db.session.execute(stmt_records).scalars().all()

            # 按用户分组检查
            checked_user_ids = {r.user_id for r in today_records if r.status == 1}
            missed_user_ids = {r.user_id for r in today_records if r.status == 0}

            # 为未打卡的用户创建记录
            for user_id in active_user_ids:
                if user_id not in checked_user_ids and user_id not in missed_user_ids:
                    CheckinRecordService._create_record(
                        rule_id=rule.community_rule_id,
                        user_id=user_id,
                        checkin_time=None,
                        planned_time=planned_dt,
                        status=0,
                        rule_source='community'
                    )
                    current_app.logger.info(
                        f"[community-missing-mark] 用户 {user_id} 社区规则 {rule.community_rule_id} 标记为miss，计划时间 {planned_dt}"
                    )

        except Exception as e:
            current_app.logger.error(
                f"[community-missing-mark] 处理社区规则 {rule.community_rule_id} 时出错: {str(e)}", exc_info=True
            )


def _process_all_day_missed_for_yesterday(now):
    """处理全天规则的未打卡标记（每天运行一次，检查前一天的记录）"""
    yesterday = (now.date() - timedelta(days=1))

    try:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        stmt = select(CheckinRule).where(CheckinRule.status != 2, CheckinRule.time_slot_type == 5)  # 排除已删除的规则，只查询全天规则
        rules = db.session.execute(stmt).scalars().all()
    except Exception as e:
        # 如果数据库表不存在，跳过本次检查
        if "no such table" in str(e).lower():
            current_app.logger.warning(f"[all-day-missing-mark] 数据库表尚未创建，跳过检查。")
            return
        else:
            # 其他错误继续抛出
            raise e

    for rule in rules:
        try:
            user = db.session.get(User, rule.user_id)
            if not user:
                continue

            # 跳过昨天创建的规则，给用户时间打卡
            if rule.created_at and rule.created_at.date() == yesterday:
                continue

            # 检查规则昨天是否应该打卡
            if not _should_check_today(rule, yesterday):
                continue

            # 计算计划打卡时间
            planned_dt = _planned_time_for_rule(rule, yesterday)

            # 查询昨天的打卡记录
            yesterday_records = CheckinRecordService._query_records_by_rule_and_date(rule.rule_id, yesterday)

            has_checked = any(r.status == 1 for r in yesterday_records)
            has_missed = any(r.status == 0 for r in yesterday_records)
            if has_checked or has_missed:
                continue

            # 使用 service 方法创建记录
            CheckinRecordService._create_record(
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                checkin_time=None,
                planned_time=planned_dt,
                status=0
            )
            current_app.logger.info(
                f"[all-day-missing-mark] 用户 {rule.user_id} 全天规则 {rule.rule_id} 标记为miss，计划时间 {planned_dt}"
            )
        except Exception as e:
            current_app.logger.error(
                f"[all-day-missing-mark] 处理全天规则 {rule.rule_id} 时出错: {str(e)}", exc_info=True
            )


def _process_community_all_day_missed_for_yesterday(now):
    """处理社区全天规则的未打卡标记（每天运行一次，检查前一天的记录）"""
    yesterday = (now.date() - timedelta(days=1))

    try:
        # 使用 SQLAlchemy 2.0 的 select() 语句
        # 查询所有启用的社区全天规则
        stmt = select(CommunityCheckinRule).where(
            CommunityCheckinRule.status == 1,
            CommunityCheckinRule.time_slot_type == 5
        )
        community_rules = db.session.execute(stmt).scalars().all()
    except Exception as e:
        if "no such table" in str(e).lower():
            current_app.logger.warning(f"[community-all-day-missing-mark] 数据库表尚未创建，跳过检查。")
            return
        else:
            raise e

    for rule in community_rules:
        try:
            # 跳过昨天创建的规则，给用户时间打卡
            if rule.created_at and rule.created_at.date() == yesterday:
                continue

            # 检查规则昨天是否应该打卡
            if not _should_check_community_rule_today(rule, yesterday):
                continue

            # 计算计划打卡时间
            planned_dt = _planned_time_for_community_rule(rule, yesterday)

            # 获取该社区的所有工作人员（排除）
            stmt_staff = select(CommunityStaff).where(
                CommunityStaff.community_id == rule.community_id,
                CommunityStaff.removed_at.is_(None)
            )
            staff_user_ids = [s.user_id for s in db.session.execute(stmt_staff).scalars().all()]

            # 获取该社区所有普通用户（排除工作人员）
            stmt_users = select(User).where(User.community_id == rule.community_id)
            if staff_user_ids:
                from sqlalchemy import not_
                stmt_users = stmt_users.where(not_(User.user_id.in_(staff_user_ids)))
            all_users = db.session.execute(stmt_users).scalars().all()

            if not all_users:
                continue

            # 获取该规则的激活用户映射
            active_user_ids = []
            for u in all_users:
                stmt_mapping = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == u.user_id,
                    UserCommunityRule.community_rule_id == rule.community_rule_id,
                    UserCommunityRule.is_active == True
                )
                mapping = db.session.execute(stmt_mapping).scalar_one_or_none()
                if mapping:
                    active_user_ids.append(u.user_id)

            if not active_user_ids:
                continue

            # 查询昨天的打卡记录
            stmt_records = select(CheckinRecord).where(
                CheckinRecord.community_rule_id == rule.community_rule_id,
                CheckinRecord.user_id.in_(active_user_ids),
                CheckinRecord.planned_time >= planned_dt,
                CheckinRecord.planned_time < planned_dt + timedelta(days=1)
            )
            yesterday_records = db.session.execute(stmt_records).scalars().all()

            # 按用户分组检查
            checked_user_ids = {r.user_id for r in yesterday_records if r.status == 1}
            missed_user_ids = {r.user_id for r in yesterday_records if r.status == 0}

            # 为未打卡的用户创建记录
            for user_id in active_user_ids:
                if user_id not in checked_user_ids and user_id not in missed_user_ids:
                    CheckinRecordService._create_record(
                        rule_id=rule.community_rule_id,
                        user_id=user_id,
                        checkin_time=None,
                        planned_time=planned_dt,
                        status=0,
                        rule_source='community'
                    )
                    current_app.logger.info(
                        f"[community-all-day-missing-mark] 用户 {user_id} 社区全天规则 {rule.community_rule_id} 标记为miss，计划时间 {planned_dt}"
                    )

        except Exception as e:
            current_app.logger.error(
                f"[community-all-day-missing-mark] 处理社区全天规则 {rule.community_rule_id} 时出错: {str(e)}", exc_info=True
            )


def _run_loop():
    """运行后台检查服务，每5分钟检查一次（跳过全天规则）"""
    interval_minutes = int(os.getenv('MISS_CHECK_INTERVAL_MINUTES', '5'))
    interval_seconds = max(1, interval_minutes * 60)
    current_app.logger.info(
        f"[missing-mark] 后台服务启动，检查间隔 {interval_minutes} 分钟（跳过全天规则）"
    )

    while True:
        try:
            with current_app.app_context():
                now = datetime.now()
                _process_missed_for_today(now)
                _process_community_missed_for_today(now)
        except Exception as e:
            current_app.logger.error(f"[missing-mark] 后台服务循环错误: {str(e)}", exc_info=True)
        finally:
            time_module.sleep(interval_seconds)


def _run_daily_loop():
    """运行每日检查服务，每天凌晨检查一次全天规则的missed状态"""
    while True:
        try:
            with current_app.app_context():
                now = datetime.now()
                # 只在凌晨 00:00:00 到 00:05:00 之间运行
                if now.hour == 0 and now.minute < 5:
                    current_app.logger.info("[daily-missing-mark] 开始执行每日全天规则检查")
                    _process_all_day_missed_for_yesterday(now)
                    _process_community_all_day_missed_for_yesterday(now)
                    current_app.logger.info("[daily-missing-mark] 每日全天规则检查完成")
                else:
                    # 计算到下一次凌晨 00:00:00 的间隔
                    tomorrow = now.date() + timedelta(days=1)
                    next_run = datetime.combine(tomorrow, time(0, 0))
                    sleep_seconds = (next_run - now).total_seconds()
                    current_app.logger.info(
                        f"[daily-missing-mark] 等待到 {next_run} 执行下次检查，间隔 {sleep_seconds/3600:.2f} 小时"
                    )
                    time_module.sleep(sleep_seconds)
                    continue
        except Exception as e:
            current_app.logger.error(f"[daily-missing-mark] 每日检查服务错误: {str(e)}", exc_info=True)
            # 出错后等待1小时再重试
            time_module.sleep(3600)


def start_missing_check_service(app):
    """启动缺失检查服务（每5分钟检查一次，跳过全天规则）"""
    try:
        # 创建后台线程
        t = threading.Thread(target=_run_loop_with_context, daemon=True, args=(app,))
        t.start()
        app.logger.info("[missing-mark] 后台服务线程已启动（每5分钟检查一次）")
    except Exception as e:
        app.logger.error(f"[missing-mark] 启动后台服务失败: {str(e)}")


def start_daily_check_service(app):
    """启动每日检查服务（每天凌晨检查一次全天规则）"""
    try:
        # 创建后台线程
        t = threading.Thread(target=_run_daily_loop_with_context, daemon=True, args=(app,))
        t.start()
        app.logger.info("[daily-missing-mark] 每日检查服务线程已启动（每天凌晨检查一次）")
    except Exception as e:
        app.logger.error(f"[daily-missing-mark] 启动每日检查服务失败: {str(e)}")


def _run_loop_with_context(app):
    """在线程中运行循环，保持应用上下文"""
    with app.app_context():
        _run_loop()


def _run_daily_loop_with_context(app):
    """在线程中运行每日循环，保持应用上下文"""
    with app.app_context():
        _run_daily_loop()

