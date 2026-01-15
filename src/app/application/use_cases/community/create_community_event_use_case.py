"""
创建社区事件用例
"""
import logging
from typing import Optional
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, User, Community, CommunityEvent
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class CreateCommunityEventUseCase(BaseUseCase):
    """创建社区事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(
        self,
        user_id: int,
        community_id: int,
        title: str,
        description: str = "",
        event_type: str = "call_for_help",
        location: str = "",
        target_user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        执行创建社区事件

        Args:
            user_id: 创建者用户ID
            community_id: 社区ID
            title: 事件标题
            description: 事件描述
            event_type: 事件类型
            location: 事件地点
            target_user_id: 目标用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(user_id, community_id, title)
            if not validation_result.is_success:
                return validation_result

            # 2. 验证用户和社区
            user = db.session.get(User, user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            community = db.session.get(Community, community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 验证用户是否属于该社区
            if user.community_id != community_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='用户不属于该社区'
                )

            # 4. 检查是否为一键求助类型且已有进行中的事件
            if event_type == 'call_for_help' and target_user_id:
                existing_check = self._check_existing_active_event(target_user_id)
                if existing_check:
                    return existing_check

            # 5. 创建事件
            with transaction():
                event = CommunityEvent(
                    community_id=community_id,
                    title=title,
                    description=description,
                    event_type=event_type,
                    location=location,
                    target_user_id=target_user_id,
                    created_by=user_id
                )
                db.session.add(event)
                db.session.flush()

            logger.info(f"用户{user_id}在社区{community_id}创建了事件{event.event_id}")

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='事件创建成功',
                data={'event': event.to_dict()}
            )

        except Exception as e:
            logger.error(f"创建事件失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建事件失败: {str(e)}'
            )

    def _validate_params(self, user_id: int, community_id: int, title: str) -> UseCaseResult:
        """验证基本参数"""
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID不能为空'
            )

        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID不能为空'
            )

        if not title or not title.strip():
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='事件标题不能为空'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _check_existing_active_event(self, target_user_id: int) -> Optional[UseCaseResult]:
        """检查用户是否已有进行中的一键求助事件"""
        stmt_existing = select(CommunityEvent).where(
            CommunityEvent.target_user_id == target_user_id,
            CommunityEvent.event_type == 'call_for_help',
            CommunityEvent.status == 1  # 进行中
        )
        existing_event = db.session.execute(stmt_existing).scalars().first()

        if existing_event:
            logger.warning(f"用户{target_user_id}已有进行中的一键求助事件{existing_event.event_id}")
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='您已有进行中的求助事件，请先关闭或等待工作人员处理'
            )

        return None
