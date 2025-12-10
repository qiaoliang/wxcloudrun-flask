"""
社区管理视图模块
包含社区CRUD、用户管理、申请处理等功能
"""

import logging
from flask import request
from wxcloudrun import app, db
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.utils.auth import verify_token
from wxcloudrun.model import User, Community, CommunityAdmin, CommunityApplication, UserAuditLog
from wxcloudrun.community_service import CommunityService

app_logger = logging.getLogger('log')


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
        'admin_count': community.admins.count(),
        'user_count': len(community.users) if community.users else 0
    }


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
        for admin in community.admins:
            admins.append({
                'user_id': admin.user_id,
                'nickname': admin.user.nickname,
                'avatar_url': admin.user.avatar_url,
                'role': admin.role,
                'role_name': admin.role_name,
                'created_at': admin.created_at.isoformat() if admin.created_at else None
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


@app.route('/api/communities/<int:community_id>/admins', methods=['GET'])
def get_community_admins(community_id):
    """获取社区管理员列表"""
    app.logger.info(f'=== 开始获取社区管理员列表: {community_id} ===')
    
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
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')
        
        admins = []
        for admin in community.admins:
            admins.append({
                'user_id': admin.user_id,
                'nickname': admin.user.nickname,
                'avatar_url': admin.user.avatar_url,
                'phone_number': admin.user.phone_number,
                'role': admin.role,
                'role_name': admin.role_name,
                'created_at': admin.created_at.isoformat() if admin.created_at else None
            })
        
        app.logger.info(f'成功获取社区管理员列表: {community_id}, 共 {len(admins)} 个管理员')
        return make_succ_response(admins)
    
    except Exception as e:
        app_logger.error(f'获取社区管理员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'获取社区管理员列表失败: {str(e)}')


@app.route('/api/communities/<int:community_id>/admins', methods=['POST'])
def add_community_admin(community_id):
    """添加社区管理员"""
    app.logger.info(f'=== 开始添加社区管理员: {community_id} ===')
    
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
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')
        
        user_ids = params.get('user_ids', [])
        if not user_ids:
            return make_err_response({}, '缺少用户ID列表')
        
        role = params.get('role', 2)  # 默认普通管理员
        
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')
        
        results = []
        for target_user_id in user_ids:
            try:
                target_user = User.query.get(target_user_id)
                if not target_user:
                    results.append({
                        'user_id': target_user_id,
                        'success': False,
                        'message': '用户不存在'
                    })
                    continue
                
                # 添加管理员
                CommunityService.add_community_admin(
                    community_id=community_id,
                    user_id=target_user_id,
                    role=role,
                    operator_id=user_id
                )
                
                results.append({
                    'user_id': target_user_id,
                    'success': True,
                    'message': '添加成功'
                })
                
            except Exception as e:
                results.append({
                    'user_id': target_user_id,
                    'success': False,
                    'message': str(e)
                })
        
        app.logger.info(f'添加社区管理员完成: {community_id}')
        return make_succ_response(results)
    
    except Exception as e:
        app_logger.error(f'添加社区管理员失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'添加社区管理员失败: {str(e)}')


@app.route('/api/communities/<int:community_id>/admins/<int:target_user_id>', methods=['DELETE'])
def remove_community_admin(community_id, target_user_id):
    """移除社区管理员"""
    app.logger.info(f'=== 开始移除社区管理员: {community_id}, 用户: {target_user_id} ===')
    
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
        CommunityService.remove_community_admin(
            community_id=community_id,
            user_id=target_user_id,
            operator_id=user_id
        )
        
        app.logger.info(f'移除社区管理员成功: {community_id}, 用户: {target_user_id}')
        return make_succ_response({'message': '移除成功'})
    
    except Exception as e:
        app_logger.error(f'移除社区管理员失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


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


@app.route('/api/communities/<int:community_id>/users/<int:target_user_id>/set-admin', methods=['POST'])
def set_user_as_admin(community_id, target_user_id):
    """将用户设为社区管理员"""
    app.logger.info(f'=== 开始设置用户为管理员: {community_id}, 用户: {target_user_id} ===')
    
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
        params = request.get_json() or {}
        role = params.get('role', 2)  # 默认普通管理员
        
        CommunityService.add_community_admin(
            community_id=community_id,
            user_id=target_user_id,
            role=role,
            operator_id=user_id
        )
        
        app.logger.info(f'设置用户为管理员成功: {community_id}, 用户: {target_user_id}')
        return make_succ_response({'message': '设置成功'})
    
    except Exception as e:
        app_logger.error(f'设置用户为管理员失败: {str(e)}', exc_info=True)
        return make_err_response({}, str(e))


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
        
        # 获取或创建默认社区
        default_community = CommunityService.get_or_create_default_community()
        
        # 将用户移到默认社区
        target_user.community_id = default_community.community_id
        
        # 如果用户是原社区的管理员，移除管理员权限
        admin_role = CommunityAdmin.query.filter_by(
            community_id=community_id,
            user_id=target_user_id
        ).first()
        if admin_role:
            db.session.delete(admin_role)
        
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


@app.route('/api/communities/<int:community_id>/admins/<int:user_id>/role', methods=['PUT'])
def update_admin_role(community_id, user_id):
    """更新社区管理员角色"""
    app.logger.info(f'=== 开始更新管理员角色: 社区{community_id}, 用户{user_id} ===')
    
    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response
    
    operator_id = decoded.get('user_id')
    operator = User.query.get(operator_id)
    
    # 检查超级管理员权限
    error = _check_super_admin_permission(operator)
    if error:
        return error
    
    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')
        
        new_role = params.get('role')
        if new_role is None:
            return make_err_response({}, '缺少角色参数')
        
        # 验证角色值
        if new_role not in [1, 2]:  # 1: 社区主管, 2: 社区专员
            return make_err_response({}, 'Invalid role')
        
        # 检查社区是否存在
        community = Community.query.get(community_id)
        if not community:
            return make_err_response({}, '社区不存在')
        
        # 检查用户是否是社区管理员
        admin = CommunityAdmin.query.filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        if not admin:
            return make_err_response({}, '用户不是该社区的管理员')
        
        # 检查是否会移除最后一个社区主管
        if admin.role == 1 and new_role != 1:
            supervisor_count = CommunityAdmin.query.filter_by(
                community_id=community_id,
                role=1
            ).count()
            if supervisor_count <= 1:
                return make_err_response({}, '不能移除最后一个社区主管')
        
        # 更新角色
        admin.role = new_role
        db.session.commit()
        
        app_logger.info(f'更新管理员角色成功: 社区{community_id}, 用户{user_id}, 新角色{new_role}')
        return make_succ_response({'message': 'Role updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        app_logger.error(f'更新管理员角色失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'更新管理员角色失败: {str(e)}')