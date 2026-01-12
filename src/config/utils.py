"""
配置工具类
提供环境判断等辅助功能
"""
import os


class EnvironmentHelper:
    """环境辅助类"""

    ENV_FILE_MAPPING = {
        'unit': '.env.unit',
        'dev': '.env.dev',
        'func': '.env.function',
        'function': '.env.function',
        'uat': '.env.uat',
        'prod': '.env.prod'
    }

    @staticmethod
    def get_env_type() -> str:
        """获取当前环境类型"""
        return os.getenv('ENV_TYPE', 'unit')

    @staticmethod
    def get_env_file() -> str:
        """获取环境配置文件路径"""
        env_type = EnvironmentHelper.get_env_type()
        return EnvironmentHelper.ENV_FILE_MAPPING.get(env_type, '.env.unit')

    @staticmethod
    def is_production() -> bool:
        """是否为生产环境"""
        return EnvironmentHelper.get_env_type() == 'prod'

    @staticmethod
    def is_uat() -> bool:
        """是否为UAT环境"""
        return EnvironmentHelper.get_env_type() == 'uat'

    @staticmethod
    def is_unit() -> bool:
        """是否为单元测试环境"""
        return EnvironmentHelper.get_env_type() == 'unit'

    @staticmethod
    def is_function() -> bool:
        """是否为功能测试环境"""
        env_type = EnvironmentHelper.get_env_type()
        return env_type in ['func', 'function']

    @staticmethod
    def is_debug_mode() -> bool:
        """是否为调试模式"""
        env_type = EnvironmentHelper.get_env_type()
        return env_type in ['function', 'uat']

    @staticmethod
    def is_running_in_docker() -> bool:
        """检测是否在 Docker 容器中运行"""
        # 方法1: 检查 /.dockerenv 文件是否存在
        if os.path.exists('/.dockerenv'):
            return True

        # 方法2: 检查 /proc/1/cgroup 文件
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup_content = f.read()
                if 'docker' in cgroup_content or 'kubepods' in cgroup_content:
                    return True
        except (FileNotFoundError, PermissionError):
            pass

        return False