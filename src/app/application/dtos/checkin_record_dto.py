"""
打卡记录数据传输对象

负责 CheckinRecordEntity 与 API 响应格式之间的转换
"""
from typing import Optional, List
from datetime import datetime


class CheckinRecordDTO:
    """打卡记录数据传输对象"""

    @staticmethod
    def from_entity(record: 'CheckinRecordEntity') -> dict:
        """
        将领域实体转换为API响应格式

        Args:
            record: 打卡记录领域实体

        Returns:
            dict: API响应格式
        """
        # 状态映射
        status_map = {
            0: 'pending',
            1: 'completed',
            2: 'missed',
            3: 'cancelled'
        }
        status_name = status_map.get(record.checkin_status, 'unknown')

        return {
            'record_id': record.record_id,
            'rule_id': record.rule_id,
            'user_id': record.user_id,
            'planned_time': record.planned_checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.planned_checkin_time else None,
            'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
            'status': record.checkin_status,
            'status_name': status_name,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else None,
            'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else None
        }

    @staticmethod
    def from_entity_list(records: List['CheckinRecordEntity']) -> List[dict]:
        """
        将领域实体列表转换为API响应格式

        Args:
            records: 领域实体列表

        Returns:
            List[dict]: API响应格式列表
        """
        return [CheckinRecordDTO.from_entity(record) for record in records]

    @staticmethod
    def from_pagination_result(total: int, page: int, page_size: int,
                              records: List['CheckinRecordEntity']) -> dict:
        """
        创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            records: 领域实体列表

        Returns:
            dict: 分页响应
        """
        from .common_dto import PaginationDTO

        return PaginationDTO.from_entity(
            total=total,
            page=page,
            page_size=page_size,
            items=CheckinRecordDTO.from_entity_list(records)
        )
