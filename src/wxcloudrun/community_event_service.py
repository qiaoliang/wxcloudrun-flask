"""
社区事件服务 - Flask-SQLAlchemy版本
提供社区求助和应援事件的管理功能
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from database.flask_models import db, CommunityEvent, EventSupport, User, Community
from wxcloudrun.community_service import CommunityService

logger = logging.getLogger(__name__)


class CommunityEventService:
    """社区事件服务类"""

    @staticmethod
    def create_event(user_id: int, community_id: int, title: str, 
                    description: str = "", event_type: str = "call_for_help",
                    location: str = "", target_user_id: int = None) -> Dict:
        """
        创建社区事件
        
        Args:
            user_id: 创建者用户ID
            community_id: 社区ID
            title: 事件标题
            description: 事件描述
            event_type: 事件类型
            location: 事件地点
            target_user_id: 目标用户ID
            
        Returns:
            Dict: 创建结果
        """
        try:
            # 验证用户和社区
            user = db.session.query(User).get(user_id)
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            community = db.session.query(Community).get(community_id)
            if not community:
                return {'success': False, 'message': '社区不存在'}
            
            # 验证用户是否属于该社区
            if user.community_id != community_id:
                return {'success': False, 'message': '用户不属于该社区'}
            
            # 创建事件
            event = CommunityEvent(
                community_id=community_id,
                title=title,
                description=description,
                event_type=event_type,
                location=location,
                target_user_id=target_user_id,
                created_by=user_id
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"用户{user_id}在社区{community_id}创建了事件{event.event_id}")
            
            return {
                'success': True,
                'message': '事件创建成功',
                'event': event.to_dict()
            }
            
        except Exception as e:
            logger.error(f"创建事件失败: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'创建事件失败: {str(e)}'}

    @staticmethod
    def get_community_events(community_id: int, status_filter: int = None, 
                           event_type_filter: str = None) -> Dict:
        """
        获取社区事件列表
        
        Args:
            community_id: 社区ID
            status_filter: 状态过滤（可选）
            event_type_filter: 事件类型过滤（可选）
            
        Returns:
            Dict: 查询结果
        """
        try:
            query = db.session.query(CommunityEvent).filter(
                CommunityEvent.community_id == community_id
            )
            
            # 应用过滤条件
            if status_filter is not None:
                query = query.filter(CommunityEvent.status == status_filter)
            
            if event_type_filter is not None:
                query = query.filter(CommunityEvent.event_type == event_type_filter)
            
            events = query.order_by(CommunityEvent.created_at.desc()).all()
            
            return {
                'success': True,
                'events': [event.to_dict() for event in events]
            }
            
        except Exception as e:
            logger.error(f"获取社区事件失败: {str(e)}")
            return {'success': False, 'message': f'获取事件失败: {str(e)}'}

    @staticmethod
    def get_event_detail(event_id: int) -> Dict:
        """
        获取事件详情
        
        Args:
            event_id: 事件ID
            
        Returns:
            Dict: 事件详情
        """
        try:
            event = db.session.query(CommunityEvent).get(event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 获取应援记录
            supports = db.session.query(EventSupport).filter(
                EventSupport.event_id == event_id,
                EventSupport.status == 1
            ).order_by(EventSupport.created_at.desc()).all()
            
            event_data = event.to_dict()
            event_data['supports'] = [support.to_dict() for support in supports]
            
            return {
                'success': True,
                'event': event_data
            }
            
        except Exception as e:
            logger.error(f"获取事件详情失败: {str(e)}")
            return {'success': False, 'message': f'获取事件详情失败: {str(e)}'}

    @staticmethod
    def create_support(event_id: int, supporter_id: int, support_content: str) -> Dict:
        """
        创建应援记录
        
        Args:
            event_id: 事件ID
            supporter_id: 应援者ID
            support_content: 应援内容
            
        Returns:
            Dict: 创建结果
        """
        try:
            # 验证事件存在
            event = db.session.query(CommunityEvent).get(event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 验证事件状态
            if event.status != 1:  # 不是进行中状态
                return {'success': False, 'message': '事件已结束，无法应援'}
            
            # 验证应援者
            supporter = db.session.query(User).get(supporter_id)
            if not supporter:
                return {'success': False, 'message': '应援者不存在'}
            
            # 验证应援者是否为社区工作人员
            if not CommunityService.has_community_permission(supporter_id, event.community_id):
                return {'success': False, 'message': '无权限进行应援操作'}
            
            # 检查是否已经应援过
            existing_support = db.session.query(EventSupport).filter(
                EventSupport.event_id == event_id,
                EventSupport.supporter_id == supporter_id,
                EventSupport.status == 1
            ).first()
            
            if existing_support:
                return {'success': False, 'message': '您已经应援过该事件'}
            
            # 创建应援记录
            support = EventSupport(
                event_id=event_id,
                supporter_id=supporter_id,
                support_content=support_content
            )
            
            db.session.add(support)
            db.session.commit()
            
            logger.info(f"用户{supporter_id}对事件{event_id}进行了应援")
            
            return {
                'success': True,
                'message': '应援成功',
                'support': support.to_dict()
            }
            
        except Exception as e:
            logger.error(f"创建应援失败: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'应援失败: {str(e)}'}

    @staticmethod
    def get_community_stats(community_id: int) -> Dict:
        """
        获取社区事件统计
        
        Args:
            community_id: 社区ID
            
        Returns:
            Dict: 统计数据
        """
        try:
            # 验证社区是否存在
            community = db.session.query(Community).get(community_id)
            if not community:
                return {'success': False, 'message': '社区不存在'}
            
            # 未结束事件数量（状态为1-进行中）
            active_events_count = db.session.query(CommunityEvent).filter(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1
            ).count()
            
            # 应援数量（未结束事件中的supporting类型事件数量）
            support_events_count = db.session.query(CommunityEvent).filter(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1,
                CommunityEvent.event_type == 'supporting'
            ).count()
            
            return {
                'success': True,
                'active_events': active_events_count,
                'support_count': support_events_count
            }
            
        except Exception as e:
            logger.error(f"获取社区统计失败: {str(e)}")
            return {'success': False, 'message': f'获取统计失败: {str(e)}'}