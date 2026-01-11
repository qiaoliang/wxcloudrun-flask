"""
关闭事件用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CommunityEvent


class CloseEventUseCase(BaseUseCase):
    """关闭事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(
        self,
        user_id: int,
        event_id: int,
        closure_reason: str
    ) -> UseCaseResult:
        """
        执行关闭事件用例

        Args:
            user_id: 用户ID
            event_id: 事件ID
            closure_reason: 关闭原因

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

            if not closure_reason or len(closure_reason) < 10 or len(closure_reason) > 500:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='关闭原因长度必须在10-500字符之间'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 4. 验证事件状态
            if event.status != 1:  # 不是进行中状态
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=f'事件当前状态为 {event.status_label}，无法关闭'
                )

            # 5. 验证权限（事件发起者、目标用户、社区工作人员）
            is_creator = (event.created_by == user_id)
            is_target_user = (event.target_user_id == user_id)
            is_staff = self.community_staff_repository.exists(event.community_id, user_id)

            if not (is_creator or is_target_user or is_staff):
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='只有事件发起者、目标用户或社区工作人员可以关闭事件'
                )

            # 6. 确定关闭类型
            closure_type = 2 if is_staff else 1  # 1=用户关闭，2=工作人员关闭

            # 7. 关闭事件
            success = self.community_event_repository.close_event(
                event_id=event_id,
                closed_by=user_id,
                closure_type=closure_type,
                closure_reason=closure_reason
            )

            if not success:
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='关闭事件失败'
                )

            # 8. 获取更新后的事件
            updated_event = self.community_event_repository.find_by_id(event_id)

            self.logger.info(f"用户{user_id}关闭了事件{event_id}，类型：{closure_type}，原因：{closure_reason}")

            # 9. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='事件已关闭',
                data={
                    'event_id': updated_event.event_id,
                    'closed_by': updated_event.closed_by,
                    'closed_at': updated_event.closed_at.isoformat() if updated_event.closed_at else None,
                    'closure_type': updated_event.closure_type,
                    'closure_type_label': updated_event.closure_type_label,
                    'closure_reason': updated_event.closure_reason
                }
            )

        except ValueError as e:
            self.logger.error(f'关闭事件失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'关闭事件失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'关闭事件失败: {str(e)}'
            )