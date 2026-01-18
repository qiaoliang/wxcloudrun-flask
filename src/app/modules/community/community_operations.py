"""
社区操作路由
包含社区的创建、更新、状态切换和删除操作
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
# 移除 db 直接访问,改用 UseCase 返回的完整数据
from wxcloudrun.utils.validators import _audit
from app.shared.constants.roles import Role
from app.application.use_cases.community import (
    CreateCommunityUseCase,
    UpdateCommunityUseCase,
    DeleteCommunityUseCase,
    ToggleCommunityStatusUseCase,
    CheckCommunityPermissionUseCase,
    AddCommunityStaffUseCase
)
from app.application.use_cases.auth import GetCurrentUserUseCase

app_logger = logging.getLogger('log')


@community_bp.route('/community/create', methods=['POST'])
def create_community():
    """创建社区"""
    current_app.logger.info('=== 开始创建社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')

    # 使用GetCurrentUserUseCase获取用户对象
    get_user_use_case = GetCurrentUserUseCase()
    user_result = get_user_use_case.execute(user_id)
    user = user_result.data if user_result.is_success else None

    # 检查权限
    if not user or user.role < 3:  # 社区管理员及以上
        return make_err_response({}, '无权限创建社区')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        name = params.get('name', '').strip()
        description = params.get('description', '').strip()
        location = params.get('location', '').strip()
        location_lat = params.get('location_lat')
        location_lon = params.get('location_lon')
        manager_id = params.get('manager_id')
        province = params.get('province')
        city = params.get('city')
        district = params.get('district')
        street = params.get('street')

        if not name:
            return make_err_response({}, '社区名称不能为空')

        # 使用应用服务用例创建社区
        use_case = CreateCommunityUseCase()
        result = use_case.execute(
            name=name,
            description=description,
            creator_id=user_id,
            location=location,
            location_lat=location_lat,
            location_lon=location_lon,
            manager_id=manager_id,
            province=province,
            city=city,
            district=district,
            street=street
        )

        if not result.is_success:
            # 统一返回 "创建失败" 消息，以保持与测试的兼容性
            return make_err_response({}, '创建失败')

        community_id = result.data.get('community_id')

        # 如果没有指定主管，将创建者设置为主管并添加到 CommunityStaff 表
        # 如果指定了主管，将主管添加到 CommunityStaff 表
        target_manager_id = manager_id if manager_id else user_id
        
        # 将主管添加到 CommunityStaff 表
        if target_manager_id:
            try:
                add_staff_use_case = AddCommunityStaffUseCase()
                add_staff_result = add_staff_use_case.execute(
                    operator_user_id=user_id,
                    community_id=community_id,
                    user_ids=[target_manager_id],
                    role='manager'
                )
                if add_staff_result.is_success:
                    current_app.logger.info(f'已将主管添加到 CommunityStaff 表: community_id={community_id}, manager_id={target_manager_id}')
                else:
                    current_app.logger.warning(f'添加主管到 CommunityStaff 表失败: {add_staff_result.message}')
            except Exception as e:
                current_app.logger.error(f'添加主管到 CommunityStaff 表失败: {str(e)}', exc_info=True)
                # 不影响社区创建成功，只记录错误

        # 记录审计日志
        _audit(user_id, 'create_community', {
            'community_id': community_id,
            'name': name,
            'manager_id': manager_id
        })

        current_app.logger.info(f'创建社区成功: community_id={community_id}, name={name}, manager_id={manager_id}')

        # 直接返回 UseCase 的结果（已包含所有必要信息）
        return make_succ_response({
            'community_id': community_id,
            'name': result.data.get('name'),
            'description': result.data.get('description'),
            'creator_id': result.data.get('creator_id'),
            'manager_id': result.data.get('manager_id'),
            'manager_name': result.data.get('manager', {}).get('nickname') if result.data.get('manager') else None,
            'manager': result.data.get('manager'),
            'location': result.data.get('location'),
            'location_lat': result.data.get('location_lat'),
            'location_lon': result.data.get('location_lon'),
            'province': result.data.get('province'),
            'city': result.data.get('city'),
            'district': result.data.get('district'),
            'street': result.data.get('street'),
            'status': result.data.get('status'),
            'created_at': result.data.get('created_at'),
            'settings': result.data.get('settings'),
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
        from app.application.use_cases.community import CheckCommunityPermissionUseCase
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用应用服务用例更新社区信息
        from app.application.use_cases.community import UpdateCommunityUseCase

        use_case = UpdateCommunityUseCase()
        result = use_case.execute(
            community_id=community_id,
            name=params.get('name'),
            description=params.get('description'),
            location=params.get('location'),
            manager_id=params.get('manager_id'),
            location_lat=params.get('location_lat'),
            location_lon=params.get('location_lon'),
            province=params.get('province'),
            city=params.get('city'),
            district=params.get('district'),
            street=params.get('street'),
            status=params.get('status')
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(user_id, 'update_community', {
            'community_id': community_id,
            'updated_fields': list(params.keys())
        })

        current_app.logger.info(f'更新社区信息成功: community_id={community_id}')
        return make_succ_response({'message': '更新成功'})

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

    # 使用GetCurrentUserUseCase获取用户对象
    get_user_use_case = GetCurrentUserUseCase()
    user_result = get_user_use_case.execute(user_id)
    user = user_result.data if user_result.is_success else None

    # 检查权限
    if not user or user.role == Role.SOLO:  # 只有超级管理员可以切换状态
        return make_err_response({}, '无权限执行此操作')

    try:
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        community_id = params.get('community_id')
        if not community_id:
            return make_err_response({}, '缺少社区ID')

        status = params.get('status')
        if not status:
            return make_err_response({}, '缺少状态参数')

        # 切换状态
        toggle_status_use_case = ToggleCommunityStatusUseCase()
        result = toggle_status_use_case.execute(community_id, status)

        if result.is_success:
            # 记录审计日志
            _audit(user_id, 'toggle_community_status', {
                'community_id': community_id
            })

            current_app.logger.info(f'切换社区状态成功: community_id={community_id}')
            return make_succ_response({'message': '切换成功'})
        else:
            return make_err_response({}, result.message)

    except Exception as e:
        current_app.logger.error(f'切换社区状态失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'切换失败: {str(e)}')


@community_bp.route('/community/delete', methods=['POST'])
def delete_community():
    """删除社区"""
    current_app.logger.info('=== 开始删除社区 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')

    # 使用GetCurrentUserUseCase获取用户对象
    get_user_use_case = GetCurrentUserUseCase()
    user_result = get_user_use_case.execute(user_id)
    user = user_result.data if user_result.is_success else None

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

        # 使用应用服务用例删除社区
        use_case = DeleteCommunityUseCase()
        result = use_case.execute(
            community_id=community_id,
            user_id=user_id
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(user_id, 'delete_community', {
            'community_id': community_id
        })

        current_app.logger.info(f'删除社区成功: community_id={community_id}')
        # 直接返回 UseCase 的结果（已包含社区名称）
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'删除社区失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'删除失败: {str(e)}')
