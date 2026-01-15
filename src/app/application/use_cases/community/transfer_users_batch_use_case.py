"""
批量转移用户到目标社区用例
"""
import logging
from typing import List, Dict
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.community.handle_user_community_change_use_case import HandleUserCommunityChangeUseCase
from database.flask_models import db, User, Community, CommunityStaff, CommunityEvent, UserAuditLog
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, STAFF_ROLE_MANAGER
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)

# 事件状态常量
EVENT_STATUS_ONGOING = 1
EVENT_STATUS_COMPLETED = 2
EVENT_STATUS_CANCELLED = 3


class TransferUsersBatchUseCase(BaseUseCase):
    """批量转移用户到目标社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

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
                operator_user = db.session.get(User, operator_user_id)
                if not operator_user:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message='操作者用户不存在'
                    )

                # 超级管理员可以跳过权限检查
                if operator_user.role != Role.SUPER_ADMIN:
                    # 验证操作者在源社区是主管
                    stmt_source_staff = select(CommunityStaff).where(
                        CommunityStaff.community_id == source_community_id,
                        CommunityStaff.user_id == operator_user_id,
                        CommunityStaff.role == STAFF_ROLE_MANAGER,
                        CommunityStaff.removed_at.is_(None)
                    )
                    source_staff = db.session.execute(stmt_source_staff).scalar_one_or_none()
                    if not source_staff:
                        return UseCaseResult(
                            status=UseCaseStatus.FORBIDDEN,
                            message='权限不足：您不是源社区的主管'
                        )

                    # 验证操作者在目标社区是主管
                    stmt_target_staff = select(CommunityStaff).where(
                        CommunityStaff.community_id == target_community_id,
                        CommunityStaff.user_id == operator_user_id,
                        CommunityStaff.role == STAFF_ROLE_MANAGER,
                        CommunityStaff.removed_at.is_(None)
                    )
                    target_staff = db.session.execute(stmt_target_staff).scalar_one_or_none()
                    if not target_staff:
                        return UseCaseResult(
                            status=UseCaseStatus.FORBIDDEN,
                            message='权限不足：您不是目标社区的主管'
                        )

                # 2.2 验证社区存在
                source_community = db.session.get(Community, source_community_id)
                if not source_community:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'源社区{source_community_id}不存在'
                    )

                target_community = db.session.get(Community, target_community_id)
                if not target_community:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'目标社区{target_community_id}不存在'
                    )

                # 2.3 处理用户转移
                transfer_result = self._transfer_users(
                    source_community_id, target_community_id, user_ids
                )

                # 2.4 切换打卡规则（使用 HandleUserCommunityChangeUseCase）
                rules_updated = 0
                handle_community_change_use_case = HandleUserCommunityChangeUseCase()
                for user_id in transfer_result['transferred_user_ids']:
                    try:
                        result = handle_community_change_use_case.execute(
                            user_id, source_community_id, target_community_id
                        )
                        if result.is_success:
                            rules_updated += result.data.get('activated_count', 0)
                        else:
                            logger.error(f'切换用户{user_id}的打卡规则失败: {result.message}')
                            transfer_result['failed'].append({
                                'user_id': user_id,
                                'reason': f'规则切换失败: {result.message}'
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
                    # 使用批量更新提高性能
                    events_transferred = db.session.query(CommunityEvent).filter(
                        CommunityEvent.community_id == source_community_id,
                        CommunityEvent.target_user_id.in_(transfer_result['transferred_user_ids']),
                        CommunityEvent.status == EVENT_STATUS_ONGOING  # 仅转移进行中的事件
                    ).update(
                        {'community_id': target_community_id},
                        synchronize_session=False
                    )

                    logger.info(f'转移了{events_transferred}个未完成事件')

                # 2.6 记录审计日志
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
                # 检查用户是否存在
                user = db.session.get(User, user_id)
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
            error_details = "; ".join([f"用户{f['user_id']}: {f['reason']}" for f in failed])
            raise ValueError(f'所有用户转移失败: {error_details}')

        return {
            'success_count': success_count,
            'skipped_count': skipped_count,
            'failed': failed,
            'transferred_user_ids': transferred_user_ids,
            'transferred_users_info': transferred_users_info
        }
