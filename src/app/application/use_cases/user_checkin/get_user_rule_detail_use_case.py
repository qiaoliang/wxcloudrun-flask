"""
获取用户打卡规则详情用例
"""
from flask import has_app_context
from database.flask_models import db, CheckinRule
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


class GetUserRuleDetailUseCase(BaseUseCase):
    """获取用户打卡规则详情用例"""

    def _validate(self, user_id: int, rule_id: int) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        if not rule_id or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID无效'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, rule_id: int) -> UseCaseResult:
        """
        执行获取用户打卡规则详情操作

        Args:
            user_id: 用户ID
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果
        """
        # 先尝试获取个人规则
        checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
        rule = checkin_rule_repo.find_by_id(rule_id)

        if rule and rule.user_id == user_id:
            rule_dict = rule.to_dict()
            rule_dict['rule_source'] = 'personal'
            rule_dict['is_editable'] = True

            _get_logger().info(f'成功获取用户 {user_id} 的个人规则详情，规则ID: {rule_id}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data=rule_dict
            )

        # 如果不是个人规则，尝试获取社区规则
        community_checkin_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
        community_rule = community_checkin_rule_repo.find_by_id(rule_id)

        if community_rule:
            # 检查用户是否有权限查看此规则
            user_repo = RepositoryFactory.get_user_repository()
            user = user_repo.find_by_id(user_id)
            if not user or user.community_id != community_rule.community_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='社区规则不存在或无权限'
                )

            # 检查规则是否对用户生效
            user_community_rule_repo = RepositoryFactory.get_user_community_rule_repository()
            mapping = user_community_rule_repo.find_by_user_and_rule(user_id, rule_id)

            if not mapping or not mapping.is_active:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='此规则未对您生效'
                )

            rule_dict = community_rule.to_dict()
            rule_dict['rule_source'] = 'community'
            rule_dict['is_editable'] = False

            # 添加额外信息
            if community_rule.community:
                rule_dict['community_name'] = community_rule.community.name
            if community_rule.creator:
                rule_dict['created_by_name'] = community_rule.creator.nickname or community_rule.creator.phone
            if community_rule.updater:
                rule_dict['updated_by_name'] = community_rule.updater.nickname or community_rule.updater.phone

            _get_logger().info(f'成功获取用户 {user_id} 的社区规则详情，规则ID: {rule_id}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data=rule_dict
            )

        return UseCaseResult(
            status=UseCaseStatus.BUSINESS_ERROR,
            message='规则不存在'
        )