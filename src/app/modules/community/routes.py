"""
社区管理模块路由
包含社区CRUD、用户管理、申请处理等功能
"""

import logging
import re
import os
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.decorators import login_required
from app.shared.utils.auth import verify_token, require_community_staff, get_current_user
from database.flask_models import db, User, Community, CommunityApplication, UserAuditLog, CommunityStaff
from wxcloudrun.community_staff_service import CommunityStaffService
from wxcloudrun.community_service import CommunityService
from wxcloudrun.user_service import UserService
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_NAME, DEFAULT_BLACK_ROOM_ID
from wxcloudrun.utils.validators import _audit, _hash_code

app_logger = logging.getLogger('log')


def _calculate_phone_hash(phone):
    """
    计算手机号的hash值
    """
    from hashlib import sha256
    phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
    return sha256(
        f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()


def _check_super_admin_permission(user):
    """检查超级管理员权限"""
    if not user or user.role != 4:  # 4是超级管理员
        current_app.logger.warning(f'用户 {user.user_id if user else None} 无超级管理员权限')
        return make_err_response({}, '无权限访问')
    return None


def _format_community_info(community, include_admin_count=False):
    """
    格式化社区信息
    
    Args:
        community: Community对象
        include_admin_count: 是否包含管理员数量
    
    Returns:
        dict: 格式化后的社区信息
    """
    # 获取创建者信息
    creator = None
    if community.creator_id:
        creator_user = User.query.get(community.creator_id)
        if creator_user:
            creator = {
                'user_id': creator_user.user_id,
                'nickname': creator_user.nickname,
                'avatar_url': creator_user.avatar_url
            }

    # 获取管理员数量
    admin_count = 0
    user_count = 0
    if include_admin_count:
        admin_count = CommunityStaff.query.filter_by(
            community_id=community.community_id,
            role=3  # 社区管理员
        ).count()
        user_count = CommunityStaff.query.filter_by(
            community_id=community.community_id
        ).count()

    return {
        'community_id': community.community_id,
        'name': community.name,
        'description': community.description,
        'creator_id': community.creator_id,
        'creator': creator,
        'status': community.status,
        'created_at': community.created_at.isoformat() if community.created_at else None,
        'updated_at': community.updated_at.isoformat() if community.updated_at else None,
        'admin_count': admin_count,
        'user_count': user_count
    }


@community_bp.route('/communities', methods=['GET'])
def get_communities():
    """获取社区列表（超级管理员专用）- 为了兼容应用初始化测试"""
    current_app.logger.info('=== 开始获取社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限
    error = _check_super_admin_permission(user)
    if error:
        return error

    try:
        # Using Flask-SQLAlchemy db.session
        # 查询所有社区
        communities = db.session.query(Community).all()
        
        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community, include_admin_count=True)
            communities_data.append(community_data)

        current_app.logger.info(f'获取社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区列表失败')


@community_bp.route('/community/list', methods=['GET'])
def get_community_list():
    """获取社区列表（用户可见的社区列表）"""
    current_app.logger.info('=== 开始获取社区列表（用户可见） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取用户可见的社区列表
        communities = CommunityService.get_user_visible_communities(user_id)
        
        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取用户社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取用户社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区列表失败')


@community_bp.route('/communities/<int:community_id>/users', methods=['GET'])
def get_community_users(community_id):
    """获取社区用户列表"""
    current_app.logger.info(f'=== 开始获取社区用户列表: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'请求用户ID: {user_id}')

    try:
        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        role_filter = request.args.get('role')  # 可选的角色过滤

        # 获取社区用户
        result = CommunityService.get_community_users(
            community_id, page, per_page, role_filter
        )

        # 格式化用户信息
        users_data = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users_data.append(user_data)

        response_data = {
            'users': users_data,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users_data) == per_page
        }

        current_app.logger.info(f'获取社区用户列表成功: {community_id}, 共 {len(users_data)} 个用户')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区用户列表失败')


@community_bp.route('/communities/<int:community_id>/users/<int:target_user_id>', methods=['DELETE'])
def remove_community_user(community_id, target_user_id):
    """从社区中移除用户"""
    current_app.logger.info(f'=== 开始移除社区用户: community_id={community_id}, user_id={target_user_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 移除用户
        success = CommunityService.remove_user_from_community(community_id, target_user_id)
        
        if success:
            # 记录审计日志
            _audit(operator_id, 'remove_community_user', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })
            
            current_app.logger.info(f'移除社区用户成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功'})
        else:
            return make_err_response({}, '移除失败')

    except Exception as e:
        current_app.logger.error(f'移除社区用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


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
        community = Community.query.get(community_id)
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
    user = User.query.get(user_id)

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
    user = User.query.get(user_id)

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        reason = params.get('reason', '')

        CommunityService.process_application(
            application_id=application_id,
            approve=False,
            processor_id=user_id,
            reason=reason
        )

        current_app.logger.info(f'社区申请拒绝成功: {application_id}')
        return make_succ_response({'message': '拒绝成功'})

    except Exception as e:
        current_app.logger.error(f'拒绝社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


@community_bp.route('/user/community', methods=['GET'])
def get_user_community():
    """获取用户当前社区信息"""
    current_app.logger.info('=== 开始获取用户当前社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        user = User.query.get(user_id)
        if not user:
            return make_err_response({}, '用户不存在')

        if not user.community_id:
            return make_err_response({}, '用户未加入社区')

        community = Community.query.get(user.community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查用户是否真的属于该社区
        if not CommunityService.verify_user_community_access(user_id, user.community_id):
            return make_err_response({}, '用户不属于该社区')

        community_data = _format_community_info(community)

        current_app.logger.info(f'获取用户社区信息成功: user_id={user_id}, community_id={user.community_id}')
        return make_succ_response(community_data)

    except Exception as e:
        current_app.logger.error(f'获取用户社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区信息失败')


@community_bp.route('/user/managed-communities', methods=['GET'])
def get_managed_communities():
    """获取用户管理的社区列表（默认7个）"""
    from app.shared.utils.auth import get_current_user

    current_app.logger.info('=== 开始获取可管理社区列表 ===')

    # 获取当前用户（装饰器已验证token）
    user = get_current_user()

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        # 获取用户可管理的社区
        communities = CommunityService.get_user_managed_communities(user.user_id)
        
        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可管理社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可管理社区列表失败')


@community_bp.route('/communities/available', methods=['GET'])
def get_available_communities():
    """获取可加入的社区列表"""
    current_app.logger.info('=== 开始获取可加入社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取可加入的社区列表
        communities = CommunityService.get_available_communities(user_id)
        
        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可加入社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可加入社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可加入社区列表失败')


@community_bp.route('/community/staff/list', methods=['GET'])
def get_community_staff_list():
    """获取社区工作人员列表"""
    current_app.logger.info('=== 开始获取社区工作人员列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json() or {}
        community_id = params.get('community_id')
        
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区工作人员
        staff_list = CommunityStaffService.get_community_staff(community_id)
        
        # 格式化工作人员信息
        staff_data = []
        for staff in staff_list:
            user = User.query.get(staff.user_id)
            if user:
                staff_info = {
                    'staff_id': staff.staff_id,
                    'user_id': user.user_id,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'role': staff.role_name,
                    'created_at': staff.created_at.isoformat() if staff.created_at else None
                }
                staff_data.append(staff_info)

        current_app.logger.info(f'获取社区工作人员列表成功: community_id={community_id}, 共 {len(staff_data)} 人')
        return make_succ_response({'staff': staff_data})

    except Exception as e:
        current_app.logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取工作人员列表失败')


@community_bp.route('/community/staff/list-enhanced', methods=['GET'])
def get_community_staff_list_enhanced():
    """获取社区工作人员列表（增强版，包含更多字段）"""
    current_app.logger.info('=== 开始获取社区工作人员列表（增强版） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json() or {}
        community_id = params.get('community_id')
        
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区工作人员
        staff_list = CommunityStaffService.get_community_staff_enhanced(community_id)
        
        # 格式化工作人员信息
        staff_data = []
        for staff in staff_list:
            user = User.query.get(staff.user_id)
            if user:
                staff_info = {
                    'staff_id': staff.staff_id,
                    'user_id': user.user_id,
                    'wechat_openid': user.wechat_openid,
                    'phone_number': user.phone_number,
                    'nickname': user.nickname,
                    'name': user.name,
                    'avatar_url': user.avatar_url,
                    'role': staff.role_name,
                    'created_at': staff.created_at.isoformat() if staff.created_at else None,
                    'last_active_at': user.last_active_at.isoformat() if user.last_active_at else None
                }
                staff_data.append(staff_info)

        current_app.logger.info(f'获取社区工作人员列表成功: community_id={community_id}, 共 {len(staff_data)} 人')
        return make_succ_response({'staff': staff_data})

    except Exception as e:
        current_app.logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取工作人员列表失败')


@community_bp.route('/community/add-staff', methods=['POST'])
def add_community_staff():
    """添加社区工作人员"""
    current_app.logger.info('=== 开始添加社区工作人员 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        target_user_id = params.get('user_id')
        role = params.get('role')  # 2: 社区专员, 3: 社区管理员

        if not all([community_id, target_user_id, role]):
            return make_err_response({}, '缺少必要参数')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 添加工作人员
        success = CommunityStaffService.add_community_staff(
            community_id, target_user_id, role, operator_id
        )

        if success:
            # 记录审计日志
            _audit(operator_id, 'add_community_staff', {
                'community_id': community_id,
                'target_user_id': target_user_id,
                'role': role
            })
            
            current_app.logger.info(f'添加社区工作人员成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '添加成功'})
        else:
            return make_err_response({}, '添加失败')

    except Exception as e:
        current_app.logger.error(f'添加社区工作人员失败: {str(e)}', exc_info=True)
        return make_err_response({}, '添加失败')


@community_bp.route('/community/remove-staff', methods=['POST'])
def remove_community_staff():
    """移除社区工作人员"""
    current_app.logger.info('=== 开始移除社区工作人员 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        target_user_id = params.get('user_id')

        if not all([community_id, target_user_id]):
            return make_err_response({}, '缺少必要参数')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 移除工作人员
        success = CommunityStaffService.remove_community_staff(
            community_id, target_user_id, operator_id
        )

        if success:
            # 记录审计日志
            _audit(operator_id, 'remove_community_staff', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })
            
            current_app.logger.info(f'移除社区工作人员成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功'})
        else:
            return make_err_response({}, '移除失败')

    except Exception as e:
        current_app.logger.error(f'移除社区工作人员失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


@community_bp.route('/community/users', methods=['GET'])
def get_community_users_v2():
    """获取社区用户列表（新版）"""
    current_app.logger.info('=== 开始获取社区用户列表（新版） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json() or {}
        community_id = params.get('community_id')
        
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区用户
        users = CommunityService.get_community_users_v2(community_id)
        
        # 格式化用户信息
        users_data = []
        for user in users:
            user_info = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_active_at': user.last_active_at.isoformat() if user.last_active_at else None
            }
            users_data.append(user_info)

        current_app.logger.info(f'获取社区用户列表成功: community_id={community_id}, 共 {len(users_data)} 个用户')
        return make_succ_response({'users': users_data})

    except Exception as e:
        current_app.logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取用户列表失败')


@community_bp.route('/community/add-users', methods=['POST'])
def add_users_to_community():
    """批量添加用户到社区"""
    current_app.logger.info('=== 开始批量添加用户到社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        user_ids = params.get('user_ids', [])

        if not community_id or not user_ids:
            return make_err_response({}, '缺少社区ID或用户ID列表')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 批量添加用户
        result = CommunityService.add_users_to_community(community_id, user_ids, operator_id)
        
        # 记录审计日志
        _audit(operator_id, 'add_users_to_community', {
            'community_id': community_id,
            'user_ids': user_ids,
            'success_count': result.get('success_count', 0),
            'fail_count': result.get('fail_count', 0)
        })

        current_app.logger.info(f'批量添加用户到社区完成: community_id={community_id}, 成功={result.get("success_count", 0)}, 失败={result.get("fail_count", 0)}')
        return make_succ_response(result)

    except Exception as e:
        current_app.logger.error(f'批量添加用户到社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '批量添加失败')


@community_bp.route('/community/remove-user', methods=['POST'])
def remove_user_from_community():
    """从社区中移除用户"""
    current_app.logger.info('=== 开始从社区中移除用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        target_user_id = params.get('user_id')

        if not all([community_id, target_user_id]):
            return make_err_response({}, '缺少社区ID或目标用户ID')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 移除用户
        success = CommunityService.remove_user_from_community(community_id, target_user_id)
        
        if success:
            # 记录审计日志
            _audit(operator_id, 'remove_user_from_community', {
                'community_id': community_id,
                'target_user_id': target_user_id
            })
            
            current_app.logger.info(f'从社区中移除用户成功: community_id={community_id}, user_id={target_user_id}')
            return make_succ_response({'message': '移除成功'})
        else:
            return make_err_response({}, '移除失败')

    except Exception as e:
        current_app.logger.error(f'从社区中移除用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


@community_bp.route('/community/create', methods=['POST'])
def create_community():
    """创建社区"""
    current_app.logger.info('=== 开始创建社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限
    if not user or user.role < 3:  # 社区管理员及以上
        return make_err_response({}, '无权限创建社区')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        name = params.get('name', '').strip()
        description = params.get('description', '').strip()
        avatar_url = params.get('avatar_url', '')

        if not name:
            return make_err_response({}, '社区名称不能为空')

        # 创建社区
        community = CommunityService.create_community(
            name=name,
            description=description,
            avatar_url=avatar_url,
            creator_id=user_id
        )

        # 记录审计日志
        _audit(user_id, 'create_community', {
            'community_id': community.community_id,
            'name': name
        })

        current_app.logger.info(f'创建社区成功: community_id={community.community_id}, name={name}')
        return make_succ_response({
            'community_id': community.community_id,
            'message': '创建成功'
        })

    except Exception as e:
        current_app.logger.error(f'创建社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '创建失败')


@community_bp.route('/community/update', methods=['POST'])
def update_community():
    """更新社区信息"""
    current_app.logger.info('=== 开始更新社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 更新社区信息
        success = CommunityService.update_community(community_id, params, user_id)
        
        if success:
            # 记录审计日志
            _audit(user_id, 'update_community', {
                'community_id': community_id,
                'updated_fields': list(params.keys())
            })
            
            current_app.logger.info(f'更新社区信息成功: community_id={community_id}')
            return make_succ_response({'message': '更新成功'})
        else:
            return make_err_response({}, '更新失败')

    except Exception as e:
        current_app.logger.error(f'更新社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, '更新失败')


@community_bp.route('/community/toggle-status', methods=['POST'])
def toggle_community_status():
    """切换社区状态"""
    current_app.logger.info('=== 开始切换社区状态 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限
    if not user or user.role < 4:  # 只有超级管理员可以切换状态
        return make_err_response({}, '无权限执行此操作')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 切换状态
        success = CommunityService.toggle_community_status(community_id, user_id)
        
        if success:
            # 记录审计日志
            _audit(user_id, 'toggle_community_status', {
                'community_id': community_id
            })
            
            current_app.logger.info(f'切换社区状态成功: community_id={community_id}')
            return make_succ_response({'message': '切换成功'})
        else:
            return make_err_response({}, '切换失败')

    except Exception as e:
        current_app.logger.error(f'切换社区状态失败: {str(e)}', exc_info=True)
        return make_err_response({}, '切换失败')


@community_bp.route('/community/delete', methods=['POST'])
def delete_community():
    """删除社区"""
    current_app.logger.info('=== 开始删除社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限
    if not user or user.role < 4:  # 只有超级管理员可以删除社区
        return make_err_response({}, '无权限执行此操作')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 删除社区
        success = CommunityService.delete_community(community_id, user_id)
        
        if success:
            # 记录审计日志
            _audit(user_id, 'delete_community', {
                'community_id': community_id
            })
            
            current_app.logger.info(f'删除社区成功: community_id={community_id}')
            return make_succ_response({'message': '删除成功'})
        else:
            return make_err_response({}, '删除失败')

    except Exception as e:
        current_app.logger.error(f'删除社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '删除失败')


@community_bp.route('/user/search', methods=['GET'])
def search_users():
    """搜索用户"""
    current_app.logger.info('=== 开始搜索用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'搜索用户ID: {user_id}')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        search_type = request.args.get('type', 'all')  # all, phone, nickname
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'搜索参数: keyword={keyword}, type={search_type}, page={page}, per_page={per_page}')

        # 执行搜索
        if search_type == 'phone':
            result = CommunityService.search_users_by_phone(keyword, page, per_page)
        elif search_type == 'nickname':
            result = CommunityService.search_users_by_nickname(keyword, page, per_page)
        else:
            # 全局搜索
            result = CommunityService.search_users(keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["total"]} 条记录')

        # 构造返回数据
        users = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users.append(user_data)

        response_data = {
            'users': users,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@community_bp.route('/user/search-all-excluding-blackroom', methods=['GET'])
def search_users_excluding_blackroom():
    """搜索用户（排除黑名单房间）"""
    current_app.logger.info('=== 开始搜索用户（排除黑名单房间） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'搜索用户ID: {user_id}')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'搜索参数: keyword={keyword}, page={page}, per_page={per_page}')

        # 执行搜索（排除黑名单房间）
        result = CommunityService.search_users_excluding_blackroom(keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["total"]} 条记录')

        # 构造返回数据
        users = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users.append(user_data)

        response_data = {
            'users': users,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@community_bp.route('/communities/ankafamily/users/search', methods=['GET'])
def search_ankafamily_users():
    """搜索安卡家族用户"""
    current_app.logger.info('=== 开始搜索安卡家族用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'搜索用户ID: {user_id}')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'搜索参数: keyword={keyword}, page={page}, per_page={per_page}')

        # 执行搜索
        result = CommunityService.search_ankafamily_users(keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["total"]} 条记录')

        # 构造返回数据
        users = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users.append(user_data)

        response_data = {
            'users': users,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'搜索安卡家族用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@community_bp.route('/community/communities/manage/list', methods=['GET'])
def get_manageable_communities():
    """获取可管理的社区列表"""
    current_app.logger.info('=== 开始获取可管理的社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取用户对象
        user = UserService.query_user_by_id(user_id)
        if not user:
            return make_err_response({}, '用户不存在')
        
        # 获取可管理的社区列表
        communities, total = CommunityService.get_manageable_communities(user)
        
        # 格式化社区信息
        communities_data = []
        for community in communities:
            community_data = _format_community_info(community)
            communities_data.append(community_data)

        current_app.logger.info(f'获取可管理社区列表成功，共 {len(communities_data)} 个社区')
        return make_succ_response({'communities': communities_data})

    except Exception as e:
        current_app.logger.error(f'获取可管理社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取可管理社区列表失败')


@community_bp.route('/communities/manage/search', methods=['GET'])
def search_manageable_communities():
    """搜索可管理的社区"""
    current_app.logger.info('=== 开始搜索可管理的社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'搜索参数: keyword={keyword}, page={page}, per_page={per_page}')

        # 执行搜索
        result = CommunityService.search_manageable_communities(user_id, keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["total"]} 条记录')

        # 构造返回数据
        communities = []
        for community in result.get('communities', []):
            community_data = _format_community_info(community)
            communities.append(community_data)

        response_data = {
            'communities': communities,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(communities) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'搜索可管理社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')


@community_bp.route('/communities/manage/<int:community_id>/access-check', methods=['GET'])
def check_community_access(community_id):
    """检查社区访问权限"""
    current_app.logger.info(f'=== 开始检查社区访问权限: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 检查权限
        has_permission = CommunityService.has_community_permission(user_id, community_id)
        
        # 获取用户在社区中的角色
        user_role = None
        if has_permission:
            user_role = CommunityService.get_user_role_in_community(user_id, community_id)

        response_data = {
            'community_id': community_id,
            'has_permission': has_permission,
            'user_role': user_role
        }

        current_app.logger.info(f'社区访问权限检查完成: community_id={community_id}, has_permission={has_permission}, user_role={user_role}')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'检查社区访问权限失败: {str(e)}', exc_info=True)
        return make_err_response({}, '权限检查失败')


@community_bp.route('/communities/<int:community_id>', methods=['GET'])
def get_community_detail(community_id):
    """获取社区详情"""
    current_app.logger.info(f'=== 开始获取社区详情: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # 检查权限
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区详情
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 格式化社区信息
        community_data = _format_community_info(community, include_admin_count=True)

        # 获取社区统计信息
        stats = CommunityService.get_community_stats(community_id)
        community_data.update(stats)

        current_app.logger.info(f'获取社区详情成功: community_id={community_id}')
        return make_succ_response(community_data)

    except Exception as e:
        current_app.logger.error(f'获取社区详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取社区详情失败')


@community_bp.route('/community/create-user', methods=['POST'])
def create_community_user():
    """在社区中创建用户"""
    current_app.logger.info('=== 开始在社区中创建用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        user_data = params.get('user_data', {})

        if not community_id or not user_data:
            return make_err_response({}, '缺少社区ID或用户数据')

        # 检查权限
        if not CommunityService.has_community_permission(operator_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 创建用户
        user = CommunityService.create_user_in_community(community_id, user_data, operator_id)
        
        if user:
            # 记录审计日志
            _audit(operator_id, 'create_community_user', {
                'community_id': community_id,
                'created_user_id': user.user_id
            })
            
            current_app.logger.info(f'在社区中创建用户成功: community_id={community_id}, user_id={user.user_id}')
            return make_succ_response({
                'user_id': user.user_id,
                'message': '创建成功'
            })
        else:
            return make_err_response({}, '创建失败')

    except Exception as e:
        current_app.logger.error(f'在社区中创建用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '创建失败')


@community_bp.route('/user/switch-community', methods=['POST'])
def switch_user_community():
    """切换用户社区"""
    current_app.logger.info('=== 开始切换用户社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 切换社区
        success = CommunityService.switch_user_community(user_id, community_id)
        
        if success:
            # 记录审计日志
            _audit(user_id, 'switch_community', {
                'community_id': community_id
            })
            
            current_app.logger.info(f'切换用户社区成功: user_id={user_id}, community_id={community_id}')
            return make_succ_response({'message': '切换成功'})
        else:
            return make_err_response({}, '切换失败')

    except Exception as e:
        current_app.logger.error(f'切换用户社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, '切换失败')


@community_bp.route('/communities/ankafamily/users/search', methods=['GET'])
def search_ankafamily_users():
    """从安卡大家庭搜索用户（用于添加用户到其他社区）"""
    current_app.logger.info('=== 开始从安卡大家庭搜索用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'搜索用户ID: {user_id}')

    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        current_app.logger.info(f'安卡家庭用户搜索参数: keyword={keyword}, page={page}, per_page={per_page}')

        # 获取安卡大家庭社区ID（假设ID为1）
        from const_default import DEFAULT_COMMUNITY_ID
        ankafamily_community_id = DEFAULT_COMMUNITY_ID

        # 检查用户是否有权限从安卡大家庭搜索用户
        if not CommunityService.has_community_permission(user_id, ankafamily_community_id):
            return make_err_response({}, '无权限从安卡大家庭搜索用户')

        # 执行搜索
        result = CommunityService.get_community_users(
            ankafamily_community_id, page, per_page, None, keyword
        )

        # 格式化用户信息，包含社区信息
        users_data = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'role': user.role_name,
                'status': user.status,
                'community_id': user.community_id,
                'is_staff': user.community_id == ankafamily_community_id and user.role >= 2,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            users_data.append(user_data)

        response_data = {
            'users': users_data,
            'total': result.get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users_data) == per_page
        }

        current_app.logger.info(f'安卡家庭用户搜索成功: 找到 {len(users_data)} 个用户')
        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'安卡家庭用户搜索失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')