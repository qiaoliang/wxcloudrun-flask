"""
获取今日打卡用例
"""
import logging
from datetime import date, datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CheckinRule, CheckinRecord


class GetTodayCheckinsUseCase(BaseUseCase):
    """获取今日打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取今日打卡用例

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 获取用户的所有打卡规则
            rules = self.checkin_rule_repository.find_active_by_user_id(user_id)

            # 4. 获取今日日期
            today = date.today()

            # 5. 筛选今日需要打卡的规则
            today_rules = []
            for rule in rules:
                if self._should_checkin_today(rule, today):
                    today_rules.append(rule)

            # 6. 获取今日的打卡记录
            today_records = self.checkin_record_repository.find_today_records(user_id)

            # 7. 构建结果数据
            checkin_items = []
            for rule in today_rules:
                # 查找该规则今日的打卡记录
                record = None
                for r in today_records:
                    if r.rule_id == rule.rule_id:
                        record = r
                        break

                # 确定状态名称
                status_name = 'pending'  # 默认状态
                if record:
                    if record.status == 1:  # 已打卡
                        status_name = 'checked'
                    elif record.status == 2:  # 已撤销
                        status_name = 'unchecked'
                checkin_item = {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'frequency_type': rule.frequency_type,
                    'time_slot_type': rule.time_slot_type,
                    'custom_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                    'status': status_name,
                    'checkin_time': None,
                    'record_id': None
                }

                if record:
                    checkin_item['checkin_time'] = record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None
                    checkin_item['record_id'] = record.record_id

                checkin_items.append(checkin_item)

            # 按规则ID排序，确保返回顺序一致
            checkin_items.sort(key=lambda x: x['rule_id'])

            self.logger.info(f'获取今日打卡成功: user_id={user_id}, 规则数={len(checkin_items)}')

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取今日打卡成功',
                data={
                    'user_id': user_id,
                    'date': today.isoformat(),
                    'checkin_items': checkin_items,
                    'total': len(checkin_items),
                    'checked': len([item for item in checkin_items if item['status'] == 1]),
                    'unchecked': len([item for item in checkin_items if item['status'] == 0])
                }
            )

        except ValueError as e:
            self.logger.error(f'获取今日打卡失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'获取今日打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取今日打卡失败: {str(e)}'
            )

    def _should_checkin_today(self, rule: CheckinRule, today: date) -> bool:
        """
        判断今天是否需要打卡

        Args:
            rule: 打卡规则
            today: 今天的日期

        Returns:
            Boolean
        """
        frequency_type = rule.frequency_type
        week_days = rule.week_days
        custom_start_date = rule.custom_start_date
        custom_end_date = rule.custom_end_date

        if frequency_type == 1:  # 每周
            today_weekday = today.weekday()  # 0是周一，6是周日
            return bool(week_days & (1 << today_weekday))
        elif frequency_type == 2:  # 工作日
            return today.weekday() < 5  # 周一到周五
        elif frequency_type == 3:  # 自定义日期范围
            if custom_start_date and custom_end_date:
                return custom_start_date <= today <= custom_end_date
            return False
        else:  # 每天 (frequency_type == 0)
            return True