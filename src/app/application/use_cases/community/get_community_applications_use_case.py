"""
获取社区申请列表用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from database.flask_models import db, CommunityApplication
from sqlalchemy import select, func
from typing import Optional


class GetCommunityApplicationsUseCase(BaseUseCase):
    """获取社区申请列表用例"""

    def _validate(self, user_id: int, page: int = 1, per_page: int = 20, 
                  status_filter: Optional[str] = None) -> UseCaseResult:
        """
        验证参数

        Args:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status_filter: 状态过滤

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="用户ID不能为空"
            )

        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="页码必须大于0"
            )

        if per_page < 1 or per_page > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message="每页数量必须在1-100之间"
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, page: int = 1, per_page: int = 20,
                 status_filter: Optional[str] = None) -> UseCaseResult:
        """
        执行获取社区申请列表

        Args:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status_filter: 状态过滤 (可选: 'pending', 'approved', 'rejected')

        Returns:
            UseCaseResult: 包含申请列表和分页信息
        """
        try:
            # 构建查询条件
            conditions = [CommunityApplication.user_id == user_id]
            
            # 状态过滤
            if status_filter:
                status_map = {
                    'pending': 1,
                    'approved': 2,
                    'rejected': 3
                }
                if status_filter in status_map:
                    conditions.append(CommunityApplication.status == status_map[status_filter])
                else:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message=f"无效的状态过滤值: {status_filter}"
                    )

            # 计算总数
            count_stmt = select(func.count()).select_from(CommunityApplication)
            for condition in conditions:
                count_stmt = count_stmt.where(condition)
            total_result = db.session.execute(count_stmt)
            total = total_result.scalar()

            # 查询申请列表
            offset = (page - 1) * per_page
            stmt = (
                select(CommunityApplication)
                .where(*conditions)
                .order_by(CommunityApplication.created_at.desc())
                .limit(per_page)
                .offset(offset)
            )
            applications = db.session.execute(stmt).scalars().all()

            # 构造返回数据
            applications_data = []
            for app in applications:
                app_data = {
                    'application_id': app.application_id,
                    'community_id': app.target_community_id,
                    'community_name': app.target_community.name if app.target_community else None,
                    'applicant_id': app.user_id,
                    'applicant_name': app.user.nickname if app.user else None,
                    'status': app.status,
                    'status_text': self._get_status_text(app.status),
                    'message': app.reason,
                    'rejection_reason': app.rejection_reason,
                    'created_at': app.created_at.isoformat() if app.created_at else None,
                    'updated_at': app.updated_at.isoformat() if app.updated_at else None
                }
                applications_data.append(app_data)

            response_data = {
                'applications': applications_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'has_next': (page * per_page) < total
            }

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message="获取申请列表成功",
                data=response_data
            )

        except Exception as e:
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"获取申请列表失败: {str(e)}"
            )

    def _get_status_text(self, status: int) -> str:
        """
        获取状态文本

        Args:
            status: 状态码

        Returns:
            str: 状态文本
        """
        status_map = {
            1: 'pending',
            2: 'approved',
            3: 'rejected'
        }
        return status_map.get(status, 'unknown')