"""
SMS验证码发送集成测试
测试/api/sms/send_code端点，验证真实API行为
严格遵循测试反模式指南，避免测试mock行为
"""

import pytest
import json
import sys
import os
import time
from datetime import datetime, timedelta

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import VerificationCode, db
from .conftest import IntegrationTestBase


class TestSmsSendCodeIntegration(IntegrationTestBase):
    """SMS验证码发送集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 不需要预先创建数据，SMS API是独立的
            cls.test_phone_numbers = [
                '13800008001',
                '+8613800008002',
                '13900008003',
                '13800008888'
            ]

    def make_direct_request(self, method, endpoint, data=None):
        """直接发送请求（SMS API不需要认证）"""
        client = self.get_test_client()
        
        if data is not None:
            data = json.dumps(data)
            headers = {'content-type': 'application/json'}
        else:
            headers = {}
        
        return getattr(client, method.lower())(endpoint, data=data, headers=headers)

    def test_send_code_success_mock_environment(self):
        """测试在mock环境下成功发送验证码"""
        # 测试基本发送功能
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={'phone': self.test_phone_numbers[0]}
        )
        
        # 验证响应结构
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'data' in data
        
        response_data = data['data']
        assert 'message' in response_data
        assert '验证码发送成功（测试环境）' in response_data['message']
        assert 'code' in response_data  # 测试环境返回验证码
        
        # 验证验证码格式（6位数字）
        code = response_data['code']
        assert len(code) == 6
        assert code.isdigit()

    def test_send_code_with_purpose_parameter(self):
        """测试带有purpose参数的验证码发送"""
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={
                'phone': self.test_phone_numbers[1],
                'purpose': 'login'
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'code' in data['data']

    def test_send_code_default_purpose(self):
        """测试默认purpose参数（register）"""
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={'phone': self.test_phone_numbers[2]}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        # 验证数据库记录purpose为默认值
        with self.app.app_context():
            vc = VerificationCode.query.filter_by(
                phone_number=self.test_phone_numbers[2]
            ).first()
            assert vc is not None
            assert vc.purpose == 'register'

    def test_send_code_missing_phone_parameter(self):
        """测试缺少phone参数"""
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={}  # 空对象，缺少phone参数
        )
        
        # 验证错误响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert '缺少phone参数' in data['msg']

    def test_send_code_empty_phone_parameter(self):
        """测试phone参数为空"""
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={'phone': ''}  # 空字符串
        )
        
        # 验证错误响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert '缺少phone参数' in data['msg']

    def test_send_code_phone_number_normalization(self):
        """测试手机号标准化处理"""
        # 测试带+86前缀的手机号
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={'phone': '+8613800008002'}
        )
        
        # 验证响应成功
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        # 验证数据库中存储的是标准化后的手机号（无+86前缀）
        with self.app.app_context():
            vc = VerificationCode.query.filter_by(
                phone_number='13800008002'  # 标准化后的号码
            ).first()
            assert vc is not None

    def test_send_code_create_new_record(self):
        """测试创建新的验证码记录"""
        phone = self.test_phone_numbers[3]
        
        # 确保数据库中没有该手机的记录
        with self.app.app_context():
            existing_vc = VerificationCode.query.filter_by(
                phone_number=phone
            ).first()
            assert existing_vc is None
        
        # 发送验证码
        response = self.make_direct_request(
            'POST',
            '/api/sms/send_code',
            data={'phone': phone}
        )
        
        # 验证响应成功
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        # 验证数据库记录创建
        with self.app.app_context():
            vc = VerificationCode.query.filter_by(
                phone_number=phone
            ).first()
            assert vc is not None
            assert vc.phone_number == phone
            assert vc.purpose == 'register'  # 默认purpose
            assert vc.code_hash is not None
            assert vc.salt is not None
            assert vc.expires_at is not None
            assert vc.last_sent_at is not None
            assert not vc.is_used  # 默认未使用

