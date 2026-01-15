"""
创建社区用例
"""
import json
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.domain.entities.user_entity import UserEntity
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.community_events import CommunityCreatedEvent
from app.domain.events.event_bus import event_bus
from database.flask_models import Community


class CreateCommunityUseCase(BaseUseCase):
    """创建社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        name: str,
        description: str,
        creator_id: int,
        location: Optional[str] = None,
        settings: Optional[dict] = None,
        manager_id: Optional[int] = None,
        location_lat: Optional[float] = None,
        location_lon: Optional[float] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        street: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行创建社区用例

        Args:
            name: 社区名称
            description: 社区描述
            creator_id: 创建者ID
            location: 地理位置
            settings: 社区设置
            manager_id: 主管ID
            location_lat: 纬度
            location_lon: 经度
            province: 省份
            city: 城市
            district: 区县
            street: 街道

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not name or not name.strip():
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区名称不能为空'
                )

            # description 是可选的，如果为空则使用默认值
            if not description:
                description = f'{name}的描述'

            # 2. 验证创建者是否存在
            creator = self.user_repository.find_by_id(creator_id)
            if not creator:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='创建者不存在'
                )

            # 3. 检查社区名称是否已存在
            existing_community = self.community_repository.find_by_name(name)
            if existing_community:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=f'社区名称已存在: {name}'
                )

            # 4. 处理 settings 字段
            settings_json = None
            if settings is not None:
                if isinstance(settings, dict):
                    settings_json = json.dumps(settings)
                else:
                    settings_json = settings

            # 5. 创建社区
            community = Community(
                name=name.strip(),
                description=description,
                creator_id=creator_id,
                location=location,
                settings=settings_json,
                manager_id=manager_id,
                location_lat=location_lat,
                location_lon=location_lon,
                province=province,
                city=city,
                district=district,
                street=street,
                status=1
            )

            saved_community = self.community_repository.save(community)

            self.logger.info(f'创建社区成功: community_id={saved_community.community_id}, name={name}')

            # 6. 发布领域事件
            event = CommunityCreatedEvent(
                community_id=saved_community.community_id,
                creator_id=creator_id,
                community_name=name
            )
            event_bus.publish(event)

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='社区创建成功',
                data={
                    'community_id': saved_community.community_id,
                    'name': saved_community.name,
                    'description': saved_community.description,
                    'creator_id': saved_community.creator_id,
                    'location': saved_community.location,
                    'status': saved_community.status
                }
            )

        except ValueError as e:
            self.logger.error(f'创建社区失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'创建社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建社区失败: {str(e)}'
            )