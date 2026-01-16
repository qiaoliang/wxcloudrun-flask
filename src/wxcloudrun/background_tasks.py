"""
后台任务模块
已迁移到UseCase，保留此文件以保持向后兼容
"""
import logging
from datetime import datetime

from flask import current_app
from app.application.use_cases.background_task import (
    CheckMissedCheckinUseCase,
    CheckDailyCheckinUseCase,
    UpdateAbnormalityValuesUseCase,
    CheckExpiredInvitationsUseCase
)

logger = logging.getLogger('log')

# 全局变量，记录上次执行全天规则检查的日期
_last_daily_check_date = None


def daily_check():
    """执行全天规则的missing检查（每天最多执行一次）"""
    global _last_daily_check_date

    today = datetime.now().date()

    # 检查今天是否已经执行过
    if _last_daily_check_date == today:
        return  # 今天已执行，跳过

    try:
        with current_app.app_context():
            use_case = CheckDailyCheckinUseCase()
            result = use_case.execute()

        # 更新执行日期
        _last_daily_check_date = today
        current_app.logger.info(f"[daily-check] 全天规则检查完成，日期: {today}")

    except Exception as e:
        current_app.logger.error(f"[daily-check] 执行失败: {str(e)}", exc_info=True)


def _run_loop():
    """运行后台检查服务，每5分钟检查一次"""
    import os
    import time as time_module
    from datetime import timedelta

    interval_minutes = int(os.getenv('MISS_CHECK_INTERVAL_MINUTES', '5'))
    interval_seconds = max(1, interval_minutes * 60)
    current_app.logger.info(
        f"[missing-check] 后台服务启动，检查间隔 {interval_minutes} 分钟"
    )

    while True:
        try:
            with current_app.app_context():
                now = datetime.now()

                # 常规规则检查（非全天规则）
                use_case = CheckMissedCheckinUseCase()
                result = use_case.execute(check_time=now)

                current_app.logger.info(f"[missing-check] 缺失打卡检查任务完成: {result.data}")

        except Exception as e:
            current_app.logger.error(f"[missing-check] 后台服务循环错误: {str(e)}", exc_info=True)
        finally:
            time_module.sleep(interval_seconds)


def start_missing_check_service(app):
    """启动缺失检查服务（每5分钟检查一次）"""
    try:
        import threading

        # 创建后台线程
        t = threading.Thread(target=_run_loop_with_context, daemon=True, args=(app,))
        t.start()
        app.logger.info("[missing-check] 后台服务线程已启动（每5分钟检查一次）")
    except Exception as e:
        app.logger.error(f"[missing-check] 启动后台服务失败: {str(e)}")


def _run_loop_with_context(app):
    """在线程中运行循环，保持应用上下文"""
    with app.app_context():
        _run_loop()


def run_missing_check():
    """执行缺失打卡检查（供定时任务调用）"""
    try:
        now = datetime.now()
        use_case = CheckMissedCheckinCheckinUseCase()
        result = use_case.execute(check_time=now)
        return result
    except Exception as e:
        current_app.logger.error(f"[missing-check] 执行失败: {str(e)}", exc_info)
        return None


def run_daily_check():
    """执行全天规则检查（供定时任务调用）"""
    try:
        use_case = CheckDailyCheckinUseCase()
        result = use_case.execute()
        return result
    except Exception as e:
        current_app.logger.error(f"[daily-check] 执行失败: {str(e)}", exc_info)
        return None


def run_abnormality_calculation():
    """执行异常值计算（供定时任务调用）"""
    try:
        use_case = UpdateAbnormalityValuesUseCase()
        result = use_case.execute()
        return result
    except Exception as e:
        current_app.logger.error(f"[abnormality-calculation] 执行失败: {str(e)}", exc_info)
        return None


def run_check_expired_invitations():
    """执行邀请过期检查（供定时任务调用）"""
    try:
        use_case = CheckExpiredInvitationsUseCase()
        result = use_case.execute()
        return result
    except Exception as e:
        current_app.logger.error(f"[check-expired-invitations] 执行失败: {str(e)}", exc_info)
        return None