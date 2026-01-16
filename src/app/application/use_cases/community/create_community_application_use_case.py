"""
创建社区申请用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from database.flask_models import db, CommunityApplication, Community, User
from sqlalchemy import select
from datetime import datetime


class CreateCommunityApplicationUseCase(BaseUseCase):
    """创建社区申请用例"""

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
            # 检查社区是否存在
            community = db.session.get(Community, community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message="社区不存在"
                )

            # 检查用户是否存在
            user = db.session.get(User, user_id)
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
            db.session.rollback()
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"申请提交失败: {str(e)}"
            )