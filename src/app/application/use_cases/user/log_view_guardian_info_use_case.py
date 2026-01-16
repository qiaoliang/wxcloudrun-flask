"""
记录查看监护人信息用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, UserAuditLog
from datetime import datetime


class LogViewGuardianInfoUseCase(BaseUseCase):
    """记录查看监护人信息用例"""

    def execute(self, viewer_id: int, guardian_id: int, ward_user_id: int, community_id: int) -> UseCaseResult:
        """
        记录查看监护人信息

        Args:
            viewer_id: 查看者用户ID
            guardian_id: 监护人用户ID
            ward_user_id: 被监护人用户ID
            community_id: 社区ID

        Returns:
            UseCaseResult: 记录结果
        """
        try:
            if not all([viewer_id, guardian_id, ward_user_id, community_id]):
                return UseCaseResult.fail("缺少必要参数")

            # 创建审计日志
            audit_log = UserAuditLog(
                user_id=viewer_id,
                action_type='view_guardian_info',
                action_time=datetime.utcnow(),
                community_id=community_id,
                details={
                    'guardian_id': guardian_id,
                    'ward_user_id': ward_user_id
                }
            )

            db.session.add(audit_log)
            db.session.commit()

            return UseCaseResult.success(None, "记录成功")

        except Exception as e:
            db.session.rollback()
            return UseCaseResult.fail(f"记录失败: {str(e)}")