"""
事件管理模块路由
"""
import logging
from flask import request
from . import events_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import require_token, require_community_staff_member, require_community_membership
from wxcloudrun.community_event_service import CommunityEventService
from wxcloudrun.community_service import CommunityService
from database.flask_models import db, User

logger = logging.getLogger(__name__)


@events_bp.route('/events', methods=['POST'])
@require_community_membership()
def create_event(decoded):
    """创建社区事件"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response('请求数据不能为空')
        
        # 必填参数验证
        required_fields = ['community_id', 'title']
        for field in required_fields:
            if field not in data or not data[field]:
                return make_err_response(f'缺少必填参数: {field}')
        
        user_id = decoded['user_id']
        community_id = data['community_id']
        title = data['title']
        description = data.get('description', '')
        event_type = data.get('event_type', 'call_for_help')
        location = data.get('location', '')
        target_user_id = data.get('target_user_id')
        
        # 验证事件类型
        if event_type not in ['call_for_help', 'supporting']:
            return make_err_response('无效的事件类型')
        
        result = CommunityEventService.create_event(
            user_id=user_id,
            community_id=community_id,
            title=title,
            description=description,
            event_type=event_type,
            location=location,
            target_user_id=target_user_id
        )
        
        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])
            
    except Exception as e:
        logger.error(f"创建事件API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/communities/<int:community_id>/events', methods=['GET'])
@require_community_staff_member()
def get_community_events(decoded, community_id):
    """获取社区事件列表"""
    try:
        # 获取查询参数
        status_filter = request.args.get('status', type=int)
        event_type_filter = request.args.get('event_type')
        
        # 获取当前用户信息
        user_id = decoded.get('user_id')
        user = db.session.get(User, user_id)
        
        if not user:
            return make_err_response('用户不存在')
        
        result = CommunityEventService.get_community_events(
            community_id=community_id,
            status_filter=status_filter,
            event_type_filter=event_type_filter,
            current_user=user
        )
        
        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])
            
    except Exception as e:
        logger.error(f"获取社区事件API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>', methods=['GET'])
@require_community_staff_member()
def get_event_detail(decoded, event_id):
    """获取事件详情"""
    try:
        # 先获取事件详情
        result = CommunityEventService.get_event_detail(event_id)
        
        if not result['success']:
            return make_err_response(result['message'])
        
        # 兼容前端：将 supports 字段改为 messages
        result_data = {
            'event': result.get('event'),
            'messages': result.get('supports', [])
        }
        
        return make_succ_response(result_data)
            
    except Exception as e:
        logger.error(f"获取事件详情API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>/support', methods=['POST'])
@require_community_staff_member()
def create_event_support(decoded, event_id):
    """创建事件应援"""
    try:
        data = request.get_json()
        if not data or 'support_content' not in data:
            return make_err_response('缺少应援内容')
        
        support_content = data['support_content']
        if not support_content.strip():
            return make_err_response('应援内容不能为空')
        
        result = CommunityEventService.create_support(
            event_id=event_id,
            supporter_id=decoded['user_id'],
            support_content=support_content.strip()
        )
        
        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])
            
    except Exception as e:
        logger.error(f"创建应援API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/communities/<int:community_id>/stats', methods=['GET'])
@require_community_membership()
def get_community_stats(decoded, community_id):
    """获取社区事件统计"""
    try:
        result = CommunityEventService.get_community_stats(community_id)

        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])

    except Exception as e:
        logger.error(f"获取社区统计API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/communities/<int:community_id>/pending-events', methods=['GET'])
@require_community_staff_member()
def get_pending_events(decoded, community_id):
    """获取社区未处理的求助事件"""
    try:
        result = CommunityEventService.get_pending_events(community_id)

        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])

    except Exception as e:
        logger.error(f"获取未处理事件API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>/respond', methods=['POST'])
@require_community_staff_member()
def add_staff_response(decoded, event_id):
    """工作人员添加回应"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response('请求数据不能为空')

        staff_id = decoded['user_id']
        content = data.get('content', '')
        media_url = data.get('media_url')
        support_tags = data.get('support_tags', [])

        # 至少要有文字内容或媒体文件
        if not content.strip() and not media_url:
            return make_err_response('请至少提供文字内容或媒体文件')

        result = CommunityEventService.add_staff_response(
            event_id=event_id,
            staff_id=staff_id,
            content=content,
            media_url=media_url,
            support_tags=support_tags
        )

        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])

    except Exception as e:
        logger.error(f"添加工作人员回应API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>/location', methods=['PUT'])
@require_community_membership()
def update_event_location(decoded, event_id):
    """更新事件位置信息"""
    try:
        data = request.get_json()
        if not data:
            return make_err_response('请求数据不能为空')
        
        location = data.get('location', '')
        location_lat = data.get('location_lat')
        location_lon = data.get('location_lon')
        
        # 至少需要 location 或坐标信息
        if not location and (location_lat is None or location_lon is None):
            return make_err_response('请提供位置信息')
        
        result = CommunityEventService.update_event_location(
            event_id=event_id,
            location=location,
            location_lat=location_lat,
            location_lon=location_lon
        )
        
        if result['success']:
            return make_succ_response(result)
        else:
            return make_err_response(result['message'])
            
    except Exception as e:
        logger.error(f"更新事件位置API异常: {str(e)}")
        return make_err_response('服务器内部错误')