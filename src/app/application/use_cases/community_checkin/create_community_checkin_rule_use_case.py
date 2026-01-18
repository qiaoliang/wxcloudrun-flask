"""
创建社区打卡规则用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import CommunityCheckinRule
from app.shared.utils.transaction import transactional


class CreateCommunityCheckinRuleUseCase(BaseUseCase):
    """创建社区打卡规则用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, params: dict, community_id: int, user_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            params: 请求参数
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not params:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数不能为空'
            )

        if not isinstance(params, dict):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求参数格式错误'
            )

        required_fields = ['rule_name']
        for field in required_fields:
            if field not in params:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'缺少必要参数: {field}'
                )

        if not isinstance(community_id, int) or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID必须为正整数'
            )

        if not isinstance(user_id, int) or user_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    @transactional

    def _execute(self, params: dict, community_id: int, user_id: int) -> UseCaseResult:
        """
        执行创建社区打卡规则操作

        Args:
            params: 请求参数
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 创建CommunityCheckinRule实体
            rule = CommunityCheckinRule(
                community_id=community_id,
                rule_name=params['rule_name'],
                custom_time=params.get('custom_time', None),
                icon_url=params.get('icon_url', '📋'),
                status=1,  # 默认启用
                created_by=user_id
            )

            # 保存到数据库
            saved_rule = self.checkin_rule_repository.save(rule)

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'成功创建社区打卡规则，规则ID: {saved_rule.community_rule_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='创建成功',
                data={
                    'rule_id': saved_rule.community_rule_id,
                    'rule_name': saved_rule.rule_name,
                    'message': '创建成功'
                }
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'创建社区打卡规则失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建规则失败: {str(e)}'
            )
