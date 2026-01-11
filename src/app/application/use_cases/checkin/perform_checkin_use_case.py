"""
执行打卡用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CheckinRecord


class PerformCheckinUseCase(BaseUseCase):
    """执行打卡用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    def execute(
        self,
        user_id: int,
        record_id: int,
        checkin_type: Optional[str] = None,
        content: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行打卡用例

        Args:
            user_id: 用户ID
            record_id: 记录ID
            checkin_type: 打卡类型
            content: 打卡内容

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not record_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='记录ID不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找打卡记录
            record = self.checkin_record_repository.find_by_id(record_id)
            if not record:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡记录不存在'
                )

            # 4. 验证记录归属
            if record.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限操作此打卡记录'
                )

            # 5. 检查记录状态
            if record.status == 1:  # 已打卡
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='已打卡，无需重复打卡'
                )

            if record.status == 2:  # 已撤销
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='打卡记录已撤销'
                )

            # 6. 更新打卡记录
            record.checkin_time = datetime.now()
            record.status = 1  # 已打卡
            record.updated_at = datetime.now()

            if checkin_type:
                record.checkin_type = checkin_type
            if content:
                record.content = content

            updated_record = self.checkin_record_repository.update(record)

            self.logger.info(f'执行打卡成功: record_id={record_id}, user_id={user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡成功',
                data={
                    'record_id': updated_record.record_id,
                    'user_id': updated_record.user_id,
                    'checkin_time': updated_record.checkin_time.isoformat() if updated_record.checkin_time else None,
                    'status': updated_record.status,
                    'checkin_type': updated_record.checkin_type
                }
            )

        except ValueError as e:
            self.logger.error(f'执行打卡失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'执行打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'执行打卡失败: {str(e)}'
            )