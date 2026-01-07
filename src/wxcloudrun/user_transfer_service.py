"""
用户批量转移服务模块
提供批量转移用户到目标社区的功能
"""
import logging
from datetime import datetime
from sqlalchemy import select
from database.flask_models import db, User, Community, CommunityStaff, CommunityEvent, UserAuditLog
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, STAFF_ROLE_MANAGER
from app.shared.utils.transaction import transaction
from wxcloudrun.community_staff_service import CommunityStaffService

logger = logging.getLogger(__name__)

class UserTransferService:
    """用户批量转移服务"""

    @staticmethod
    def transfer_users_batch(operator_user_id, source_community_id, target_community_id, user_ids):
        """
        批量转移用户到目标社区

        Args:
            operator_user_id: 操作者用户ID
            source_community_id: 源社区ID
            target_community_id: 目标社区ID
            user_ids: 待转移用户ID列表（最多10个）

        Returns:
            dict: {
                'success_count': int,          # 成功转移数量
                'skipped_count': int,          # 静默跳过数量
                'failed': list,                # 失败列表
                'transferred_users': list,     # 成功用户信息
                'events_transferred': int,     # 转移的事件数
                'rules_updated': int           # 规则更新数
            }

        Raises:
            ValueError: 权限不足、参数错误等不可恢复错误
        """
        # 参数验证
        if not operator_user_id:
            raise ValueError('操作者用户ID不能为空')

        if not source_community_id or not target_community_id:
            raise ValueError('源社区ID和目标社区ID不能为空')

        if source_community_id == target_community_id:
            raise ValueError('源社区和目标社区不能相同')

        if not user_ids or not isinstance(user_ids, list):
            raise ValueError('用户ID列表不能为空')

        if len(user_ids) > 10:
            raise ValueError('一次最多转移10个用户')

        # 去重用户ID
        user_ids = list(set(user_ids))

        with transaction():
            # 1. 验证操作者权限
            operator_user = db.session.get(User, operator_user_id)
            if not operator_user:
                raise ValueError('操作者用户不存在')

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
                    raise ValueError('权限不足：您不是源社区的主管')

                # 验证操作者在目标社区是主管
                stmt_target_staff = select(CommunityStaff).where(
                    CommunityStaff.community_id == target_community_id,
                    CommunityStaff.user_id == operator_user_id,
                    CommunityStaff.role == STAFF_ROLE_MANAGER,
                    CommunityStaff.removed_at.is_(None)
                )
                target_staff = db.session.execute(stmt_target_staff).scalar_one_or_none()
                if not target_staff:
                    raise ValueError('权限不足：您不是目标社区的主管')

            # 2. 验证社区存在
            source_community = db.session.get(Community, source_community_id)
            if not source_community:
                raise ValueError(f'源社区{source_community_id}不存在')

            target_community = db.session.get(Community, target_community_id)
            if not target_community:
                raise ValueError(f'目标社区{target_community_id}不存在')

            # 3. 验证并处理用户
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
                        logger.info(f'用户{user_id}已不在源社区{source_community_id}，跳过转移')
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

            # 4. 切换打卡规则（复用现有方法）
            rules_updated = 0
            for user_id in transferred_user_ids:
                try:
                    result = CommunityStaffService.handle_user_community_change(
                        user_id, source_community_id, target_community_id
                    )
                    rules_updated += result.get('activated_count', 0)
                except Exception as e:
                    logger.error(f'切换用户{user_id}的打卡规则失败: {str(e)}')

            # 5. 转移未完成事件
            events_transferred = 0
            if transferred_user_ids:
                stmt_events = select(CommunityEvent).where(
                    CommunityEvent.community_id == source_community_id,
                    CommunityEvent.target_user_id.in_(transferred_user_ids),
                    CommunityEvent.status == 1  # 仅转移进行中的事件
                )
                events = db.session.execute(stmt_events).scalars().all()

                for event in events:
                    event.community_id = target_community_id
                    events_transferred += 1

                logger.info(f'转移了{events_transferred}个未完成事件')

            # 6. 记录审计日志
            audit_log = UserAuditLog(
                user_id=operator_user_id,
                action="batch_transfer_users",
                detail=f"批量转移{success_count}个用户：从社区{source_community_id}到{target_community_id}，跳过{skipped_count}个，失败{len(failed)}个"
            )
            db.session.add(audit_log)

            return {
                'success_count': success_count,
                'skipped_count': skipped_count,
                'failed': failed,
                'transferred_users': transferred_users_info,
                'events_transferred': events_transferred,
                'rules_updated': rules_updated
            }