"""
端到端测试：环境配置 API
测试启动 Flask 应用并访问 http://localhost:9999/env 端点
"""

import os
import sys
import time
import signal
import subprocess
import requests
import pytest


class TestEnvAPIE2E:
    """环境配置 API 端到端测试"""

    def test_env_endpoint_returns_200(self, base_url):
        """测试 /env 端点返回 200 状态码"""
        # 发送请求到 /env 端点
        response = requests.get(f'{base_url}/env', timeout=10)
        
        # 验证响应状态码
        assert response.status_code == 200, f"期望状态码 200，实际得到 {response.status_code}"
        
        # 验证响应内容包含环境配置查看器页面
        assert '环境配置查看器' in response.text, "响应内容应包含环境配置查看器页面"
        
        print("✓ /env 端点返回 200 状态码")

    def test_env_api_endpoint_returns_200(self, base_url):
        """测试 /api/get_envs API 端点返回 200 状态码"""
        # 发送请求到 /api/get_envs 端点
        response = requests.get(f'{base_url}/api/get_envs', timeout=10)
        
        # 验证响应状态码
        assert response.status_code == 200, f"期望状态码 200，实际得到 {response.status_code}"
        
        # 验证响应是有效的 JSON
        response_data = response.json()
        assert response_data['code'] == 1, "API 应返回成功状态"
        assert 'data' in response_data, "响应应包含 data 字段"
        
        # 验证环境配置数据
        env_data = response_data['data']
        assert 'environment' in env_data, "环境配置应包含 environment 字段"
        assert 'variables' in env_data, "环境配置应包含 variables 字段"
        
        print("✓ /api/get_envs 端点返回 200 状态码并包含有效数据")

    def test_env_api_toml_format(self, base_url):
        """测试 /api/get_envs 端点支持 TOML 格式输出"""
        # 发送请求请求 TOML 格式
        response = requests.get(
            f'{base_url}/api/get_envs?format=toml', 
            timeout=10,
            headers={'Accept': 'text/plain'}
        )
        
        # 验证响应状态码
        assert response.status_code == 200, f"期望状态码 200，实际得到 {response.status_code}"
        
        # 验证响应内容类型
        content_type = response.headers.get('Content-Type', '')
        assert 'text/plain' in content_type, f"TOML 格式应返回 text/plain 内容类型，实际得到: {content_type}"
        
        # 验证响应内容包含环境配置信息
        content = response.text
        assert len(content) > 0, "响应内容不应为空"
        
        # 检查是否包含环境配置相关内容（更宽松的检查）
        has_env_info = ('environment' in content.lower() or 
                       '环境' in content or 
                       'env' in content.lower())
        assert has_env_info, "响应内容应包含环境配置信息"
        
        print("✓ /api/get_envs 端点成功返回 TOML 格式数据")
        
        print("✓ /api/get_envs 端点成功返回 TOML 格式数据")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
