"""
批量获取规则来源信息用例
"""
from flask import current_app
from database.flask_models import db
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetRulesSourceInfoUseCase(BaseUseCase):
    """批量获取规则来源信息用例"""

    def _validate(self, user_id: int, rule_ids: list = None,
                  community_rule_ids: list = None) -> UseCaseResult:
        """
        验证输入参数

        Args:
            user_id: 用户ID
            rule_ids: 个人规则ID列表
            community_rule_ids: 社区规则ID列表

        Returns:
            UseCaseResult: 验证结果
        """
        if not user_id or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID无效'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int, rule_ids: list = None,
                 community_rule_ids: list = None) -> UseCaseResult:
        """
        执行批量获取规则来源信息操作

        Args:
            user_id: 用户ID
            rule_ids: 个人规则ID列表
            community_rule_ids: 社区规则ID列表

        Returns:
            UseCaseResult: 执行结果
        """
        if rule_ids is None:
            rule_ids = []
        if community_rule_ids is None:
            community_rule_ids = []

        source_info = {
            'personal_rules': [],
            'community_rules': []
        }

        # 获取个人规则来源信息
        if rule_ids:
            checkin_rule_repo = RepositoryFactory.get_checkin_rule_repository()
            for rule_id in rule_ids:
                rule = checkin_rule_repo.find_by_id(rule_id)
                if rule and rule.user_id == user_id:
                    source_info['personal_rules'].append({
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'rule_source': 'personal',
                        'is_editable': True
                    })

        # 获取社区规则来源信息
        if community_rule_ids:
            community_checkin_rule_repo = RepositoryFactory.get_community_checkin_rule_repository()
            user_community_rule_repo = RepositoryFactory.get_user_community_rule_repository()
            user_repo = RepositoryFactory.get_user_repository()

            for rule_id in community_rule_ids:
                rule = community_checkin_rule_repo.find_by_id(rule_id)
                if rule:
                    # 检查用户是否有权限查看此规则
                    user = user_repo.find_by_id(user_id)
                    if user and user.community_id == rule.community_id:
                        mapping = user_community_rule_repo.find_by_user_and_rule(user_id, rule_id)
                        if mapping and mapping.is_active:
                            source_info['community_rules'].append({
                                'rule_id': rule.community_rule_id,
                                'rule_name': rule.rule_name,
                                'rule_source': 'community',
                                'is_editable': False,
                                'community_name': rule.community.name if rule.community else None
                            })

        current_app.logger.info(f'成功获取用户 {user_id} 的规则来源信息')
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取来源信息成功',
            data=source_info
        )