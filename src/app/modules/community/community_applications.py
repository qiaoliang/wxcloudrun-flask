"""
社区申请管理路由
包含社区申请的查询、创建、批准和拒绝操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from database.flask_models import db, User, Community
from wxcloudrun.community_service import CommunityService
from wxcloudrun.utils.validators import _audit

app_logger = logging.getLogger('log')


@community_bp.route('/community/applications', methods=['GET'])
def get_community_applications():
    """获取社区申请列表"""
    current_app.logger.info('=== 开始获取社区申请列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status_filter = request.args.get('status')  # 可选的状态过滤

        # 获取申请列表
        result = CommunityService.get_community_applications(
            user_id, page, per_page, status_filter
        )

        # 格式化申请信息
        applications_data = []
        for app in result.get('applications', []):
            app_data = {
                'application_id': app.application_id,
                'community_id': app.community_id,
                'community_name': app.community.name if app.community else None,
                'applicant_id': app.applicant_id,
                'applicant_name': app.applicant.nickname if app.applicant else None,
                'status': app.status,
                'message': app.message,
                'created_at': app.created_at.isoformat() if app.created_at else None,
                'updated_at': app.updated_at.isoformat() if app.updated_at else None
            }
            applications_data.append(app_data)

        response_data = {
            'applications': applications_data,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(applications_data) == per_page
        }

        current_app.logger.info(f'获取社区申请列表成功，共 {len(applications_data)} 条申请')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取社区申请列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取申请列表失败')


@community_bp.route('/community/applications', methods=['POST'])
def create_community_application():
    """创建社区申请"""
    current_app.logger.info('=== 开始创建社区申请 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'申请人ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        message = params.get('message', '')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 创建申请
        application = CommunityService.create_community_application(
            user_id, community_id, message
        )

        # 记录审计日志
        _audit(user_id, 'create_community_application', {
            'community_id': community_id,
            'application_id': application.application_id
        })

        current_app.logger.info(f'创建社区申请成功: application_id={application.application_id}')
        return make_succ_response({
            'application_id': application.application_id,
            'message': '申请提交成功'
        })

    except Exception as e:
        current_app.logger.error(f'创建社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, '申请提交失败')


@community_bp.route('/community/applications/<int:application_id>/approve', methods=['PUT'])
def approve_application(application_id):
    """批准社区申请"""
    current_app.logger.info(f'=== 开始批准社区申请: {application_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    try:
        CommunityService.process_application(
            application_id=application_id,
            approve=True,
            processor_id=user_id
        )

        current_app.logger.info(f'社区申请批准成功: {application_id}')
        return make_succ_response({'message': '批准成功'})

    except Exception as e:
        current_app.logger.error(f'批准社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


@community_bp.route('/community/applications/<int:application_id>/reject', methods=['PUT'])
def reject_application(application_id):
    """拒绝社区申请"""
    current_app.logger.info(f'=== 开始拒绝社区申请: {application_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = db.session.get(User, user_id)

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        rejection_reason = params.get('reason', '')

        CommunityService.process_application(
            application_id=application_id,
            approve=False,
            processor_id=user_id,
            rejection_reason=rejection_reason
        )

        current_app.logger.info(f'社区申请拒绝成功: {application_id}')
        return make_succ_response({'message': '拒绝成功'})

    except Exception as e:
        current_app.logger.error(f'拒绝社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))