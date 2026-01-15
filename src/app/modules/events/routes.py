"""
事件管理模块路由
"""
import logging
from flask import request
from . import events_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import require_token, require_community_staff_member, require_community_membership

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

        # 使用应用服务用例创建事件
        from app.application.use_cases.events import CreateEventUseCase

        use_case = CreateEventUseCase()
        result = use_case.execute(
            user_id=user_id,
            community_id=community_id,
            title=title,
            description=description,
            event_type=event_type,
            location=location,
            target_user_id=target_user_id
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

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

        # 使用应用服务用例获取社区事件列表
        from app.application.use_cases.events import GetCommunityEventsUseCase

        use_case = GetCommunityEventsUseCase()
        result = use_case.execute(
            community_id=community_id,
            event_type=event_type_filter,
            status=status_filter
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"获取社区事件API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>', methods=['GET'])
@require_community_staff_member()
def get_event_detail(decoded, event_id):
    """获取事件详情"""
    try:
        # 使用应用服务用例获取事件详情
        from app.application.use_cases.events import GetEventDetailsUseCase

        use_case = GetEventDetailsUseCase()
        result = use_case.execute(event_id=event_id)

        if result.is_success:
            # 兼容前端：将 messages 字段改为 supports
            result_data = {
                'event': result.data.get('event'),
                'supports': result.data.get('messages', [])
            }
            return make_succ_response(result_data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"获取事件详情API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>/support', methods=['POST'])
@require_community_staff_member()
def create_event_support(decoded, event_id):
    """创建事件应援"""
    try:
        data = request.get_json()
        if not data or 'message_content' not in data:
            return make_err_response('缺少应援内容')

        message_content = data['message_content']
        if not message_content.strip():
            return make_err_response('应援内容不能为空')

        # 使用应用服务用例创建应援
        from app.application.use_cases.events import SupportEventUseCase

        use_case = SupportEventUseCase()
        result = use_case.execute(
            sender_id=decoded['user_id'],
            event_id=event_id,
            message_content=message_content.strip()
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"创建应援API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/communities/<int:community_id>/stats', methods=['GET'])
@require_community_membership()
def get_community_stats(decoded, community_id):
    """获取社区事件统计"""
    try:
        # 使用应用服务用例获取社区统计
        from app.application.use_cases.events import GetCommunityStatsUseCase

        use_case = GetCommunityStatsUseCase()
        result = use_case.execute(community_id=community_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"获取社区统计API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/communities/<int:community_id>/pending-events', methods=['GET'])
@require_community_staff_member()
def get_pending_events(decoded, community_id):
    """获取社区未处理的求助事件"""
    try:
        # 使用应用服务用例获取未处理事件
        from app.application.use_cases.events import GetPendingEventsUseCase

        use_case = GetPendingEventsUseCase()
        result = use_case.execute(community_id=community_id)

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

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
        message_tags = data.get('message_tags', [])

        # 使用应用服务用例添加回应
        from app.application.use_cases.events import AddEventMessageUseCase

        use_case = AddEventMessageUseCase()
        result = use_case.execute(
            event_id=event_id,
            sender_id=staff_id,
            content=content,
            media_url=media_url,
            message_tags=message_tags
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

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

        # 使用应用服务用例更新事件位置
        from app.application.use_cases.events import UpdateEventLocationUseCase

        use_case = UpdateEventLocationUseCase()
        result = use_case.execute(
            event_id=event_id,
            location=location,
            location_lat=location_lat,
            location_lon=location_lon
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"更新事件位置API异常: {str(e)}")
        return make_err_response('服务器内部错误')


@events_bp.route('/events/<int:event_id>/close', methods=['PUT'])
@require_token()
def close_event(decoded, event_id):
    """关闭事件（通用接口）"""
    try:
        data = request.get_json()
        if not data or 'closure_reason' not in data:
            return make_err_response('缺少关闭原因')

        closure_reason = data.get('closure_reason', '').strip()
        if not closure_reason:
            return make_err_response('关闭原因不能为空')

        user_id = decoded.get('user_id')

        # 使用应用服务用例关闭事件
        from app.application.use_cases.events import CloseEventUseCase

        use_case = CloseEventUseCase()
        result = use_case.execute(
            event_id=event_id,
            user_id=user_id,
            closure_reason=closure_reason
        )

        if result.is_success:
            return make_succ_response(result.data)
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        logger.error(f"关闭事件API异常: {str(e)}", exc_info=True)
        return make_err_response('服务器内部错误')