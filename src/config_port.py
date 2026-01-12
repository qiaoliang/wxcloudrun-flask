"""
端口配置统一管理
所有环境的端口配置集中在此文件中
"""

# 端口配置映射
# ENV_TYPE -> 端口号
PORT_CONFIG = {
    'func': 9999,      # 功能测试环境
    'function': 9999,  # 开发环境
    'unit': 9999,      # 单元测试环境
    'uat': 8080,       # UAT环境
    'prod': 8080,      # 生产环境
}

# 默认端口（当 ENV_TYPE 未知时）
DEFAULT_PORT = 8080


def get_port(env_type: str) -> int:
    """
    根据环境类型获取端口

    Args:
        env_type: 环境类型 (func, function, unit, uat, prod)

    Returns:
        对应的端口号
    """
    return PORT_CONFIG.get(env_type, DEFAULT_PORT)


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