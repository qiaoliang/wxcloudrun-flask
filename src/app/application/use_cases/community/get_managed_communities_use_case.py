"""
获取可管理社区列表用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetManagedCommunitiesUseCase(BaseUseCase):
    """获取可管理社区列表用例"""

    def __init__(self):
        super().__init__()
        self.community_staff_repo = RepositoryFactory.get_community_staff_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.logger = logging.getLogger(__name__)

    def execute(self, user_id: int, limit: int = 7) -> UseCaseResult:
        """
        执行获取可管理社区列表用例

        Args:
            user_id: 用户ID
            limit: 返回社区数量限制

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询用户作为工作人员的社区
            # 用户可以管理的社区包括：用户是工作人员的社区
            staff_relations = self.community_staff_repo.find_by_user_id(user_id, include_removed=False)
            
            # 构造社区列表
            communities_data = []
            for staff_relation in staff_relations:
                # 获取社区对象
                community = self.community_repository.find_by_id(staff_relation.community_id)
                
                # 只返回活跃的社区（status == 1）
                if community and community.status == 1:
                    communities_data.append({
                        'community_id': community.community_id,
                        'name': community.name,
                        'description': community.description,
                        'location': community.location,
                        'status': community.status,
                        'role': staff_relation.role,
                        'created_at': community.created_at.isoformat() if community.created_at else None
                    })
            
            # 3. 查询用户创建的社区（即使不在 community_staff 表中）
            created_communities = self.community_repository.find_by_creator_id(user_id)
            for community in created_communities:
                # 只返回活跃的社区（status == 1）
                if community.status == 1:
                    # 检查是否已经在列表中
                    exists = any(c['community_id'] == community.community_id for c in communities_data)
                    if not exists:
                        communities_data.append({
                            'community_id': community.community_id,
                            'name': community.name,
                            'description': community.description,
                            'location': community.location,
                            'status': community.status,
                            'role': 'creator',  # 标记为创建者
                            'created_at': community.created_at.isoformat() if community.created_at else None
                        })
            
            # 按创建时间倒序排序
            communities_data.sort(key=lambda x: x['created_at'] or '', reverse=True)
            
            # 应用 limit 限制
            if limit > 0:
                communities_data = communities_data[:limit]

            self.logger.info(f'获取可管理社区列表成功: user_id={user_id}, count={len(communities_data)}')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取可管理社区列表成功',
                data={'communities': communities_data, 'count': len(communities_data)}
            )

        except Exception as e:
            self.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取可管理社区列表失败: {str(e)}'
            )