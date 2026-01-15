"""
处理用户社区变更用例
处理用户社区变更时的规则管理和工作人员关系
"""
import logging
from typing import Dict
from sqlalchemy import select, delete

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, User, CommunityStaff, UserCommunityRule, CommunityCheckinRule
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class HandleUserCommunityChangeUseCase(BaseUseCase):
    """处理用户社区变更用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        user_id: int,
        old_community_id: int,
        new_community_id: int
    ) -> UseCaseResult:
        """
        执行用户社区变更处理

        Args:
            user_id: 用户ID
            old_community_id: 原社区ID（可能为None）
            new_community_id: 新社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            from datetime import datetime

            with transaction():
                # 0. 更新用户的社区归属
                user = db.session.get(User, user_id)
                if not user:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'用户不存在: {user_id}'
                    )

                old_user_community_id = user.community_id
                user.community_id = new_community_id
                if new_community_id != old_user_community_id:
                    user.community_joined_at = datetime.now()

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
                    stmt_delete = delete(CommunityStaff).where(
                        CommunityStaff.community_id == old_community_id,
                        CommunityStaff.user_id == user_id
                    )
                    db.session.execute(stmt_delete)

                # 如果新社区存在，检查是否需要添加工作人员关系
                if new_community_id:
                    if user.role in COMMUNITY_STAFF_ROLES:  # 如果是管理员或以上
                        staff = CommunityStaff(
                            community_id=new_community_id,
                            user_id=user_id,
                            role=STAFF_ROLE_MANAGER if user.role in ADMIN_ROLES else STAFF_ROLE_STAFF
                        )
                        db.session.add(staff)

            logger.info(f"用户{user_id}社区切换完成: 停用{deactivated_count}个旧规则，激活{activated_count}个新规则")

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='社区切换成功',
                data={
                    'success': True,
                    'deactivated_count': deactivated_count,
                    'activated_count': activated_count,
                    'message': f'成功停用{deactivated_count}个旧规则，激活{activated_count}个新规则'
                }
            )

        except Exception as e:
            logger.error(f"处理用户社区切换失败: {str(e)}")
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"处理社区切换失败: {str(e)}"
            )

    def _deactivate_old_community_rules(self, user_id: int, old_community_id: int) -> int:
        """
        停用旧社区的规则

        Args:
            user_id: 用户ID
            old_community_id: 原社区ID

        Returns:
            int: 停用的规则数量
        """
        # 查找用户与旧社区规则的激活映射记录
        stmt_old = select(UserCommunityRule).join(CommunityCheckinRule).where(
            UserCommunityRule.user_id == user_id,
            CommunityCheckinRule.community_id == old_community_id,
            UserCommunityRule.is_active == True
        )
        old_mappings = db.session.execute(stmt_old).scalars().all()

        # 将这些规则标记为停用
        deactivated_count = 0
        for mapping in old_mappings:
            mapping.is_active = False
            deactivated_count += 1

        logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
        return deactivated_count

    def _activate_new_community_rules(self, user_id: int, new_community_id: int) -> int:
        """
        激活新社区的规则

        Args:
            user_id: 用户ID
            new_community_id: 新社区ID

        Returns:
            int: 激活的规则数量
        """
        # 获取新社区的所有启用规则
        stmt_new = select(CommunityCheckinRule).where(
            CommunityCheckinRule.community_id == new_community_id,
            CommunityCheckinRule.status == 1  # 启用状态
        )
        new_community_rules = db.session.execute(stmt_new).scalars().all()

        activated_count = 0

        # 为用户创建或激活规则映射
        for rule in new_community_rules:
            # 查找是否已存在映射记录
            stmt_mapping = select(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id,
                UserCommunityRule.community_rule_id == rule.community_rule_id
            )
            existing_mapping = db.session.execute(stmt_mapping).scalar_one_or_none()

            if existing_mapping:
                # 如果存在且当前是停用状态，重新激活
                if not existing_mapping.is_active:
                    existing_mapping.is_active = True
                    activated_count += 1
            else:
                # 如果不存在，创建新映射
                new_mapping = UserCommunityRule(
                    user_id=user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                db.session.add(new_mapping)
                activated_count += 1

        logger.info(f"用户{user_id}已激活{activated_count}个新社区规则")
        return activated_count
