"""
简化的手机号登录API快照对比集成测试
"""

import pytest
import json
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community


class TestAuthLoginPhoneSimple:
    """简化的手机号登录API测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        os.environ['ENV_TYPE'] = 'unit'
        
        from app import create_app
        from app.extensions import db
        
        cls.app = create_app()
        cls.db = db
        
        with cls.app.app_context():
            cls.db.create_all()
            cls._create_test_data()
    
    @classmethod
    def teardown_class(cls):
        """类级别的清理"""
        with cls.app.app_context():
            cls.db.drop_all()
    
    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        # 创建测试用户
        cls.test_user = User(
            wechat_openid='test_simple_user',
            phone_number='13900007997',
            nickname='测试用户',
            name='测试用户',
            role=1,  # 普通用户
            status=1,
            password_salt='test_salt',
            password_hash='test_hash'
        )
        cls.db.session.add(cls.test_user)
        
        # 创建测试社区
        cls.test_community = Community(
            name='测试社区',
            description='用于测试的社区',
            creator_id=cls.test_user.user_id
        )
        cls.db.session.add(cls.test_community)
        
        cls.db.session.flush()
        
        # 建立用户-社区关系
        cls.test_user.community_id = cls.test_community.community_id
        
        # 设置密码哈希
        from hashlib import sha256
        test_password = "Firefox0820"
        cls.test_user.password_hash = sha256(f"{test_password}:{cls.test_user.password_salt}".encode('utf-8')).hexdigest()
        
        cls.db.session.commit()
    
    def get_test_client(self):
        """获取测试客户端"""
        return self.app.test_client()
    
    def test_login_phone_basic(self):
        """测试基本的手机号登录功能"""
        client = self.get_test_client()
        
        login_data = {
            'phone': '13900007997',
            'code': '123456',  # 测试验证码
            'password': 'Firefox0820'
        }
        
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证基本响应结构
        assert data['code'] == 1
        assert data['msg'] == 'success'
        assert 'data' in data
        
        # 验证关键字段
        response_data = data['data']
        assert 'user_id' in response_data
        assert 'phone_number' in response_data
        assert 'nickname' in response_data
        assert 'role' in response_data
        assert 'community_id' in response_data
        assert 'community_name' in response_data
        
        # 验证数据一致性
        assert response_data['user_id'] == self.test_user.user_id
        assert response_data['phone_number'] == self.test_user.phone_number
        assert response_data['nickname'] == self.test_user.nickname
        assert response_data['role'] == '普通用户'  # role=1 对应的角色名
        assert response_data['community_id'] == self.test_community.community_id
        assert response_data['community_name'] == self.test_community.name
        
        print("✅ 基本手机号登录测试通过")
        print(f"用户ID: {response_data['user_id']}")
        print(f"角色: {response_data['role']}")
        print(f"社区: {response_data['community_name']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])