"""
获取用户所有打卡规则用例
"""
from flask import has_app_context
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.flask_models import db, CheckinRule, CommunityCheckinRule, UserCommunityRule
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
import logging

app_logger = logging.getLogger('log')


def _get_logger():
    """获取logger，避免在模块级别访问current_app"""
    if has_app_context():
        from flask import current_app
        return current_app.logger
    return app_logger


class GetUserAllRulesUseCase(BaseUseCase):
    """获取用户所有打卡规则用例"""

    def _validate(self, user_id: int, method: str = 'GET', params: dict = None) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            method: HTTP 方法（GET/DELETE）
            params: 请求参数（仅 DELETE 方法需要）

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        # 处理 DELETE 方法（删除个人规则）的验证
        if method == 'DELETE':
            if not params:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='缺少请求参数'
                )

            rule_id = params.get('rule_id')
            rule_source = params.get('rule_source')

            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='缺少规则ID参数'
                )

            # 只允许删除个人规则
            if rule_source == 'community':
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='不允许删除社区规则'
                )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, method: str = 'GET', params: dict = None) -> UseCaseResult:
        """
        执行获取用户所有打卡规则操作

        Args:
            user_id: 用户ID
            method: HTTP 方法（GET/DELETE）
            params: 请求参数（仅 DELETE 方法需要）

        Returns:
            UseCaseResult: 执行结果
        """
        # 处理 DELETE 方法（删除个人规则）
        if method == 'DELETE':
            rule_id = params.get('rule_id')

            # 使用 Repository 删除个人规则
            checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
            rule = checkin_rule_repo.find_by_id(int(rule_id))

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='规则不存在'
                )

            if rule.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='无权限删除此规则'
                )

            checkin_rule_repo.soft_delete(int(rule_id))
            _get_logger().info(f'用户 {user_id} 成功删除个人打卡规则')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='删除规则成功',
                data={'deleted': True}
            )

        # 处理 GET 方法（获取所有规则）
        all_rules = []

        # 获取用户信息
        user_repo = RepositoryFactory.get_user_repository()
        user = user_repo.find_by_id(user_id)
        if user and user.community_id:
            # 获取用户所属社区的所有规则（包括启用和停用的）
            community_checkin_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
            community_rules = community_checkin_rule_repo.find_by_community_id(
                user.community_id, include_deleted=False
            )

            # 获取用户的规则映射状态
            user_community_rule_repo = RepositoryFactory.get_user_community_rule_repository()
            user_mappings = user_community_rule_repo.find_by_user_id(user_id, include_inactive=True)
            user_mapping_dict = {m.community_rule_id: m.is_active for m in user_mappings}

            for rule in community_rules:
                rule_dict = rule.to_dict()
                rule_dict['rule_source'] = 'community'
                rule_dict['is_editable'] = False  # 社区规则用户不可编辑
                rule_dict['source_label'] = '社区规则'

                # 添加社区信息
                if rule.community:
                    rule_dict['community_name'] = rule.community.name
                    rule_dict['source_label'] = f'社区规则 ({rule.community.name})'

                # 添加创建者信息
                if rule.creator:
                    rule_dict['created_by_name'] = rule.creator.nickname or rule.creator.phone

                # 根据规则状态和用户映射状态判断是否对用户激活
                is_rule_enabled = rule_dict.get('status') == 1
                is_user_mapping_active = user_mapping_dict.get(rule.community_rule_id, False)
                rule_dict['is_user_mapping_active'] = is_user_mapping_active
                rule_dict['is_active_for_user'] = is_rule_enabled and is_user_mapping_active

                # 添加规则状态描述
                if is_rule_enabled and is_user_mapping_active:
                    rule_dict['status_label'] = '启用'
                elif not is_rule_enabled:
                    rule_dict['status_label'] = '停用'
                else:
                    rule_dict['status_label'] = '未激活'

                all_rules.append(rule_dict)

        # 获取个人规则（在社区规则后显示）
        checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
        personal_rules = checkin_rule_repo.find_active_by_user_id(user_id)
        _get_logger().info(f"获取个人规则: 用户ID={user_id}, 规则数量={len(personal_rules)}")

        for rule in personal_rules:
            rule_dict = rule.to_dict()
            rule_dict['rule_source'] = 'personal'
            rule_dict['is_editable'] = True
            rule_dict['source_label'] = '个人规则'
            rule_dict['is_active_for_user'] = True  # 个人规则默认对用户激活
            rule_dict['status_label'] = '启用'
            all_rules.append(rule_dict)

        _get_logger().info(f'成功获取用户 {user_id} 的所有打卡规则，共 {len(all_rules)} 条规则')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取规则成功',
            data={'rules': all_rules}
        )