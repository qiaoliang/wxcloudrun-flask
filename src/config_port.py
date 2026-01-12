"""
端口配置统一管理
从环境变量读取端口配置
"""

import os


def get_port(env_type: str) -> int:
    """
    根据环境类型获取端口

    优先级：
    1. EXPOSE_PORT 环境变量（最高优先级）
    2. 根据 ENV_TYPE 从环境变量读取
    3. 默认端口 8080

    Args:
        env_type: 环境类型 (func, function, unit, uat, prod)

    Returns:
        对应的端口号
    """
    # 1. 优先使用 EXPOSE_PORT 环境变量
    if 'EXPOSE_PORT' in os.environ:
        return int(os.environ['EXPOSE_PORT'])

    # 2. 根据 ENV_TYPE 从环境变量读取端口
    port_env_var = f'PORT_{env_type.upper()}'
    if port_env_var in os.environ:
        return int(os.environ[port_env_var])

    # 3. 默认端口映射
    default_ports = {
        'func': 9999,
        'function': 9999,
        'unit': 9999,
        'uat': 8080,
        'prod': 8080,
    }

    return default_ports.get(env_type, 8080)


def get_env_type_from_port(port: int) -> str:
    """
    根据端口获取环境类型（反向查找）

    Args:
        port: 端口号

    Returns:
        环境类型，如果找不到则返回 None
    """
    # 从环境变量读取所有端口配置
    port_map = {
        'func': int(os.environ.get('PORT_FUNC', 9999)),
        'function': int(os.environ.get('PORT_FUNCTION', 9999)),
        'unit': int(os.environ.get('PORT_UNIT', 9999)),
        'uat': int(os.environ.get('PORT_UAT', 8080)),
        'prod': int(os.environ.get('PORT_PROD', 8080)),
    }

    for env, p in port_map.items():
        if p == port:
            return env
    return None