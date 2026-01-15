"""
获取社区打卡规则列表用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from ..base import BaseUseCase, UseCaseResult, UseCaseStatus


class GetCommunityCheckinRulesUseCase(BaseUseCase):
    """获取社区打卡规则列表用例"""

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
            # 调用服务层获取规则列表
            if grouped:
                # 返回按状态分组的规则（包括已删除的）
                result = CommunityCheckinRuleService.get_all_community_rules_grouped(
                    community_id
                )
                current_app.logger.info(
                    f'成功获取社区 {community_id} 的分组打卡规则，'
                    f'停用={len(result.get("disabled", []))}, '
                    f'启用={len(result.get("enabled", []))}, '
                    f'删除={len(result.get("deleted", []))}'
                )
            else:
                # 返回扁平列表
                # 默认返回所有未删除的规则（包括停用的），
                # 只有status='enabled'时才只返回启用状态的规则
                include_disabled = (status_filter != 'enabled')
                rules = CommunityCheckinRuleService.get_community_rules(
                    community_id, include_disabled
                )

                # 简单包装结果格式，保持与预期一致
                result = {
                    'rules': rules,
                    'total': len(rules),
                    'page': page,
                    'per_page': per_page
                }
                current_app.logger.info(
                    f'成功获取社区 {community_id} 的打卡规则列表，共 {len(result.get("rules", []))} 条规则'
                )

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取规则列表成功',
                data=result
            )

        except Exception as e:
            current_app.logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取规则列表失败: {str(e)}'
            )