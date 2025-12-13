"""
社区管理视图模块
包含社区CRUD、用户管理、申请处理等功能
"""

import logging
from flask import request
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.utils.auth import verify_token
from database import get_database
from database.models import User, Community, CommunityApplication, UserAuditLog, CommunityStaff
from wxcloudrun.community_service import CommunityService

app_logger = logging.getLogger('log')

# 获取数据库实例
db = get_database()


def _check_community_admin_permission(user, community_id):
    """检查社区管理员权限"""
    if not user.can_manage_community(community_id):
        return make_err_response({}, "权限不足")
    return None


def _check_super_admin_permission(user):
    """检查超级管理员权限"""
    if user.role != 4:
        return make_err_response({}, "需要超级管理员权限")
    return None


def _format_community_data(community):
    """格式化社区数据"""
    return {
        'community_id': community.community_id,
        'name': community.name,
        'description': community.description,
        'status': community.status,
        'status_name': community.status_name,
        'location': community.location,
        'is_default': community.is_default,
        'created_at': community.created_at.isoformat() if community.created_at else None,
        'updated_at': community.updated_at.isoformat() if community.updated_at else None,
        'creator': {
            'user_id': community.creator_user_id,
            'nickname': community.creator.nickname if community.creator else None
        } if community.creator else None,
        'admin_count': CommunityStaff.query.filter_by(community_id=community.community_id).count(),
        'user_count': len(community.users) if community.users else 0
    }


@app.route('/api/community/list', methods=['GET'])
def get_community_list():
    """获取社区列表 (新版API,支持分页和筛选)"""
    from database.models import CommunityStaff

    app_logger.info('=== 开始获取社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    # 检查权限: 仅super_admin
    if user.role != 4:
        return make_err_response({}, '权限不足，需要超级管理员权限')

    try:
        # 获取请求参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        status_filter = request.args.get('status', 'all')  # all/active/inactive

        # 构建查询
        query = Community.query

        # 状态筛选
        if status_filter == 'active':
            query = query.filter_by(status=1)
        elif status_filter == 'inactive':
            query = query.filter_by(status=2)

        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        communities = query.order_by(Community.created_at.desc()).offset(offset).limit(page_size).all()

        # 格式化响应数据
        result = []
        for community in communities:
            # 获取主管信息
            manager = CommunityStaff.query.filter_by(
                community_id=community.community_id,
                role='manager'
            ).first()

            manager_name = None
            manager_id = None
            if manager:
                manager_user = User.query.get(manager.user_id)
                if manager_user:
                    manager_name = manager_user.nickname
                    manager_id = str(manager.user_id)

            community_data = {
                'id': str(community.community_id),
                'name': community.name,
                'location': community.location or '',
                'location_lat': None,  # TODO: 添加到数据库字段
                'location_lon': None,  # TODO: 添加到数据库字段
                'status': 'active' if community.status == 1 else 'inactive',
                'manager_id': manager_id,
                'manager_name': manager_name,
                'description': community.description or '',
                'created_at': community.created_at.isoformat() if community.created_at else None,
                'updated_at': community.updated_at.isoformat() if community.updated_at else None
            }
            result.append(community_data)

        has_more = (page * page_size) < total

        app_logger.info(f'成功获取社区列表，共 {len(result)} 个社区')
        return make_succ_response({
            'communities': result,
            'total': total,
            'has_more': has_more,
            'current_page': page
        })

    except Exception as e:
        app_logger.error(f'获取社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区列表失败: {str(e)}')


@app.route('/api/communities', methods=['GET'])
def get_communities():
    """获取社区列表（超级管理员专用）"""
    app.logger.info('=== 开始获取社区列表 ===')

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
        communities = Community.query.all()
        result = [_format_community_data(c) for c in communities]

        app.logger.info(f'成功获取社区列表，共 {len(result)} 个社区')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区列表失败: {str(e)}')


@app.route('/api/communities', methods=['POST'])
def create_community():
    """创建新社区（超级管理员专用）"""
    app.logger.info('=== 开始创建新社区 ===')

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
        params = request.get_json() or {}
        name = params.get('name')
        description = params.get('description', '')
        location = params.get('location', '')

        # 验证必填参数
        if not name:
            return make_err_response({}, '社区名称不能为空')

        # 使用CommunityService创建社区
        community = CommunityService.create_community(
            name=name,
            description=description,
            creator_id=user_id,
            location=location
        )

        result = _format_community_data(community)
        app_logger.info(f'成功创建社区: {name}, ID: {community.community_id}')
        return make_succ_response(result)

    except ValueError as e:
        # 业务逻辑错误（如社区名称已存在）
        app_logger.warning(f'创建社区失败: {str(e)}')
        return make_err_response({}, str(e))
    except Exception as e:
        app_logger.error(f'创建社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建社区失败: {str(e)}')


@app.route('/api/communities/<int:community_id>', methods=['GET'])
def get_community(community_id):
    """获取社区详情"""
    app.logger.info(f'=== 开始获取社区详情: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    try:
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查权限（超级管理员或该社区管理员）
        if user.role != 4 and not user.is_community_admin(community_id):
            return make_err_response({}, '权限不足')

        result = _format_community_data(community)

        # 添加管理员列表
        admins = []
        staff_members = CommunityStaff.query.filter_by(community_id=community.community_id).all()
        for staff in staff_members:
            admins.append({
                'user_id': staff.user_id,
                'nickname': staff.user.nickname,
                'avatar_url': staff.user.avatar_url,
                'role': staff.role,
                'role_name': staff.role,
                'added_at': staff.added_at.isoformat() if staff.added_at else None
            })
        result['admins'] = admins

        app.logger.info(f'成功获取社区详情: {community_id}')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取社区详情失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区详情失败: {str(e)}')


@app.route('/api/communities/<int:community_id>', methods=['PUT'])
def update_community(community_id):
    """更新社区信息"""
    app.logger.info(f'=== 开始更新社区信息: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    try:
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查权限（超级管理员或该社区管理员）
        if user.role != 4 and not user.is_community_admin(community_id):
            return make_err_response({}, '权限不足')

        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        # 更新字段
        if 'name' in params:
            new_name = params['name']
            if not new_name:
                return make_err_response({}, '社区名称不能为空')

            # 检查名称是否与其他社区重复
            existing = Community.query.filter(
                Community.name == new_name,
                Community.community_id != community_id
            ).first()
            if existing:
                return make_err_response({}, '社区名称已存在')

            community.name = new_name

        if 'description' in params:
            community.description = params['description']

        if 'location' in params:
            community.location = params['location']

        if 'status' in params:
            community.status = params['status']

        # 更新时间
        from datetime import datetime
        community.updated_at = datetime.now()

        db.session.commit()

        result = _format_community_data(community)
        app.logger.info(f'成功更新社区信息: {community_id}')
        return make_succ_response(result)

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'更新社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'更新社区信息失败: {str(e)}')











@app.route('/api/communities/<int:community_id>/users', methods=['GET'])
def get_community_users(community_id):
    """获取社区用户列表（非管理员）"""
    app.logger.info(f'=== 开始获取社区用户列表: {community_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限
    error = _check_community_admin_permission(user, community_id)
    if error:
        return error

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')

        pagination = CommunityService.search_community_users(
            community_id=community_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        users = []
        for u in pagination.items:
            users.append({
                'user_id': u.user_id,
                'nickname': u.nickname,
                'avatar_url': u.avatar_url,
                'phone_number': u.phone_number,
                'role': u.role,
                'role_name': u.role_name,
                'verification_status': u.verification_status,
                'created_at': u.created_at.isoformat() if u.created_at else None
            })

        result = {
            'users': users,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }

        app.logger.info(f'成功获取社区用户列表: {community_id}, 共 {len(users)} 个用户')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区用户列表失败: {str(e)}')





@app.route('/api/communities/<int:community_id>/users/<int:target_user_id>', methods=['DELETE'])
def remove_user_from_community(community_id, target_user_id):
    """从社区中移除用户（超级管理员专用）"""
    app.logger.info(f'=== 开始从社区中移除用户: {community_id}, 用户: {target_user_id} ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    # 检查权限（仅超级管理员可以移除用户）
    error = _check_super_admin_permission(user)
    if error:
        return error

    try:
        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查目标用户是否存在
        target_user = User.query.get(target_user_id)
        if not target_user:
            return make_err_response({}, '用户不存在')

        # 检查用户是否在该社区中
        if target_user.community_id != community_id:
            return make_err_response({}, '用户不在该社区中')

        # 不能从默认社区移除用户
        if community.is_default:
            return make_err_response({}, '不能从默认社区移除用户')

        # 获取默认社区
        from database.initialization import get_default_community
        default_community_info = get_default_community()
        if not default_community_info:
            return make_err_response({}, '默认社区不存在，请确保数据库已正确初始化')
        
        # 获取默认社区对象
        default_community = Community.query.get(default_community_info['community_id'])
        if not default_community:
            return make_err_response({}, '默认社区不存在，请确保数据库已正确初始化')

        # 将用户移到默认社区
        target_user.community_id = default_community.community_id

        # 如果用户是原社区的管理员，移除管理员权限
        from database.models import CommunityStaff
        staff_role = CommunityStaff.query.filter_by(
            community_id=community_id,
            user_id=target_user_id
        ).first()
        if staff_role:
            db.session.delete(staff_role)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=user_id,
            action="remove_user_from_community",
            detail=f"从社区{community_id}移除用户{target_user_id}，移至默认社区{default_community.community_id}"
        )
        db.session.add(audit_log)

        db.session.commit()

        app.logger.info(f'从社区移除用户成功: {community_id}, 用户: {target_user_id}, 已移至默认社区')
        return make_succ_response({'message': '移除成功'})

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'从社区移除用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'从社区移除用户失败: {str(e)}')


@app.route('/api/community/applications', methods=['GET'])
def get_community_applications():
    """获取社区申请列表（管理员专用）"""
    app.logger.info('=== 开始获取社区申请列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    try:
        applications = user.get_pending_applications()

        result = []
        for application in applications:
            result.append({
                'application_id': application.application_id,
                'user': {
                    'user_id': application.user.user_id,
                    'nickname': application.user.nickname,
                    'avatar_url': application.user.avatar_url,
                    'phone_number': application.user.phone_number,
                    'role': application.user.role,
                    'role_name': application.user.role_name
                },
                'community': {
                    'community_id': application.target_community.community_id,
                    'name': application.target_community.name,
                    'description': application.target_community.description
                },
                'reason': application.reason,
                'status': application.status,
                'status_name': application.status_name,
                'created_at': application.created_at.isoformat() if application.created_at else None
            })

        app.logger.info(f'成功获取社区申请列表，共 {len(result)} 个申请')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取社区申请列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区申请列表失败: {str(e)}')


@app.route('/api/community/applications', methods=['POST'])
def create_community_application():
    """提交社区申请"""
    app.logger.info('=== 开始提交社区申请 ===')

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

        community_id = params.get('community_id')
        reason = params.get('reason', '')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 检查是否已经在该社区
        if user.community_id == community_id:
            return make_err_response({}, '您已经是该社区的成员')

        # 提交申请
        success, message = user.apply_to_community(community_id, reason)
        if not success:
            return make_err_response({}, message)

        app.logger.info(f'社区申请提交成功: 用户ID={user_id}, 社区ID={community_id}')
        return make_succ_response({'message': '申请已提交'})

    except Exception as e:
        app_logger.error(f'提交社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'提交社区申请失败: {str(e)}')


@app.route('/api/community/applications/<int:application_id>/approve', methods=['PUT'])
def approve_application(application_id):
    """批准社区申请"""
    app.logger.info(f'=== 开始批准社区申请: {application_id} ===')

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

        app.logger.info(f'社区申请批准成功: {application_id}')
        return make_succ_response({'message': '批准成功'})

    except Exception as e:
        app_logger.error(f'批准社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


@app.route('/api/community/applications/<int:application_id>/reject', methods=['PUT'])
def reject_application(application_id):
    """拒绝社区申请"""
    app.logger.info(f'=== 开始拒绝社区申请: {application_id} ===')

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

        rejection_reason = params.get('rejection_reason')
        if not rejection_reason:
            return make_err_response({}, '缺少拒绝理由')

        CommunityService.process_application(
            application_id=application_id,
            approve=False,
            processor_id=user_id,
            rejection_reason=rejection_reason
        )

        app.logger.info(f'社区申请拒绝成功: {application_id}')
        return make_succ_response({'message': '拒绝成功'})

    except Exception as e:
        app_logger.error(f'拒绝社区申请失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


@app.route('/api/user/community', methods=['GET'])
def get_user_community():
    """获取当前用户的社区信息"""
    app.logger.info('=== 开始获取用户社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    try:
        if not user.community_id:
            return make_succ_response({'community': None})

        community = Community.query.get(user.community_id)
        if not community:
            return make_err_response({}, '用户所属社区不存在')

        result = {
            'community': {
                'community_id': community.community_id,
                'name': community.name,
                'description': community.description,
                'is_default': community.is_default
            },
            'is_admin': user.is_community_admin(),
            'is_primary_admin': user.is_primary_admin()
        }

        app.logger.info(f'成功获取用户社区信息: 用户ID={user_id}, 社区ID={community.community_id}')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取用户社区信息失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取用户社区信息失败: {str(e)}')


@app.route('/api/user/managed-communities', methods=['GET'])
def get_managed_communities():
    """获取当前用户管理的社区列表"""
    from database.models import CommunityStaff

    app.logger.info('=== 开始获取用户管理的社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    app.logger.info(f'用户信息: ID={user_id}, role={user.role}')

    try:
        # 检查用户是否为超级管理员或社区工作人员
        # 使用新的统一角色权限模型：不再基于user.role字段，而是检查CommunityStaff表
        is_super_admin = user.role == 4
        is_community_admin_result = user.is_community_admin()

        app.logger.info(f'权限检查: is_super_admin={is_super_admin}, is_community_admin={is_community_admin_result}')

        if not is_super_admin and not is_community_admin_result:
            app.logger.info('权限检查失败，返回权限不足错误')
            return make_err_response({}, '权限不足，仅社区工作人员可访问')

        communities_data = []

        # 超级管理员（role=4）可以看到所有社区
        if user.role == 4:
            communities = Community.query.filter_by(status=1).all()
            for community in communities:
                # 获取社区工作人员数量
                staff_count = CommunityStaff.query.filter_by(community_id=community.community_id).count()
                # 获取社区用户数量
                user_count = User.query.filter_by(community_id=community.community_id).count()

                communities_data.append({
                    'community_id': community.community_id,
                    'name': community.name,
                    'description': community.description,
                    'location': community.location,
                    'is_default': community.is_default,
                    'staff_count': staff_count,
                    'user_count': user_count,
                    'user_role': 'super_admin',  # 超级管理员标识
                    'created_at': community.created_at.isoformat() if community.created_at else None
                })
        else:
            # 其他工作人员只能看到自己管理的社区
            staff_roles = CommunityStaff.query.filter_by(user_id=user_id).all()
            for staff_role in staff_roles:
                community = staff_role.community
                if community and community.status == 1:  # 只显示启用的社区
                    # 获取社区工作人员数量
                    staff_count = CommunityStaff.query.filter_by(community_id=community.community_id).count()
                    # 获取社区用户数量
                    user_count = User.query.filter_by(community_id=community.community_id).count()

                    communities_data.append({
                        'community_id': community.community_id,
                        'name': community.name,
                        'description': community.description,
                        'location': community.location,
                        'is_default': community.is_default,
                        'staff_count': staff_count,
                        'user_count': user_count,
                        'user_role': staff_role.role,  # 'manager' 或 'staff'
                        'role_in_community': staff_role.role,
                        'created_at': community.created_at.isoformat() if community.created_at else None
                    })

        # 按创建时间倒序排列
        communities_data.sort(key=lambda x: x['created_at'] or '', reverse=True)

        app.logger.info(f'成功获取用户管理的社区列表: 用户ID={user_id}, 社区数量={len(communities_data)}')
        return make_succ_response({
            'communities': communities_data,
            'total': len(communities_data),
            'user_role': 'super_admin' if user.role == 4 else 'community_staff'
        })

    except Exception as e:
        app_logger.error(f'获取用户管理的社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取用户管理的社区列表失败: {str(e)}')


@app.route('/api/communities/available', methods=['GET'])
def get_available_communities():
    """获取可申请的社区列表"""
    app.logger.info('=== 开始获取可申请的社区列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        communities = CommunityService.get_available_communities()

        result = []
        for community in communities:
            result.append({
                'community_id': community.community_id,
                'name': community.name,
                'description': community.description,
                'location': community.location,
                'user_count': len(community.users) if community.users else 0
            })

        app.logger.info(f'成功获取可申请社区列表，共 {len(result)} 个社区')
        return make_succ_response(result)

    except Exception as e:
        app_logger.error(f'获取可申请社区列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取可申请社区列表失败: {str(e)}')





# ============================================
# 工作人员管理相关API
# ============================================

@app.route('/api/community/staff/list', methods=['GET'])
def get_community_staff_list():
    """获取社区工作人员列表"""
    from database.models import CommunityStaff

    app_logger.info('=== 开始获取社区工作人员列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        community_id = request.args.get('community_id')
        role_filter = request.args.get('role', 'all')  # all/manager/staff
        sort_by = request.args.get('sort_by', 'time')  # name/role/time

        if not community_id:
            return make_err_response({}, '缺少社区ID参数')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin 或 community_manager
        if user.role != 4:  # 不是super_admin
            # 检查是否是该社区的manager
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id,
                role='manager'
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        # 构建查询
        query = CommunityStaff.query.filter_by(community_id=community_id)

        # 角色筛选
        if role_filter != 'all':
            query = query.filter_by(role=role_filter)

        # 排序
        if sort_by == 'name':
            query = query.join(User).order_by(User.nickname)
        elif sort_by == 'role':
            query = query.order_by(CommunityStaff.role.desc())  # manager在前
        else:  # time
            query = query.order_by(CommunityStaff.added_at.desc())

        staff_list = query.all()

        # 格式化响应数据
        staff_members = []
        for staff in staff_list:
            staff_user = User.query.get(staff.user_id)
            if not staff_user:
                continue

            # 获取该用户所属的所有社区
            user_communities = []
            user_staff_records = CommunityStaff.query.filter_by(user_id=staff.user_id).all()
            for record in user_staff_records:
                comm = Community.query.get(record.community_id)
                if comm:
                    user_communities.append({
                        'id': str(comm.community_id),
                        'name': comm.name,
                        'location': comm.location or ''
                    })

            member_data = {
                'user_id': str(staff_user.user_id),
                'nickname': staff_user.nickname,
                'avatar_url': staff_user.avatar_url,
                'phone_number': staff_user.phone_number,
                'role': staff.role,
                'communities': user_communities,
                'added_time': staff.added_at.isoformat() if staff.added_at else None
            }

            # 仅staff角色有scope字段
            if staff.role == 'staff' and staff.scope:
                member_data['scope'] = staff.scope

            staff_members.append(member_data)

        app_logger.info(f'成功获取社区工作人员列表，共 {len(staff_members)} 人')
        return make_succ_response({'staff_members': staff_members})

    except Exception as e:
        app_logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取工作人员列表失败: {str(e)}')


@app.route('/api/community/add-staff', methods=['POST'])
def add_community_staff():
    """添加社区工作人员"""
    from database.models import CommunityStaff

    app_logger.info('=== 开始添加社区工作人员 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        data = request.get_json()
        community_id = data.get('community_id')
        user_ids = data.get('user_ids', [])
        role = data.get('role', 'staff')  # manager 或 staff

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        if not user_ids or not isinstance(user_ids, list):
            return make_err_response({}, '用户ID列表不能为空')

        if role not in ['manager', 'staff']:
            return make_err_response({}, '角色参数错误，必须是manager或staff')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin 或 community_manager
        if user.role != 4:  # 不是super_admin
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id,
                role='manager'
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        # 如果是添加主管,只能添加一个
        if role == 'manager' and len(user_ids) > 1:
            return make_err_response({}, '主管只能添加一个')

        # 检查是否已有主管
        if role == 'manager':
            existing_manager = CommunityStaff.query.filter_by(
                community_id=community_id,
                role='manager'
            ).first()
            if existing_manager:
                return make_err_response({}, '该社区已有主管')

        added_count = 0
        failed = []

        for uid in user_ids:
            try:
                # 检查用户是否存在
                target_user = User.query.get(uid)
                if not target_user:
                    failed.append({'user_id': uid, 'reason': '用户不存在'})
                    continue

                # 检查用户是否已在当前社区任职（避免在同一社区重复任职）
                existing_in_current_community = CommunityStaff.query.filter_by(
                    community_id=community_id,
                    user_id=uid
                ).first()

                if existing_in_current_community:
                    failed.append({'user_id': uid, 'reason': '用户已在当前社区任职'})
                    continue

                # 添加工作人员
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=uid,
                    role=role
                )
                db.session.add(staff)
                added_count += 1

            except Exception as e:
                app_logger.error(f'添加工作人员失败 user_id={uid}: {str(e)}')
                failed.append({'user_id': uid, 'reason': str(e)})

        db.session.commit()

        app_logger.info(f'添加工作人员完成: 成功{added_count}人, 失败{len(failed)}人')

        if added_count == 0:
            return make_err_response({'failed': failed}, '添加失败')

        return make_succ_response({
            'added_count': added_count,
            'failed': failed
        })

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'添加社区工作人员失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'添加工作人员失败: {str(e)}')


@app.route('/api/community/remove-staff', methods=['POST'])
def remove_community_staff():
    """移除社区工作人员"""
    from database.models import CommunityStaff

    app_logger.info('=== 开始移除社区工作人员 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        data = request.get_json()
        community_id = data.get('community_id')
        target_user_id = data.get('user_id')

        if not community_id or not target_user_id:
            return make_err_response({}, '缺少必要参数')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin 或 community_manager
        if user.role != 4:  # 不是super_admin
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id,
                role='manager'
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        # 查找工作人员记录
        staff = CommunityStaff.query.filter_by(
            community_id=community_id,
            user_id=target_user_id
        ).first()

        if not staff:
            return make_err_response({}, '工作人员不存在')

        # 删除记录
        db.session.delete(staff)
        db.session.commit()

        app_logger.info(f'移除工作人员成功: 社区{community_id}, 用户{target_user_id}')
        return make_succ_response({})

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'移除社区工作人员失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'移除工作人员失败: {str(e)}')


# ============================================
# 社区用户管理相关API
# ============================================

@app.route('/api/community/users', methods=['GET'])
def get_community_users_list():
    """获取社区用户列表 (新版API)"""
    from database.models import CommunityMember, CommunityStaff
    from database.models import CheckinRecord
    from datetime import date

    app_logger.info('=== 开始获取社区用户列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        # 获取请求参数
        community_id = request.args.get('community_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        if not community_id:
            return make_err_response({}, '缺少社区ID参数')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin, community_manager 或 community_staff
        if user.role != 4:  # 不是super_admin
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        # 分页查询社区成员
        offset = (page - 1) * page_size
        query = CommunityMember.query.filter_by(community_id=community_id)
        total = query.count()
        members = query.order_by(CommunityMember.joined_at.desc()).offset(offset).limit(page_size).all()

        # 格式化响应数据
        users = []
        today = date.today()

        for member in members:
            member_user = User.query.get(member.user_id)
            if not member_user:
                continue

            # 获取今日未完成打卡数和详情
            from sqlalchemy import and_, func
            unchecked_records = CheckinRecord.query.filter(
                and_(
                    CheckinRecord.solo_user_id == member.user_id,
                    func.date(CheckinRecord.planned_time) == today,
                    CheckinRecord.status == 0  # 0-missed(未打卡)
                )
            ).all()

            unchecked_items = []
            for record in unchecked_records:
                if record.rule:
                    unchecked_items.append({
                        'rule_id': str(record.rule_id),
                        'rule_name': record.rule.rule_name,
                        'planned_time': record.rule.planned_time.strftime('%H:%M:%S') if record.rule.planned_time else None
                    })

            user_data = {
                'user_id': str(member_user.user_id),
                'nickname': member_user.nickname,
                'avatar_url': member_user.avatar_url,
                'phone_number': member_user.phone_number,
                'join_time': member.joined_at.isoformat() if member.joined_at else None,
                'unchecked_count': len(unchecked_items),
                'unchecked_items': unchecked_items
            }

            users.append(user_data)

        has_more = (page * page_size) < total

        app_logger.info(f'成功获取社区用户列表，共 {len(users)} 人')
        return make_succ_response({
            'users': users,
            'total': total,
            'has_more': has_more,
            'current_page': page
        })

    except Exception as e:
        app_logger.error(f'获取社区用户列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取用户列表失败: {str(e)}')


@app.route('/api/community/add-users', methods=['POST'])
def add_community_users():
    """添加社区用户"""
    from database.models import CommunityMember, CommunityStaff

    app_logger.info('=== 开始添加社区用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        data = request.get_json()
        community_id = data.get('community_id')
        user_ids = data.get('user_ids', [])

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        if not user_ids or not isinstance(user_ids, list):
            return make_err_response({}, '用户ID列表不能为空')

        if len(user_ids) > 50:
            return make_err_response({}, '最多只能添加50个用户')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin, community_manager 或 community_staff
        if user.role != 4:  # 不是super_admin
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        added_count = 0
        failed = []

        for uid in user_ids:
            try:
                # 检查用户是否存在
                target_user = User.query.get(uid)
                if not target_user:
                    failed.append({'user_id': uid, 'reason': '用户不存在'})
                    continue

                # 检查是否已在社区
                existing = CommunityMember.query.filter_by(
                    community_id=community_id,
                    user_id=uid
                ).first()

                if existing:
                    failed.append({'user_id': uid, 'reason': '用户已在社区'})
                    continue

                # 添加用户到社区
                member = CommunityMember(
                    community_id=community_id,
                    user_id=uid
                )
                db.session.add(member)
                added_count += 1

            except Exception as e:
                app_logger.error(f'添加用户失败 user_id={uid}: {str(e)}')
                failed.append({'user_id': uid, 'reason': str(e)})

        db.session.commit()

        app_logger.info(f'添加社区用户完成: 成功{added_count}人, 失败{len(failed)}人')

        if added_count == 0:
            return make_err_response({'added_count': added_count, 'failed': failed}, '添加失败')

        return make_succ_response({
            'added_count': added_count,
            'failed': failed
        })

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'添加社区用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'添加用户失败: {str(e)}')


@app.route('/api/community/remove-user', methods=['POST'])
def remove_community_user():
    """移除社区用户"""
    from database.models import CommunityMember, CommunityStaff

    app_logger.info('=== 开始移除社区用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        data = request.get_json()
        community_id = data.get('community_id')
        target_user_id = data.get('user_id')

        if not community_id or not target_user_id:
            return make_err_response({}, '缺少必要参数')

        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 权限检查: super_admin, community_manager 或 community_staff
        if user.role != 4:  # 不是super_admin
            staff_record = CommunityStaff.query.filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()
            if not staff_record:
                return make_err_response({}, '权限不足')

        # 查找成员记录
        member = CommunityMember.query.filter_by(
            community_id=community_id,
            user_id=target_user_id
        ).first()

        if not member:
            return make_err_response({}, '用户不在该社区')

        # 特殊社区逻辑处理
        moved_to = None

        # 获取特殊社区ID
        anka_family = Community.query.filter_by(name='安卡大家庭').first()
        blackhouse = Community.query.filter_by(name='黑屋').first()

        # 如果从"安卡大家庭"移除,移入"黑屋"
        if community.name == '安卡大家庭' and blackhouse:
            # 检查是否已在黑屋
            existing_in_blackhouse = CommunityMember.query.filter_by(
                community_id=blackhouse.community_id,
                user_id=target_user_id
            ).first()

            if not existing_in_blackhouse:
                blackhouse_member = CommunityMember(
                    community_id=blackhouse.community_id,
                    user_id=target_user_id
                )
                db.session.add(blackhouse_member)
                moved_to = '黑屋'

        # 如果从普通社区移除
        elif community.name not in ['安卡大家庭', '黑屋']:
            # 检查用户是否还属于其他普通社区
            other_memberships = CommunityMember.query.filter(
                CommunityMember.user_id == target_user_id,
                CommunityMember.community_id != community_id
            ).join(Community).filter(
                Community.name.notin_(['安卡大家庭', '黑屋'])
            ).count()

            # 如果不属于任何其他普通社区,移入"安卡大家庭"
            if other_memberships == 0 and anka_family:
                # 检查是否已在安卡大家庭
                existing_in_anka = CommunityMember.query.filter_by(
                    community_id=anka_family.community_id,
                    user_id=target_user_id
                ).first()

                if not existing_in_anka:
                    anka_member = CommunityMember(
                        community_id=anka_family.community_id,
                        user_id=target_user_id
                    )
                    db.session.add(anka_member)
                    moved_to = '安卡大家庭'

        # 删除成员记录
        db.session.delete(member)
        db.session.commit()

        app_logger.info(f'移除社区用户成功: 社区{community_id}, 用户{target_user_id}, 移至{moved_to}')
        return make_succ_response({'moved_to': moved_to})

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'移除社区用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'移除用户失败: {str(e)}')


# ============================================
# 社区CRUD相关API (中优先级)
# ============================================

@app.route('/api/community/create', methods=['POST'])
def create_community_new():
    """创建社区 (新版API)"""
    app_logger.info('=== 开始创建社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    # 检查权限: 仅super_admin
    if user.role != 4:
        return make_err_response({}, '权限不足，需要超级管理员权限')

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        location = data.get('location', '').strip()
        location_lat = data.get('location_lat')
        location_lon = data.get('location_lon')
        manager_id = data.get('manager_id')
        description = data.get('description', '').strip()

        # 参数验证
        if not name:
            return make_err_response({}, '社区名称不能为空')

        if len(name) < 2 or len(name) > 50:
            return make_err_response({}, '社区名称长度必须在2-50个字符之间')

        if not location:
            return make_err_response({}, '社区位置不能为空')

        if description and len(description) > 200:
            return make_err_response({}, '社区描述不能超过200个字符')

        # 检查社区名称是否已存在
        existing = Community.query.filter_by(name=name).first()
        if existing:
            return make_err_response({}, '社区名称已存在')

        # 如果指定了主管,检查用户是否存在
        if manager_id:
            manager = User.query.get(manager_id)
            if not manager:
                return make_err_response({}, '指定的主管不存在')

        # 创建社区
        community = Community(
            name=name,
            description=description,
            creator_user_id=user_id,
            location=location,
            status=1,  # 默认启用
            is_default=False
        )

        db.session.add(community)
        db.session.flush()  # 获取community_id

        # 如果指定了主管,添加到工作人员表
        if manager_id:
            from database.models import CommunityStaff
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=manager_id,
                role='manager'
            )
            db.session.add(staff)

        db.session.commit()

        app_logger.info(f'创建社区成功: {name} (ID: {community.community_id})')
        return make_succ_response({
            'community_id': str(community.community_id),
            'name': community.name,
            'location': community.location,
            'status': 'active',
            'created_at': community.created_at.isoformat() if community.created_at else None
        })

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'创建社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'创建社区失败: {str(e)}')


@app.route('/api/community/update', methods=['POST'])
def update_community_new():
    """更新社区信息 (新版API)"""
    app_logger.info('=== 开始更新社区信息 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    # 检查权限: 仅super_admin
    if user.role != 4:
        return make_err_response({}, '权限不足，需要超级管理员权限')

    try:
        data = request.get_json()
        community_id = data.get('community_id')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 查找社区
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 更新字段
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return make_err_response({}, '社区名称不能为空')
            if len(name) < 2 or len(name) > 50:
                return make_err_response({}, '社区名称长度必须在2-50个字符之间')

            # 检查名称是否与其他社区重复
            existing = Community.query.filter(
                Community.name == name,
                Community.community_id != community_id
            ).first()
            if existing:
                return make_err_response({}, '社区名称已存在')

            community.name = name

        if 'location' in data:
            community.location = data['location'].strip()

        if 'location_lat' in data:
            community.location_lat = data['location_lat']

        if 'location_lon' in data:
            community.location_lon = data['location_lon']

        if 'description' in data:
            desc = data['description'].strip()
            if desc and len(desc) > 200:
                return make_err_response({}, '社区描述不能超过200个字符')
            community.description = desc

        # 如果更新了主管
        if 'manager_id' in data:
            from database.models import CommunityStaff
            new_manager_id = data['manager_id']

            if new_manager_id:
                # 检查新主管是否存在
                new_manager = User.query.get(new_manager_id)
                if not new_manager:
                    return make_err_response({}, '指定的主管不存在')

                # 移除旧主管
                old_manager = CommunityStaff.query.filter_by(
                    community_id=community_id,
                    role='manager'
                ).first()
                if old_manager:
                    db.session.delete(old_manager)

                # 添加新主管
                new_staff = CommunityStaff(
                    community_id=community_id,
                    user_id=new_manager_id,
                    role='manager'
                )
                db.session.add(new_staff)

        db.session.commit()

        app_logger.info(f'更新社区成功: {community.name} (ID: {community_id})')
        return make_succ_response({
            'community_id': str(community_id),
            'updated_at': community.updated_at.isoformat() if community.updated_at else None
        })

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'更新社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'更新社区失败: {str(e)}')


@app.route('/api/community/toggle-status', methods=['POST'])
def toggle_community_status_new():
    """切换社区状态 (新版API)"""
    app_logger.info('=== 开始切换社区状态 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    # 检查权限: 仅super_admin
    if user.role != 4:
        return make_err_response({}, '权限不足，需要超级管理员权限')

    try:
        data = request.get_json()
        community_id = data.get('community_id')
        status = data.get('status', '').strip()

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        if status not in ['active', 'inactive']:
            return make_err_response({}, '状态参数错误，必须是active或inactive')

        # 查找社区
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 特殊社区不能停用
        if community.name in ['安卡大家庭', '黑屋']:
            return make_err_response({}, '特殊社区不能停用')

        # 更新状态
        community.status = 1 if status == 'active' else 2
        db.session.commit()

        app_logger.info(f'切换社区状态成功: {community.name} -> {status}')
        return make_succ_response({
            'community_id': str(community_id),
            'status': status
        })

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'切换社区状态失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'切换状态失败: {str(e)}')


@app.route('/api/community/delete', methods=['POST'])
def delete_community_new():
    """删除社区 (新版API)"""
    from database.models import CommunityMember, CommunityStaff

    app_logger.info('=== 开始删除社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    # 检查权限: 仅super_admin
    if user.role != 4:
        return make_err_response({}, '权限不足，需要超级管理员权限')

    try:
        data = request.get_json()
        community_id = data.get('community_id')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 查找社区
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')

        # 特殊社区不能删除
        if community.name in ['安卡大家庭', '黑屋']:
            return make_err_response({}, '特殊社区不能删除')

        # 检查社区状态
        if community.status == 1:
            return make_err_response({}, '请先停用社区')

        # 检查社区内是否还有用户
        member_count = CommunityMember.query.filter_by(community_id=community_id).count()
        if member_count > 0:
            return make_err_response({
                'user_count': member_count
            }, '社区内还有用户，无法删除')

        # 删除相关数据
        CommunityStaff.query.filter_by(community_id=community_id).delete()
        CommunityApplication.query.filter_by(target_community_id=community_id).delete()

        # 删除社区
        db.session.delete(community)
        db.session.commit()

        app_logger.info(f'删除社区成功: {community.name} (ID: {community_id})')
        return make_succ_response({})

    except Exception as e:
        db.session.rollback()
        app_logger.error(f'删除社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'删除社区失败: {str(e)}')


@app.route('/api/user/search', methods=['GET'])
def search_users_for_community():
    """搜索用户 (社区管理用)"""
    from database.models import CommunityStaff, CommunityMember

    app_logger.info('=== 开始搜索用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return make_err_response({}, '用户不存在')

    try:
        keyword = request.args.get('keyword', '').strip()
        community_id = request.args.get('community_id')

        if not keyword:
            return make_err_response({}, '搜索关键词不能为空')

        # 搜索用户 (按昵称或手机号)
        users_query = User.query.filter(
            (User.nickname.like(f'%{keyword}%')) |
            (User.phone_number.like(f'%{keyword}%'))
        ).limit(20)

        users = users_query.all()

        # 格式化响应
        result = []
        for u in users:
            # 检查是否已是任何社区的工作人员
            is_staff = CommunityStaff.query.filter_by(user_id=u.user_id).first() is not None

            user_data = {
                'user_id': str(u.user_id),
                'nickname': u.nickname,
                'avatar_url': u.avatar_url,
                'phone_number': u.phone_number,
                'is_staff': is_staff
            }

            # 如果指定了community_id,检查是否已在该社区
            if community_id:
                already_in = CommunityMember.query.filter_by(
                    community_id=community_id,
                    user_id=u.user_id
                ).first() is not None
                user_data['already_in_community'] = already_in

            result.append(user_data)

        app_logger.info(f'搜索用户成功: 关键词"{keyword}", 找到{len(result)}个用户')
        return make_succ_response({'users': result})

    except Exception as e:
        app_logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'搜索用户失败: {str(e)}')