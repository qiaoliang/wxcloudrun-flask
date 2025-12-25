"""
社区测试工具方法
处理固定社区（安卡大家庭、黑屋）的创建和获取逻辑
避免测试用例之间的数据冲突
"""

import sys
import os
from datetime import datetime

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import Community
from const_default import DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_ID, DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME


def get_or_create_special_communities(session):
    """
    获取或创建特殊社区（安卡大家庭和黑屋）
    避免测试用例之间的数据冲突
    
    Args:
        session: 数据库会话
        
    Returns:
        tuple: (ankafamily_community, blackhouse_community)
    """
    # 尝试获取安卡大家庭社区
    ankafamily = session.query(Community).filter_by(
        community_id=DEFAULT_COMMUNITY_ID
    ).first()
    
    if not ankafamily:
        # 创建安卡大家庭社区
        ankafamily = Community(
            community_id=DEFAULT_COMMUNITY_ID,
            name=DEFAULT_COMMUNITY_NAME,
            description="默认社区",
            status=1,
            created_at=datetime(2023, 1, 1)  # 固定创建时间用于测试排序
        )
        session.add(ankafamily)
    
    # 尝试获取黑屋社区
    blackhouse = session.query(Community).filter_by(
        community_id=DEFAULT_BLACK_ROOM_ID
    ).first()
    
    if not blackhouse:
        # 创建黑屋社区
        blackhouse = Community(
            community_id=DEFAULT_BLACK_ROOM_ID,
            name=DEFAULT_BLACK_ROOM_NAME,
            description="黑屋社区",
            status=1,
            created_at=datetime(2023, 6, 1)  # 固定创建时间用于测试排序
        )
        session.add(blackhouse)
    
    # 提交更改
    session.flush()
    
    return ankafamily, blackhouse


def create_normal_community(session, name=None, description=None, status=1, created_at=None):
    """
    创建普通社区用于测试
    
    Args:
        session: 数据库会话
        name: 社区名称（可选）
        description: 社区描述（可选）
        status: 社区状态（默认为1）
        created_at: 创建时间（可选）
        
    Returns:
        Community: 创建的社区对象
    """
    if name is None:
        name = f"测试社区_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    if description is None:
        description = f"{name}的描述"
    
    if created_at is None:
        created_at = datetime.now()
    
    community = Community(
        name=name,
        description=description,
        status=status,
        created_at=created_at
    )
    session.add(community)
    session.flush()
    
    return community


def ensure_special_communities_exist(session):
    """
    确保特殊社区存在（兼容性方法）
    
    Args:
        session: 数据库会话
        
    Returns:
        None
    """
    get_or_create_special_communities(session)


def disable_special_community(session, community_id):
    """
    禁用特殊社区（用于测试禁用状态）
    
    Args:
        session: 数据库会话
        community_id: 社区ID
        
    Returns:
        Community: 更新后的社区对象
    """
    community = session.query(Community).filter_by(
        community_id=community_id
    ).first()
    
    if community:
        community.status = 0  # 禁用
        session.flush()
    
    return community