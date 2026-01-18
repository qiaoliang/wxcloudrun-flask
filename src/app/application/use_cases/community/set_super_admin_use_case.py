"""
设置超级管理员用例（重构后 - 符合DDD架构）

重构要点：
- 使用 with transaction() 确保事务一致性
- 使用 AuditLogRepository 记录审计日志
- 消除 db.session.add() 直接访问
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class SetSuperAdminUseCase(BaseUseCase):
    """设置超级管理员用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.staff_repository = RepositoryFactory.get_community_staff_repository()
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()  # ✅ 新增

    @transactional


    def execute(
        self,
        operator_user_id: int,
        target_user_id: int,
        is_super_admin: bool
    ) -> UseCaseResult:
        """
        执行设置超级管理员用例

        Args:
            operator_user_id: 操作者用户ID
            target_user_id: 目标用户ID
            is_super_admin: True设置为超级管理员，False取消超级管理员

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not operator_user_id or not target_user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 检查操作者权限
            # ✅ 使用Repository代替 db.session.get(User, operator_user_id)
            operator = self.user_repository.find_by_id(operator_user_id)
            if not operator or operator.role != Role.SUPER_ADMIN:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='只有超级管理员才能设置其他超级管理员'
                )

            # 3. 检查目标用户是否存在
            # ✅ 使用Repository代替 db.session.get(User, target_user_id)
            target_user = self.user_repository.find_by_id(target_user_id)
            if not target_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='目标用户不存在'
                )

            # 4. 不能修改自己的超级管理员身份
            if operator_user_id == target_user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='不能修改自己的超级管理员身份'
                )

            # 5. 执行设置或取消
            if is_super_admin:
                # 设置为超级管理员
                if target_user.role == Role.SUPER_ADMIN:
                    return UseCaseResult(
                        status=UseCaseStatus.SUCCESS,
                        message='该用户已经是超级管理员',
                        data={'success': True, 'message': '该用户已经是超级管理员'}
                    )

                # ✅ 使用事务上下文管理器确保事务一致性
                with transaction():
                    target_user.role = Role.SUPER_ADMIN
                    # ✅ 使用Repository代替 db.session.flush()
                    self.user_repository.save(target_user)

                    # ✅ 使用Repository保存审计日志
                    self.audit_log_repository.create(
                        user_id=operator_user_id,
                        action="set_super_admin",
                        detail=f"将用户{target_user_id}设置为超级管理员"
                    )

                logger.info(f'用户{operator_user_id}将用户{target_user_id}设置为超级管理员')

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='已设置为超级管理员',
                    data={'success': True, 'message': '已设置为超级管理员'}
                )
            else:
                # 取消超级管理员
                if target_user.role != Role.SUPER_ADMIN:
                    return UseCaseResult(
                        status=UseCaseStatus.SUCCESS,
                        message='该用户不是超级管理员',
                        data={'success': True, 'message': '该用户不是超级管理员'}
                    )

                # 取消超级管理员身份，根据工作人员身份重新计算role
                # ✅ 使用Repository查询用户在所有社区的工作人员角色
                staff_records = self.staff_repository.find_by_user_id(target_user_id, include_removed=False)

                # 重新计算用户角色
                if not staff_records:
                    # 如果没有任何工作人员记录，设为普通用户
                    new_role = Role.SOLO
                else:
                    # 检查是否有主管角色
                    has_manager = any(record.role == STAFF_ROLE_MANAGER for record in staff_records)
                    new_role = Role.MANAGER if has_manager else Role.STAFF

                # ✅ 使用事务上下文管理器确保事务一致性
                with transaction():
                    target_user.role = new_role
                    # ✅ 使用Repository代替 db.session.flush()
                    self.user_repository.save(target_user)

                    # ✅ 使用Repository保存审计日志
                    self.audit_log_repository.create(
                        user_id=operator_user_id,
                        action="remove_super_admin",
                        detail=f"取消用户{target_user_id}的超级管理员身份，新角色为{new_role}"
                    )

                logger.info(f'用户{operator_user_id}取消用户{target_user_id}的超级管理员身份，新角色为{new_role}')

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message=f'已取消超级管理员，当前角色为{new_role}',
                    data={'success': True, 'message': f'已取消超级管理员，当前角色为{new_role}'}
                )

        except ValueError as e:
            logger.error(f'设置超级管理员失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=str(e)
            )
        except Exception as e:
            logger.error(f'设置超级管理员失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'设置失败: {str(e)}'
            )

from app.shared.utils.transaction import transactional