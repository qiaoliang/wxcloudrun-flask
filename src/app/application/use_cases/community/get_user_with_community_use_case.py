"""
获取用户及其社区信息用例
"""
import logging
from datetime import datetime
from typing import Optional
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserWithCommunityUseCase(BaseUseCase):
    """获取用户及其社区信息用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    @transactional


    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取用户社区信息

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 包含用户和社区信息的结果
        """
        try:
            # 1. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult.fail('用户不存在', status=UseCaseStatus.NOT_FOUND)

            # 2. 检查用户是否属于社区
            if not user.community_id:
                return UseCaseResult.fail('用户未加入社区', status=UseCaseStatus.BUSINESS_ERROR)

            # 3. 查询社区
            community = self.community_repository.find_by_id(user.community_id)
            if not community:
                return UseCaseResult.fail('社区不存在', status=UseCaseStatus.NOT_FOUND)

            # 4. 检查访问权限
            from app.application.use_cases.community import VerifyUserCommunityAccessUseCase
            verify_access_use_case = VerifyUserCommunityAccessUseCase()
            access_result = verify_access_use_case.execute(user_id, user.community_id)
            has_access = access_result.data.get('has_access', False) if access_result.is_success else False

            if not has_access:
                return UseCaseResult.fail('用户不属于该社区', status=UseCaseStatus.FORBIDDEN)

            # 5. 使用 FormatCommunityInfoUseCase 格式化社区信息
            from app.application.use_cases.community import FormatCommunityInfoUseCase
            format_use_case = FormatCommunityInfoUseCase()
            format_result = format_use_case.execute(community.community_id)

            if not format_result.is_success:
                return UseCaseResult.fail(format_result.message)

            # 6. 返回完整信息
            return UseCaseResult.success(
                data={
                    'user_id': user.user_id,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'role': user.role,
                    'role_name': user.role_name,
                    'community': format_result.data
                }
            )

        except Exception as e:
            return UseCaseResult.fail(f'获取用户社区信息失败: {str(e)}')


class UpdateUserCommunityUseCase(BaseUseCase):
    """更新用户社区用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()

    def execute(self, user_id: int, community_id: int) -> UseCaseResult:
        """
        执行更新用户社区

        Args:
            user_id: 用户ID
            community_id: 新社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult.fail('用户不存在', status=UseCaseStatus.NOT_FOUND)

            # 2. 查询目标社区
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult.fail('社区不存在', status=UseCaseStatus.NOT_FOUND)

            # 3. 更新用户社区
            old_community_id = user.community_id
            user.community_id = community_id
            user.community_joined_at = datetime.now()

            # 4. 保存更改
            self.user_repository.save(user)

            # 5. 记录审计日志
            self.audit_log_repository.create(
                user_id=user_id,
                action='switch_community',
                detail=f'从社区{old_community_id}切换到社区{community_id}'
            )

            return UseCaseResult.success(
                data={
                    'user_id': user_id,
                    'community_id': community_id,
                    'old_community_id': old_community_id,
                    'community_name': community.name,
                    'message': '切换成功'
                }
            )

        except Exception as e:
            return UseCaseResult.fail(f'切换用户社区失败: {str(e)}')


class CreateUserInCommunityUseCase(BaseUseCase):
    """在社区中创建用户用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()

    def execute(self, operator_id: int, community_id: int, user_data: dict) -> UseCaseResult:
        """
        在社区中创建用户

        Args:
            operator_id: 操作者ID
            community_id: 社区ID
            user_data: 用户数据字典

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id or not user_data:
                return UseCaseResult.fail('缺少社区ID或用户数据', status=UseCaseStatus.VALIDATION_ERROR)

            phone_number = user_data.get('phone_number', '')
            nickname = user_data.get('nickname', '')
            name = user_data.get('name', '')
            avatar_url = user_data.get('avatar_url', '')
            role = user_data.get('role', 1)

            # 2. 检查权限
            from app.application.use_cases.community import CheckCommunityPermissionUseCase
            check_permission_use_case = CheckCommunityPermissionUseCase()
            permission_result = check_permission_use_case.execute(operator_id, community_id)
            has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False

            if not has_permission:
                return UseCaseResult.fail('无权限访问该社区', status=UseCaseStatus.FORBIDDEN)

            # 3. 检查手机号是否已存在
            existing_user = self.user_repository.find_by_phone_number(phone_number)
            if existing_user:
                return UseCaseResult.fail('手机号已被使用', status=UseCaseStatus.BUSINESS_ERROR)

            # 4. 检查社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult.fail('社区不存在', status=UseCaseStatus.NOT_FOUND)

            # 5. 创建用户 (通过 User 工厂方法)
            from database.flask_models import User  # 仅在 UseCase 中导入用于创建
            user = User(
                phone_number=phone_number,
                nickname=nickname,
                name=name,
                avatar_url=avatar_url,
                role=role,
                community_id=community_id,
                status=1,
                created_at=datetime.now()
            )

            # 6. 保存用户
            created_user = self.user_repository.save(user)

            # 7. 记录审计日志
            self.audit_log_repository.create(
                user_id=operator_id,
                action='create_community_user',
                detail=f'在社区{community_id}中创建用户'
            )

            # 8. 返回结果
            return UseCaseResult.success(
                data={
                    'user_id': created_user.user_id,
                    'phone_number': created_user.phone_number,
                    'nickname': created_user.nickname,
                    'message': '创建成功'
                }
            )

        except Exception as e:
            return UseCaseResult.fail(f'创建用户失败: {str(e)}')
