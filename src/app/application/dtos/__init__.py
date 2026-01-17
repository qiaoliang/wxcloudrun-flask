"""
应用层DTO(数据传输对象)

DTO负责领域实体与API响应格式之间的转换,隔离Controller层与领域层
"""
from .checkin_rule_dto import CheckinRuleDTO
from .checkin_record_dto import CheckinRecordDTO
from .common_dto import PaginationDTO, ResponseDTO

__all__ = [
    'CheckinRuleDTO',
    'CheckinRecordDTO',
    'PaginationDTO',
    'ResponseDTO',
]
