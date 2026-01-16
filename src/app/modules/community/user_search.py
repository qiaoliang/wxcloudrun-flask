"""
用户搜索路由
包含用户搜索相关功能
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from app.application.use_cases.community import SearchUsersUseCase

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

        # 使用UseCase执行搜索
        search_use_case = SearchUsersUseCase()
        result = search_use_case.execute(
            keyword=keyword,
            page=page,
            per_page=per_page,
            search_type=search_type
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'搜索结果: 找到 {result.data["total"]} 条记录')

        return make_succ_response(result.data)

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

        # 使用UseCase执行搜索（排除黑名单房间）
        search_use_case = SearchUsersUseCase()
        result = search_use_case.execute(
            keyword=keyword,
            page=page,
            per_page=per_page,
            search_type='all',
            exclude_blackroom=True
        )

        if not result.is_success:
            return make_err_response({}, result.message)

        current_app.logger.info(f'搜索结果: 找到 {result.data["total"]} 条记录')

        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '搜索失败')

