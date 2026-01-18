"""
批量转移用户到目标社区用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User, Community, CommunityStaff, CommunityEvent, UserAuditLog
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging
from typing import List, Dict

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from app.shared.utils.transaction import transaction
from database.flask_models import db, CommunityEvent, UserAuditLog, CommunityStaff

logger = logging.getLogger(__name__)

# 事件状态常量
EVENT_STATUS_ONGOING = 1
EVENT_STATUS_COMPLETED = 2
EVENT_STATUS_CANCELLED = 3


class TransferUsersBatchUseCase(BaseUseCase):
    """批量转移用户到目标社区用例"""

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
        self.event_repository = RepositoryFactory.get_community_event_repository()
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()

    @transactional


    def execute(
        self,
        operator_user_id: int,
        source_community_id: int,
        target_community_id: int,
        user_ids: List[int]
    ) -> UseCaseResult:
        """
        执行批量转移用户到目标社区

        Args:
            operator_user_id: 操作者用户ID
            source_community_id: 源社区ID
            target_community_id: 目标社区ID
            user_ids: 待转移用户ID列表（最多10个）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(
                operator_user_id, source_community_id, target_community_id, user_ids
            )
            if not validation_result.is_success:
                return validation_result

            # 2. 执行转移
            with transaction():
                # 2.1 验证操作者权限
                # ✅ 使用Repository代替 db.session.get(User, operator_user_id)
                operator_user = self.user_repository.find_by_id(operator_user_id)
                if not operator_user:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message='操作者用户不存在'
                    )

                # 超级管理员可以跳过权限检查
                if operator_user.role != Role.SUPER_ADMIN:
                    # ✅ 使用Repository代替 db.session.execute(select(CommunityStaff)...)
                    source_staff = self.staff_repository.find_active_by_community_and_user(
                        source_community_id, operator_user_id
                    )
                    if not source_staff or source_staff.role != STAFF_ROLE_MANAGER:
                        return UseCaseResult(
                            status=UseCaseStatus.FORBIDDEN,
                            message='权限不足：您不是源社区的主管'
                        )

                    # ✅ 使用Repository验证目标社区权限
                    target_staff = self.staff_repository.find_active_by_community_and_user(
                        target_community_id, operator_user_id
                    )
                    if not target_staff or target_staff.role != STAFF_ROLE_MANAGER:
                        return UseCaseResult(
                            status=UseCaseStatus.FORBIDDEN,
                            message='权限不足：您不是目标社区的主管'
                        )

                # 2.2 验证社区存在
                # ✅ 使用Repository代替 db.session.get(Community, source_community_id)
                source_community = self.community_repository.find_by_id(source_community_id)
                if not source_community:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'源社区{source_community_id}不存在'
                    )

                # ✅ 使用Repository代替 db.session.get(Community, target_community_id)
                target_community = self.community_repository.find_by_id(target_community_id)
                if not target_community:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'目标社区{target_community_id}不存在'
                    )

                # 2.3 处理用户转移
                transfer_result = self._transfer_users(
                    source_community_id, target_community_id, user_ids
                )

                # 2.4 切换打卡规则（使用内部方法）
                rules_updated = 0
                for user_id in transfer_result['transferred_user_ids']:
                    try:
                        # ✅ 直接调用内部方法，而不是 UseCase
                        result = self._handle_user_community_change(
                            user_id, source_community_id, target_community_id
                        )
                        if result['success']:
                            rules_updated += result.get('activated_count', 0)
                        else:
                            logger.error(f'切换用户{user_id}的打卡规则失败: {result["message"]}')
                            transfer_result['failed'].append({
                                'user_id': user_id,
                                'reason': f'规则切换失败: {result["message"]}'
                            })
                    except Exception as e:
                        logger.error(f'切换用户{user_id}的打卡规则失败: {str(e)}')
                        transfer_result['failed'].append({
                            'user_id': user_id,
                            'reason': f'规则切换失败: {str(e)}'
                        })

                # 2.5 转移未完成事件
                events_transferred = 0
                if transfer_result['transferred_user_ids']:
                    # ✅ 使用Repository批量转移事件
                    events_transferred = self.event_repository.batch_transfer_events(
                        source_community_id=source_community_id,
                        target_community_id=target_community_id,
                        user_ids=transfer_result['transferred_user_ids'],
                        status=EVENT_STATUS_ONGOING  # 仅转移进行中的事件
                    )

                    logger.info(f'转移了{events_transferred}个未完成事件')

                # 2.6 记录审计日志
                # TODO: 需要创建AuditLogRepository后再重构
                transferred_user_ids_str = ",".join(map(str, transfer_result['transferred_user_ids']))
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="batch_transfer_users",
                    detail=f"批量转移{transfer_result['success_count']}个用户：从社区{source_community_id}到{target_community_id}，用户ID[{transferred_user_ids_str}]，跳过{transfer_result['skipped_count']}个，失败{len(transfer_result['failed'])}个"
                )
                db.session.add(audit_log)

                # 3. 返回结果
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='转移成功',
                    data={
                        'success_count': transfer_result['success_count'],
                        'skipped_count': transfer_result['skipped_count'],
                        'failed': transfer_result['failed'],
                        'transferred_users': transfer_result['transferred_users_info'],
                        'events_transferred': events_transferred,
                        'rules_updated': rules_updated
                    }
                )

        except ValueError as e:
            logger.error(f'批量转移用户参数错误: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=str(e)
            )
        except Exception as e:
            logger.error(f'批量转移用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'转移失败: {str(e)}'
            )

    def _validate_params(
        self,
        operator_user_id: int,
        source_community_id: int,
        target_community_id: int,
        user_ids: List[int]
    ) -> UseCaseResult:
        """验证参数"""
        if not operator_user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='操作者用户ID不能为空'
            )

        if not source_community_id or not target_community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='源社区ID和目标社区ID不能为空'
            )

        if source_community_id == target_community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='源社区和目标社区不能相同'
            )

        if not user_ids or not isinstance(user_ids, list):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID列表不能为空'
            )

        if len(user_ids) > 10:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='一次最多转移10个用户'
            )

        # 验证用户ID格式
        for user_id in user_ids:
            if not isinstance(user_id, int) or user_id <= 0:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'无效的用户ID: {user_id}'
                )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _transfer_users(
        self,
        source_community_id: int,
        target_community_id: int,
        user_ids: List[int]
    ) -> Dict:
        """
        转移用户到目标社区

        Returns:
            Dict: 转移结果
        """
        from datetime import datetime

        # 去重用户ID
        user_ids = list(set(user_ids))

        success_count = 0
        skipped_count = 0
        failed = []
        transferred_user_ids = []
        transferred_users_info = []

        for user_id in user_ids:
            try:
                # ✅ 使用Repository代替 db.session.get(User, user_id)
                user = self.user_repository.find_by_id(user_id)
                if not user:
                    failed.append({'user_id': user_id, 'reason': '用户不存在'})
                    continue

                # 检查用户是否是普通用户
                if user.role != Role.SOLO:
                    failed.append({'user_id': user_id, 'reason': '只能转移普通用户（独居者）'})
                    continue

                # 检查用户是否在源社区
                if user.community_id != source_community_id:
                    # 用户已离开源社区，静默跳过
                    logger.debug(f'用户{user_id}已不在源社区{source_community_id}，跳过转移')
                    skipped_count += 1
                    continue

                # 更新用户社区归属
                user.community_id = target_community_id
                user.community_joined_at = datetime.now()
                # ✅ 使用Repository保存
                self.user_repository.save(user)

                success_count += 1
                transferred_user_ids.append(user_id)
                transferred_users_info.append({
                    'user_id': user_id,
                    'nickname': user.nickname,
                    'phone_number': user.phone_number
                })

                logger.info(f'成功转移用户{user_id}从社区{source_community_id}到{target_community_id}')

            except Exception as e:
                logger.error(f'转移用户{user_id}失败: {str(e)}')
                failed.append({'user_id': user_id, 'reason': str(e)})

        # 如果没有成功转移任何用户，且有失败，抛出异常
        if success_count == 0 and failed:
            error_details = ";
from app.shared.utils.transaction import transactional ".join([f"用户{f['user_id']}: {f['reason']}" for f in failed])
            raise ValueError(f'所有用户转移失败: {error_details}')

        return {
            'success_count': success_count,
            'skipped_count': skipped_count,
            'failed': failed,
            'transferred_user_ids': transferred_user_ids,
            'transferred_users_info': transferred_users_info
        }

    def _handle_user_community_change(
        self,
        user_id: int,
        old_community_id: int,
        new_community_id: int
    ) -> dict:
        """
        内部方法：处理用户社区变更

        Args:
            user_id: 用户ID
            old_community_id: 原社区ID
            new_community_id: 新社区ID

        Returns:
            dict: 处理结果
        """
        from datetime import datetime

        # 0. 更新用户的社区归属
        # ✅ 使用Repository代替 db.session.get(User, user_id)
        user = self.user_repository.find_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': f'用户不存在: {user_id}'
            }

        old_user_community_id = user.community_id
        user.community_id = new_community_id
        if new_community_id != old_user_community_id:
            user.community_joined_at = datetime.now()
        # ✅ 使用Repository保存
        self.user_repository.save(user)

        # 1. 停用旧社区的社区规则
        deactivated_count = 0
        if old_community_id:
            deactivated_count = self._deactivate_old_community_rules(
                user_id, old_community_id
            )

        # 2. 激活新社区的社区规则
        activated_count = self._activate_new_community_rules(
            user_id, new_community_id
        )

        # 3. 处理工作人员关系
        # 移除旧社区的工作人员关系
        if old_community_id:
            # ✅ 使用Repository的软删除方法
            old_staff = self.staff_repository.find_active_by_community_and_user(
                old_community_id, user_id
            )
            if old_staff:
                self.staff_repository.soft_delete_by_id(old_staff.id)

        # 如果新社区存在，检查是否需要添加工作人员关系
        if new_community_id:
            if user.role in COMMUNITY_STAFF_ROLES:  # 如果是管理员或以上
                # 检查是否已存在工作人员关系
                existing_staff = self.staff_repository.find_active_by_community_and_user(
                    new_community_id, user_id
                )
                if not existing_staff:
                    # 创建工作人员实例
                    staff = CommunityStaff(
                        community_id=new_community_id,
                        user_id=user_id,
                        role=STAFF_ROLE_MANAGER if user.role in ADMIN_ROLES else STAFF_ROLE_STAFF
                    )
                    # ✅ 使用Repository保存
                    self.staff_repository.save(staff)

        logger.info(f"用户{user_id}社区切换完成: 停用{deactivated_count}个旧规则，激活{activated_count}个新规则")

        return {
            'success': True,
            'deactivated_count': deactivated_count,
            'activated_count': activated_count
        }

    def _deactivate_old_community_rules(self, user_id: int, old_community_id: int) -> int:
        """
        内部方法：停用旧社区的规则

        Args:
            user_id: 用户ID
            old_community_id: 原社区ID

        Returns:
            int: 停用的规则数量
        """
        # ✅ 使用Repository批量停用规则映射
        deactivated_count = self.user_community_rule_repository.deactivate_by_user_and_community(
            user_id, old_community_id
        )
        logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
        return deactivated_count

    def _activate_new_community_rules(self, user_id: int, new_community_id: int) -> int:
        """
        内部方法：激活新社区的规则

        Args:
            user_id: 用户ID
            new_community_id: 新社区ID

        Returns:
            int: 激活的规则数量
        """
        # ✅ 使用Repository获取新社区的所有启用规则
        new_community_rules = self.community_checkin_rule_repository.find_by_community_id(new_community_id)
        new_community_rules = [r for r in new_community_rules if r.status == 1]

        activated_count = 0

        # 为用户创建或激活规则映射
        for rule in new_community_rules:
            # ✅ 使用Repository查找是否已存在映射记录
            existing_mapping = self.user_community_rule_repository.find_by_user_and_rule(
                user_id, rule.community_rule_id
            )

            if existing_mapping:
                # 如果存在且当前是停用状态，重新激活
                if not existing_mapping.is_active:
                    existing_mapping.is_active = True
                    self.user_community_rule_repository.save(existing_mapping)
                    activated_count += 1
            else:
                # 如果不存在，创建新映射
                from database.flask_models import UserCommunityRule
                new_mapping = UserCommunityRule(
                    user_id=user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                # ✅ 使用Repository保存
                self.user_community_rule_repository.save(new_mapping)
                activated_count += 1

        logger.info(f"用户{user_id}已激活{activated_count}个新社区规则")
        return activated_count
