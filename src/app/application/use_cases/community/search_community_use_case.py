"""
搜索社区用例
"""
import logging
from typing import Optional, List

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.repositories.community_repository import CommunityRepository


class SearchCommunityUseCase(BaseUseCase):
    """搜索社区用例"""

    def __init__(self):
        super().__init__()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(
        self,
        keyword: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行搜索社区用例

        Args:
            keyword: 搜索关键词（社区名称、描述）
            province: 省份
            city: 城市
            district: 区县
            status: 社区状态
            page: 页码
            page_size: 每页数量

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if page < 1:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='页码必须大于0'
                )

            if page_size < 1 or page_size > 100:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='每页数量必须在1-100之间'
                )

            # 2. 搜索社区
            communities = self.community_repository.search(
                keyword=keyword,
                province=province,
                city=city,
                district=district,
                status=status
            )

            # 3. 分页处理
            total = len(communities)
            start = (page - 1) * page_size
            end = start + page_size
            paged_communities = communities[start:end]

            # 4. 构造响应数据
            community_list = []
            for community in paged_communities:
                community_list.append({
                    'community_id': community.community_id,
                    'name': community.name,
                    'description': community.description,
                    'location': community.location,
                    'province': community.province,
                    'city': community.city,
                    'district': community.district,
                    'street': community.street,
                    'status': community.status,
                    'created_at': community.created_at.isoformat() if community.created_at else None
                })

            response_data = {
                'communities': community_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

            self.logger.info(f'搜索社区成功: keyword={keyword}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='搜索社区成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'搜索社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'搜索社区失败: {str(e)}'
            )