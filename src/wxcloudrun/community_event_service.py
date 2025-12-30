"""
社区事件服务 - Flask-SQLAlchemy版本
提供社区求助和应援事件的管理功能
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import select, func

from database.flask_models import db, CommunityEvent, EventSupport, User, Community
from wxcloudrun.community_service import CommunityService
from app.shared.utils.transaction import transactional, transaction

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
            user = db.session.get(User, user_id)
            if not user:
                return {'success': False, 'message': '用户不存在'}

            community = db.session.get(Community, community_id)
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

            with transaction():
                db.session.add(event)
                db.session.flush()

            logger.info(f"用户{user_id}在社区{community_id}创建了事件{event.event_id}")

            return {
                'success': True,
                'message': '事件创建成功',
                'event': event.to_dict()
            }

        except Exception as e:
            logger.error(f"创建事件失败: {str(e)}")
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
            # 使用 SQLAlchemy 2.0 的 select() 语句
            stmt = select(CommunityEvent).where(
                CommunityEvent.community_id == community_id
            )
            
            # 应用过滤条件
            if status_filter is not None:
                stmt = stmt.where(CommunityEvent.status == status_filter)
            
            if event_type_filter is not None:
                stmt = stmt.where(CommunityEvent.event_type == event_type_filter)
            
            stmt = stmt.order_by(CommunityEvent.created_at.desc())
            events = db.session.execute(stmt).scalars().all()
            
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
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 获取应援记录
            stmt = select(EventSupport).where(
                EventSupport.event_id == event_id,
                EventSupport.status == 1
            ).order_by(EventSupport.created_at.desc())
            supports = db.session.execute(stmt).scalars().all()
            
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
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}

            # 验证事件状态
            if event.status != 1:  # 不是进行中状态
                return {'success': False, 'message': '事件已结束，无法应援'}

            # 验证应援者
            supporter = db.session.get(User, supporter_id)
            if not supporter:
                return {'success': False, 'message': '应援者不存在'}

            # 验证应援者是否为社区工作人员
            if not CommunityService.has_community_permission(supporter_id, event.community_id):
                return {'success': False, 'message': '无权限进行应援操作'}

            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 检查是否已经应援过
            stmt = select(EventSupport).where(
                EventSupport.event_id == event_id,
                EventSupport.supporter_id == supporter_id,
                EventSupport.status == 1
            )
            existing_support = db.session.execute(stmt).scalar_one_or_none()

            if existing_support:
                return {'success': False, 'message': '您已经应援过该事件'}

            # 创建应援记录
            support = EventSupport(
                event_id=event_id,
                supporter_id=supporter_id,
                support_content=support_content
            )

            with transaction():
                db.session.add(support)
                db.session.flush()

            logger.info(f"用户{supporter_id}对事件{event_id}进行了应援")

            return {
                'success': True,
                'message': '应援成功',
                'support': support.to_dict()
            }

        except Exception as e:
            logger.error(f"创建应援失败: {str(e)}")
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
            community = db.session.get(Community, community_id)
            if not community:
                return {'success': False, 'message': '社区不存在'}
            
            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 未结束事件数量（状态为1-进行中）
            stmt_active = select(func.count()).select_from(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1
            )
            active_events_count = db.session.execute(stmt_active).scalar()

            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 应援数量（未结束事件中的supporting类型事件数量）
            stmt_support = select(func.count()).select_from(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.status == 1,
                CommunityEvent.event_type == 'supporting'
            )
            support_events_count = db.session.execute(stmt_support).scalar()

            return {
                'success': True,
                'active_events': active_events_count,
                'support_count': support_events_count
            }

        except Exception as e:
            logger.error(f"获取社区统计失败: {str(e)}")
            return {'success': False, 'message': f'获取统计失败: {str(e)}'}

    @staticmethod
    def get_user_active_event(user_id: int) -> Dict:
        """
        获取用户当前进行中的事件（call_for_help类型）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 查询结果
        """
        try:
            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 查询用户作为target_user的进行中事件
            stmt = select(CommunityEvent).where(
                CommunityEvent.target_user_id == user_id,
                CommunityEvent.event_type == 'call_for_help',
                CommunityEvent.status == 1  # 进行中
            ).order_by(CommunityEvent.created_at.desc())

            # 使用 first() 而不是 scalar_one_or_none()，避免多行数据错误
            # 如果用户有多个进行中的事件，只返回最新的一条
            event = db.session.execute(stmt).scalars().first()
            
            if not event:
                return {
                    'success': True,
                    'event': None,
                    'messages': []
                }
            
            # 获取事件消息（EventSupport记录）
            stmt_messages = select(EventSupport).where(
                EventSupport.event_id == event.event_id,
                EventSupport.status == 1
            ).order_by(EventSupport.created_at.desc())
            
            messages = db.session.execute(stmt_messages).scalars().all()
            
            return {
                'success': True,
                'event': event.to_dict(),
                'messages': [msg.to_dict() for msg in messages]
            }
            
        except Exception as e:
            logger.error(f"获取用户进行中事件失败: {str(e)}")
            return {'success': False, 'message': f'获取事件失败: {str(e)}'}

    @staticmethod
    def add_event_message(event_id: int, user_id: int, message_type: str = 'text',
                        content: str = '', media_url: str = None, 
                        media_duration: int = None, support_tags: list = None) -> Dict:
        """
        添加事件消息
        
        Args:
            event_id: 事件ID
            user_id: 用户ID
            message_type: 消息类型（text/voice/image）
            content: 文字内容
            media_url: 媒体文件URL
            media_duration: 语音时长（秒）
            support_tags: 回应标签（工作人员使用）
            
        Returns:
            Dict: 添加结果
        """
        try:
            # 验证事件存在
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 验证事件状态
            if event.status != 1:
                return {'success': False, 'message': '事件已结束，无法添加消息'}
            
            # 验证用户权限
            user = db.session.get(User, user_id)
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            # 检查用户是否为事件相关人员（发起者或目标用户或社区工作人员）
            is_event_user = (event.created_by == user_id or event.target_user_id == user_id)
            is_staff = CommunityService.has_community_permission(user_id, event.community_id)
            
            if not is_event_user and not is_staff:
                return {'success': False, 'message': '无权限添加消息'}
            
            # 创建消息记录
            message = EventSupport(
                event_id=event_id,
                supporter_id=user_id,
                support_content=content,
                message_type=message_type,
                media_url=media_url,
                media_duration=media_duration,
                support_tags=support_tags
            )
            
            with transaction():
                db.session.add(message)
                db.session.flush()
            
            logger.info(f"用户{user_id}向事件{event_id}添加了{message_type}消息")
            
            return {
                'success': True,
                'message': '消息添加成功',
                'message_data': message.to_dict()
            }
            
        except Exception as e:
            logger.error(f"添加事件消息失败: {str(e)}")
            return {'success': False, 'message': f'添加消息失败: {str(e)}'}

    @staticmethod
    def close_event(event_id: int, user_id: int, closure_reason: str) -> Dict:
        """
        关闭事件
        
        Args:
            event_id: 事件ID
            user_id: 用户ID
            closure_reason: 关闭原因
            
        Returns:
            Dict: 关闭结果
        """
        try:
            # 导入 EventClosure 模型
            from database.flask_models import EventClosure
            
            # 验证事件存在
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 验证事件状态
            if event.status != 1:
                return {'success': False, 'message': '事件已关闭'}
            
            # 验证用户权限（只有事件发起者或目标用户可以关闭）
            if event.created_by != user_id and event.target_user_id != user_id:
                return {'success': False, 'message': '只有事件发起者或目标用户可以关闭事件'}
            
            with transaction():
                # 创建关闭记录
                closure = EventClosure(
                    event_id=event_id,
                    closed_by=user_id,
                    closure_reason=closure_reason,
                    closure_status='user_closed'
                )
                db.session.add(closure)
                
                # 更新事件状态
                event.status = 2  # 已完成
                event.completed_at = datetime.now()
                
                db.session.flush()
            
            logger.info(f"用户{user_id}关闭了事件{event_id}，原因：{closure_reason}")
            
            return {
                'success': True,
                'message': '事件已关闭',
                'closure': closure.to_dict()
            }
            
        except Exception as e:
            logger.error(f"关闭事件失败: {str(e)}")
            return {'success': False, 'message': f'关闭事件失败: {str(e)}'}

    @staticmethod
    def get_event_history(event_id: int, limit: int = 50) -> Dict:
        """
        获取事件历史记录
        
        Args:
            event_id: 事件ID
            limit: 返回消息数量限制
            
        Returns:
            Dict: 历史记录
        """
        try:
            # 验证事件存在
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 获取事件消息
            stmt = select(EventSupport).where(
                EventSupport.event_id == event_id,
                EventSupport.status == 1
            ).order_by(EventSupport.created_at.desc()).limit(limit)
            
            messages = db.session.execute(stmt).scalars().all()
            
            return {
                'success': True,
                'event': event.to_dict(),
                'messages': [msg.to_dict() for msg in messages],
                'total': len(messages)
            }
            
        except Exception as e:
            logger.error(f"获取事件历史失败: {str(e)}")
            return {'success': False, 'message': f'获取历史失败: {str(e)}'}

    @staticmethod
    def get_pending_events(community_id: int) -> Dict:
        """
        获取社区未处理的求助事件
        
        Args:
            community_id: 社区ID
            
        Returns:
            Dict: 未处理事件列表
        """
        try:
            # 验证社区是否存在
            community = db.session.get(Community, community_id)
            if not community:
                return {'success': False, 'message': '社区不存在'}
            
            # 使用 SQLAlchemy 2.0 的 select() 语句
            # 查询未处理的call_for_help类型事件
            stmt = select(CommunityEvent).where(
                CommunityEvent.community_id == community_id,
                CommunityEvent.event_type == 'call_for_help',
                CommunityEvent.status == 1
            ).order_by(CommunityEvent.created_at.desc())
            
            events = db.session.execute(stmt).scalars().all()
            
            return {
                'success': True,
                'events': [event.to_dict() for event in events],
                'count': len(events)
            }
            
        except Exception as e:
            logger.error(f"获取未处理事件失败: {str(e)}")
            return {'success': False, 'message': f'获取未处理事件失败: {str(e)}'}

    @staticmethod
    def add_staff_response(event_id: int, staff_id: int, content: str = '',
                          media_url: str = None, support_tags: list = None) -> Dict:
        """
        工作人员添加回应
        
        Args:
            event_id: 事件ID
            staff_id: 工作人员ID
            content: 文字内容
            media_url: 媒体文件URL
            support_tags: 回应标签
            
        Returns:
            Dict: 添加结果
        """
        try:
            # 验证事件存在
            event = db.session.get(CommunityEvent, event_id)
            if not event:
                return {'success': False, 'message': '事件不存在'}
            
            # 验证事件状态
            if event.status != 1:
                return {'success': False, 'message': '事件已结束'}
            
            # 验证工作人员权限
            if not CommunityService.has_community_permission(staff_id, event.community_id):
                return {'success': False, 'message': '无权限进行此操作'}
            
            # 创建回应记录
            message = EventSupport(
                event_id=event_id,
                supporter_id=staff_id,
                support_content=content,
                message_type='text',
                media_url=media_url,
                support_tags=support_tags
            )
            
            with transaction():
                db.session.add(message)
                db.session.flush()
            
            logger.info(f"工作人员{staff_id}对事件{event_id}添加了回应")
            
            return {
                'success': True,
                'message': '回应添加成功',
                'message_data': message.to_dict()
            }
            
        except Exception as e:
            logger.error(f"添加工作人员回应失败: {str(e)}")
            return {'success': False, 'message': f'添加回应失败: {str(e)}'}