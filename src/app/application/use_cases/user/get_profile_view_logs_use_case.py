"""
获取浏览记录列表用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, UserAuditLog
from sqlalchemy import select, desc


class GetProfileViewLogsUseCase(BaseUseCase):
    """获取浏览记录列表用例"""

    def execute(self, community_id: int, viewer_id: int = None, limit: int = 100) -> UseCaseResult:
        """
        获取浏览记录列表

        Args:
            community_id: 社区ID
            viewer_id: 查看者用户ID（可选，用于过滤特定查看者的记录）
            limit: 返回记录数量限制

        Returns:
            UseCaseResult: 包含浏览记录列表
        """
        try:
            if not community_id:
                return UseCaseResult.fail("社区ID不能为空")

            # 构建查询
            stmt = select(UserAuditLog).where(
                UserAuditLog.community_id == community_id,
                UserAuditLog.action_type == 'view_profile'
            )

            # 如果指定了查看者，过滤该查看者的记录
            if viewer_id:
                stmt = stmt.where(UserAuditLog.user_id == viewer_id)

            # 按时间倒序排列，限制返回数量
            stmt = stmt.order_by(desc(UserAuditLog.action_time)).limit(limit)

            logs = db.session.execute(stmt).scalars().all()

            # 构造返回数据
            logs_data = []
            for log in logs:
                log_data = {
                    'log_id': log.log_id,
                    'user_id': log.user_id,
                    'action_type': log.action_type,
                    'action_time': log.action_time.isoformat() if log.action_time else None,
                    'community_id': log.community_id,
                    'details': log.details
                }
                logs_data.append(log_data)

            return UseCaseResult.success({'logs': logs_data}, "获取浏览记录成功")

        except Exception as e:
            return UseCaseResult.fail(f"获取浏览记录失败: {str(e)}")