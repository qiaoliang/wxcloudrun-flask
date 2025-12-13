"""
pytest配置文件
提供本地 Flask 测试环境的 fixture
"""

import os
import sys
import pytest
import subprocess
import time
import requests
import threading
import jwt
import datetime
import socket
import uuid
import tempfile
from typing import Optional

import logging

# 全局日志配置（可放在 conftest.py 或测试文件开头）
# logging.basicConfig(
#     level=logging.DEBUG,  # 开启 DEBUG 级别输出
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 包含级别标识
#     handlers=[
#         logging.StreamHandler(),  # 输出到控制台
#         logging.FileHandler("test_debug.log", encoding="utf-8")  # 可选：输出到日志文件
#     ]
# )

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# 并发测试管理
_concurrent_operations = 0
_concurrent_lock = threading.Lock()


def get_free_port() -> int:
    """
    获取一个可用的端口号

    Returns:
        int: 可用的端口号
    """
    with socket.create_server(('localhost', 0)) as s:
        return s.getsockname()[1]


@pytest.fixture(scope="function")
def test_server():
    """
    函数级别的fixture，为每个测试函数启动独立的 Flask 进程
    """
    print("\n=== 启动 Flask 测试服务器 ===")

    # 动态分配端口
    port = get_free_port()
    base_url = f"http://localhost:{port}"

    # 设置环境变量
    env = os.environ.copy()
    env['ENV_TYPE'] = 'unit'  # 使用 unit 环境但使用文件数据库
    # 使用临时文件数据库而不是内存数据库，确保数据在同一进程内持久化
    temp_db = tempfile.mktemp(suffix='.db')
    env['SQLITE_DB_PATH'] = temp_db
    env['PYTHONPATH'] = os.path.join(project_root, 'src')
    
    # 启动 Flask 进程
    process = None
    try:
        # 启动进程
        process = subprocess.Popen(
            [sys.executable, 'main.py', 'localhost', str(port)],
            cwd=os.path.join(project_root, 'src'),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    # 等待服务启动
        max_wait_time = 30  # 最大等待30秒
        wait_interval = 1   # 每秒检查一次
        service_ready = False

        for _ in range(max_wait_time):
            try:
                response = requests.get(f"{base_url}/api/count", timeout=2)
                if response.status_code == 200:
                    service_ready = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(wait_interval)

        if not service_ready:
            # 获取进程输出用于调试
            stdout, stderr = process.communicate(timeout=1)
            raise RuntimeError(
                f"Flask 服务在{max_wait_time}秒内未能启动成功。\n"
                f"端口: {port}\n"
                f"进程输出:\n{stdout}\n"
                f"错误输出:\n{stderr}"
            )

        print(f"✅ Flask 服务器已启动，访问地址: {base_url}")

        yield base_url

    except Exception as e:
        raise RuntimeError(f"启动 Flask 服务器失败: {str(e)}")

    finally:
        print("\n=== 清理 Flask 测试服务器 ===")
        # 清理进程
        if process:
            try:
                # 尝试优雅终止
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 如果优雅终止失败，强制杀死
                    process.kill()
                    process.wait()
                print("✅ Flask 服务器已清理")
            except Exception as e:
                print(f"⚠️ 清理 Flask 服务器时发生错误: {str(e)}")
        
        # 清理临时数据库文件
        if 'temp_db' in locals():
            try:
                import os
                if os.path.exists(temp_db):
                    os.unlink(temp_db)
                    print(f"✅ 临时数据库文件已清理: {temp_db}")
            except Exception as e:
                print(f"⚠️ 清理临时数据库文件时发生错误: {str(e)}")


def _increment_concurrent_operations():
    """增加并发操作计数"""
    global _concurrent_operations
    with _concurrent_lock:
        _concurrent_operations += 1
        return _concurrent_operations


def _decrement_concurrent_operations():
    """减少并发操作计数"""
    global _concurrent_operations
    with _concurrent_lock:
        _concurrent_operations -= 1
        return _concurrent_operations


def _has_concurrent_operations():
    """检查是否有活跃的并发操作"""
    global _concurrent_operations
    with _concurrent_lock:
        return _concurrent_operations > 0


@pytest.fixture(autouse=True)
def cleanup_test_data(test_server: str):
    """
    自动使用的fixture，在每个测试后清理数据
    智能处理并发测试，避免在并发操作期间清理数据
    """
    # 测试前不需要特殊操作
    yield

    # 测试后清理计数器数据
    # 如果有活跃的并发操作，等待它们完成
    max_wait_time = 10  # 最大等待10秒
    wait_interval = 0.1  # 每100ms检查一次

    waited_time = 0
    while _has_concurrent_operations() and waited_time < max_wait_time:
        time.sleep(wait_interval)
        waited_time += wait_interval

    if _has_concurrent_operations():
        print(f"⚠️ 等待{max_wait_time}秒后仍有并发操作，强制清理数据")

    try:
        # 清理计数器数据
        response = requests.post(
            f"{test_server}/api/count",
            json={"action": "clear"},
            timeout=5
        )
        if response.status_code != 200:
            print(f"⚠️ 清理计数器数据失败: {response.text}")

        # 清理所有用户数据（通过直接访问数据库）
        # 这是一个测试环境的特殊清理操作
        clear_response = requests.post(
            f"{test_server}/api/count",
            json={"action": "clear_users"},
            timeout=5
        )
        # 如果清理用户的接口不存在，我们忽略错误（因为这是测试专用的）
        if clear_response.status_code != 200:
            print(f"⚠️ 清理用户数据接口不存在或失败（这是正常的）")
    except Exception as e:
        print(f"⚠️ 清理测试数据时发生错误: {str(e)}")


@pytest.fixture
def concurrent_context():
    """
    并发测试上下文fixture
    在并发测试中使用，标记并发操作的开始和结束
    """
    _increment_concurrent_operations()
    yield
    _decrement_concurrent_operations()


@pytest.fixture
def valid_token():
    """
    生成有效的JWT token fixture
    默认使用mock环境的openid和user_id
    """
    # 获取TOKEN_SECRET
    try:
        from config_manager import get_token_secret
        token_secret = get_token_secret()
    except (ImportError, ValueError):
        # 如果无法导入或获取TOKEN_SECRET，使用默认值
        token_secret = os.getenv('TOKEN_SECRET', 'default_token_secret_for_testing')

    # 创建token payload
    payload = {
        'openid': 'mock_openid_fixed_for_testing',
        'user_id': 1,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)
    }

    # 生成token
    token = jwt.encode(payload, token_secret, algorithm='HS256')
    return token


@pytest.fixture
def auth_headers(valid_token: str):
    """
    生成包含认证头的请求头字典fixture
    自动使用valid_token fixture生成的token
    """
    return {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def custom_token():
    """
    生成自定义参数的JWT token fixture
    可用于测试特定用户或不同过期时间的场景
    """
    def _generate_token(openid="mock_openid_fixed_for_testing", user_id=1, hours=2):
        # 获取TOKEN_SECRET
        try:
            from config_manager import get_token_secret
            token_secret = get_token_secret()
        except (ImportError, ValueError):
            token_secret = os.getenv('TOKEN_SECRET', 'default_token_secret_for_testing')

        # 创建token payload
        payload = {
            'openid': openid,
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=hours)
        }

        # 生成token
        token = jwt.encode(payload, token_secret, algorithm='HS256')
        return token

    return _generate_token

