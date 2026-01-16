"""
记录用户资料查看日志用例
"""
import logging
from datetime import datetime
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.shared.utils.transaction import transactional
from database.flask_models import db, UserAuditLog


class LogProfileViewUseCase(BaseUseCase):
    """记录用户资料查看日志用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @transactional
    def execute(self, viewer_id: int, viewed_user_id: int, community_id: int) -> UseCaseResult:
        """
        执行记录用户资料查看日志用例

        Args:
            viewer_id: 查看者ID
            viewed_user_id: 被查看者ID
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not viewer_id or not viewed_user_id or not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 创建审计日志
            audit_log = UserAuditLog(
                user_id=viewer_id,
                action='view_profile',
                details={
                    'viewed_user_id': viewed_user_id,
                    'community_id': community_id
                },
                created_at=datetime.now()
            )

            db.session.add(audit_log)

            self.logger.info(f'记录用户资料查看日志成功: viewer_id={viewer_id}, viewed_user_id={viewed_user_id}')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='记录查看日志成功'
            )

        except Exception as e:
            self.logger.error(f'记录用户资料查看日志失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'记录查看日志失败: {str(e)}'
            )