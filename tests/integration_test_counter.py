"""
计数器 API 集成测试模块：使用 docker-compose 启动开发环境并测试计数器 API 功能
"""
import os
import time
import requests
import subprocess
import pytest
from typing import Generator


@pytest.fixture(scope="module")
def docker_compose_env() -> Generator[str, None, None]:
    """
    启动 docker-compose 开发环境的 fixture
    """
    # 检查 docker-compose 文件是否存在
    if not os.path.exists("docker-compose.dev.yml"):
        pytest.skip("docker-compose.dev.yml 文件不存在，跳过集成测试")
    
    # 设置环境变量
    env_vars = {
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", "rootpassword"),
        "WX_APPID": os.environ.get("WX_APPID", "test_appid"),
        "WX_SECRET": os.environ.get("WX_SECRET", "test_secret"),
        "TOKEN_SECRET": os.environ.get("TOKEN_SECRET", "test_token_secret")
    }
    
    # 创建临时的 .env 文件
    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()])
    with open(".env.test", "w") as f:
        f.write(env_content)
    
    try:
        # 停止可能存在的服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 启动开发环境
        compose_process = subprocess.Popen([
            "docker-compose", "-f", "docker-compose.dev.yml", "up", "--build"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待服务启动
        base_url = "http://localhost:8080"
        if not wait_for_service(f"{base_url}/", timeout=180):
            raise RuntimeError("服务启动超时")
        
        # 等待 MySQL 服务完全准备就绪
        time.sleep(15)
        
        yield base_url  # 提供服务 URL 给测试用例
        
    finally:
        # 清理：停止 docker-compose 服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 删除临时 .env 文件
        if os.path.exists(".env.test"):
            os.remove(".env.test")


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """
    等待服务启动
    :param url: 服务 URL
    :param timeout: 超时时间（秒）
    :return: 是否成功连接
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


def test_get_initial_count(docker_compose_env: str):
    """
    测试 GET /api/count - 获取初始计数
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    response = requests.get(f"{base_url}/api/count")
    
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    assert isinstance(data['data'], int)
    print(f"初始计数: {data['data']}")


def test_post_count_inc(docker_compose_env: str):
    """
    测试 POST /api/count - 自增操作
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 首先获取初始计数
    response = requests.get(f"{base_url}/api/count")
    assert response.status_code == 200
    initial_data = response.json()
    assert initial_data['code'] == 1
    initial_count = initial_data['data']
    
    # 执行自增操作
    response = requests.post(
        f"{base_url}/api/count",
        json={"action": "inc"},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    assert isinstance(data['data'], int)
    incremented_count = data['data']
    
    # 验证自增结果
    assert incremented_count == initial_count + 1
    print(f"自增操作: {initial_count} -> {incremented_count}")


def test_post_count_clear(docker_compose_env: str):
    """
    测试 POST /api/count - 清零操作
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 执行清零操作
    response = requests.post(
        f"{base_url}/api/count",
        json={"action": "clear"},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    
    # 验证清零后状态
    response = requests.get(f"{base_url}/api/count")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    assert isinstance(data['data'], int)
    final_count = data['data']
    
    print(f"清零操作后计数: {final_count}")


def test_complete_counter_workflow(docker_compose_env: str):
    """
    测试完整的计数器工作流程
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 1. 获取初始计数
    response = requests.get(f"{base_url}/api/count")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    initial_count = data['data']
    
    # 2. 自增
    response = requests.post(
        f"{base_url}/api/count",
        json={"action": "inc"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    first_increment = data['data']
    assert first_increment == initial_count + 1
    
    # 3. 再次自增
    response = requests.post(
        f"{base_url}/api/count",
        json={"action": "inc"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    second_increment = data['data']
    assert second_increment == initial_count + 2
    
    # 4. 清零
    response = requests.post(
        f"{base_url}/api/count",
        json={"action": "clear"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    
    # 5. 验证清零后状态
    response = requests.get(f"{base_url}/api/count")
    assert response.status_code == 200
    data = response.json()
    assert data['code'] == 1
    final_count = data['data']
    
    print(f"完整工作流程: {initial_count} -> {first_increment} -> {second_increment} -> {final_count}")
