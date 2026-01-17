"""
打卡规则数据传输对象

负责 CheckinRuleEntity 与 API 响应格式之间的转换
"""
from typing import Optional, List, Any
from datetime import datetime


class CheckinRuleDTO:
    """打卡规则数据传输对象"""

    @staticmethod
    def from_entity(rule: 'CheckinRuleEntity') -> dict:
        """
        将领域实体转换为API响应格式

        Args:
            rule: 打卡规则领域实体

        Returns:
            dict: API响应格式
        """
        return {
            'rule_id': rule.rule_id,
            'user_id': rule.user_id,
            'rule_name': rule.rule_name,
            'frequency_type': rule.frequency_type,
            'time_slot_type': rule.time_slot_type,
            'status': rule.status,
            'community_id': rule.community_id,
            'icon_url': rule.icon_url,
            'custom_time': rule.custom_time,  # 字符串格式 HH:MM:SS
            'week_days': rule.week_days,  # 整数位掩码
            'custom_start_date': rule.custom_start_date.isoformat() if rule.custom_start_date else None,
            'custom_end_date': rule.custom_end_date.isoformat() if rule.custom_end_date else None,
            'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else None,
            'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else None
        }

    @staticmethod
    def from_entity_list(entities: List['CheckinRuleEntity']) -> List[dict]:
        """
        将领域实体列表转换为API响应格式

        Args:
            entities: 领域实体列表

        Returns:
            List[dict]: API响应格式列表
        """
        return [CheckinRuleDTO.from_entity(entity) for entity in entities]

    @staticmethod
    def from_pagination_result(total: int, page: int, page_size: int,
                              entities: List['CheckinRuleEntity']) -> dict:
        """
        创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            entities: 领域实体列表

        Returns:
            dict: 分页响应
        """
        from .common_dto import PaginationDTO

        return PaginationDTO.from_entity(
            total=total,
            page=page,
            page_size=page_size,
            items=CheckinRuleDTO.from_entity_list(entities)
        )
