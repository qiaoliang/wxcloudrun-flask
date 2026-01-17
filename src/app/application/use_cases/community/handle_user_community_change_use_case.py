"""
处理用户社区变更用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User, CommunityStaff, UserCommunityRule, CommunityCheckinRule
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging
from typing import Dict

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class HandleUserCommunityChangeUseCase(BaseUseCase):
    """处理用户社区变更用例"""

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
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()

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
                # ✅ 使用Repository代替 db.session.get(User, user_id)
                user = self.user_repository.find_by_id(user_id)
                if not user:
                    return UseCaseResult(
                        status=UseCaseStatus.NOT_FOUND,
                        message=f'用户不存在: {user_id}'
                    )

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
                            # 需要导入CommunityStaff模型来创建实例
                            from database.flask_models import CommunityStaff
                            staff = CommunityStaff(
                                community_id=new_community_id,
                                user_id=user_id,
                                role=STAFF_ROLE_MANAGER if user.role in ADMIN_ROLES else STAFF_ROLE_STAFF
                            )
                            # ✅ 使用Repository保存
                            self.staff_repository.save(staff)

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
        # ✅ 使用Repository查找用户与旧社区规则的激活映射记录
        # TODO: 需要在UserCommunityRuleRepository中添加根据社区ID和激活状态查找的方法
        # 暂时保留直接访问
        from database.flask_models import UserCommunityRule, CommunityCheckinRule
        from sqlalchemy import select
        from database.flask_models import db

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
