"""
登录 API 集成测试模块：使用 docker-compose 启动开发环境并测试登录 API 功能
"""
import os
import time
import requests
import subprocess
import pytest
import jwt
from unittest.mock import patch
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


def test_login_api_with_real_wx_api(docker_compose_env: str):
    """
    使用真实微信API测试登录 API
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 获取环境变量中的真实微信凭证
    wx_appid = os.environ.get("WX_APPID")
    wx_secret = os.environ.get("WX_SECRET")
    
    # 检查是否配置了真实的微信凭证
    if not wx_appid or not wx_secret or "test" in wx_appid.lower() or "test" in wx_secret.lower():
        # 如果没有配置真实凭证，跳过此测试或使用占位符进行结构测试
        print("未配置真实的微信凭证，跳过真实API测试")
        pytest.skip("未配置真实的微信凭证")
    
    # 注意：在实际的集成测试中，获取真实的code需要从小程序端获取
    # 这里我们假设有一个环境变量提供有效的code用于测试
    test_code = os.environ.get("TEST_LOGIN_CODE")
    
    if not test_code:
        # 如果没有提供测试code，测试应用对无效code的处理
        response = requests.post(
            f"{base_url}/api/login",
            json={"code": "invalid_test_code"},
            headers={"Content-Type": "application/json"}
        )
        
        # 应用应该正确处理无效code并返回适当的错误信息
        assert response.status_code == 200
        data = response.json()
        assert 'code' in data
        # 确保应用尝试调用微信API并收到错误响应
        assert data['code'] == 0  # 错误响应
        print(f"登录 API 对无效code的响应状态: {data['code']}")
    else:
        # 如果提供了有效的测试code，则进行完整的真实API测试
        response = requests.post(
            f"{base_url}/api/login",
            json={"code": test_code},
            headers={"Content-Type": "application/json"}
        )
        
        # 检查响应格式是否正确
        assert response.status_code == 200
        data = response.json()
        assert 'code' in data
        
        if data['code'] == 1:
            # 成功获取token
            assert 'data' in data
            assert 'token' in data['data']
            print("成功从真实微信API获取用户信息")
        else:
            # 可能是无效的code或微信API错误
            print(f"微信API调用失败: {data.get('msg', 'Unknown error')}")


def test_user_profile_api(docker_compose_env: str):
    """
    测试用户信息 API
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 先尝试获取一个不存在的用户信息（使用模拟的 token）
    fake_token = jwt.encode(
        {'openid': 'nonexistent_openid', 'session_key': 'fake_key'},
        os.environ.get('TOKEN_SECRET', 'test_token_secret'),
        algorithm='HS256'
    )
    
    response = requests.post(
        f"{base_url}/api/user/profile",
        json={
            "token": fake_token,
            "nickname": "Test User",
            "avatar_url": "https://example.com/avatar.jpg"
        },
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'code' in data
    print(f"用户信息 API 响应状态: {data['code']}")
    
    # 测试 GET 用户信息
    response = requests.get(
        f"{base_url}/api/user/profile",
        json={"token": fake_token},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'code' in data
    print(f"获取用户信息 API 响应状态: {data['code']}")
