"""
获取社区打卡规则列表用例
"""
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCommunityCheckinRulesUseCase(BaseUseCase):
    """获取社区打卡规则列表用例"""

    def __init__(self):
        """初始化用例，注入依赖的仓储"""
        self.checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()

    def _validate(self, community_id: int, page: int = 1, per_page: int = 20,
                  status_filter: str = None, grouped: bool = False) -> UseCaseResult:
        """
        验证参数

        Args:
            community_id: 社区ID
            page: 页码（默认1）
            per_page: 每页数量（默认20，最大100）
            status_filter: 状态过滤（enabled/disable）
            grouped: 是否返回分组数据（默认false）

        Returns:
            UseCaseResult: 验证结果
        """
        if not isinstance(community_id, int) or community_id <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='社区ID必须为正整数'
            )

        if not isinstance(page, int) or page <= 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='页码必须为正整数'
            )

        if not isinstance(per_page, int) or per_page <= 0 or per_page > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        if status_filter is not None and status_filter not in ['enabled', 'disabled']:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='状态过滤参数必须是 enabled 或 disabled'
            )

        if not isinstance(grouped, bool):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='分组参数必须是布尔值'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='验证通过'
        )

    def _execute(self, community_id: int, page: int = 1, per_page: int = 20,
                 status_filter: str = None, grouped: bool = False) -> UseCaseResult:
        """
        执行获取社区打卡规则列表操作

        Args:
            community_id: 社区ID
            page: 页码（默认1）
            per_page: 每页数量（默认20，最大100）
            status_filter: 状态过滤（enabled/disable）
            grouped: 是否返回分组数据（默认false）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if grouped:
                # 返回按状态分组的规则
                grouped_data = self.checkin_rule_repository.get_all_grouped_by_status(community_id)

                # 序列化数据
                serialized_data = {
                    'enabled': [rule.to_dict() for rule in grouped_data.get('enabled', [])],
                    'disabled': [rule.to_dict() for rule in grouped_data.get('disabled', [])],
                    'deleted': [rule.to_dict() for rule in grouped_data.get('deleted', [])]
                }

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='获取规则列表成功',
                    data=serialized_data
                )
            else:
                # 获取规则列表（分页）
                if status_filter == 'enabled':
                    rules = self.checkin_rule_repository.get_all_enabled_by_community_id(community_id)
                elif status_filter == 'disabled':
                    rules = self.checkin_rule_repository.find_by_community_id(community_id, include_deleted=False)
                    rules = [r for r in rules if r.status == 0]  # 0=disabled
                else:
                    rules = self.checkin_rule_repository.find_by_community_id(community_id, include_deleted=False)

                # 分页
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                total = len(rules)

                paginated_rules = rules[start_idx:end_idx]

                # 序列化数据并转换字段名以匹配API文档
                serialized_rules = []
                for rule in paginated_rules:
                    rule_dict = rule.to_dict()
                    # 转换week_days为数组
                    repeat_days = []
                    if rule_dict.get('week_days'):
                        for i in range(7):
                            if rule_dict['week_days'] & (1 << i):
                                repeat_days.append(i + 1)

                    # 获取创建者信息
                    created_by_name = rule.creator.nickname if rule.creator else '未知'

                    # 转换为API期望的字段名
                    api_rule = {
                        'community_rule_id': rule_dict['community_rule_id'],
                        'rule_name': rule_dict['rule_name'],
                        'icon_url': rule_dict.get('icon_url', ''),
                        'description': '',  # 模型没有description字段
                        'checkin_time': rule_dict.get('custom_time', ''),  # custom_time -> checkin_time
                        'repeat_days': repeat_days,
                        'is_enabled': rule_dict['status'] == 1,
                        'created_by_name': created_by_name
                    }
                    serialized_rules.append(api_rule)

                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='获取规则列表成功',
                    data={
                        'rules': serialized_rules,
                        'total': total,
                        'page': page,
                        'per_page': per_page,
                        'has_next': end_idx < total
                    }
                )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则列表失败: {str(e)}'
            )
