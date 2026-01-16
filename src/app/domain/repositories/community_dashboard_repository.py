"""
社区仪表板仓储接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import date


class CommunityDashboardRepository(ABC):
    """社区仪表板仓储接口"""

    @abstractmethod
    def get_community_stats(self, community_id: int) -> Dict:
        """
        获取社区统计数据

        Args:
            community_id: 社区ID

        Returns:
            统计数据字典，包含:
            - total_users: 用户总数
            - today_checkin_rate: 今日打卡率
            - unchecked_count: 未打卡人数
            - total_rules: 规则总数
        """
        pass

    @abstractmethod
    def get_abnormal_users(
        self,
        community_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        获取异常用户列表

        Args:
            community_id: 社区ID
            page: 页码
            page_size: 每页数量

        Returns:
            异常用户列表字典，包含:
            - users: 用户列表
            - total: 总数
            - page: 当前页
            - page_size: 每页数量
            - has_next: 是否有下一页
        """
        pass

    @abstractmethod
    def get_trend_data(self, community_id: int, days: int = 7) -> Dict:
        """
        获取历史趋势数据

        Args:
            community_id: 社区ID
            days: 天数（7或30）

        Returns:
            趋势数据字典，包含:
            - date_range: 日期范围列表
            - checkin_rates: 打卡率列表
            - rule_missed_stats: 规则逾期统计列表
        """
        pass

    @abstractmethod
    def get_pending_events(self, community_id: int, limit: int = 3) -> List[Dict]:
        """
        获取未处理的事件列表

        Args:
            community_id: 社区ID
            limit: 最大返回数量

        Returns:
            未处理事件列表，每个事件包含:
            - event_id: 事件ID
            - type: 事件类型
            - title: 事件标题
            - description: 事件描述
            - created_at: 创建时间
            - relative_time: 相对时间描述
        """
        pass

    @abstractmethod
    def get_user_abnormality_detail(
        self,
        community_id: int,
        user_id: int
    ) -> Dict:
        """
        获取用户的异常值详情

        Args:
            community_id: 社区ID
            user_id: 用户ID

        Returns:
            用户异常值详情字典，包含:
            - user_id: 用户ID
            - date: 日期
            - total_abnormality: 总异常值
            - rule_details: 规则详情列表
        """
        pass

    @abstractmethod
    def has_permission(self, user_id: int, community_id: int) -> bool:
        """
        检查用户是否有权限访问社区数据看板

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            是否有权限
        """
        pass

    @abstractmethod
    def get_community_checkin_stats(self, community_id: int, days: int = 7) -> Dict:
        """
        获取社区打卡统计信息

        Args:
            community_id: 社区ID
            days: 统计天数（默认7天）

        Returns:
            统计数据字典，包含:
            - stats: 每个规则的打卡统计列表
            - total_rules: 规则总数
        """
        pass

    @abstractmethod
    def get_community_daily_stats(self, community_id: int) -> Dict:
        """
        获取社区每日打卡统计

        Args:
            community_id: 社区ID

        Returns:
            每日统计数据字典，包含:
            - user_count: 用户数
            - total_rules: 规则数
            - total_checkins: 总打卡数
            - completed_checkins: 已完成打卡数
            - missed_checkins: 未完成打卡数
            - checkin_rate: 打卡率
            - unchecked_user_count: 未打卡用户数
        """
        pass
