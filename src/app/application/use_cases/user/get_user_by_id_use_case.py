"""
根据ID获取用户用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db
- 使用UserRepository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserByIdUseCase(BaseUseCase):
    """根据ID获取用户用例"""

    def __init__(self):
        """
        初始化用例，注入UserRepository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取UserRepository接口
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行根据ID获取用户用例

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询用户（包含社区关联）
            # ✅ 使用Repository代替 db.session.execute(select(User)...)
            user = self.user_repository.find_by_id(user_id)

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 构造用户数据
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'address': user.address,
                'motto': user.motto,
                'emergency_contact_name': user.emergency_contact_name,
                'emergency_contact_phone': user.emergency_contact_phone,
                'emergency_contact_address': user.emergency_contact_address,
                'role': user.role,
                'role_name': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }

            self.logger.info(f'根据ID获取用户成功: user_id={user_id}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取用户成功',
                data=user_data
            )

        except Exception as e:
            self.logger.error(f'根据ID获取用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取用户失败: {str(e)}'
            )