"""
端口配置统一管理
根据 ENV_TYPE 决定端口
"""

import os


# 端口映射配置
PORT_CONFIG = {
    'func': 9999,      # 功能测试环境
    'function': 9999,  # 开发环境
    'unit': 9999,      # 单元测试环境
    'uat': 8080,       # UAT环境
    'prod': 8080,      # 生产环境
}


def get_port(env_type: str) -> int:
    """
    根据环境类型获取端口

    优先级：
    1. EXPOSE_PORT 环境变量（最高优先级，可覆盖）
    2. 根据 ENV_TYPE 从配置映射获取

    Args:
        env_type: 环境类型 (func, function, unit, uat, prod)

    Returns:
        对应的端口号
    """
    # 1. 优先使用 EXPOSE_PORT 环境变量（用于临时覆盖）
    if 'EXPOSE_PORT' in os.environ:
        return int(os.environ['EXPOSE_PORT'])

    # 2. 根据 ENV_TYPE 从配置映射获取端口
    return PORT_CONFIG.get(env_type, 8080)


def get_env_type_from_port(port: int) -> str:
    """
    根据端口获取环境类型（反向查找）

    Args:
        port: 端口号

    Returns:
        环境类型，如果找不到则返回 None
    """
    for env, p in PORT_CONFIG.items():
        if p == port:
            return env
    return None