"""
路由层辅助函数
提供路由层的通用辅助函数，简化重复代码
"""

import logging
from functools import wraps
from typing import Callable, Optional, Any
from flask import request, current_app
from app.shared import make_succ_response, make_err_response
from app.shared.utils.auth import verify_token

logger = logging.getLogger('log')


def with_validated_user(f: Callable) -> Callable:
    """
    装饰器：验证 token 并将 user_id 添加到 kwargs

    使用方式：
    @with_validated_user
    def my_route(user_id: int, other_param: str):
        # user_id 已从 token 中提取并验证
        pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 验证 token
        decoded, error_response = verify_token()
        if error_response:
            return error_response

        # 提取 user_id
        user_id = decoded.get('user_id')
        if not user_id:
            return make_err_response({}, 'token 无效')

        # 将 user_id 添加到 kwargs
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)

    return decorated_function


def with_user_verification(f: Callable) -> Callable:
    """
    装饰器：验证 token 并验证用户存在性

    使用方式：
    @with_user_verification
    def my_route(user_id: int, user: dict, other_param: str):
        # user_id 已从 token 中提取
        # user 是通过 GetUserByIdUseCase 获取的用户对象
        pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.application.use_cases.user import GetUserByIdUseCase

        # 验证 token
        decoded, error_response = verify_token()
        if error_response:
            return error_response

        # 提取 user_id
        user_id = decoded.get('user_id')
        if not user_id:
            return make_err_response({}, 'token 无效')

        # 验证用户存在
        get_user_use_case = GetUserByIdUseCase()
        user_result = get_user_use_case.execute(user_id=user_id)
        if not user_result.is_success:
            current_app.logger.error(f'数据库中未找到 user_id 为 {user_id} 的用户')
            return make_err_response({}, '用户不存在')

        # 将 user_id 和 user 添加到 kwargs
        kwargs['user_id'] = user_id
        kwargs['user'] = user_result.data
        return f(*args, **kwargs)

    return decorated_function


def execute_use_case(use_case_class: type, *args, **kwargs) -> Any:
    """
    执行 UseCase 的通用函数

    Args:
        use_case_class: UseCase 类
        *args, **kwargs: 传递给 UseCase.execute() 的参数

    Returns:
        UseCaseResult 对象
    """
    use_case = use_case_class()
    return use_case.execute(*args, **kwargs)


def handle_use_case_result(result) -> tuple:
    """
    处理 UseCase 结果并返回 Flask 响应

    Args:
        result: UseCaseResult 对象

    Returns:
        Flask 响应元组 (response, status_code)
    """
    if result.is_success:
        return make_succ_response(result.data), 200
    else:
        return make_err_response({}, result.message), 400


def get_json_params(required_fields: Optional[list] = None) -> tuple[Optional[dict], Optional[str]]:
    """
    获取并验证请求 JSON 参数

    Args:
        required_fields: 必需字段列表

    Returns:
        (params, error_message) 元组
    """
    try:
        params = request.get_json(force=False, silent=True)
        # 检查 params 是否为 None 或空字典
        if not params or (isinstance(params, dict) and len(params) == 0):
            return None, '缺少请求体参数'
    except Exception:
        return None, '请求体格式错误'

    if required_fields:
        missing_fields = [f for f in required_fields if f not in params or not params.get(f)]
        if missing_fields:
            return None, f'缺少参数: {", ".join(missing_fields)}'

    return params, None
