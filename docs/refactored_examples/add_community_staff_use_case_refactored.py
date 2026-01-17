"""
添加社区工作人员用例（重构后 - 符合DDD架构）

重构要点：
1. 移除直接导入 database.flask_models 中的 db, User, Community, CommunityStaff
2. 使用Repository接口访问数据，符合依赖倒置原则（DIP）
3. 所有数据库操作通过Repository抽象层
"""
import logging
from typing import List, Dict

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.constants.roles import Role, STAFF_ROLE_STAFF, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class AddCommunityStaffUseCaseRefactored(BaseUseCase):
    """添加社区工作人员用例（重构版）"""

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
        self.staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(
        self,
        operator_user_id: int,
        community_id: int,
        user_ids: List[int],
        role: str = 'staff'
    ) -> UseCaseResult:
        """
        执行添加社区工作人员

        Args:
            operator_user_id: 操作者用户ID
            community_id: 社区ID
            user_ids: 要添加的用户ID列表
            role: 角色，'manager' 或 'staff'

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(operator_user_id, community_id, user_ids, role)
            if not validation_result.is_success:
                return validation_result

            # 2. 验证并处理用户ID
            processed_user_ids = self._process_user_ids(user_ids)
            if not processed_user_ids['valid_ids']:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'所有用户ID都无效: {processed_user_ids["failed"]}'
                )

            # 3. 验证权限
            operator_user = self.user_repository.find_by_id(operator_user_id)
            if not operator_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='操作者用户不存在'
                )

            # ✅ 使用Repository检查权限，不再直接访问db.session
            # 检查操作者权限
            if operator_user.role != Role.SUPER_ADMIN:
                staff_record = self.staff_repository.find_active_by_community_and_user(
                    community_id, operator_user_id
                )
                if not staff_record:
                    return UseCaseResult(
                        status=UseCaseStatus.FORBIDDEN,
                        message='权限不足，需要社区工作人员权限'
                    )

                # 如果是专员（非主管）尝试添加任何工作人员，则拒绝
                if staff_record.role == STAFF_ROLE_STAFF:
                    return UseCaseResult(
                        status=UseCaseStatus.FORBIDDEN,
                        message='专员不能添加工作人员，需要主管权限'
                    )

            # 4. 执行添加
            result = self._add_staff(
                operator_user, community_id, processed_user_ids['valid_ids'], role
            )

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加成功',
                data=result
            )

        except ValueError as e:
            logger.error(f'添加社区工作人员失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=str(e)
            )
        except Exception as e:
            logger.error(f'添加社区工作人员失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加失败: {str(e)}'
            )

    def _validate_params(
        self,
        operator_user_id: int,
        community_id: int,
        user_ids: List[int],
        role: str
    ) -> UseCaseResult:
        """
        验证参数

        重构点：使用community_repository代替db.session.get(Community, id)
        """
        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少社区ID'
            )

        if not user_ids or not isinstance(user_ids, list):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID列表不能为空'
            )

        if role not in [STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF]:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='角色参数错误，必须是manager或staff'
            )

        # ✅ 使用Repository检查社区是否存在
        community = self.community_repository.find_by_id(community_id)
        if not community:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message='社区不存在'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _process_user_ids(self, user_ids: List[int]) -> Dict:
        """处理用户ID，返回有效和无效的ID"""
        valid_ids = []
        failed = []

        for uid in user_ids:
            try:
                # 尝试转换为整数
                if isinstance(uid, str):
                    uid_int = int(uid)
                elif isinstance(uid, int):
                    uid_int = uid
                else:
                    failed.append({'user_id': uid, 'reason': f'无效的用户ID类型: {type(uid).__name__}'})
                    continue

                # 验证整数是否有效（正数）
                if uid_int <= 0:
                    failed.append({'user_id': uid, 'reason': '用户ID必须为正整数'})
                    continue

                valid_ids.append(uid_int)
            except (ValueError, TypeError) as e:
                failed.append({'user_id': uid, 'reason': f'无效的用户ID格式: {str(e)}'})
                continue

        return {'valid_ids': valid_ids, 'failed': failed}

    def _add_staff(
        self,
        operator_user,
        community_id: int,
        user_ids: List[int],
        role: str
    ) -> Dict:
        """
        添加工作人员到社区

        重构点：使用staff_repository代替直接查询CommunityStaff
        """
        from datetime import datetime

        # 如果是添加主管,只能添加一个
        if role == STAFF_ROLE_MANAGER and len(user_ids) > 1:
            raise ValueError('主管只能添加一个')

        # ✅ 使用Repository检查是否已有主管
        # 检查是否已有主管（但排除正在升级的情况）
        if role == STAFF_ROLE_MANAGER:
            existing_managers = self.staff_repository.find_active_by_community_and_role(
                community_id, STAFF_ROLE_MANAGER
            )
            if existing_managers and existing_managers[0].user_id not in user_ids:
                raise ValueError('该社区已有主管，不能重复添加')

        # 处理每个用户
        added_count = 0
        failed_list = []

        for user_id in user_ids:
            try:
                # ✅ 使用Repository获取用户
                target_user = self.user_repository.find_by_id(user_id)
                if not target_user:
                    failed_list.append({'user_id': user_id, 'reason': '用户不存在'})
                    continue

                # ✅ 使用Repository检查是否已经是工作人员
                existing_staff = self.staff_repository.find_active_by_community_and_user(
                    community_id, user_id
                )

                from database.flask_models import CommunityStaff  # 仅用于创建实例

                if existing_staff:
                    # 如果角色不同，更新角色
                    if existing_staff.role != role:
                        existing_staff.role = role
                        existing_staff.updated_at = datetime.now()
                        self.staff_repository.update(existing_staff)
                        added_count += 1
                    else:
                        failed_list.append({
                            'user_id': user_id,
                            'reason': f'用户已经是该社区的{role}'
                        })
                else:
                    # 创建新的工作人员记录
                    new_staff = CommunityStaff(
                        community_id=community_id,
                        user_id=user_id,
                        role=role,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.staff_repository.save(new_staff)

                    # 更新用户的社区ID
                    target_user.community_id = community_id
                    self.user_repository.save(target_user)

                    # 更新用户角色
                    self._recalculate_user_role(target_user)

                    added_count += 1

            except Exception as e:
                logger.error(f'添加用户 {user_id} 失败: {str(e)}', exc_info=True)
                failed_list.append({'user_id': user_id, 'reason': f'添加失败: {str(e)}'})

        return {
            'added_count': added_count,
            'total_count': len(user_ids),
            'failed': failed_list
        }

    def _recalculate_user_role(self, user) -> None:
        """
        重新计算用户角色

        根据用户在所有社区的工作人员角色，计算其最终角色
        """
        from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES

        # 获取用户所有的工作人员记录
        all_staff_records = self.staff_repository.find_by_user_id(user.user_id, include_removed=False)

        if not all_staff_records:
            # 如果没有任何工作人员记录，恢复为普通用户
            if user.role not in ADMIN_ROLES:
                user.role = Role.USER
            return

        # 检查是否有主管角色
        has_manager = any(record.role == STAFF_ROLE_MANAGER for record in all_staff_records)

        if has_manager:
            user.role = Role.MANAGER
        else:
            user.role = Role.STAFF

        # 保存用户
        self.user_repository.save(user)


# ========================================
# 重构前后对比
# ========================================

"""
BEFORE (违反DDD):

from database.flask_models import db, User, Community, CommunityStaff

operator_user = db.session.get(User, operator_user_id)  # ❌ 直接访问DB
community = db.session.get(Community, community_id)      # ❌ 直接访问DB

stmt = select(CommunityStaff).where(...)
staff_record = db.session.execute(stmt).scalar_one_or_none()  # ❌ 直接访问DB


AFTER (符合DDD):

operator_user = self.user_repository.find_by_id(operator_user_id)  # ✅ 通过Repository
community = self.community_repository.find_by_id(community_id)      # ✅ 通过Repository

staff_record = self.staff_repository.find_active_by_community_and_user(
    community_id, operator_user_id
)  # ✅ 通过Repository


优势：
1. ✅ 符合依赖倒置原则（DIP）
2. ✅ UseCase不依赖具体实现，只依赖抽象接口
3. ✅ 便于单元测试（可以Mock Repository）
4. ✅ 便于替换数据存储实现（如从SQL切换到NoSQL）
5. ✅ 代码更清晰，职责更明确
"""
