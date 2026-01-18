"""
更新社区用例
"""
import json
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.community_events import CommunityUpdatedEvent, CommunityManagerChangedEvent, CommunityStatusChangedEvent, CommunitySettingsUpdatedEvent
from app.domain.events.event_bus import event_bus
from app.domain.repositories.community_repository import CommunityRepository
from app.shared.utils.transaction import transactional


class UpdateCommunityUseCase(BaseUseCase):
    """更新社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    @transactional

    def execute(
        self,
        community_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        settings: Optional[dict] = None,
        manager_id: Optional[int] = None,
        location_lat: Optional[float] = None,
        location_lon: Optional[float] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        street: Optional[str] = None,
        status: Optional[int] = None
    ) -> UseCaseResult:
        """
        执行更新社区用例

        Args:
            community_id: 社区ID
            name: 社区名称
            description: 社区描述
            location: 地理位置
            settings: 社区设置
            manager_id: 主管ID
            location_lat: 纬度
            location_lon: 经度
            province: 省份
            city: 城市
            district: 区县
            street: 街道
            status: 社区状态

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

            # 3. 更新社区信息
            if name is not None:
                if not name or not name.strip():
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='社区名称不能为空'
                    )

                # 检查社区名称是否已存在（排除自己）
                existing_community = self.community_repository.find_by_name(name.strip())
                if existing_community and existing_community.community_id != community_id:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message=f'社区名称已存在: {name}'
                    )

                community.name = name.strip()

            if description is not None:
                if not description:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='社区描述不能为空'
                    )
                community.description = description

            if location is not None:
                community.location = location

            if settings is not None:
                if isinstance(settings, dict):
                    community.settings = json.dumps(settings)
                else:
                    community.settings = settings

            if manager_id is not None:
                # 验证主管是否存在
                if manager_id:
                    manager = self.user_repository.find_by_id(manager_id)
                    if not manager:
                        return UseCaseResult(
                            status=UseCaseStatus.NOT_FOUND,
                            message='主管不存在'
                        )
                community.manager_id = manager_id

            if location_lat is not None:
                community.location_lat = location_lat

            if location_lon is not None:
                community.location_lon = location_lon

            if province is not None:
                community.province = province

            if city is not None:
                community.city = city

            if district is not None:
                community.district = district

            if street is not None:
                community.street = street

            if status is not None:
                community.status = status

            # 4. 保存更新
            updated_community = self.community_repository.save(community)

            self.logger.info(f'更新社区成功: community_id={community_id}')

            # 5. 发布领域事件
            updated_fields = {}
            if name is not None:
                updated_fields['name'] = name
            if description is not None:
                updated_fields['description'] = description
            if location is not None:
                updated_fields['location'] = location
            if manager_id is not None:
                updated_fields['manager_id'] = manager_id
                # 发布主管变更事件
                manager_change_event = CommunityManagerChangedEvent(
                    community_id=community_id,
                    old_manager_id=community.manager_id,
                    new_manager_id=manager_id
                )
                event_bus.publish(manager_change_event)
            if status is not None:
                updated_fields['status'] = status
                # 发布状态变更事件
                status_change_event = CommunityStatusChangedEvent(
                    community_id=community_id,
                    old_status=community.status,
                    new_status=status,
                    operator_id=0  # TODO: 从上下文获取操作者ID
                )
                event_bus.publish(status_change_event)
            if settings is not None:
                updated_fields['settings'] = settings
                # 发布设置更新事件
                settings_event = CommunitySettingsUpdatedEvent(
                    community_id=community_id,
                    settings=settings,
                    operator_id=0  # TODO: 从上下文获取操作者ID
                )
                event_bus.publish(settings_event)

            if updated_fields:
                update_event = CommunityUpdatedEvent(
                    community_id=community_id,
                    updater_id=0,  # TODO: 从上下文获取操作者ID
                    updated_fields=updated_fields
                )
                event_bus.publish(update_event)

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='社区更新成功',
                data={
                    'community_id': updated_community.community_id,
                    'name': updated_community.name,
                    'description': updated_community.description,
                    'location': updated_community.location,
                    'status': updated_community.status
                }
            )

        except Exception as e:
            self.logger.error(f'更新社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新社区失败: {str(e)}'
            )