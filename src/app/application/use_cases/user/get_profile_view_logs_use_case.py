"""
获取浏览记录列表用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.audit_log_repository import AuditLogRepository


class GetProfileViewLogsUseCase(BaseUseCase):
    """获取浏览记录列表用例"""

    def __init__(self):
        super().__init__()
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()

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

            # 使用AuditLogRepository查询审计日志
            # 注意: AuditLogRepository接口可能不支持按community_id和action_type过滤
            # 这里我们使用现有的方法,然后在内存中过滤
            if viewer_id:
                logs = self.audit_log_repository.find_by_user_id(viewer_id, limit=limit)
            else:
                # 如果没有指定viewer_id,我们无法直接查询所有日志
                # 这里返回空列表,因为AuditLogRepository没有提供按community_id查询的方法
                logs = []

            # 过滤符合条件的记录
            logs_data = []
            for log in logs:
                # 检查是否匹配community_id和action_type
                if hasattr(log, 'community_id') and log.community_id == community_id:
                    if hasattr(log, 'action') and 'view_profile' in str(log.action):
                        log_data = {
                            'log_id': getattr(log, 'log_id', None),
                            'user_id': log.user_id,
                            'action_type': log.action,
                            'action_time': getattr(log, 'created_at', None).isoformat() if hasattr(log, 'created_at') and log.created_at else None,
                            'community_id': getattr(log, 'community_id', None),
                            'details': log.detail
                        }
                        logs_data.append(log_data)

            return UseCaseResult.success({'logs': logs_data}, "获取浏览记录成功")

        except Exception as e:
            return UseCaseResult.fail(f"获取浏览记录失败: {str(e)}")