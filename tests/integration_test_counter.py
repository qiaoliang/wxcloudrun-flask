"""
计数器 API 集成测试模块：使用统一的 docker-compose 环境并测试计数器 API 功能
"""
import os
import time
import requests
import subprocess
import pytest


@pytest.mark.integration
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