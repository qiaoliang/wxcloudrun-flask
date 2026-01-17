"""
通用DTO
"""
from typing import List, Optional, Any


class PaginationDTO:
    """分页数据传输对象"""

    @staticmethod
    def from_entity(total: int, page: int, page_size: int, items: List[Any]) -> dict:
        """
        从领域实体列表创建分页响应

        Args:
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            items: 领域实体列表

        Returns:
            dict: API分页响应格式
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'items': items
        }


class ResponseDTO:
    """统一响应格式"""

    @staticmethod
    def success(data: Any = None, message: str = '操作成功') -> dict:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息

        Returns:
            dict: 成功响应格式
        """
        return {
            'status': 'success',
            'message': message,
            'data': data
        }

    @staticmethod
    def error(message: str, code: str = 'ERROR') -> dict:
        """
        错误响应

        Args:
            message: 错误消息
            code: 错误码

        Returns:
            dict: 错误响应格式
        """
        return {
            'status': 'error',
            'code': code,
            'message': message
        }
