"""
更新异常值UseCase
用于定时任务计算用户未按时打卡的异常值
"""
import logging
from datetime import datetime, date
from typing import Dict
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.abnormality_calculator import AbnormalityCalculator

logger = logging.getLogger(__name__)


class UpdateAbnormalityValuesUseCase(BaseUseCase):
    """更新异常值用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    def execute(self, target_date: date = None) -> UseCaseResult:
        """执行异常值计算

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            UseCaseResult: 包含统计信息
        """
        if target_date is None:
            target_date = date.today()

        try:
            # 使用AbnormalityCalculator计算所有待计算用户的异常值
            stats = AbnormalityCalculator.calculate_all_pending_users(target_date)

            self.logger.info(f"异常值计算完成: {stats}")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='异常值计算完成',
                data=stats
            )

        except Exception as e:
            self.logger.error(f"异常值计算失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'异常值计算失败: {str(e)}',
                data={'errors': 1}
            )