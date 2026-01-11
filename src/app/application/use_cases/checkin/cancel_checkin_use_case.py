"""
取消打卡用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class CancelCheckinUseCase(BaseUseCase):
    """取消打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, record_id: int, user_id: int, reason: str = None) -> UseCaseResult:
        """
        执行取消打卡用例

        Args:
            record_id: 打卡记录ID
            user_id: 用户ID
            reason: 取消原因

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not record_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='打卡记录ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询打卡记录
            record = self.checkin_record_repository.find_by_id(record_id)
            if not record:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡记录不存在'
                )

            # 3. 验证权限（只有记录创建者或管理员可以取消）
            if record.user_id != user_id:
                user = self.user_repository.find_by_id(user_id)
                if not user or user.role not in [3, 4]:  # 不是社区主管或超级管理员
                    return UseCaseResult(
                        status=UseCaseStatus.UNAUTHORIZED,
                        message='无权取消此打卡记录'
                    )

            # 4. 检查打卡状态（只有未完成的打卡可以取消）
            if record.checkin_status == 2:  # 2=已完成
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='打卡已完成，无法取消'
                )

            # 5. 取消打卡记录
            self.checkin_record_repository.cancel(record_id, reason or '用户取消打卡')

            self.logger.info(f'取消打卡成功: record_id={record_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡取消成功',
                data={
                    'record_id': record_id
                }
            )

        except Exception as e:
            self.logger.error(f'取消打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'取消打卡失败: {str(e)}'
            )