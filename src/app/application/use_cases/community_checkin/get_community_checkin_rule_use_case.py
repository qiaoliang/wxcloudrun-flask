"""
获取单个社区打卡规则详情用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityCheckinRuleUseCase(BaseUseCase):
    """获取单个社区打卡规则详情用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, rule_id: int) -> UseCaseResult:
        """
        验证参数

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(rule_id, int) or rule_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID必须为正整数'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, rule_id: int) -> UseCaseResult:
        """
        执行获取单个社区打卡规则详情操作

        Args:
            rule_id: 规则ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 调用Repository获取规则详情
            rule = self.checkin_rule_repository.find_by_id(rule_id)

            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'规则 {rule_id} 不存在'
                )

            # 检查规则是否已删除(status=2)
            if rule.status == 2:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'规则 {rule_id} 已删除'
                )

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'成功获取社区打卡规则详情，规则ID: {rule.community_rule_id}')

            # 获取创建者信息
            created_by_name = rule.creator.nickname if rule.creator else '未知'

            # 转换week_days为数组
            repeat_days = []
            if rule.week_days:
                for i in range(7):
                    if rule.week_days & (1 << i):
                        repeat_days.append(i + 1)

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则详情成功',
                data={
                    'community_rule_id': rule.community_rule_id,
                    'rule_name': rule.rule_name,
                    'description': '',  # 模型没有description字段,返回空字符串
                    'checkin_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                    'repeat_days': repeat_days,
                    'is_enabled': rule.status == 1,
                    'created_by_name': created_by_name,
                    'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else None,
                    'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else None
                }
            )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'获取社区打卡规则详情失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则详情失败: {str(e)}'
            )
