"""
创建社区申请用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, CommunityApplication, Community, User
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from datetime import datetime
from sqlalchemy import select


class CreateCommunityApplicationUseCase(BaseUseCase):
    """创建社区申请用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def _validate(self, user_id: int, community_id: int, message: str = "") -> UseCaseResult:
        """
        验证参数

        Args:
            user_id: 用户ID
            community_id: 社区ID
            message: 申请消息

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="用户ID不能为空"
            )

        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="社区ID不能为空"
            )

        if message and len(message) > 500:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="申请消息不能超过500个字符"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, community_id: int, message: str = "") -> UseCaseResult:
        """
        执行创建社区申请

        Args:
            user_id: 用户ID
            community_id: 社区ID
            message: 申请消息

        Returns:
            UseCaseResult: 包含创建的申请ID
        """
        try:
            # ✅ 使用Repository代替 db.session.get(Community, community_id)
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="社区不存在"
                )

            # ✅ 使用Repository代替 db.session.get(User, user_id)
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="用户不存在"
                )

            # 检查用户是否已经是该社区的成员
            if user.community_id == community_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message="您已经是该社区的成员"
                )

            # TODO: 需要创建CommunityApplicationRepository后再重构
            # 暂时保留直接访问
            from database.flask_models import db, CommunityApplication

            # 检查是否已经有待审核的申请
            existing_application = db.session.execute(
                select(CommunityApplication).where(
                    CommunityApplication.user_id == user_id,
                    CommunityApplication.target_community_id == community_id,
                    CommunityApplication.status == 1  # 待审核
                )
            ).scalar_one_or_none()

            if existing_application:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message="您已经有一个待审核的申请"
                )

            # 创建申请
            application = CommunityApplication(
                user_id=user_id,
                target_community_id=community_id,
                status=1,  # 待审核
                reason=message,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.session.add(application)
            db.session.flush()  # 获取application_id

            response_data = {
                'application_id': application.application_id,
                'message': '申请提交成功'
            }

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message="申请提交成功",
                data=response_data
            )

        except Exception as e:
            from database.flask_models import db
            db.session.rollback()
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"申请提交失败: {str(e)}"
            )
