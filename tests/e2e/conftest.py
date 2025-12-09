"""
pytest配置文件
提供UAT Docker环境的fixture
"""

import os
import sys
import pytest
import subprocess
import time
import requests
import threading
from docker.errors import DockerException

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# UAT环境配置
UAT_CONTAINER_NAME = "s-uat-e2e-test"
UAT_IMAGE_NAME = "safeguard-uat-img"
UAT_PORT = 8080
UAT_HOST = "localhost"
UAT_BASE_URL = f"http://{UAT_HOST}:{UAT_PORT}"

# 并发测试管理
_concurrent_operations = 0
_concurrent_lock = threading.Lock()


@pytest.fixture(scope="session")
def uat_environment():
    """
    会话级别的fixture, 负责启动和停止UAT Docker环境
    """
    print("\n=== 启动UAT Docker环境 ===")
    
    # 检查Docker是否可用
    try:
        import docker
        client = docker.from_env()
        client.ping()
    except Exception as e:
        raise RuntimeError(f"Docker不可用: {str(e)}")
    
    # 停止并删除可能存在的同名容器
    try:
        subprocess.run(["docker", "stop", UAT_CONTAINER_NAME], 
                      capture_output=True, check=False)
        subprocess.run(["docker", "rm", UAT_CONTAINER_NAME], 
                      capture_output=True, check=False)
    except:
        pass
    
    # 启动UAT容器
    try:
        # 检查镜像是否存在
        result = subprocess.run(
            ["docker", "images", "-q", UAT_IMAGE_NAME],
            capture_output=True, text=True, check=True
        )
        if not result.stdout.strip():
            raise RuntimeError(f"Docker镜像 {UAT_IMAGE_NAME} 不存在，请先构建")
        
        # 启动容器
        subprocess.run([
            "docker", "run", "-d",
            "--name", UAT_CONTAINER_NAME,
            "-p", f"{UAT_PORT}:8080",
            "-e", "ENV_TYPE=uat",
            UAT_IMAGE_NAME
        ], check=True, capture_output=True)
        
        # 等待服务启动
        max_wait_time = 30  # 最大等待30秒
        wait_interval = 1   # 每秒检查一次
        service_ready = False
        
        for _ in range(max_wait_time):
            try:
                response = requests.get(f"{UAT_BASE_URL}/api/count", timeout=2)
                if response.status_code == 200:
                    service_ready = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(wait_interval)
        
        if not service_ready:
            # 获取容器日志用于调试
            logs = subprocess.run(
                ["docker", "logs", UAT_CONTAINER_NAME],
                capture_output=True, text=True
            ).stdout
            raise RuntimeError(
                f"UAT服务在{max_wait_time}秒内未能启动成功。\n"
                f"容器日志:\n{logs}"
            )
        
        print(f"✅ UAT环境已启动，访问地址: {UAT_BASE_URL}")
        
        yield UAT_BASE_URL
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"启动UAT容器失败: {str(e)}\n错误输出: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"启动UAT环境时发生错误: {str(e)}")
    
    finally:
        print("\n=== 清理UAT Docker环境 ===")
        # 停止并删除容器
        try:
            subprocess.run(["docker", "stop", UAT_CONTAINER_NAME], 
                          capture_output=True, check=False)
            subprocess.run(["docker", "rm", UAT_CONTAINER_NAME], 
                          capture_output=True, check=False)
            print("✅ UAT环境已清理")
        except Exception as e:
            print(f"⚠️ 清理UAT环境时发生错误: {str(e)}")


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
def cleanup_test_data(uat_environment):
    """
    自动使用的fixture, 在每个测试后清理数据
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
        response = requests.post(
            f"{uat_environment}/api/count",
            json={"action": "clear"},
            timeout=5
        )
        if response.status_code != 200:
            print(f"⚠️ 清理测试数据失败: {response.text}")
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