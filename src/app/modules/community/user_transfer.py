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
from wxcloudrun.utils.validators import _audit

app_logger = logging.getLogger('log')


@community_bp.route('/transfer-users', methods=['POST'])
def transfer_users():
    """
    批量转移用户到目标社区

    请求参数:
        source_community_id (int): 源社区ID
        target_community_id (int): 目标社区ID
        user_ids (List[int]): 用户ID列表（最多10个）

    请求示例:
        {
            "source_community_id": 1,
            "target_community_id": 2,
            "user_ids": [101, 102, 103]
        }

    响应:
        code (int): 1-成功，0-失败
        msg (str): 状态消息
        data (dict): 转移结果
            success_count (int): 成功转移数量
            skipped_count (int): 静默跳过数量
            failed (List[dict]): 失败列表
            transferred_users (List[dict]): 成功用户信息
            events_transferred (int): 转移的事件数
            rules_updated (int): 规则更新数
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

        # 限制日志中记录的用户ID数量，避免日志过长
        user_ids_log = user_ids[:5] if len(user_ids) > 5 else user_ids
        user_ids_log_str = f'{user_ids_log}...' if len(user_ids) > 5 else str(user_ids_log)
        current_app.logger.info(
            f'转移参数: source_community_id={source_community_id}, '
            f'target_community_id={target_community_id}, '
            f'user_ids={user_ids_log_str}'
        )

        # 参数验证
        if not source_community_id or not target_community_id:
            return make_err_response({}, '源社区ID和目标社区ID不能为空')

        if not user_ids or not isinstance(user_ids, list):
            return make_err_response({}, '用户ID列表不能为空')

        if len(user_ids) > 10:
            return make_err_response({}, '一次最多转移10个用户')

        # 验证社区ID格式
        try:
            source_community_id = int(source_community_id)
            target_community_id = int(target_community_id)
            if source_community_id <= 0 or target_community_id <= 0:
                return make_err_response({}, '社区ID必须为正整数')
        except (ValueError, TypeError):
            return make_err_response({}, '社区ID格式错误')

        # 验证用户ID格式
        valid_user_ids = []
        for user_id in user_ids:
            try:
                uid_int = int(user_id)
                if uid_int <= 0:
                    continue
                valid_user_ids.append(uid_int)
            except (ValueError, TypeError):
                continue

        if not valid_user_ids:
            return make_err_response({}, '没有有效的用户ID')

        user_ids = valid_user_ids

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

        # 记录审计日志
        _audit(operator_user_id, 'batch_transfer_users', {
            'source_community_id': source_community_id,
            'target_community_id': target_community_id,
            'user_ids': user_ids,
            'success_count': result.get('success_count', 0),
            'skipped_count': result.get('skipped_count', 0),
            'failed_count': len(result.get('failed', []))
        })

        return make_succ_response(result, '转移成功')

    except ValueError as e:
        error_msg = str(e)
        # 对ValueError进行分类处理，返回更友好的错误消息
        if '权限不足' in error_msg:
            user_msg = '权限不足，无法执行此操作'
        elif '不存在' in error_msg:
            user_msg = '指定的用户或社区不存在'
        elif '不能相同' in error_msg:
            user_msg = '源社区和目标社区不能相同'
        elif '最多' in error_msg:
            user_msg = error_msg  # 保留原始错误消息
        else:
            user_msg = '参数错误，请检查输入'

        current_app.logger.warning(f'批量转移用户参数错误: {error_msg}')
        return make_err_response({}, user_msg)
    except Exception as e:
        current_app.logger.error(f'批量转移用户失败: {str(e)}', exc_info=True)
        return make_err_response({}, '转移失败，请稍后重试')