"""
获取社区打卡规则列表用例
"""
from flask import current_app
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService


class GetCommunityCheckinRulesUseCase:
    """获取社区打卡规则列表用例"""

    def execute(self, community_id: int, page: int = 1, per_page: int = 20,
                status_filter: str = None, grouped: bool = False) -> dict:
        """
        执行获取社区打卡规则列表操作

        Args:
            community_id: 社区ID
            page: 页码（默认1）
            per_page: 每页数量（默认20，最大100）
            status_filter: 状态过滤（enabled/disable）
            grouped: 是否返回分组数据（默认false）

        Returns:
            dict: 包含成功状态和响应数据
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

            return {
                'success': True,
                'message': '获取规则列表成功',
                'data': result
            }

        except Exception as e:
            current_app.logger.error(f'获取社区打卡规则列表失败: {str(e)}', exc_info=True)
            return {
                'success': False,
                'message': f'获取规则列表失败: {str(e)}',
                'data': {}
            }