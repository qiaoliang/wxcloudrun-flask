"""
配置加载器
负责加载和验证应用配置
"""
import os
from dotenv import load_dotenv
from .domain import (
    AppConfig,
    DatabaseConfig,
    WeChatConfig,
    RedisConfig,
    EnvironmentType
)
from .utils import EnvironmentHelper
from .port import get_port


class ConfigLoader:
    """配置加载器"""

    def __init__(self, env_type: str = None):
        self.env_type = env_type or EnvironmentHelper.get_env_type()

    def load(self) -> AppConfig:
        """加载完整配置"""
        # 加载环境配置文件
        self._load_env_file()

        # 构建配置对象
        return AppConfig(
            environment=EnvironmentType(self.env_type),
            database=self._load_database_config(),
            wechat=self._load_wechat_config(),
            redis=self._load_redis_config(),
            port=get_port(self.env_type),
            debug=EnvironmentHelper.is_debug_mode(),
            token_secret=self._load_token_secret(),
            phone_encryption_key=self._load_phone_encryption_key()
        )

    def _load_env_file(self) -> None:
        """加载环境配置文件"""
        env_file = EnvironmentHelper.get_env_file()

        # 优先加载环境特定配置
        if os.path.exists(env_file):
            load_dotenv(env_file, override=False)
        else:
            # 回退到基础配置
            load_dotenv('.env', override=False)

    def _load_database_config(self) -> DatabaseConfig:
        """加载数据库配置"""
        if EnvironmentHelper.is_unit():
            return DatabaseConfig(
                uri='sqlite:///:memory:',
                testing=True,
                debug=True,
                database_type='memory',
                database_path=None
            )

        # 获取数据库路径
        db_path = self._get_database_path()

        return DatabaseConfig(
            uri=f'sqlite:///{db_path}',
            testing=False,
            debug=EnvironmentHelper.is_debug_mode(),
            database_type='sqlite',
            database_path=db_path
        )

    def _get_database_path(self) -> str:
        """获取数据库路径"""
        env_type = self.env_type

        # 根据环境类型设置默认路径
        if env_type == 'prod':
            if EnvironmentHelper.is_running_in_docker():
                default_path = '/app/data/prod.db'
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                default_path = os.path.join(script_dir, '..', 'data', 'prod.db')
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(script_dir, '..', 'data', f'{env_type}.db')

        # 允许环境变量覆盖
        db_path = os.getenv("SQLITE_DB_PATH", default_path)

        # 确保使用绝对路径
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)

        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        return db_path

    def _load_wechat_config(self) -> WeChatConfig:
        """加载微信配置"""
        appid = os.getenv('WX_APPID', 'test_appid')
        secret = os.getenv('WX_SECRET', 'test_secret')

        # 在测试环境中使用默认值
        if EnvironmentHelper.is_unit() or EnvironmentHelper.is_function():
            appid = appid or 'test_appid'
            secret = secret or 'test_secret'
        else:
            if not appid:
                raise ValueError("WX_APPID 环境变量未设置或为空")
            if not secret:
                raise ValueError("WX_SECRET 环境变量未设置或为空")

        use_mock = EnvironmentHelper.is_unit() or EnvironmentHelper.is_function() or EnvironmentHelper.is_uat()

        return WeChatConfig(
            appid=appid,
            secret=secret,
            use_mock=use_mock
        )

    def _load_redis_config(self) -> RedisConfig:
        """加载Redis配置"""
        if EnvironmentHelper.is_unit():
            return RedisConfig(
                host='localhost',
                port=6379,
                db=0,
                password=None,
                use_fake=True
            )

        return RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD'),
            use_fake=False
        )

    def _load_token_secret(self) -> str:
        """加载JWT token密钥"""
        token_secret = os.getenv('TOKEN_SECRET')
        if not token_secret:
            if EnvironmentHelper.is_unit():
                # 单元测试环境使用默认值
                return 'test_token_secret_for_unit_tests'
            raise ValueError("TOKEN_SECRET 环境变量未设置或为空")
        return token_secret

    def _load_phone_encryption_key(self) -> str:
        """加载手机号加密密钥"""
        encryption_key = os.getenv('PHONE_ENCRYPTION_KEY')
        if not encryption_key:
            if EnvironmentHelper.is_unit():
                # 单元测试环境使用默认值
                return 'test_phone_encryption_key_for_unit_tests'
            raise ValueError("PHONE_ENCRYPTION_KEY 环境变量未设置或为空")
        return encryption_key


def load_config(env_type: str = None) -> AppConfig:
    """
    加载应用配置

    Args:
        env_type: 环境类型，如果不指定则从环境变量读取

    Returns:
        应用配置对象
    """
    loader = ConfigLoader(env_type)
    return loader.load()