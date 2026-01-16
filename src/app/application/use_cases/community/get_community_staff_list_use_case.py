"""
获取社区工作人员列表用例
"""

import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from database.flask_models import db, User, CommunityStaff
from sqlalchemy import select, func
from app.shared.constants.roles import STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF

logger = logging.getLogger(__name__)


class GetCommunityStaffListUseCase(BaseUseCase):
    """获取社区工作人员列表用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        community_id: int,
        role: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> UseCaseResult:
        """
        获取社区工作人员列表

        Args:
            community_id: 社区ID
            role: 角色筛选 ('manager', 'staff' 或 None 表示全部)
            page: 页码，从1开始
            limit: 每页数量

        Returns:
            UseCaseResult: 包含工作人员列表和分页信息
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(community_id, role, page, limit)
            if not validation_result.is_success:
                return validation_result

            # 2. 构建查询
            stmt = select(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.removed_at.is_(None)
            )

            # 角色筛选
            if role and role != 'all':
                if role == 'manager':
                    stmt = stmt.where(CommunityStaff.role == STAFF_ROLE_MANAGER)
                elif role == 'staff':
                    stmt = stmt.where(CommunityStaff.role == STAFF_ROLE_STAFF)

            # 获取总数
            count_stmt = select(func.count()).select_from(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.removed_at.is_(None)
            )
            if role and role != 'all':
                if role == 'manager':
                    count_stmt = count_stmt.where(CommunityStaff.role == STAFF_ROLE_MANAGER)
                elif role == 'staff':
                    count_stmt = count_stmt.where(CommunityStaff.role == STAFF_ROLE_STAFF)

            total_count = db.session.execute(count_stmt).scalar()

            # 添加排序和分页
            stmt = stmt.order_by(CommunityStaff.added_at.desc())
            stmt = stmt.offset((page - 1) * limit).limit(limit)

            # 执行查询
            staff_list = db.session.execute(stmt).scalars().all()

            # 3. 构造返回数据
            staff_data = []
            for staff in staff_list:
                user = db.session.get(User, staff.user_id)
                if user:
                    staff_info = {
                        'staff_id': staff.id,
                        'user_id': user.user_id,
                        'wechat_openid': user.wechat_openid,
                        'phone_number': user.phone_number,
                        'nickname': user.nickname,
                        'name': user.name,
                        'avatar_url': user.avatar_url,
                        'role': staff.role,
                        'added_at': staff.added_at.isoformat() if staff.added_at else None
                    }
                    staff_data.append(staff_info)

            # 计算分页信息
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
            has_more = page < total_pages

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取工作人员列表成功',
                data={
                    'staff': staff_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total_count,
                        'total_pages': total_pages,
                        'has_more': has_more
                    }
                }
            )

        except Exception as e:
            logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取工作人员列表失败: {str(e)}'
            )

    def _validate_params(
        self,
        community_id: int,
        role: Optional[str],
        page: int,
        limit: int
    ) -> UseCaseResult:
        """验证参数"""
        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少社区ID'
            )

        # 验证role参数
        if role and role not in ['all', 'manager', 'staff']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=f'无效的角色参数，支持的角色: all, manager, staff'
            )

        # 验证分页参数
        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='页码必须大于0'
            )

        if limit < 1 or limit > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )