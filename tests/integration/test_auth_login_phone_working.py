"""
可工作的手机号登录API快照对比集成测试
"""

import pytest
import json
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community


class TestAuthLoginPhoneWorking:
    """可工作的手机号登录API测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        # 设置测试环境变量
        os.environ['ENV_TYPE'] = 'unit'
        os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'
        
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
        from hashlib import sha256
        
        # 设置phone_secret以匹配UserService中的哈希算法
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_number = '13900007997'
        phone_hash = sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()
        
        # 创建测试用户
        cls.test_user = User(
            wechat_openid='test_working_user',
            phone_number=phone_number,
            phone_hash=phone_hash,  # 关键：设置phone_hash字段
            nickname='测试用户',
            name='测试用户',
            role=1,  # 普通用户
            status=1,
            password_salt='test_salt'
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
        test_password = "Firefox0820"
        cls.test_user.password_hash = sha256(f"{test_password}:{cls.test_user.password_salt}".encode('utf-8')).hexdigest()
        
        cls.db.session.commit()
        
        print(f"✅ 创建测试用户: user_id={cls.test_user.user_id}")
        print(f"✅ phone_number: {cls.test_user.phone_number}")
        print(f"✅ phone_hash: {cls.test_user.phone_hash[:20]}...")
        print(f"✅ community_id: {cls.test_user.community_id}")
        print(f"✅ TOKEN_SECRET: {os.getenv('TOKEN_SECRET')[:20]}...")
    
    def get_test_client(self):
        """获取测试客户端"""
        return self.app.test_client()
    
    def test_login_phone_snapshot_success(self):
        """测试登录API快照对比成功案例"""
        client = self.get_test_client()
        
        login_data = {
            'phone': '13900007997',
            'code': '123456',  # 测试验证码
            'password': 'Firefox0820'
        }
        
        # 发送登录请求
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        print(f"📱 登录响应状态码: {response.status_code}")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证基本响应结构
        assert data['code'] == 1
        assert data['msg'] == 'success'
        assert 'data' in data
        
        response_data = data['data']
        print(f"📋 完整响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        # 定义预期快照数据（排除动态字段）
        expected_snapshot = {
            'user_id': self.test_user.user_id,
            'wechat_openid': self.test_user.wechat_openid,
            'phone_number': self.test_user.phone_number,
            'nickname': self.test_user.nickname,
            'name': self.test_user.name,
            'avatar_url': self.test_user.avatar_url,
            'role': '普通用户',  # role=1 对应的角色名
            'community_id': self.test_community.community_id,
            'community_name': self.test_community.name,
            'status': self.test_user.status,
            'login_type': 'existing_user'
        }
        
        # 执行快照对比
        mismatches = []
        matched_fields = []
        
        for key, expected_value in expected_snapshot.items():
            if key not in response_data:
                mismatches.append(f"❌ 缺少字段: {key}")
            elif response_data[key] != expected_value:
                mismatches.append(f"❌ 字段 {key} 不匹配: 期望 '{expected_value}', 实际 '{response_data[key]}'")
            else:
                matched_fields.append(f"✅ {key}")
        
        # 验证动态字段存在
        dynamic_fields = ['token', 'refresh_token']
        for field in dynamic_fields:
            if field not in response_data:
                mismatches.append(f"❌ 缺少动态字段: {field}")
            else:
                matched_fields.append(f"✅ {field} (存在)")
        
        # 输出匹配结果
        print(f"\n📊 快照对比结果:")
        print(f"✅ 匹配字段 ({len(matched_fields)}): {', '.join(matched_fields)}")
        if mismatches:
            print(f"❌ 不匹配字段 ({len(mismatches)}): {'; '.join(mismatches)}")
        
        # 断言无不匹配项
        assert not mismatches, f"快照对比失败，发现 {len(mismatches)} 个不匹配项"
        
        # 验证数据类型正确性
        assert isinstance(response_data['user_id'], int)
        assert isinstance(response_data['community_id'], int)
        assert isinstance(response_data['role'], str)
        assert isinstance(response_data['login_type'], str)
        
        print(f"\n🎉 快照对比测试完全通过！")
        print(f"📈 数据一致性: 100% ({len(matched_fields)}/{len(expected_snapshot) + len(dynamic_fields)} 字段匹配)")
    
    def test_login_phone_error_cases(self):
        """测试登录API错误情况的数据一致性"""
        client = self.get_test_client()
        
        # 测试用例：错误的验证码
        error_cases = [
            {
                'name': '错误验证码',
                'data': {'phone': '13900007997', 'code': '999999', 'password': 'Firefox0820'},
                'expected_code': 0,
                'expected_msg_key': '验证码无效或已过期'
            },
            {
                'name': '错误密码',
                'data': {'phone': '13900007997', 'code': '123456', 'password': 'wrong_password'},
                'expected_code': 0,
                'expected_msg_key': '密码不正确'
            },
            {
                'name': '缺少参数',
                'data': {'phone': '13900007997', 'code': '123456'},  # 缺少password
                'expected_code': 0,
                'expected_msg_key': '缺少phone、code或password参数'
            }
        ]
        
        for case in error_cases:
            print(f"\n🧪 测试错误情况: {case['name']}")
            
            response = client.post('/api/auth/login_phone',
                                 data=json.dumps(case['data']),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # 验证错误响应结构
            assert data['code'] == case['expected_code']
            assert case['expected_msg_key'] in data['msg']
            assert 'data' in data
            
            print(f"✅ {case['name']} 错误响应验证通过: {data['msg']}")
    
    def test_login_phone_super_admin_role(self):
        """测试超级管理员角色的数据一致性"""
        # 创建超级管理员用户
        from hashlib import sha256
        
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_number = '13900007998'
        phone_hash = sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()
        
        super_admin = User(
            wechat_openid='test_super_admin',
            phone_number=phone_number,
            phone_hash=phone_hash,
            nickname='超级管理员',
            name='超级管理员',
            role=4,  # 超级系统管理员
            status=1,
            password_salt='admin_salt',
            password_hash=sha256(f"Firefox0820:admin_salt".encode('utf-8')).hexdigest(),
            community_id=self.test_community.community_id
        )
        self.db.session.add(super_admin)
        self.db.session.commit()
        
        try:
            client = self.get_test_client()
            
            login_data = {
                'phone': phone_number,
                'code': '123456',
                'password': 'Firefox0820'
            }
            
            response = client.post('/api/auth/login_phone',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            response_data = data['data']
            
            # 验证超级管理员角色一致性
            assert response_data['role'] == '超级系统管理员'
            assert response_data['nickname'] == '超级管理员'
            assert response_data['user_id'] == super_admin.user_id
            
            print(f"✅ 超级管理员角色验证通过")
            print(f"👤 角色: {response_data['role']}")
            print(f"🆔 用户ID: {response_data['user_id']}")
            
        finally:
            # 清理测试用户
            self.db.session.delete(super_admin)
            self.db.session.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
