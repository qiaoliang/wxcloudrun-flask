import os
from pathlib import Path


def load_env_file(env_file_path=".env"):
    """
    从指定的.env文件加载环境变量
    """
    env_path = Path(env_file_path)

    if env_path.is_file():
        with open(env_path, 'r') as file:
            for line in file:
                line = line.strip()
                # 跳过空行和注释行
                if line and not line.startswith('#'):
                    # 支持 KEY=VALUE 格式
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # 去除值中的注释（如果有）
                        if '#' in value:
                            value = value.split('#', 1)[0].strip()

                        # 去除值两端的引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # 只有当环境变量未设置时才使用默认值
                        if key not in os.environ:
                            os.environ[key] = value
                    elif line.strip():  # 如果行不为空但不包含=，可能是KEY=格式
                        os.environ[line] = ""


def get_env_with_defaults(defaults):
    """
    从环境变量获取值，如果未设置则使用默认值
    """
    env_vars = {}
    for key, default_value in defaults.items():
        env_vars[key] = os.environ.get(key, default_value)
    return env_vars