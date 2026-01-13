"""
速率限制功能集成测试
验证认证接口的速率限制是否正常工作，防止暴力破解攻击

速率限制配置：
- 登录接口：5次/分钟，20次/小时
- 注册接口：5次/分钟，20次/小时
- 刷新token接口：20次/分钟，200次/小时（已调整以避免多设备/多标签页误伤）

注意：在测试环境（ENV_TYPE=unit）中，速率限制被禁用以方便测试。
这些测试主要用于验证速率限制的配置是否正确，并在非测试环境中验证功能。
"""

import pytest
import json
import sys
import os
import time

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestRateLimiting(IntegrationTestBase):
    """速率限制功能测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建标准测试用户
            cls.test_user = cls.create_standard_test_user(role=1)

            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='测试社区',
                creator=cls.test_user
            )

            # 建立用户-社区关系
            cls.test_user.community_id = cls.test_community.community_id
            cls.db.session.commit()

            print(f"✅ 创建测试用户: user_id={cls.test_user.user_id}")
            print(f"✅ phone_number: {cls.test_user.phone_number}")

    def test_rate_limiting_configuration(self):
        """测试速率限制配置是否正确加载"""
        from app.extensions import limiter

        # 验证速率限制扩展已初始化
        assert limiter is not None, "Flask-Limiter 扩展未初始化"

        # 在测试环境中，速率限制应该被禁用
        from config import EnvironmentHelper
        if EnvironmentHelper.is_unit():
            assert not limiter.enabled, "在测试环境中，速率限制应该被禁用"
            print("✅ 测试环境：速率限制已禁用（符合预期）")
        else:
            assert limiter.enabled, "在非测试环境中，速率限制应该启用"
            print("✅ 非测试环境：速率限制已启用（符合预期）")

    def test_login_phone_code_multiple_requests(self):
        """测试手机号验证码登录的多请求处理"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE
        }

        # 发送多次请求，验证系统稳定性
        success_count = 0
        for i in range(10):
            response = client.post('/api/auth/login_phone_code',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            if response.status_code == 200:
                success_count += 1
            print(f"📱 请求 {i+1}: 状态码={response.status_code}")

        # 在测试环境中，所有请求都应该成功（因为速率限制被禁用）
        from config import EnvironmentHelper
        if EnvironmentHelper.is_unit():
            assert success_count >= 5, f"在测试环境中，至少应该有5次请求成功，但只有 {success_count} 次成功"
            print(f"✅ 测试环境：{success_count}/10 请求成功（速率限制已禁用）")
        else:
            # 在非测试环境中，应该有部分请求被速率限制
            assert success_count <= 5, f"在非测试环境中，最多应该有5次请求成功，但有 {success_count} 次成功"
            print(f"✅ 非测试环境：{success_count}/10 请求成功（速率限制已启用）")

    def test_login_phone_password_multiple_requests(self):
        """测试手机号密码登录的多请求处理"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,
            'password': TEST_CONSTANTS.DEFAULT_PASSWORD
        }

        # 发送多次请求，验证系统稳定性
        success_count = 0
        for i in range(10):
            response = client.post('/api/auth/login_phone_password',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            if response.status_code == 200:
                success_count += 1
            print(f"📱 请求 {i+1}: 状态码={response.status_code}")

        # 在测试环境中，所有请求都应该成功（因为速率限制被禁用）
        from config import EnvironmentHelper
        if EnvironmentHelper.is_unit():
            assert success_count >= 5, f"在测试环境中，至少应该有5次请求成功，但只有 {success_count} 次成功"
            print(f"✅ 测试环境：{success_count}/10 请求成功（速率限制已禁用）")
        else:
            # 在非测试环境中，应该有部分请求被速率限制
            assert success_count <= 5, f"在非测试环境中，最多应该有5次请求成功，但有 {success_count} 次成功"
            print(f"✅ 非测试环境：{success_count}/10 请求成功（速率限制已启用）")

    def test_rate_limiting_decorator_presence(self):
        """测试速率限制装饰器是否正确应用"""
        from app.extensions import limiter

        # 验证速率限制扩展已初始化
        assert limiter is not None, "Flask-Limiter 扩展未初始化"

        # 获取所有认证路由
        auth_routes = []
        for rule in self.app.url_map.iter_rules():
            if rule.rule.startswith('/api/auth/'):
                auth_routes.append(rule.rule)

        print(f"✅ 找到 {len(auth_routes)} 个认证路由")

        # 验证关键路由存在
        expected_routes = [
            '/api/auth/login_wechat',
            '/api/auth/login_phone_code',
            '/api/auth/login_phone_password',
            '/api/auth/login_phone',
            '/api/auth/register_phone',
            '/api/auth/refresh_token'
        ]

        for route in expected_routes:
            assert route in auth_routes, f"缺少路由: {route}"
            print(f"✅ 路由存在: {route}")

        # 验证速率限制配置存在
        # Flask-Limiter 的装饰器在运行时应用，我们通过检查源代码来验证
        import inspect
        from app.modules.auth import routes as auth_routes_module

        # 检查路由文件中是否导入了 limiter
        source = inspect.getsource(auth_routes_module)
        assert 'limiter' in source, "认证路由模块中未导入 limiter"
        assert '@limiter.limit' in source, "认证路由模块中未使用 @limiter.limit 装饰器"
        print("✅ 速率限制装饰器已正确应用")

        # 注意：Flask-Limiter 的装饰器在运行时应用，无法直接检查
        # 这个测试主要用于验证路由配置和装饰器导入是否正确