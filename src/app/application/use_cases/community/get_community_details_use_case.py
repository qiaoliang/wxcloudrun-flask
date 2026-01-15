"""
获取社区详情用例
"""
import json
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import Community


class GetCommunityDetailsUseCase(BaseUseCase):
    """获取社区详情用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(self, community_id: int) -> UseCaseResult:
        """
        执行获取社区详情用例

        Args:
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区ID不能为空'
                )

            # 2. 查询社区
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 查询创建者信息
            creator = None
            if community.creator_id:
                creator = self.user_repository.find_by_id(community.creator_id)

            # 4. 查询主管信息
            manager = None
            if community.manager_id:
                manager = self.user_repository.find_by_id(community.manager_id)

            # 5. 统计社区工作人员数量
            staff_count = self.community_staff_repository.count_by_community_id(community_id)

            # 6. 统计社区用户数量
            user_count = len(self.user_repository.find_by_community_id(community_id))

            # 7. 处理 settings 字段
            settings_dict = None
            if community.settings:
                try:
                    settings_dict = json.loads(community.settings)
                except json.JSONDecodeError:
                    settings_dict = {}

            # 8. 构造响应数据
            response_data = {
                'community_id': community.community_id,
                'name': community.name,
                'description': community.description,
                'creator_id': community.creator_id,
                'manager_id': community.manager_id,
                'location': community.location,
                'location_lat': community.location_lat,
                'location_lon': community.location_lon,
                'province': community.province,
                'city': community.city,
                'district': community.district,
                'street': community.street,
                'status': community.status,
                'settings': settings_dict,
                'created_at': community.created_at.isoformat() if community.created_at else None,
                'updated_at': community.updated_at.isoformat() if community.updated_at else None,
                'creator': {
                    'user_id': creator.user_id,
                    'nickname': creator.nickname,
                    'phone_number': creator.phone_number
                } if creator else None,
                'manager': {
                    'user_id': manager.user_id,
                    'nickname': manager.nickname,
                    'phone_number': manager.phone_number
                } if manager else None,
                'staff_count': staff_count,
                'user_count': user_count
            }

            self.logger.info(f'获取社区详情成功: community_id={community_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取社区详情成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'获取社区详情失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取社区详情失败: {str(e)}'
            )