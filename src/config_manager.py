"""
环境配置管理模块
根据 ENV_TYPE 环境变量自动加载对应的配置
"""
import os
import json
import re
from typing import Dict, Any, Tuple
from dotenv import load_dotenv


def load_environment_config():
    """
    根据 ENV_TYPE 加载对应环境的配置文件
    """
    env_type = os.getenv('ENV_TYPE', 'unit')

    # 根据环境类型加载对应的配置文件
    if env_type == 'unit':
        env_file = '.env.unit'
    elif env_type == 'dev':
        env_file = '.env.dev'
    elif env_type == 'func':
        env_file = '.env.function'
    elif env_type == 'function':
        env_file = '.env.function'
    elif env_type == 'uat':
        env_file = '.env.uat'
    elif env_type == 'prod':
        env_file = '.env.prod'
    else:
        # 默认使用 unit 环境
        env_file = '.env.unit'
        os.environ['ENV_TYPE'] = 'unit'

    # 加载对应环境的配置文件
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)  # 不覆盖已存在的环境变量
    else:
        # 如果特定环境配置文件不存在，尝试加载基础配置
        # 但不覆盖已存在的环境变量（优先使用 Docker 传入的环境变量）
        load_dotenv('.env', override=False)


def get_database_config() -> Dict[str, Any]:
    """
    根据环境类型获取数据库配置
    """
    env_type = os.getenv('ENV_TYPE', 'unit')

    db_cfg = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'DEBUG': True,
        'DATABASE_TYPE': 'memory',
        'DATABASE_PATH': None
    }

    if env_type != 'unit':        # 根据环境类型设置不同的默认路径，可被环境变量 SQLITE_DB_PATH 覆盖
        if env_type == 'prod':
            default_path = '/app/data/prod.db'
        else:
            # 获取当前脚本所在目录的绝对路径，确保数据库路径固定
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(script_dir, 'data', f'{env_type}.db')

        db_path = os.getenv("SQLITE_DB_PATH", default_path)

        # 确保使用绝对路径以避免相对路径问题
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)

        # 在非prod环境中确保目录存在（prod环境的目录由容器创建）
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir) and env_type != 'prod':
            os.makedirs(db_dir, exist_ok=True)

        db_cfg = {
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'TESTING': False,
            # function 和 uat 环境开启调试模式
            'DEBUG': env_type in ['function', 'uat'],
            'DATABASE_TYPE': 'sqlite',
            'DATABASE_PATH': db_path
        }
    # 注意：此时 app 可能还未初始化，不能使用 app.logger
    # print(f"数据库信息：\n    {json.dumps(db_cfg)}")  # 调试时可取消注释
    return db_cfg


def is_production_environment() -> bool:
    """
    判断是否为生产环境
    """
    return os.getenv('ENV_TYPE', 'unit') == 'prod'


def is_uat_environment() -> bool:
    """
    判断是否为UAT环境
    """
    return os.getenv('ENV_TYPE', 'unit') == 'uat'


def is_unit_environment() -> bool:
    """
    判断是否为单元测试环境
    """
    return os.getenv('ENV_TYPE', 'unit') == 'unit'


def is_function_environment() -> bool:
    """
    判断是否为功能测试环境
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    return env_type in ['func', 'function']


def should_use_mock_wechat() -> bool:
    """
    判断是否应该使用Mock微信API
    unit, func, function, uat 环境使用Mock，prod使用真实API
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    return env_type in ['unit', 'func', 'function', 'uat']


def should_use_real_sms() -> bool:
    """
    判断是否应该使用真实短信服务
    只有prod和uat环境使用真实短信服务
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    return env_type in ['uat', 'prod']


def get_token_secret() -> str:
    """
    获取JWT token密钥
    如果配置为空或不存在，则抛出异常
    """
    token_secret = os.getenv('TOKEN_SECRET')
    if not token_secret:
        raise ValueError("TOKEN_SECRET 环境变量未设置或为空")
    return token_secret


def get_wechat_config() -> Dict[str, str]:
    """
    获取微信API配置
    如果配置为空或不存在，则抛出异常
    """
    appid = os.getenv('WX_APPID')
    secret = os.getenv('WX_SECRET')

    if not appid:
        raise ValueError("WX_APPID 环境变量未设置或为空")
    if not secret:
        raise ValueError("WX_SECRET 环境变量未设置或为空")

    return {
        'appid': appid,
        'secret': secret
    }


def get_redis_config() -> Dict[str, Any]:
    """
    根据环境类型获取 Redis 配置
    """
    if is_unit_environment():
        # 在 unit 环境下，我们可能使用 fakeredis 或内存模拟
        return {
            'REDIS_HOST': 'localhost',  # 这将被应用层特殊处理以使用 fakeredis
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None,
            'USE_FAKE_REDIS': True  # 用于应用层判断是否使用 fakeredis
        }
    else:
        return {
            'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
            'REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
            'REDIS_DB': int(os.getenv('REDIS_DB', 0)),
            'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
            'USE_FAKE_REDIS': False
        }


def mask_sensitive_value(value: str, name: str) -> str:
    """
    对敏感值进行脱敏处理

    Args:
        value: 原始值
        name: 变量名，用于判断是否为敏感信息

    Returns:
        脱敏后的值
    """
    if not value or not is_sensitive_variable(name):
        return value

    length = len(value)

    if length <= 20:
        # 短字符串：处理整个字符串
        start_index = length // 3
        end_index = length * 2 // 3
        mask_length = end_index - start_index

        masked_value = (
            value[:start_index] +
            '*' * mask_length +
            value[end_index:]
        )
    else:
        # 长字符串：只处理前20个字符
        display_part = value[:20]
        start_index = 20 // 3
        end_index = 20 * 2 // 3
        mask_length = end_index - start_index

        masked_value = (
            display_part[:start_index] +
            '*' * mask_length +
            display_part[end_index:] +
            value[20:]  # 剩余部分保持原样
        )

    return masked_value


def is_sensitive_variable(name: str) -> bool:
    """
    判断变量名是否为敏感信息

    Args:
        name: 变量名

    Returns:
        是否为敏感信息
    """
    sensitive_patterns = [
        'password', 'secret', 'key', 'token', 'auth',
        'private', 'credential', 'api_key', 'access_key'
    ]

    name_lower = name.lower()
    return any(pattern in name_lower for pattern in sensitive_patterns)


def infer_data_type(value: str) -> str:
    """
    推断值的数据类型

    Args:
        value: 字符串值

    Returns:
        数据类型名称
    """
    if not value:
        return 'null'

    # 布尔值检测
    if value.lower() in ('true', 'false', 'on', 'off', 'yes', 'no', '1', '0'):
        return 'boolean'

    # 数字检测
    try:
        if '.' in value:
            float(value)
            return 'float'
        else:
            int(value)
            return 'integer'
    except ValueError:
        pass

    # JSON 检测
    try:
        json.loads(value)
        return 'json'
    except (json.JSONDecodeError, ValueError):
        pass

    # 默认为字符串
    return 'string'


def get_config_sources() -> Dict[str, Dict[str, str]]:
    """
    获取所有配置变量的来源信息

    Returns:
        包含每个变量来源信息的字典
    """
    env_type = os.getenv('ENV_TYPE', 'unit')

    # 保存当前环境变量状态
    original_env = dict(os.environ)

    # 清空环境变量以获取配置文件中的原始值
    config_sources = {}

    # 获取基础配置文件中的值
    base_env_values = {}
    if os.path.exists('.env'):
        load_dotenv('.env', override=True)
        base_env_values = dict(os.environ)

    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)

    # 获取环境特定配置文件中的值
    env_file_values = {}
    env_file = f'.env.{env_type}'
    if os.path.exists(env_file):
        # 临时加载环境特定配置
        temp_env = dict(os.environ)
        load_dotenv(env_file, override=True)
        env_file_values = dict(os.environ)
        # 恢复原始环境
        os.environ.clear()
        os.environ.update(temp_env)

    # 收集所有可能的配置变量名
    all_var_names = set(original_env.keys()) | set(
        base_env_values.keys()) | set(env_file_values.keys())

    # 分析每个变量的来源
    for var_name in all_var_names:
        sources = {
            'system_env': original_env.get(var_name),
            'env_file': env_file_values.get(var_name),
            'base_env': base_env_values.get(var_name)
        }

        # 确定活跃来源
        if original_env.get(var_name) is not None:
            active_source = 'system_env'
        elif env_file_values.get(var_name) is not None:
            active_source = 'env_file'
        elif base_env_values.get(var_name) is not None:
            active_source = 'base_env'
        else:
            active_source = None

        sources['active_source'] = active_source
        config_sources[var_name] = sources

    return config_sources


def analyze_all_configs() -> Dict[str, Any]:
    """
    分析应用程序相关的配置变量，返回详细信息

    Returns:
        包含应用程序配置分析结果的字典
    """
    env_type = os.getenv('ENV_TYPE', 'unit')

    # 定义应用程序相关的环境变量列表
    app_related_vars = {
        'SMS_PROVIDER', 'ENV_TYPE', 'TOKEN_SECRET', 'PHONE_ENCRYPTION_KEY',
        'WX_SECRET', 'VIRTUAL_ENV', 'DB_RETRY_COUNT',
        'DB_POOL_SIZE', 'WX_APPID', 'DB_RETRY_DELAY',
        'REDIS_HOST',
        'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD', 'MAIL_SERVER', 'MAIL_PORT',
        'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_USE_TLS', 'SMS_API_KEY',
        'SMS_API_SECRET', 'SQLITE_DB_PATH', 'USE_SQLITE_FOR_TESTING',
        'AUTO_RUN_MIGRATIONS', 'CONFIG_VERIFICATION_CODE_EXPIRY', 'SMS_DEBUG_RETURN_CODE'
    }

    # 获取配置来源信息
    config_sources = get_config_sources()

    # 分析每个应用程序相关的配置变量
    variables = {}
    for var_name in app_related_vars:
        sources = config_sources.get(var_name, {
            'system_env': None,
            'env_file': None,
            'base_env': None,
            'active_source': None
        })

        effective_value = os.getenv(var_name)

        # 处理敏感信息
        is_sensitive = is_sensitive_variable(var_name)
        display_value = mask_sensitive_value(
            effective_value or '', var_name) if effective_value else ''

        variables[var_name] = {
            'name': var_name,
            'effective_value': display_value,
            'sources': sources,
            'data_type': infer_data_type(effective_value or ''),
            'is_sensitive': is_sensitive
        }

    return {
        'environment': env_type,
        'config_source': f'.env.{env_type}',
        'variables': variables
    }


def detect_external_systems_status() -> Dict[str, Any]:
    """
    检测外部系统状态

    Returns:
        外部系统状态信息
    """
    external_systems = {}

    # 微信API状态
    try:
        wechat_config = get_wechat_config()
        external_systems['wechat'] = {
            'name': '微信API',
            'is_mock': should_use_mock_wechat(),
            'config': {
                'appid': wechat_config['appid'],
                'app_secret': mask_sensitive_value(wechat_config['secret'], 'WX_SECRET')
            },
            'status': 'mock_mode' if should_use_mock_wechat() else 'real_mode'
        }
    except Exception as e:
        external_systems['wechat'] = {
            'name': '微信API',
            'is_mock': True,
            'config': {'error': str(e)},
            'status': 'error'
        }

    # 短信服务状态
    sms_provider = os.getenv('SMS_PROVIDER', 'unknown')
    external_systems['sms'] = {
        'name': '短信服务',
        'is_mock': not should_use_real_sms(),
        'config': {
            'provider': sms_provider,
            'use_real': should_use_real_sms()
        },
        'status': 'real_mode' if should_use_real_sms() else 'mock_mode'
    }

    # Redis状态
    redis_config = get_redis_config()
    external_systems['redis'] = {
        'name': 'Redis',
        'is_mock': redis_config.get('USE_FAKE_REDIS', False),
        'config': {
            'host': redis_config['REDIS_HOST'],
            'port': redis_config['REDIS_PORT'],
            'db': redis_config['REDIS_DB'],
            'password': mask_sensitive_value(redis_config['REDIS_PASSWORD'] or '', 'REDIS_PASSWORD') if redis_config['REDIS_PASSWORD'] else None,
            'use_fake': redis_config['USE_FAKE_REDIS']
        },
        'status': 'mock_mode' if redis_config.get('USE_FAKE_REDIS', False) else 'configured'
    }

    # 数据库状态
    db_config = get_database_config()
    external_systems['database'] = {
        'name': '数据库',
        'is_mock': db_config.get('DATABASE_TYPE') == 'memory',
        'config': {
            'type': db_config.get('DATABASE_TYPE'),
            'path': db_config.get('DATABASE_PATH'),
            'uri': db_config.get('SQLALCHEMY_DATABASE_URI'),
            'testing': db_config.get('TESTING', False),
            'debug': db_config.get('DEBUG', False)
        },
        'status': 'memory_mode' if db_config.get('DATABASE_TYPE') == 'memory' else 'configured'
    }

    # 邮件服务状态
    mail_server = os.getenv('MAIL_SERVER')
    mail_port = os.getenv('MAIL_PORT')
    external_systems['email'] = {
        'name': '邮件服务',
        'is_mock': not bool(mail_server),
        'config': {
            'configured': bool(mail_server),
            'server': mail_server,
            'port': mail_port,
            'username': os.getenv('MAIL_USERNAME'),
            'use_tls': os.getenv('MAIL_USE_TLS') == 'true'
        },
        'status': 'configured' if mail_server else 'not_configured'
    }

    return external_systems
