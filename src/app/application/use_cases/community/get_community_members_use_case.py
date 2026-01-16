"""
获取社区成员列表用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, User, Community
from sqlalchemy import select, func


class GetCommunityMembersUseCase(BaseUseCase):
    """获取社区成员列表用例"""

    def execute(self, community_id: int, page: int = 1, per_page: int = 20) -> UseCaseResult:
        """
        获取社区成员列表

        Args:
            community_id: 社区ID
            page: 页码
            per_page: 每页数量

        Returns:
            UseCaseResult: 包含成员列表和总数
        """
        try:
            if not community_id:
                return UseCaseResult.fail("社区ID不能为空")

            # 计算总数
            count_stmt = db.session.execute(
                db.select(func.count(User.user_id)).where(User.community_id == community_id)
            )
            total = count_stmt.scalar()

            # 查询成员
            offset = (page - 1) * per_page
            stmt = db.session.execute(
                db.select(User)
                .where(User.community_id == community_id)
                .order_by(User.created_at.desc())
                .limit(per_page)
                .offset(offset)
            )
            members = stmt.scalars().all()

            # 构造返回数据
            members_data = []
            for member in members:
                member_data = {
                    'user_id': member.user_id,
                    'nickname': member.nickname,
                    'avatar_url': member.avatar_url,
                    'name': member.name,
                    'role': member.role,
                    'role_name': member.role_name,
                    'phone_number': member.phone_number,
                    'created_at': member.created_at.isoformat() if member.created_at else None
                }
                members_data.append(member_data)

            return UseCaseResult.success({
                'members': members_data,
                'total': total,
                'page': page,
                'per_page': per_page
            }, "获取成员列表成功")

        except Exception as e:
            return UseCaseResult.fail(f"获取成员列表失败: {str(e)}")