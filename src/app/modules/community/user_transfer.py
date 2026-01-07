"""
用户批量转移路由
提供批量转移用户到目标社区的API端点
"""

import logging
from flask import request, current_app
from . import community_bp
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token
from wxcloudrun.user_transfer_service import UserTransferService

app_logger = logging.getLogger('log')


@community_bp.route('/transfer-users', methods=['POST'])
def transfer_users():
    """
    批量转移用户到目标社区

    请求参数:
        source_community_id: 源社区ID
        target_community_id: 目标社区ID
        user_ids: 用户ID列表（最多10个）

    响应:
        code: 1-成功，0-失败
        msg: 状态消息
        data: 转移结果
            success_count: 成功转移数量
            skipped_count: 静默跳过数量
            failed: 失败列表
            transferred_users: 成功用户信息
            events_transferred: 转移的事件数
            rules_updated: 规则更新数
    """
    current_app.logger.info('=== 开始批量转移用户 ===')

    # 验证token
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    operator_user_id = decoded.get('user_id')
    current_app.logger.info(f'操作用户ID: {operator_user_id}')

    try:
        # 获取请求参数
        params = request.get_json()
        if not params:
            return make_err_response({}, '缺少请求参数')

        source_community_id = params.get('source_community_id')
        target_community_id = params.get('target_community_id')
        user_ids = params.get('user_ids', [])

        current_app.logger.info(
            f'转移参数: source_community_id={source_community_id}, '
            f'target_community_id={target_community_id}, '
            f'user_ids={user_ids}'
        )

        # 参数验证
        if not source_community_id or not target_community_id:
            return make_err_response({}, '源社区ID和目标社区ID不能为空')

        if not user_ids or not isinstance(user_ids, list):
            return make_err_response({}, '用户ID列表不能为空')

        if len(user_ids) > 10:
            return make_err_response({}, '一次最多转移10个用户')

        # 执行批量转移
        result = UserTransferService.transfer_users_batch(
            operator_user_id, source_community_id, target_community_id, user_ids
        )

        current_app.logger.info(
            f'批量转移完成: 成功={result.get("success_count", 0)}, '
            f'跳过={result.get("skipped_count", 0)}, '
            f'失败={len(result.get("failed", []))}, '
            f'事件转移={result.get("events_transferred", 0)}, '
            f'规则更新={result.get("rules_updated", 0)}'
        )

        return make_succ_response(result, '转移成功')

    except ValueError as e:
        current_app.logger.warning(f'批量转移用户参数错误: {str(e)}')
        return make_err_response({}, str(e))
    except Exception as e:
        current_app.logger.error(f'批量转移用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '转移失败，请稍后重试')