"""
社区工作人员管理路由
包含社区工作人员的查询、添加和移除操作
"""

import logging
from datetime import datetime
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
# 移除未使用的 db 和 User 导入,已通过 UseCase 访问数据
from wxcloudrun.utils.validators import _audit
from app.application.use_cases.community.get_community_staff_list_use_case import GetCommunityStaffListUseCase
from app.application.use_cases.community.add_community_staff_use_case import AddCommunityStaffUseCase
from app.application.use_cases.community.remove_community_staff_use_case import RemoveCommunityStaffUseCase
from app.application.use_cases.community.check_community_permission_use_case import CheckCommunityPermissionUseCase
from app.application.use_cases.community.set_super_admin_use_case import SetSuperAdminUseCase
from app.application.use_cases.community.get_admin_list_use_case import GetAdminListUseCase

app_logger = logging.getLogger('log')


@community_bp.route('/community/staff/list-enhanced', methods=['GET'])
def get_community_staff_list_enhanced():
    """获取社区工作人员列表（增强版，包含更多字段和分页）"""
    current_app.logger.info('=== 开始获取社区工作人员列表（增强版） ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    user_id = decoded.get('user_id')
    current_app.logger.info(f'用户ID: {user_id}')

    try:
        # GET请求应该从查询参数获取，而不是JSON body
        community_id = request.args.get('community_id')
        role = request.args.get('role', 'all')  # 默认返回所有角色
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        # 验证role参数
        valid_roles = ['all', 'manager', 'staff']
        if role not in valid_roles:
            return make_err_response({}, f'无效的角色参数，支持的角色: {valid_roles}')

        # 检查权限
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(user_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用新的 UseCase 获取社区工作人员列表
        use_case = GetCommunityStaffListUseCase()
        result = use_case.execute(
            community_id=int(community_id),
            role=role,
            page=page,
            limit=limit
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'获取社区工作人员列表成功: community_id={community_id}, page={page}')
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取工作人员列表失败')


@community_bp.route('/community/add-staff', methods=['POST'])
def add_community_staff():
    """添加社区工作人员（支持批量添加）"""
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
        user_ids = params.get('user_ids')  # 支持批量
        target_user_id = params.get('user_id')  # 兼容单个
        role = params.get('role')

        if not community_id:
            return make_err_response({}, '缺少社区ID')

        if not user_ids and not target_user_id:
            return make_err_response({}, '缺少用户ID')

        if not role:
            return make_err_response({}, '缺少角色参数')

        # 参数类型和格式验证
        try:
            community_id = int(community_id)
            if community_id <= 0:
                raise ValueError('社区ID必须为正整数')
        except (ValueError, TypeError):
            return make_err_response({}, '社区ID格式错误')

        # 统一处理用户ID（支持单个和批量）
        if user_ids:
            if not isinstance(user_ids, list):
                return make_err_response({}, 'user_ids必须是数组')

            if not user_ids:
                return make_err_response({}, '用户ID列表不能为空')

            # 验证每个用户ID
            valid_user_ids = []
            for uid in user_ids:
                try:
                    uid_int = int(uid)
                    if uid_int <= 0:
                        continue
                    valid_user_ids.append(uid_int)
                except (ValueError, TypeError):
                    continue

            if not valid_user_ids:
                return make_err_response({}, '没有有效的用户ID')

            final_user_ids = valid_user_ids
        else:
            # 兼容单个用户ID的情况
            try:
                target_user_id_int = int(target_user_id)
                if target_user_id_int <= 0:
                    raise ValueError('用户ID必须为正整数')
                final_user_ids = [target_user_id_int]
            except (ValueError, TypeError):
                return make_err_response({}, '用户ID格式错误')

        # 角色参数验证
        valid_roles = ['staff', 'manager']
        if role not in valid_roles:
            return make_err_response({}, f'角色参数错误，必须是: {", ".join(valid_roles)}')

        # 检查权限
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 批量操作限制验证
        if len(final_user_ids) > 50:
            return make_err_response({}, '单次添加用户数量不能超过50个')

        # 检查角色限制
        if role == 'manager' and len(final_user_ids) > 1:
            return make_err_response({}, '主管角色只能添加单个用户')

        # 使用新的 UseCase 进行批量添加
        use_case = AddCommunityStaffUseCase()
        result = use_case.execute(
            operator_user_id=operator_id,
            community_id=community_id,
            user_ids=final_user_ids,
            role=role
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(operator_id, 'add_community_staff_batch', {
            'community_id': community_id,
            'user_ids': final_user_ids,
            'role': role,
            'success_count': result.data.get('success_count', 0),
            'failed_count': len(result.data.get('failed', []))
        })

        return make_succ_response({
            'added_count': result.data.get('success_count', 0),
            'failed_count': len(result.data.get('failed', [])),
            'failed': result.data.get('failed', []),
            'added_users': result.data.get('added_users', [])
        })

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
        check_permission_use_case = CheckCommunityPermissionUseCase()
        permission_result = check_permission_use_case.execute(operator_id, community_id)
        has_permission = permission_result.data.get('has_permission', False) if permission_result.is_success else False
        if not has_permission:
            return make_err_response({}, '无权限访问该社区')

        # 使用新的 UseCase 移除工作人员
        use_case = RemoveCommunityStaffUseCase()
        result = use_case.execute(
            community_id=int(community_id),
            target_user_id=int(target_user_id),
            operator_user_id=operator_id
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        # 记录审计日志
        _audit(operator_id, 'remove_community_staff', {
            'community_id': community_id,
            'target_user_id': target_user_id
        })

        current_app.logger.info(f'移除社区工作人员成功: community_id={community_id}, user_id={target_user_id}')
        return make_succ_response({'message': '移除成功'})

    except Exception as e:
        current_app.logger.error(f'移除社区工作人员失败: {str(e)}', exc_info=True)
        return make_err_response({}, '移除失败')


@community_bp.route('/community/set-super-admin', methods=['POST'])
def set_super_admin():
    """设置或取消超级管理员"""
    current_app.logger.info('=== 开始设置/取消超级管理员 ===')

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

        target_user_id = params.get('target_user_id')
        is_super_admin = params.get('is_super_admin')

        if target_user_id is None or is_super_admin is None:
            return make_err_response({}, '缺少必要参数')

        # 使用应用服务用例设置超级管理员
        set_super_admin_use_case = SetSuperAdminUseCase()
        result = set_super_admin_use_case.execute(
            operator_user_id=operator_id,
            target_user_id=int(target_user_id),
            is_super_admin=is_super_admin
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'设置超级管理员操作完成: {result.data}')
        return make_succ_response(result.data)

    except ValueError as e:
        current_app.logger.warning(f'设置超级管理员失败: {str(e)}')
        return make_err_response({}, str(e))
    except Exception as e:
        current_app.logger.error(f'设置超级管理员失败: {str(e)}', exc_info=True)
        return make_err_response({}, '设置超级管理员失败')


@community_bp.route('/community/admin-list', methods=['GET'])
def get_admin_list():
    """获取管理员列表"""
    current_app.logger.info('=== 开始获取管理员列表 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    try:
        # 使用应用服务用例获取管理员列表
        get_admin_list_use_case = GetAdminListUseCase()
        result = get_admin_list_use_case.execute()

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'获取管理员列表成功: 共{len(result.data["admins"])}个管理员')
        return make_succ_response(result.data)
    except Exception as e:
        current_app.logger.error(f'获取管理员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取管理员列表失败')