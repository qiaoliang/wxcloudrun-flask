"""
设置超级管理员用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User, UserAuditLog
from app.shared.constants.roles import Role
from wxcloudrun.community_staff_service import CommunityStaffService

logger = logging.getLogger(__name__)


class SetSuperAdminUseCase(BaseUseCase):
    """设置超级管理员用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

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
            operator = db.session.get(User, operator_user_id)
            if not operator or operator.role != Role.SUPER_ADMIN:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='只有超级管理员才能设置其他超级管理员'
                )

            # 3. 检查目标用户是否存在
            target_user = db.session.get(User, target_user_id)
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

                target_user.role = Role.SUPER_ADMIN
                db.session.flush()

                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="set_super_admin",
                    detail=f"将用户{target_user_id}设置为超级管理员"
                )
                db.session.add(audit_log)

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

                # 先临时将角色改为普通用户，以便 _recalculate_user_role 可以正确计算
                target_user.role = Role.SOLO
                db.session.flush()

                # 取消超级管理员身份，根据工作人员身份重新计算role
                new_role = CommunityStaffService._recalculate_user_role(target_user_id)

                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="remove_super_admin",
                    detail=f"取消用户{target_user_id}的超级管理员身份，新角色为{new_role}"
                )
                db.session.add(audit_log)

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