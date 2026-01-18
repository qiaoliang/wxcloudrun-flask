"""
上传头像用例
"""
import logging
import os
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.user_entity import UserEntity
from app.domain.aggregates.user_aggregate import UserAggregate
from app.domain.events.event_bus import EventBus
from app.domain.repositories.user_repository import UserRepository


class UploadAvatarUseCase(BaseUseCase):
    """上传头像用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.event_bus = EventBus()

    @transactional


    def execute(
        self,
        user_id: int,
        file_data: bytes,
        file_name: str,
        content_type: str
    ) -> UseCaseResult:
        """
        执行上传头像用例

        Args:
            user_id: 用户ID
            file_data: 文件数据
            file_name: 文件名
            content_type: 文件类型

        Returns:
            UseCaseResult: 执行结果
        """
        try:
from app.shared.utils.transaction import transactional
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if not file_data:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='文件数据不能为空'
                )

            if not file_name:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='文件名不能为空'
                )

            # 2. 验证文件类型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if content_type not in allowed_types:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'不支持的文件类型: {content_type}'
                )

            # 3. 验证文件大小（限制为 5MB）
            max_size = 5 * 1024 * 1024  # 5MB
            if len(file_data) > max_size:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='文件大小不能超过 5MB'
                )

            # 4. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 5. 创建用户聚合根
            user_entity = UserEntity(user)
            user_aggregate = UserAggregate(user_entity)

            # 6. 生成文件名
            file_ext = os.path.splitext(file_name)[1]
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_file_name = f"avatar_{user_id}_{timestamp}{file_ext}"

            # 7. 保存文件（这里简化处理，实际应该保存到云存储或本地文件系统）
            # 注意：这里只是示例，实际项目中应该使用云存储服务（如 AWS S3、阿里云 OSS 等）
            # 或者保存到本地文件系统，并返回可访问的 URL

            # 模拟保存文件并生成 URL
            # 在实际项目中，这里应该调用文件存储服务
            avatar_url = f"/static/uploads/avatars/{new_file_name}"

            # 8. 更新用户头像
            user_aggregate.update_avatar(avatar_url)
            self.user_repository.save(user)

            # 9. 发布领域事件
            for event in user_aggregate.domain_events:
                self.event_bus.publish(event)
            user_aggregate.clear_domain_events()

            self.logger.info(f'上传头像成功: user_id={user_id}, avatar_url={avatar_url}')

            # 10. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='头像上传成功',
                data={
                    'user_id': user_id,
                    'avatar_url': avatar_url,
                    'file_name': new_file_name
                }
            )

        except Exception as e:
            self.logger.error(f'上传头像失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'上传头像失败: {str(e)}'
            )