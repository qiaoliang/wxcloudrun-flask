"""
社区打卡规则服务模块
处理社区打卡规则相关的核心业务逻辑
"""
import logging
from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from database.models import CommunityCheckinRule, UserCommunityRule, User, Community
from wxcloudrun.dao import get_db
from wxcloudrun.community_service import CommunityService
from wxcloudrun.utils.timeutil import parse_time_only, parse_date_only

logger = logging.getLogger('CommunityCheckinRuleService')


class CommunityCheckinRuleService:
    """社区打卡规则服务类"""

    @staticmethod
    def create_community_rule(rule_data, community_id, created_by):
        """
        创建社区规则（默认未启用状态）

        Args:
            rule_data: 规则数据字典
            community_id: 社区ID (可以是字符串或整数)
            created_by: 创建者用户ID (可以是字符串或整数)

        Returns:
            CommunityCheckinRule: 创建的规则对象

        Raises:
            ValueError: 参数错误或权限不足
            SQLAlchemyError: 数据库错误
        """
        try:
            # Layer 2: 业务逻辑层验证 - 验证所有输入参数
            # 处理类型转换，支持字符串和整数
            try:
                community_id_int = int(community_id) if community_id is not None else 0
                created_by_int = int(created_by) if created_by is not None else 0
            except (ValueError, TypeError):
                raise ValueError('社区ID和创建者用户ID必须为有效整数')

            if community_id_int <= 0:
                raise ValueError('社区ID必须为正整数')

            if created_by_int <= 0:
                raise ValueError('创建者用户ID必须为正整数')

            rule_name = rule_data.get('rule_name')
            if not rule_name or not rule_name.strip():
                raise ValueError('规则名称不能为空')

            # Layer 4: 调试仪表 - 记录创建上下文
            logger.debug(f"创建社区规则: community_id={community_id_int}, created_by={created_by_int}, rule_name={rule_name}")

            # 解析时间字段（在数据库会话外部进行，不依赖数据库）
            custom_time_str = rule_data.get('custom_time')
            custom_time = parse_time_only(custom_time_str) if custom_time_str else None

            # 解析日期字段
            custom_start_date_str = rule_data.get('custom_start_date')
            custom_start_date = parse_date_only(custom_start_date_str) if custom_start_date_str else None

            custom_end_date_str = rule_data.get('custom_end_date')
            custom_end_date = parse_date_only(custom_end_date_str) if custom_end_date_str else None

            with get_db().get_session() as session:
                # 验证社区存在性
                community = session.get(Community, community_id_int)
                if not community:
                    raise ValueError(f'社区不存在: {community_id_int}')

                # 验证创建者权限
                if not CommunityService.has_community_permission(created_by_int, community_id_int):
                    raise ValueError('无权限在此社区创建规则')

                # 创建规则对象
                new_rule = CommunityCheckinRule(
                    community_id=community_id_int,
                    rule_name=rule_name.strip(),
                    icon_url=rule_data.get('icon_url'),
                    frequency_type=rule_data.get('frequency_type', 0),
                    time_slot_type=rule_data.get('time_slot_type', 4),
                    custom_time=custom_time,
                    custom_start_date=custom_start_date,
                    custom_end_date=custom_end_date,
                    week_days=rule_data.get('week_days', 127),
                    status=0,  # 默认停用状态
                    created_by=created_by_int,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

                session.add(new_rule)
                session.commit()
                session.refresh(new_rule)
                session.expunge(new_rule)

            logger.info(f"创建社区规则成功: 社区ID={community_id_int}, 规则ID={new_rule.community_rule_id}, 创建者={created_by_int}")
            return new_rule

        except SQLAlchemyError as e:
            logger.error(f"创建社区规则失败: {str(e)}")
            raise

    @staticmethod
    def update_community_rule(rule_id, rule_data, updated_by):
        """
        修改社区规则（仅限未启用状态）

        Args:
            rule_id: 规则ID
            rule_data: 更新数据字典
            updated_by: 更新者用户ID (可以是字符串或整数)

        Returns:
            CommunityCheckinRule: 更新后的规则对象

        Raises:
            ValueError: 规则不存在、已启用或无权限
            SQLAlchemyError: 数据库错误
        """
        try:
            # Layer 2: 业务逻辑层验证 - 类型转换
            try:
                updated_by_int = int(updated_by) if updated_by is not None else 0
            except (ValueError, TypeError):
                raise ValueError('更新者用户ID必须为有效整数')

            if updated_by_int <= 0:
                raise ValueError('更新者用户ID必须为正整数')

            with get_db().get_session() as session:
                # 获取规则
                rule = session.query(CommunityCheckinRule).get(rule_id)
                if not rule:
                    raise ValueError(f'社区规则不存在: {rule_id}')

                # 检查规则是否已启用（status=1表示启用状态）
                if rule.status == 1:
                    raise ValueError('规则已启用，请先停用后再修改')

                # 验证更新者权限
                if not CommunityService.has_community_permission(updated_by_int, rule.community_id):
                    raise ValueError('无权限修改此规则')

                # 更新字段
                update_fields = ['rule_name', 'icon_url', 'frequency_type', 'time_slot_type', 'week_days']

                for field in update_fields:
                    if field in rule_data:
                        setattr(rule, field, rule_data[field])

                # 特殊处理时间字段
                if 'custom_time' in rule_data:
                    custom_time_str = rule_data.get('custom_time')
                    rule.custom_time = parse_time_only(custom_time_str) if custom_time_str else None

                # 特殊处理日期字段
                if 'custom_start_date' in rule_data:
                    custom_start_date_str = rule_data.get('custom_start_date')
                    rule.custom_start_date = parse_date_only(custom_start_date_str) if custom_start_date_str else None

                if 'custom_end_date' in rule_data:
                    custom_end_date_str = rule_data.get('custom_end_date')
                    rule.custom_end_date = parse_date_only(custom_end_date_str) if custom_end_date_str else None

                rule.updated_by = updated_by_int
                rule.updated_at = datetime.now()

                session.commit()
                session.refresh(rule)
                session.expunge(rule)

            logger.info(f"修改社区规则成功: 规则ID={rule_id}, 更新者={updated_by_int}")
            return rule

        except SQLAlchemyError as e:
            logger.error(f"修改社区规则失败: {str(e)}")
            raise

    @staticmethod
    def enable_community_rule(rule_id, enabled_by):
        """
        启用社区规则并同步给所有用户

        Args:
            rule_id: 规则ID
            enabled_by: 启用人用户ID (可以是字符串或整数)

        Returns:
            bool: 是否启用成功

        Raises:
            ValueError: 规则不存在、已启用或无权限
            SQLAlchemyError: 数据库错误
        """
        try:
            # Layer 2: 业务逻辑层验证 - 类型转换
            try:
                enabled_by_int = int(enabled_by) if enabled_by is not None else 0
            except (ValueError, TypeError):
                raise ValueError('启用人用户ID必须为有效整数')

            if enabled_by_int <= 0:
                raise ValueError('启用人用户ID必须为正整数')

            # Layer 4: 调试仪表 - 记录启用上下文
            logger.debug(f"启用社区规则: rule_id={rule_id}, enabled_by={enabled_by_int}")

            with get_db().get_session() as session:
                # 获取规则
                rule = session.query(CommunityCheckinRule).get(rule_id)
                if not rule:
                    raise ValueError(f'社区规则不存在: {rule_id}')

                logger.debug(f"规则当前状态: status={rule.status}, community_id={rule.community_id}")

                if rule.status == 1:
                    raise ValueError('规则已启用')

                # 验证启用人权限
                if not CommunityService.has_community_permission(enabled_by_int, rule.community_id):
                    logger.warning(f"用户无权限启用规则: user_id={enabled_by_int}, community_id={rule.community_id}")
                    raise ValueError('无权限启用此规则')

                # 获取社区所有用户
                community_users = session.query(User).filter_by(community_id=rule.community_id).all()

                # 为每个用户创建映射记录
                for user in community_users:
                    mapping = UserCommunityRule(
                        user_id=user.user_id,
                        community_rule_id=rule_id,
                        is_active=True,
                        created_at=datetime.now()
                    )
                    session.add(mapping)

                # 更新规则状态
                rule.status = 1  # 设置为启用状态
                rule.enabled_at = datetime.now()
                rule.enabled_by = enabled_by_int
                rule.updated_at = datetime.now()

                session.commit()
                # 不需要refresh，因为我们在同一个会话中修改了对象
                session.refresh(rule)
                session.expunge(rule)

            logger.info(f"启用社区规则成功: 规则ID={rule_id}, 启用人={enabled_by_int}, 影响用户数={len(community_users)}")
            return rule

        except SQLAlchemyError as e:
            logger.error(f"启用社区规则失败: {str(e)}")
            raise

    @staticmethod
    def disable_community_rule(rule_id, disabled_by):
        """
        停用社区规则并从用户移除

        Args:
            rule_id: 规则ID
            disabled_by: 停用人用户ID (可以是字符串或整数)

        Returns:
            bool: 是否停用成功

        Raises:
            ValueError: 规则不存在、未启用或无权限
            SQLAlchemyError: 数据库错误
        """
        try:
            # Layer 2: 业务逻辑层验证 - 类型转换
            try:
                disabled_by_int = int(disabled_by) if disabled_by is not None else 0
            except (ValueError, TypeError):
                raise ValueError('停用人用户ID必须为有效整数')

            if disabled_by_int <= 0:
                raise ValueError('停用人用户ID必须为正整数')

            with get_db().get_session() as session:
                # 获取规则
                rule = session.query(CommunityCheckinRule).get(rule_id)
                if not rule:
                    raise ValueError(f'社区规则不存在: {rule_id}')

                # 验证停用人权限
                if not CommunityService.has_community_permission(disabled_by_int, rule.community_id):
                    raise ValueError('无权限停用此规则')

                if rule.status != 1:
                    raise ValueError('规则未启用')

                # 更新所有用户映射为停用状态
                # TODO: 待完善
#                session.query(UserCommunityRule).filter_by(
#                    community_rule_id=rule_id,
#                    status=1
#                ).update({'is_active': False})

                # 更新规则状态
                rule.status = 0  # 设置为停用状态
                rule.disabled_at = datetime.now()
                rule.disabled_by = disabled_by_int
                rule.updated_at = datetime.now()
                session.commit()
                session.refresh(rule)
                session.expunge(rule)
            logger.info(f"停用社区规则成功: 规则ID={rule_id}, 停用人={disabled_by_int}")
            return rule

        except SQLAlchemyError as e:
            logger.error(f"停用社区规则失败: {str(e)}")
            raise

    @staticmethod
    def get_community_rules(community_id, include_disabled=False):
        """
        获取社区规则列表

        Args:
            community_id: 社区ID (可以是字符串或整数)
            include_disabled: 是否包含已停用规则

        Returns:
            list: 社区规则列表

        Raises:
            ValueError: 社区不存在或参数无效
        """
        try:
            # Layer 2: 业务逻辑层验证 - 确保社区存在且参数有效
            # 处理类型转换，支持字符串和整数
            try:
                community_id_int = int(community_id) if community_id is not None else 0
            except (ValueError, TypeError):
                raise ValueError('社区ID必须为有效整数')

            if community_id_int <= 0:
                raise ValueError('社区ID必须为正整数')

            # Layer 4: 调试仪表 - 记录详细上下文用于取证
            logger.debug(f"获取社区规则列表: community_id={community_id_int}, include_disabled={include_disabled}")

            with get_db().get_session() as session:
                # 验证社区存在性
                community = session.get(Community, community_id_int)
                if not community:
                    raise ValueError(f'社区不存在: {community_id_int}')

                # 始终排除已删除的规则 (status=2)
                from sqlalchemy.orm import joinedload
                
                query = (session.query(CommunityCheckinRule)
                        .options(
                            joinedload(CommunityCheckinRule.creator),
                            joinedload(CommunityCheckinRule.updater),
                            joinedload(CommunityCheckinRule.enabler),
                            joinedload(CommunityCheckinRule.disabler)
                        )
                        .filter_by(community_id=community_id_int)
                        .filter(CommunityCheckinRule.status != 2))

                if not include_disabled:
                    query = query.filter_by(status=1)  # 只返回启用状态的规则
                    logger.debug(f"过滤规则: 只返回启用状态(status=1), 已排除删除状态(status=2)")
                else:
                    query = query.filter(CommunityCheckinRule.status.in_([0, 1]))  # 返回启用和停用状态
                    logger.debug(f"过滤规则: 返回启用和停用状态(status in [0, 1]), 已排除删除状态(status=2)")

                rules = query.order_by(CommunityCheckinRule.created_at.desc()).all()

                # Layer 4: 调试仪表 - 记录规则状态分布
                status_counts = {}
                for rule in rules:
                    status_counts[rule.status] = status_counts.get(rule.status, 0) + 1
                logger.debug(f"规则状态分布: {status_counts}")

                # 在会话上下文中将对象转换为字典，避免离开会话后的延迟加载问题
                rules_data = []
                for rule in rules:
                    rules_data.append(rule.to_dict())

            logger.info(f"获取社区规则列表成功: 社区ID={community_id_int}, 规则数量={len(rules_data)}")
            return rules_data

        except SQLAlchemyError as e:
            logger.error(f"获取社区规则列表失败: {str(e)}")
            raise

    @staticmethod
    def get_user_community_rules(user_id):
        """
        获取用户的所有社区规则（已启用且对用户生效的）

        Args:
            user_id: 用户ID

        Returns:
            list: 用户社区规则列表
        """
        try:
            with get_db().get_session() as session:
                # 获取用户所在社区
                user = session.query(User).get(user_id)
                if not user or not user.community_id:
                    return []

                # 查询用户社区中已启用且对用户生效的规则
                rules = (session.query(CommunityCheckinRule)
                        .join(UserCommunityRule,
                              UserCommunityRule.community_rule_id == CommunityCheckinRule.community_rule_id)
                        .filter(
                            CommunityCheckinRule.community_id == user.community_id,
                            CommunityCheckinRule.status == 1,  # 启用状态
                            UserCommunityRule.user_id == user_id,
                            UserCommunityRule.is_active == True
                        )
                        .order_by(CommunityCheckinRule.created_at.asc())
                        .all())

                return rules

        except SQLAlchemyError as e:
            logger.error(f"获取用户社区规则失败: {str(e)}")
            raise

    @staticmethod
    def handle_user_community_change(user_id, old_community_id, new_community_id):
        """
        处理用户社区变更时的规则同步

        Args:
            user_id: 用户ID
            old_community_id: 旧社区ID
            new_community_id: 新社区ID

        Returns:
            bool: 是否同步成功
        """
        try:
            with get_db().get_session() as session:
                # 停用旧社区规则关联
                if old_community_id:
                    old_rules = session.query(CommunityCheckinRule).filter_by(
                        community_id=old_community_id,
                        status=1  # 启用状态
                    ).all()

                    for rule in old_rules:
                        mapping = session.query(UserCommunityRule).filter_by(
                            user_id=user_id,
                            community_rule_id=rule.community_rule_id
                        ).first()
                        if mapping:
                            mapping.is_active = False

                # 启用新社区规则关联
                if new_community_id:
                    new_rules = session.query(CommunityCheckinRule).filter_by(
                        community_id=new_community_id,
                        status=1  # 启用状态
                    ).all()

                    for rule in new_rules:
                        # 检查是否已存在映射
                        existing = session.query(UserCommunityRule).filter_by(
                            user_id=user_id,
                            community_rule_id=rule.community_rule_id
                        ).first()

                        if existing:
                            existing.is_active = True
                        else:
                            mapping = UserCommunityRule(
                                user_id=user_id,
                                community_rule_id=rule.community_rule_id,
                                is_active=True,
                                created_at=datetime.now()
                            )
                            session.add(mapping)

                session.commit()

            logger.info(f"用户社区变更规则同步成功: 用户ID={user_id}, 旧社区={old_community_id}, 新社区={new_community_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"用户社区变更规则同步失败: {str(e)}")
            raise

    @staticmethod
    def delete_community_rule(rule_id, deleted_by):
        """
        删除社区规则（仅限未启用状态）

        Args:
            rule_id: 规则ID
            deleted_by: 删除者用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 规则不存在、已启用或无权限
            SQLAlchemyError: 数据库错误
        """
        try:
            with get_db().get_session() as session:
                # 获取规则
                rule = session.query(CommunityCheckinRule).get(rule_id)
                if not rule:
                    raise ValueError(f'社区规则不存在: {rule_id}')

                if rule.status == 1:
                    raise ValueError('规则已启用，请先停用后再删除')

                # 验证删除者权限
                if not CommunityService.has_community_permission(deleted_by, rule.community_id):
                    raise ValueError('无权限删除此规则')

                # 软删除：更新状态为2（已删除）
                rule.status = 2
                rule.updated_at = datetime.now()

                session.commit()

            logger.info(f"删除社区规则成功: 规则ID={rule_id}, 删除者={deleted_by}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"删除社区规则失败: {str(e)}")
            raise

    @staticmethod
    def get_rule_detail(rule_id):
        """
        获取规则详情

        Args:
            rule_id: 规则ID

        Returns:
            CommunityCheckinRule: 规则对象

        Raises:
            ValueError: 规则不存在
        """
        with get_db().get_session() as session:
            # 使用options预先加载关系，避免延迟加载错误
            from sqlalchemy.orm import joinedload
            rule = (session.query(CommunityCheckinRule)
                   .options(
                       joinedload(CommunityCheckinRule.community),
                       joinedload(CommunityCheckinRule.creator),
                       joinedload(CommunityCheckinRule.updater),
                       joinedload(CommunityCheckinRule.enabler),
                       joinedload(CommunityCheckinRule.disabler)
                   )
                   .get(rule_id))

            if not rule:
                raise ValueError(f'社区规则不存在: {rule_id}')

            # 从会话中分离对象，避免会话绑定问题
            session.expunge(rule)

            return rule