"""
报告漏打卡用例(重构版 - 符合DDD架构)
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.infrastructure.transaction.transaction_manager import transaction
from app.domain.entities.checkin_record_entity import CheckinRecordEntity


class ReportMissCheckinUseCase(BaseUseCase):
    """报告漏打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    @transaction
    def execute(self, rule_id: int, user_id: int, reason: str = None) -> UseCaseResult:
        """
        执行报告漏打卡用例

        事务边界: 验证权限 -> 检查状态 -> 创建漏打卡记录, 所有操作在同一事务中

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            reason: 漏打卡原因

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询打卡规则
            rule_entity = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule_entity:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 3. 验证权限（只有规则创建者可以报告）
            if rule_entity.user_id != user_id:
                user = self.user_repository.find_by_id(user_id)
                if not user or user.role not in [3, 4]:  # 不是社区主管或超级管理员
                    return UseCaseResult(
                        status=UseCaseStatus.UNAUTHORIZED,
                        message='无权报告此打卡规则的漏打卡'
                    )

            # 4. 检查今日是否已有打卡记录
            today = datetime.now().date()
            today_records = self.checkin_record_repository.find_today_records(user_id, rule_id)

            if today_records:
                # 检查是否已完成打卡
                completed_records = [r for r in today_records if r.is_completed]
                if completed_records:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message='今日已完成打卡,无法报告漏打卡'
                    )

                # 检查是否已报告漏打卡
                missed_records = [r for r in today_records if r.is_missed]
                if missed_records:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message='今日已报告过漏打卡'
                    )

            # 5. 创建漏打卡记录
            planned_time = rule_entity.calculate_planned_checkin_time()
            if not planned_time:
                planned_time = datetime.now()

            miss_record = CheckinRecordEntity.create(
                record_id=0,  # 将由数据库生成
                rule_id=rule_id,
                user_id=user_id,
                planned_checkin_time=planned_time
            )
            miss_record.mark_missed()

            saved_record = self.checkin_record_repository.save_entity(miss_record)

            self.logger.info(f'报告漏打卡成功: rule_id={rule_id}, record_id={saved_record.record_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='漏打卡报告成功',
                data={
                    'record_id': saved_record.record_id,
                    'rule_id': saved_record.rule_id,
                    'user_id': saved_record.user_id,
                    'checkin_time': saved_record.actual_checkin_time.isoformat() if saved_record.actual_checkin_time else None,
                    'status': 'missed'
                }
            )

        except Exception as e:
            self.logger.error(f'报告漏打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'报告漏打卡失败: {str(e)}'
            )