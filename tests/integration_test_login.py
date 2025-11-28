"""
登录 API 集成测试模块：使用统一的 docker-compose 环境并测试登录 API 功能
"""
import os
import time
import requests
import subprocess
import pytest
import jwt
from unittest.mock import patch


@pytest.mark.integration
def test_login_api_with_real_wx_api(docker_compose_env: str):
    """
    使用真实微信API测试登录 API
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 获取环境变量中的真实微信凭证
    wx_appid = os.environ.get("WX_APPID")
    wx_secret = os.environ.get("WX_SECRET")
    
    # 检查是否在手动测试模式下运行（使用真实微信凭证）
    is_manual_test = os.environ.get("USE_REAL_WECHAT_CREDENTIALS", "").lower() == "true"
    
    # 在自动测试环境中，如果未配置真实凭证则跳过测试
    if not is_manual_test and (not wx_appid or not wx_secret or "test" in wx_appid.lower() or "test" in wx_secret.lower()):
        # 如果没有配置真实凭证，在自动测试中跳过此测试
        print("自动测试模式：未配置真实的微信凭证，跳过真实API测试")
        pytest.skip("未配置真实的微信凭证")
    
    # 在手动测试模式下，如果没有配置真实凭证则抛出错误
    if is_manual_test and (not wx_appid or not wx_secret or "test" in wx_appid.lower() or "test" in wx_secret.lower()):
        # 在手动测试中，如果未配置真实凭证则失败测试
        pytest.fail("手动测试模式：未配置真实的微信凭证 (WX_APPID 或 WX_SECRET)")
    
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


@pytest.mark.integration
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
