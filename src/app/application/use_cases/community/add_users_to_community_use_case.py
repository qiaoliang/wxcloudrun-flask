"""
批量添加用户到社区用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, User
from sqlalchemy import select


class AddUsersToCommunityUseCase(BaseUseCase):
    """批量添加用户到社区用例"""

    def execute(self, community_id: int, user_ids: list) -> UseCaseResult:
        """
        批量添加用户到社区

        Args:
            community_id: 社区ID
            user_ids: 用户ID列表

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if not community_id or not user_ids:
                return UseCaseResult.fail("参数不能为空")

            # 查询所有用户
            stmt = db.session.execute(
                db.select(User).where(User.user_id.in_(user_ids))
            )
            users = stmt.scalars().all()

            if not users:
                return UseCaseResult.fail("未找到用户")

            # 更新用户的社区ID
            updated_count = 0
            for user in users:
                if user.community_id != community_id:
                    user.community_id = community_id
                    updated_count += 1

            db.session.commit()

            return UseCaseResult.success({
                'community_id': community_id,
                'updated_count': updated_count
            }, f"成功添加 {updated_count} 个用户到社区")

        except Exception as e:
            db.session.rollback()
            return UseCaseResult.fail(f"添加用户失败: {str(e)}")