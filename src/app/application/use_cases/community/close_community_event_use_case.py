"""
关闭社区事件用例
"""
import logging
from datetime import datetime
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, CommunityEvent, CommunityStaff
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class CloseCommunityEventUseCase(BaseUseCase):
    """关闭社区事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        event_id: int,
        user_id: int,
        closure_reason: str
    ) -> UseCaseResult:
        """
        执行关闭社区事件

        Args:
            event_id: 事件ID
            user_id: 当前用户ID
            closure_reason: 关闭原因（10-500字符）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(event_id, closure_reason)
            if not validation_result.is_success:
                return validation_result

            # 2. 验证事件存在
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 3. 验证事件状态
            if event.status != 1:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'事件已关闭，当前状态为 {event.status_label}'
                )

            # 4. 验证权限
            permission_check = self._check_permission(event, user_id)
            if not permission_check['has_permission']:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message=permission_check['message']
                )

            # 5. 确定关闭类型
            closure_type = 2 if permission_check['is_staff'] else 1

            # 6. 更新事件
            with transaction():
                event.status = 2  # 已完成
                event.completed_at = datetime.now()
                event.closed_by = user_id
                event.closed_at = datetime.now()
                event.closure_type = closure_type
                event.closure_reason = closure_reason
                db.session.flush()

            logger.info(f"用户{user_id}关闭了事件{event_id}，类型：{closure_type}，原因：{closure_reason}")

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='事件已关闭',
                data={
                    'event_id': event.event_id,
                    'closed_by': event.closed_by,
                    'closed_at': event.closed_at.isoformat() if event.closed_at else None,
                    'closure_type': event.closure_type,
                    'closure_type_label': event.closure_type_label,
                    'closure_reason': event.closure_reason
                }
            )

        except Exception as e:
            logger.error(f"关闭事件失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'关闭事件失败: {str(e)}'
            )

    def _validate_params(self, event_id: int, closure_reason: str) -> UseCaseResult:
        """验证参数"""
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

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _check_permission(self, event: CommunityEvent, user_id: int) -> dict:
        """
        检查用户是否有权限关闭事件

        Returns:
            dict: {
                'has_permission': bool,
                'is_staff': bool,
                'message': str
            }
        """
        # 检查是否为事件发起者
        is_creator = (event.created_by == user_id)

        # 检查是否为目标用户
        is_target_user = (event.target_user_id == user_id)

        # 检查是否为社区工作人员
        stmt_staff = select(CommunityStaff).where(
            CommunityStaff.community_id == event.community_id,
            CommunityStaff.user_id == user_id,
            CommunityStaff.removed_at.is_(None)
        )
        is_staff = db.session.execute(stmt_staff).scalar_one_or_none() is not None

        # 只有事件发起者、目标用户或社区工作人员可以关闭事件
        if not (is_creator or is_target_user or is_staff):
            return {
                'has_permission': False,
                'is_staff': False,
                'message': '只有事件发起者、目标用户或社区工作人员可以关闭事件'
            }

        return {
            'has_permission': True,
            'is_staff': is_staff,
            'message': '权限验证通过'
        }
