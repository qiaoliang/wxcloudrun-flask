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
from database.flask_models import db, User
from wxcloudrun.community_service import CommunityService
from wxcloudrun.community_staff_service import CommunityStaffService
from wxcloudrun.utils.validators import _audit

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
        if not CommunityService.has_community_permission(user_id, community_id):
            return make_err_response({}, '无权限访问该社区')

        # 获取社区工作人员，传递role参数进行过滤
        staff_list, total_count = CommunityStaffService.get_community_staff_with_pagination(
            community_id,
            role=role if role != 'all' else None,
            page=page,
            limit=limit
        )

        # 格式化工作人员信息
        staff_data = []
        for staff in staff_list:
            user = db.session.get(User, staff.user_id)
            if user:
                staff_info = {
                    'staff_id': staff.id,
                    'user_id': user.user_id,
                    'wechat_openid': user.wechat_openid,
                    'phone_number': user.phone_number,
                    'nickname': user.nickname,
                    'name': user.name,
                    'avatar_url': user.avatar_url,
                    'role': staff.role,
                    'added_at': staff.added_at.isoformat() if staff.added_at else None
                }
                staff_data.append(staff_info)

        # 计算分页信息
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        has_more = page < total_pages

        current_app.logger.info(f'获取社区工作人员列表成功: community_id={community_id}, page={page}, 共 {len(staff_data)} 人, 总计 {total_count} 人')
        return make_succ_response({
            'staff': staff_data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'total_pages': total_pages,
                'has_more': has_more
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取社区工作人员列表失败: {str(e)}', exc_info=True)
        return make_err_response({}, '获取工作人员列表失败')


@community_bp.route('/community/add-staff', methods=['POST'])
def add_community_staff():
    """添加社区工作人员（支持批量添加）"""
    current_app.logger.info('=== 开始添加社区工作人员（深度防御验证） ===')

    # Layer 1: 入口点验证 - API边界拒绝显然无效输入
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_id = decoded.get('user_id')
    current_app.logger.info(f'Layer 1 - 操作用户ID: {operator_id}')

    try:
        params = request.get_json()
        if not params:
            current_app.logger.error('Layer 1验证失败: 缺少请求参数')
            return make_err_response({}, '缺少请求参数')

        # Layer 1: 参数存在性和类型验证
        community_id = params.get('community_id')
        user_ids = params.get('user_ids')  # 支持批量
        target_user_id = params.get('user_id')  # 兼容单个
        role = params.get('role')

        # Layer 1: 基础参数验证
        if not community_id:
            current_app.logger.error('Layer 1验证失败: 缺少社区ID')
            return make_err_response({}, '缺少社区ID')

        if not user_ids and not target_user_id:
            current_app.logger.error('Layer 1验证失败: 缺少用户ID')
            return make_err_response({}, '缺少用户ID')

        if not role:
            current_app.logger.error('Layer 1验证失败: 缺少角色参数')
            return make_err_response({}, '缺少角色参数')

        # Layer 1: 参数类型和格式验证
        try:
            community_id = int(community_id)
            if community_id <= 0:
                raise ValueError('社区ID必须为正整数')
        except (ValueError, TypeError):
            current_app.logger.error(f'Layer 1验证失败: 无效的社区ID格式: {community_id}')
            return make_err_response({}, '社区ID格式错误')

        # 统一处理用户ID（支持单个和批量）
        if user_ids:
            if not isinstance(user_ids, list):
                current_app.logger.error(f'Layer 1验证失败: user_ids必须是数组，实际类型: {type(user_ids)}')
                return make_err_response({}, 'user_ids必须是数组')

            if not user_ids:  # 空数组
                current_app.logger.error('Layer 1验证失败: user_ids数组不能为空')
                return make_err_response({}, '用户ID列表不能为空')

            # 验证每个用户ID
            valid_user_ids = []
            for uid in user_ids:
                try:
                    uid_int = int(uid)
                    if uid_int <= 0:
                        current_app.logger.warning(f'Layer 1警告: 跳过无效用户ID: {uid}')
                        continue
                    valid_user_ids.append(uid_int)
                except (ValueError, TypeError):
                    current_app.logger.warning(f'Layer 1警告: 跳过无效用户ID格式: {uid}')
                    continue

            if not valid_user_ids:
                current_app.logger.error('Layer 1验证失败: 没有有效的用户ID')
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
                current_app.logger.error(f'Layer 1验证失败: 无效的用户ID格式: {target_user_id}')
                return make_err_response({}, '用户ID格式错误')

        # Layer 1: 角色参数验证
        valid_roles = ['staff', 'manager']  # 支持的角色
        if role not in valid_roles:
            current_app.logger.error(f'Layer 1验证失败: 无效的角色参数: {role}')
            return make_err_response({}, f'角色参数错误，必须是: {", ".join(valid_roles)}')

        # Layer 4: 调试仪表 - 捕获取证上下文
        current_app.logger.info('Layer 4调试仪表 - 请求取证上下文:', {
            'operator_id': operator_id,
            'community_id': community_id,
            'user_ids_count': len(final_user_ids),
            'user_ids': final_user_ids[:5],  # 只记录前5个，避免日志过长
            'role': role,
            'request_timestamp': datetime.now().isoformat()
        })

        # Layer 2: 业务逻辑验证 - 确保该操作的数据合理
        if not CommunityService.has_community_permission(operator_id, community_id):
            current_app.logger.error(f'Layer 2验证失败: 用户 {operator_id} 无权限访问社区 {community_id}')
            return make_err_response({}, '无权限访问该社区')

        # Layer 2: 批量操作限制验证
        if len(final_user_ids) > 50:  # 防止过大批量操作
            current_app.logger.error(f'Layer 2验证失败: 批量添加用户数量过多: {len(final_user_ids)}')
            return make_err_response({}, '单次添加用户数量不能超过50个')

        # Layer 3: 环境守卫 - 在特定上下文中阻止危险操作
        # 检查角色限制
        if role == 'manager' and len(final_user_ids) > 1:
            current_app.logger.error(f'Layer 3环境守卫: 主管角色只能添加单个用户，尝试添加: {len(final_user_ids)}')
            return make_err_response({}, '主管角色只能添加单个用户')

        # Layer 3: 使用正确的服务方法进行批量添加
        try:
            result = CommunityStaffService.add_staff(
                operator_user_id=operator_id,
                community_id=community_id,
                user_ids=final_user_ids,
                role=role
            )


            # 记录审计日志
            _audit(operator_id, 'add_community_staff_batch', {
                'community_id': community_id,
                'user_ids': final_user_ids,
                'role': role,
                'success_count': result.get('success_count', 0),
                'failed_count': len(result.get('failed', []))
            })

            return make_succ_response({
                'added_count': result.get('success_count', 0),
                'failed_count': len(result.get('failed', [])),
                'failed': result.get('failed', []),
                'added_users': result.get('added_users', [])
            })

        except ValueError as e:
            current_app.logger.error(f'Layer 3环境守卫: 业务逻辑错误 - {str(e)}')
            return make_err_response({}, str(e))
        except Exception as e:
            current_app.logger.error(f'Layer 3环境守卫: 系统错误 - {str(e)}', exc_info=True)
            return make_err_response({}, '添加工作人员失败')

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
        success = CommunityStaffService.remove_staff(
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

        result = CommunityStaffService.set_super_admin(
            operator_user_id=operator_id,
            target_user_id=int(target_user_id),
            is_super_admin=is_super_admin
        )

        current_app.logger.info(f'设置超级管理员操作完成: {result}')
        return make_succ_response(result)

    except ValueError as e:
        current_app.logger.warning(f'设置超级管理员失败: {str(e)}')
        return make_err_response({}, str(e))
    except Exception as e:
        current_app.logger.error(f'设置超级管理员失败: {str(e)}', exc_info=True)
        return make_err_response({}, '设置超级管理员失败')