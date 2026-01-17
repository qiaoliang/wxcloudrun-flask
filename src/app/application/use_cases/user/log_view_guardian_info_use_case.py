"""
记录查看监护人信息用例（重构后 - 符合DDD架构）

重构要点：
- 使用 with transaction() 确保事务一致性
- 移除 db.session.commit() 直接提交
- 使用Repository保存审计日志
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.shared.utils.transaction import transaction
from datetime import datetime


class LogViewGuardianInfoUseCase(BaseUseCase):
    """记录查看监护人信息用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        from app.infrastructure.persistence.repository_factory import RepositoryFactory
        # ✅ 通过RepositoryFactory获取Repository接口
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()

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

            # ✅ 使用事务上下文管理器确保事务一致性
            with transaction():
                # 创建审计日志
                from database.flask_models import UserAuditLog
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

                # ✅ 使用Repository保存
                self.audit_log_repository.create(
                    user_id=viewer_id,
                    action='view_guardian_info',
                    detail=f"查看监护人信息: guardian_id={guardian_id}, ward_user_id={ward_user_id}, community_id={community_id}"
                )

            return UseCaseResult.success(None, "记录成功")

        except Exception as e:
            # ✅ 事务会自动回滚
            return UseCaseResult.fail(f"记录失败: {str(e)}")