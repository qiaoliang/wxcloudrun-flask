"""
获取社区列表用例（统一接口）
支持通过 type 参数获取不同类型的社区列表
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.application.use_cases.auth import GetCurrentUserUseCase
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunitiesUseCase(BaseUseCase):
    """获取社区列表用例（统一接口）"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()
        self.get_current_user_use_case = GetCurrentUserUseCase()
        self.logger = logging.getLogger(__name__)

    def execute(self, params: dict) -> UseCaseResult:
        """
        执行获取社区列表用例

        Args:
            params: 参数字典，包含：
                - type: 社区类型 ('all', 'available', 'managed')
                - user_id: 用户ID（必需，除了 type='all' 时可选）
                - limit: 返回数量限制（可选，默认100）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            community_type = params.get('type', 'all')
            user_id = params.get('user_id')
            limit = params.get('limit', 100)

            # 验证 type 参数
            if community_type not in ['all', 'available', 'managed']:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='type参数必须是 all、available 或 managed'
                )

            # 验证 limit 参数
            try:
                limit = int(limit)
                if limit < 1 or limit > 1000:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='limit参数必须在1-1000之间'
                    )
            except (ValueError, TypeError):
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='limit参数必须是整数'
                )

            # 2. 权限检查和数据获取
            communities_data = []

            if community_type == 'all':
                # 获取所有社区（需要超级管理员权限）
                if not user_id:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='缺少user_id参数'
                    )

                # 获取用户对象
                user_result = self.get_current_user_use_case.execute(user_id)
                if not user_result.is_success:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message='用户不存在'
                    )
                user = user_result.data

                # 检查超级管理员权限
                error = _check_superadmin_permission(user)
                if error:
                    return UseCaseResult(
                        status=UseCaseStatus.FORBIDDEN,
                        message='需要超级管理员权限'
                    )

                # 获取所有社区
                communities = self.community_repository.get_all()
                communities_data = self._format_communities(communities, include_worker_stats=True)

            elif community_type == 'available':
                # 获取可加入社区（用户可见）
                if not user_id:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='缺少user_id参数'
                    )

                # 获取活跃社区
                communities = self.community_repository.find_active_communities()
                communities_data = self._format_communities(communities, include_worker_stats=True)

            elif community_type == 'managed':
                # 获取用户管理的社区
                if not user_id:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='缺少user_id参数'
                    )

                # 查询用户作为工作人员的社区
                staff_relations = self.community_staff_repository.find_by_user_id(user_id, include_removed=False)

                # 获取社区对象
                community_ids = [rel.community_id for rel in staff_relations]
                communities = []
                for community_id in community_ids:
                    community = self.community_repository.find_by_id(community_id)
                    if community and community.status == 1:  # 只返回活跃社区
                        communities.append(community)

                # 格式化社区信息
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

                # 按创建时间倒序排序
                communities_data.sort(key=lambda x: x['created_at'] or '', reverse=True)

                # 应用 limit 限制
                if limit > 0:
                    communities_data = communities_data[:limit]

                print(f'Layer 2: 最终返回 {len(communities_data)} 个社区')

            self.logger.info(f'Layer 2: 业务逻辑验证 - 获取社区列表成功: type={community_type}, count={len(communities_data)}')
            if len(communities_data) == 0:
                self.logger.warning(f'Layer 2: 警告 - 没有返回任何社区！')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取社区列表成功',
                data={'communities': communities_data, 'count': len(communities_data)}
            )

        except Exception as e:
            self.logger.error(f'获取社区列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区列表失败: {str(e)}'
            )

    def _format_communities(self, communities, include_worker_stats=False):
        """格式化社区列表"""
        from .format_community_info_use_case import FormatCommunityInfoUseCase

        format_use_case = FormatCommunityInfoUseCase()
        communities_data = []

        for community in communities:
            result = format_use_case.execute(community, include_worker_stats=include_worker_stats)
            if result.is_success:
                communities_data.append(result.data)

        return communities_data