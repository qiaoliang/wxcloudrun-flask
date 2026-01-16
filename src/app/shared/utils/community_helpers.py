"""
社区相关辅助函数
提供社区规则同步、权限检查等公共逻辑
"""
import logging
from sqlalchemy import select
from database.flask_models import (
    db, User, Community, CommunityCheckinRule,
    UserCommunityRule, CommunityStaff
)
from app.shared.utils.transaction import transactional


logger = logging.getLogger(__name__)


class CommunityRuleHelper:
    """社区规则辅助类"""

    @staticmethod
    @transactional
    def activate_new_community_rules(user_id: int, community_id: int):
        """
        为新加入社区的用户激活社区打卡规则

        Args:
            user_id: 用户ID
            community_id: 社区ID

        此方法会：
        1. 查询社区所有启用的打卡规则
        2. 为用户创建对应的用户打卡规则
        3. 设置规则状态为启用
        """
        try:
            # 查询社区所有启用的打卡规则
            stmt = select(CommunityCheckinRule).where(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1  # 启用状态
            )
            community_rules = db.session.execute(stmt).scalars().all()

            if not community_rules:
                logger.info(f'社区 {community_id} 没有启用的打卡规则')
                return

            # 为用户创建对应的用户打卡规则
            for community_rule in community_rules:
                # 检查是否已存在
                existing_stmt = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == user_id,
                    UserCommunityRule.community_rule_id == community_rule.community_rule_id
                )
                existing = db.session.execute(existing_stmt).scalar_one_or_none()

                if existing:
                    # 更新现有规则
                    existing.status = 1  # 启用
                    existing.updated_at = db.func.now()
                else:
                    # 创建新规则
                    user_rule = UserCommunityRule(
                        user_id=user_id,
                        community_rule_id=community_rule.community_rule_id,
                        status=1,  # 启用
                        rule_name=community_rule.rule_name,
                        rule_type=community_rule.rule_type,
                        checkin_time=community_rule.checkin_time,
                        checkin_frequency=community_rule.checkin_frequency,
                        created_at=db.func.now(),
                        updated_at=db.func.now()
                    )
                    db.session.add(user_rule)

            logger.info(f'用户 {user_id} 已激活社区 {community_id} 的 {len(community_rules)} 个打卡规则')

        except Exception as e:
            logger.error(f'激活社区规则失败: user_id={user_id}, community_id={community_id}, error={str(e)}')
            raise


class CommunityPermissionHelper:
    """社区权限辅助类"""

    @staticmethod
    def has_community_permission(user_id: int, community_id: int) -> bool:
        """
        检查用户是否有权限访问社区

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            是否有权限
        """
        try:
            # 获取用户
            stmt = select(User).where(User.user_id == user_id)
            user = db.session.execute(stmt).scalar_one_or_none()

            if not user:
                return False

            # 超级管理员可以访问所有社区
            if user.role == 4:  # SUPER_ADMIN
                return True

            # 社区主管和专员可以访问自己所属的社区
            if user.community_id == community_id and user.role in [2, 3]:  # MANAGER, STAFF
                return True

            return False

        except Exception as e:
            logger.error(f'检查社区权限失败: user_id={user_id}, community_id={community_id}, error={str(e)}')
            return False


class CommunityRuleQueryHelper:
    """社区规则查询辅助类"""

    @staticmethod
    def get_rule_detail(rule_id: int) -> dict:
        """
        获取规则详情

        Args:
            rule_id: 规则ID

        Returns:
            规则详情字典
        """
        try:
            stmt = select(CommunityCheckinRule).where(
                CommunityCheckinRule.community_rule_id == rule_id
            )
            rule = db.session.execute(stmt).scalar_one_or_none()

            if not rule:
                return None

            return {
                'community_rule_id': rule.community_rule_id,
                'community_id': rule.community_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'checkin_time': rule.checkin_time.isoformat() if rule.checkin_time else None,
                'checkin_frequency': rule.checkin_frequency,
                'status': rule.status,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
            }

        except Exception as e:
            logger.error(f'获取规则详情失败: rule_id={rule_id}, error={str(e)}')
            raise

    @staticmethod
    def get_user_community_rules(user_id: int) -> list:
        """
        获取用户的社区规则列表

        Args:
            user_id: 用户ID

        Returns:
            用户规则列表
        """
        try:
            # 获取用户的所有用户规则
            stmt = select(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id
            ).order_by(UserCommunityRule.created_at.desc())
            
            user_rules = db.session.execute(stmt).scalars().all()

            return [
                {
                    'user_rule_id': rule.user_rule_id,
                    'community_rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'rule_type': rule.rule_type,
                    'checkin_time': rule.checkin_time.isoformat() if rule.checkin_time else None,
                    'checkin_frequency': rule.checkin_frequency,
                    'status': rule.status,
                    'created_at': rule.created_at.isoformat() if rule.created_at else None,
                    'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
                }
                for rule in user_rules
            ]

        except Exception as e:
            logger.error(f'获取用户社区规则失败: user_id={user_id}, error={str(e)}')
            raise