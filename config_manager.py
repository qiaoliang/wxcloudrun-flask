"""
环境配置管理模块
根据 ENV_TYPE 环境变量自动加载对应的配置
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv


def load_environment_config():
    """
    根据 ENV_TYPE 加载对应环境的配置文件
    """
    env_type = os.getenv('ENV_TYPE', 'unit')

    # 根据环境类型加载对应的配置文件
    if env_type == 'unit':
        env_file = '.env.unit'
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


def should_start_flask_service() -> bool:
    """
    根据环境类型判断是否应该启动 Flask 服务
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    return env_type != 'unit'


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
    return os.getenv('ENV_TYPE', 'unit') == 'function'


def should_use_mock_wechat() -> bool:
    """
    判断是否应该使用Mock微信API
    unit, function, uat 环境使用Mock，prod使用真实API
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    return env_type in ['unit', 'function', 'uat']


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
