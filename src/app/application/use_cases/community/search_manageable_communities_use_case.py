"""
搜索可管理的社区用例
"""
import logging
from sqlalchemy import or_, and_

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.domain.repositories.community_repository import CommunityRepository
from app.domain.repositories.community_staff_repository import CommunityStaffRepository


class SearchManageableCommunitiesUseCase(BaseUseCase):
    """搜索可管理的社区用例"""

    def __init__(self):
        super().__init__()
        self.community_repo = CommunityRepository()
        self.community_staff_repo = CommunityStaffRepository()
        self.logger = logging.getLogger(__name__)

    def _validate(self, user_id: int, keyword: str, page: int, per_page: int, **kwargs) -> UseCaseResult:
        """验证参数"""
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID不能为空'
            )

        if not keyword or not keyword.strip():
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='搜索关键词不能为空'
            )

        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='页码必须大于0'
            )

        if per_page < 1 or per_page > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, keyword: str, page: int, per_page: int) -> UseCaseResult:
        """
        执行搜索可管理社区逻辑

        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 计算偏移量
            offset = (page - 1) * per_page

            # 查询用户可管理的社区
            # 用户可以管理的社区包括：
            # - 用户是工作人员的社区
            # - 社区名称或地址包含关键词

            # 构建查询
            query = db.session.query(Community).join(CommunityStaff).filter(
                CommunityStaff.user_id == user_id,
                Community.status == 1,
                or_(
                    Community.name.like(f'%{keyword}%'),
                    Community.location.like(f'%{keyword}%'),
                    Community.description.like(f'%{keyword}%')
                )
            )

            # 获取总数
            total = query.count()

            # 分页查询
            communities = query.order_by(Community.created_at.desc()).offset(offset).limit(per_page).all()

            # 构造返回数据
            communities_data = []
            for community in communities:
                communities_data.append({
                    'community_id': community.community_id,
                    'name': community.name,
                    'description': community.description,
                    'location': community.location,
                    'status': community.status,
                    'created_at': community.created_at.isoformat() if community.created_at else None
                })

            self.logger.info(f'搜索可管理社区成功: user_id={user_id}, keyword={keyword}, count={len(communities_data)}, total={total}')

            # 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='搜索成功',
                data={
                    'communities': communities_data,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'has_next': len(communities_data) == per_page
                }
            )

        except Exception as e:
            self.logger.error(f'搜索可管理社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'搜索失败: {str(e)}'
            )