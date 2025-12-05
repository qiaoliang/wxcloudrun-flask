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
        load_dotenv(env_file, override=True)
    else:
        # 如果特定环境配置文件不存在，尝试加载基础配置
        load_dotenv('.env', override=True)


def get_database_config() -> Dict[str, Any]:
    """
    根据环境类型获取数据库配置
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    
    if env_type == 'unit':
        # unit 环境固定使用 SQLite 内存数据库
        return {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'TESTING': True,
            'DEBUG': True
        }
    else:
        # function, uat 和 prod 环境使用 SQLite 文件数据库
        # 根据环境类型设置不同的默认路径，可被环境变量 SQLITE_DB_PATH 覆盖
        if env_type == 'function':
            default_path = './data/function.db'
        elif env_type == 'uat':
            default_path = './data/uat.db'
        elif env_type == 'prod':
            default_path = '/app/data/prod.db'
        else:
            default_path = './data/app.db'

        db_path = os.getenv("SQLITE_DB_PATH", default_path)
        
        # 确保使用绝对路径以避免相对路径问题
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        
        # 在开发环境中确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        return {
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'TESTING': False,
            'DEBUG': env_type in ['function', 'uat']  # function 和 uat 环境开启调试模式
        }


def should_start_flask_service() -> bool:
    """
    根据环境类型判断是否应该启动 Flask 服务
    """
    env_type = os.getenv('ENV_TYPE', 'unit')
    
    # unit 环境不启动 Flask 服务，仅用于运行测试
    # unit_with_service 环境启动 Flask 服务，但使用内存数据库
    # function 和 prod 环境启动 Flask 服务
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
