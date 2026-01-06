"""
用户搜索路由
包含用户搜索相关功能
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from wxcloudrun.community_service import CommunityService
from wxcloudrun.user_service import UserService

app_logger = logging.getLogger('log')


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

        # 安全地解析page参数
        page_str = request.args.get('page', '1')
        try:
            page = int(page_str)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            current_app.logger.error(f'无效的page参数: {page_str}')
            return make_err_response({}, 'page参数必须是正整数')

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

        # 安全地解析page参数
        page_str = request.args.get('page', '1')
        try:
            page = int(page_str)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            current_app.logger.error(f'无效的page参数: {page_str}')
            return make_err_response({}, 'page参数必须是正整数')

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
        result = UserService.search_ankafamily_users(keyword, page, per_page)

        current_app.logger.info(f'搜索结果: 找到 {result["pagination"]["total"]} 条记录')

        # 构造返回数据
        users = []
        for user in result.get('users', []):
            user_data = {
                'user_id': user.get('user_id'),
                'wechat_openid': user.get('wechat_openid'),
                'phone_number': user.get('phone_number'),
                'nickname': user.get('nickname'),
                'name': user.get('name'),
                'avatar_url': user.get('avatar_url'),
                'role': user.get('role'),
                'community_id': user.get('community_id'),
                'community_name': None,  # 需要额外查询获取社区名称
                'status': user.get('status'),
                'created_at': user.get('created_at')
            }
            users.append(user_data)

        response_data = {
            'users': users,
            'total': result.get('pagination', {}).get('total', 0),
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page
        }

        return make_succ_response(response_data)

    except Exception as e:
        current_app.logger.error(f'搜索安卡家族用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')