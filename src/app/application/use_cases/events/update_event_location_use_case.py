"""
更新事件位置用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.event_bus import EventBus
from app.domain.events.community_events import EventLocationUpdatedEvent
from app.shared.utils.transaction import transactional


class UpdateEventLocationUseCase(BaseUseCase):
    """更新事件位置用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.event_bus = EventBus()

    @transactional

    def execute(
        self,
        event_id: int,
        user_id: int,
        location: str,
        location_lat: float = None,
        location_lon: float = None
    ) -> UseCaseResult:
        """
        执行更新事件位置用例

        Args:
            event_id: 事件ID
            user_id: 用户ID
            location: 位置描述
            location_lat: 纬度
            location_lon: 经度

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not event_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='事件ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 至少需要位置描述或坐标信息
            has_location = location and location.strip()
            has_coordinates = location_lat is not None and location_lon is not None

            if not has_location and not has_coordinates:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='请至少提供位置描述或坐标信息'
                )

            # 2. 查询事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 3. 验证事件状态（只有未关闭的事件可以更新）
            if event.status != 1:  # 1=pending
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='事件已关闭，无法更新位置'
                )

            # 4. 验证权限（只有事件目标用户或社区工作人员可以更新）
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            if event.target_user_id != user_id and user.role not in [2, 3, 4]:  # 不是社区工作人员
                return UseCaseResult(
                    status=UseCaseStatus.UNAUTHORIZED,
                    message='无权更新此事件位置'
                )

            # 5. 更新事件位置
            event.location = location.strip()
            if location_lat is not None:
                event.location_lat = location_lat
            if location_lon is not None:
                event.location_lon = location_lon

            # 6. 保存更新
            updated_event = self.community_event_repository.save(event)

            self.logger.info(f'更新事件位置成功: event_id={event_id}')

            # 7. 发布领域事件
            self.event_bus.publish(EventLocationUpdatedEvent(
                event_id=event_id,
                community_id=event.community_id,
                location=location.strip(),
                location_lat=location_lat,
                location_lon=location_lon
            ))

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='事件位置更新成功',
                data={
                    'event_id': updated_event.event_id,
                    'location': updated_event.location,
                    'location_lat': updated_event.location_lat,
                    'location_lon': updated_event.location_lon
                }
            )

        except Exception as e:
            self.logger.error(f'更新事件位置失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新事件位置失败: {str(e)}'
            )