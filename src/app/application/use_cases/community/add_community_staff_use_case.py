"""
添加社区工作人员用例（重构后 - 符合DDD架构）

重构要点：
- 使用 with transaction() 确保事务一致性
- 使用 AuditLogRepository 记录审计日志
- 消除 db.session.add() 直接访问
"""
import logging
from typing import List, Dict

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transactional
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_COMMUNITY_ID
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_STAFF, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class AddCommunityStaffUseCase(BaseUseCase):
    """添加社区工作人员用例"""

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
        self.audit_log_repository = RepositoryFactory.get_audit_log_repository()  # ✅ 新增

    @transactional

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
            # ✅ 使用Repository代替 db.session.get(User, operator_user_id)
            operator_user = self.user_repository.find_by_id(operator_user_id)
            if not operator_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='操作者用户不存在'
                )

            # 检查操作者权限
            if operator_user.role != Role.SUPER_ADMIN:
                # ✅ 使用Repository代替 db.session.execute(select(CommunityStaff)...)
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
        """验证参数"""
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

        # ✅ 使用Repository代替 db.session.get(Community, community_id)
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
        """添加工作人员到社区"""
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
            # 如果已有主管，且不是正在升级的这些用户之一，则拒绝
            if existing_managers and existing_managers[0].user_id not in user_ids:
                raise ValueError('该社区已有主管')

        added_users_info = []
        success_count = 0
        skipped_count = 0

        for uid in user_ids:
            try:
                # ✅ 使用Repository代替 db.session.get(User, uid)
                target_user = self.user_repository.find_by_id(uid)
                if not target_user:
                    logger.warning(f'用户{uid}不存在，跳过')
                    continue

                # Check if user has phone number
                if not target_user.phone_number or not target_user.phone_number.strip():
                    logger.warning(f'用户{uid}未绑定电话号码，跳过')
                    continue

                # 检查是否需要更新用户的社区归属
                if target_user.community_id == DEFAULT_COMMUNITY_ID:
                    target_user.community_id = community_id
                    target_user.community_joined_at = datetime.now()
                    logger.info(f'用户{uid}从安卡大家庭转入社区{community_id}')
                elif target_user.community_id != community_id:
                    logger.info(f'用户{uid}不在安卡大家庭，保持当前社区{target_user.community_id}')

                # ✅ 使用Repository检查用户是否已在当前社区任职
                existing_in_current_community = self.staff_repository.find_active_by_community_and_user(
                    community_id, uid
                )

                if existing_in_current_community:
                    # 用户已在该社区有角色
                    if existing_in_current_community.role == role:
                        # 尝试添加相同角色，静默跳过
                        logger.info(f'用户{uid}已在社区{community_id}担任{role}角色，跳过')
                        skipped_count += 1
                        continue
                    elif existing_in_current_community.role == STAFF_ROLE_STAFF and role == STAFF_ROLE_MANAGER:
                        # 专员升级为主管：允许，更新角色记录
                        existing_in_current_community.role = STAFF_ROLE_MANAGER
                        logger.info(f'用户{uid}在社区{community_id}从专员升级为主管')
                        self._recalculate_user_role(uid)
                        success_count += 1

                        # 更新用户的 role 字段
                        target_user.role = Role.MANAGER
                        self.user_repository.save(target_user)

                        continue
                    elif existing_in_current_community.role == STAFF_ROLE_MANAGER and role == STAFF_ROLE_STAFF:
                        # 主管降级为专员：只有超级管理员可以操作
                        if operator_user.role == Role.SUPER_ADMIN:
                            # 允许降级
                            existing_in_current_community.role = STAFF_ROLE_STAFF
                            logger.info(f'超级管理员将用户{uid}在社区{community_id}从主管降级为专员')
                            self._recalculate_user_role(uid)
                            success_count += 1

                            # 更新用户的 role 字段
                            target_user.role = Role.STAFF
                            self.user_repository.save(target_user)

                            continue
                        else:
                            # 非超级管理员，拒绝降级
                            logger.warning(f'用户{uid}已是该社区的主管，只有超级管理员可以降级为专员')
                            continue

                # 添加工作人员
                # 注意：需要导入CommunityStaff模型来创建实例
                from database.flask_models import CommunityStaff
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=uid,
                    role=role
                )
                # ✅ 使用Repository代替 db.session.add(staff)
                self.staff_repository.save(staff)

                # 更新用户的 role 字段
                if role == STAFF_ROLE_MANAGER:
                    target_user.role = Role.MANAGER
                elif role == STAFF_ROLE_STAFF:
                    target_user.role = Role.STAFF

                self.user_repository.save(target_user)

                # ✅ 使用Repository保存审计日志
                self.audit_log_repository.create(
                    user_id=operator_user.user_id,
                    action="add_community_staff",
                    detail=f"添加用户{uid}为社区{community_id}的{role}，更新角色为{target_user.role}"
                )

                success_count += 1

                # 添加成功用户信息
                added_users_info.append({
                    'user_id': uid,
                    'nickname': target_user.nickname,
                    'phone_number': target_user.phone_number,
                    'role': role
                })

                logger.info(f'成功添加工作人员: 社区{community_id}, 用户{uid}, 角色{role}')

            except Exception as e:
                logger.error(f'添加工作人员失败 user_id={uid}: {str(e)}')

        # 如果添加的是主管，更新Community表的manager_id字段
        if role == STAFF_ROLE_MANAGER and success_count > 0:
            # 获取添加的主管用户ID（只取第一个，因为前面已经验证只能添加一个）
            manager_user_id = user_ids[0]
            logger.info(f'准备更新社区{community_id}的主管ID为{manager_user_id}')

            # ✅ 使用Repository更新Community表的manager_id字段
            community = self.community_repository.find_by_id(community_id)
            if community:
                old_manager_id = community.manager_id
                community.manager_id = manager_user_id
                self.community_repository.save(community)
                logger.info(f'成功更新社区{community_id}的manager_id: {old_manager_id} -> {manager_user_id}')

        return {
            'success_count': success_count,
            'failed': [],
            'added_users': added_users_info,
            'skipped_count': skipped_count
        }

    def _recalculate_user_role(self, user_id: int) -> int:
        """
        重新计算用户的角色（role字段）

        Args:
            user_id: 用户ID

        Returns:
            int: 计算后的角色ID
        """
        # ✅ 使用Repository代替 db.session.get(User, user_id)
        user = self.user_repository.find_by_id(user_id)
        if user and user.role == Role.SUPER_ADMIN:
            return Role.SUPER_ADMIN

        # ✅ 使用Repository查询用户在所有社区的工作人员角色
        staff_records = self.staff_repository.find_by_user_id(user_id, include_removed=False)

        # 如果没有任何工作人员记录，设为普通用户
        if not staff_records:
            if user:
                user.role = Role.SOLO
                self.user_repository.save(user)
            return Role.SOLO

        # 检查是否有主管角色
        has_manager = any(record.role == STAFF_ROLE_MANAGER for record in staff_records)

        if has_manager:
            # 有主管角色，设为主管（role=3）
            if user:
                user.role = Role.MANAGER
                self.user_repository.save(user)
            return Role.MANAGER
        else:
            # 只有专员角色，设为专员（role=2）
            if user:
                user.role = Role.STAFF
                self.user_repository.save(user)
            return Role.STAFF

from app.shared.utils.transaction import transactional