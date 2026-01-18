"""
创建社区事件用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User, Community, CommunityEvent
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class CreateCommunityEventUseCase(BaseUseCase):
    """创建社区事件用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.event_repository = RepositoryFactory.get_community_event_repository()

    @transactional


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
            # ✅ 使用Repository代替 db.session.get(User, user_id)
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # ✅ 使用Repository代替 db.session.get(Community, community_id)
            community = self.community_repository.find_by_id(community_id)
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
                # 需要导入CommunityEvent模型来创建实例
                from database.flask_models import CommunityEvent
                event = CommunityEvent(
                    community_id=community_id,
                    title=title,
                    description=description,
                    event_type=event_type,
                    location=location,
                    target_user_id=target_user_id,
                    created_by=user_id
                )
                # ✅ 使用Repository保存
                self.event_repository.save(event)

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
        # ✅ 使用Repository查找进行中的一键求助事件
        ongoing_events = self.event_repository.find_by_target_user_id(target_user_id, status=1)
        call_for_help_events = [e for e in ongoing_events if e.event_type == 'call_for_help']

        if call_for_help_events:
            existing_event = call_for_help_events[0]
            logger.warning(f"用户{target_user_id}已有进行中的一键求助事件{existing_event.event_id}")
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='您已有进行中的求助事件，请先关闭或等待工作人员处理'
            )

        return None
