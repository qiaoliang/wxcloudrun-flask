"""
测试基类
封装Flask-SQLAlchemy的测试上下文管理，提供统一的测试基础设施
"""

import pytest
import os
import sys
import json
from hashlib import sha256
from unittest.mock import patch

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)


class TestBase:
    """测试基类，封装Flask-SQLAlchemy测试上下文管理"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置，创建应用实例"""
        # 设置测试环境
        os.environ['ENV_TYPE'] = 'unit'
        os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
        
        # 导入并创建Flask应用
        from app import create_app
        from app.extensions import db
        
        cls.app = create_app()
        cls.db = db
        
        # 在应用上下文中初始化数据库
        with cls.app.app_context():
            # 创建所有表
            cls.db.create_all()
            
            # 创建初始数据
            cls._create_initial_data()
    
    @classmethod
    def teardown_class(cls):
        """类级别的清理"""
        with cls.app.app_context():
            # 删除所有表
            cls.db.drop_all()
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        # 在应用上下文中开始事务
        with self.app.app_context():
            self.db.session.begin_nested()
    
    def teardown_method(self, method):
        """每个测试方法后的清理"""
        # 回滚事务，确保测试隔离
        with self.app.app_context():
            self.db.session.rollback()
    
    @classmethod
    def _create_initial_data(cls):
        """创建测试所需的初始数据"""
        from database.flask_models import User, Community
        
        # 创建测试用户
        test_user = User(
            wechat_openid='test_openid_123',
            phone_hash='test_phone_hash',
            nickname='测试用户',
            avatar_url='https://example.com/avatar.jpg',
            role=1  # 普通用户角色
        )
        cls.db.session.add(test_user)
        
        # 创建测试社区
        test_community = Community(
            name='测试社区',
            description='用于测试的社区',
            creator_id=test_user.user_id
        )
        cls.db.session.add(test_community)
        
        cls.db.session.commit()
        
        # 保存测试数据供子类使用
        cls.test_user = test_user
        cls.test_community = test_community
    
    def get_test_client(self):
        """获取测试客户端"""
        return self.app.test_client()
    
    def get_db_session(self):
        """获取数据库会话"""
        return self.db.session
    
    # ==================== 测试数据工厂 ====================
    
    @staticmethod
    def generate_phone_hash(phone_number):
        """生成手机号哈希"""
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        return sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_password_hash(password, salt):
        """生成密码哈希"""
        return sha256(f"{password}:{salt}".encode('utf-8')).hexdigest()
    
    @classmethod
    def create_test_user(cls, phone_number=None, role=1, suffix=None, **kwargs):
        """创建测试用户的增强方法"""
        from database.flask_models import User
        
        if phone_number is None:
            phone_number = f'1390000{suffix or "0000"}'
        
        if suffix is None:
            suffix = str(role) + phone_number[-4:]
        
        default_data = {
            'wechat_openid': f'test_openid_{suffix}',
            'phone_number': phone_number,
            'phone_hash': cls.generate_phone_hash(phone_number),
            'nickname': f'测试用户_{suffix}',
            'name': f'测试用户_{suffix}',
            'avatar_url': 'https://example.com/avatar.jpg',
            'role': role,
            'status': 1,
            'password_salt': f'test_salt_{suffix}',
        }
        default_data.update(kwargs)
        
        # 设置密码哈希
        if 'password' in default_data:
            default_data['password_hash'] = cls.generate_password_hash(
                default_data.pop('password'), default_data['password_salt']
            )
        
        user = User(**default_data)
        cls.db.session.add(user)
        cls.db.session.commit()
        return user
    
    @classmethod
    def create_test_community(cls, name=None, creator=None, **kwargs):
        """创建测试社区的增强方法"""
        from database.flask_models import Community
        
        if name is None:
            name = f'测试社区_{kwargs.get("suffix", "default")}'
        
        if creator is None:
            creator = cls.test_user
        
        default_data = {
            'name': name,
            'description': f'用于测试的社区：{name}',
            'creator_id': creator.user_id
        }
        default_data.update(kwargs)
        
        community = Community(**default_data)
        cls.db.session.add(community)
        cls.db.session.commit()
        return community
    
    # ==================== API 测试工具 ====================
    
    def get_jwt_token(self, phone_number='13900000000', password='Firefox0820'):
        """获取JWT token的标准方法"""
        client = self.get_test_client()
        
        login_data = {
            'phone': phone_number,
            'code': '123456',  # 测试验证码
            'password': password
        }
        
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        return data['data']['token']
    
    def make_authenticated_request(self, method, endpoint, data=None, phone_number='13900000000', password='Firefox0820'):
        """发送认证请求的通用方法"""
        client = self.get_test_client()
        token = self.get_jwt_token(phone_number, password)
        headers = {'Authorization': f'Bearer {token}'}
        
        if data is not None:
            data = json.dumps(data)
            headers['content-type'] = 'application/json'
        
        return getattr(client, method.lower())(endpoint, data=data, headers=headers)
    
    def assert_api_success(self, response, expected_data_keys=None):
        """标准成功响应断言"""
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        assert data['msg'] == 'success'
        assert 'data' in data
        
        if expected_data_keys:
            for key in expected_data_keys:
                assert key in data['data'], f"响应数据中缺少字段: {key}"
        
        return data
    
    def assert_api_error(self, response, expected_code=0, expected_msg_pattern=None):
        """标准错误响应断言"""
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == expected_code
        
        if expected_msg_pattern:
            assert expected_msg_pattern in data['msg'], f"错误消息不匹配: {data['msg']}"
        
        return data
    
    def create_snapshot_validator(self, expected_values):
        """创建快照对比验证器"""
        def validate_response(response):
            data = self.assert_api_success(response)
            response_data = data['data']
            
            mismatches = []
            matched_fields = []
            
            for key, expected_value in expected_values.items():
                if key not in response_data:
                    mismatches.append(f"❌ 缺少字段: {key}")
                elif response_data[key] != expected_value:
                    mismatches.append(f"❌ 字段 {key} 不匹配: 期望 '{expected_value}', 实际 '{response_data[key]}'")
                else:
                    matched_fields.append(f"✅ {key}")
            
            if mismatches:
                print(f"📊 快照对比结果:")
                print(f"✅ 匹配字段 ({len(matched_fields)}): {', '.join(matched_fields)}")
                print(f"❌ 不匹配字段 ({len(mismatches)}): {'; '.join(mismatches)}")
                assert not mismatches, f"快照对比失败，发现 {len(mismatches)} 个不匹配项"
            
            print(f"🎉 快照对比测试完全通过！")
            print(f"📈 数据一致性: 100% ({len(matched_fields)}/{len(expected_values)} 字段匹配)")
            
            return data
        
        return validate_response


class IntegrationTestBase(TestBase):
    """集成测试专用基类"""
    
    @classmethod
    def setup_class(cls):
        """集成测试专用的类级别设置"""
        # 设置测试环境变量
        os.environ['ENV_TYPE'] = 'unit'
        os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
        os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'
        
        # 导入并创建Flask应用
        from app import create_app
        from app.extensions import db
        
        cls.app = create_app()
        cls.db = db
        
        # 在应用上下文中初始化数据库
        with cls.app.app_context():
            # 创建所有表
            cls.db.create_all()
    
    @classmethod
    def create_standard_test_user(cls, role=1, phone_number='13900007997', password='Firefox0820', open_id=None):
        """创建标准测试用户（与test_auth_login_phone.py兼容）"""
        from hashlib import sha256
        
        # 设置phone_secret以匹配UserService中的哈希算法
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()
        
        # 如果没有指定open_id，使用基于phone_number的唯一ID
        if not open_id:
            open_id = f'test_snapshot_final_user_{phone_number[-4:]}'
        
        # 使用现有的create_test_user方法，但传递所有必需的参数
        return cls.create_test_user(
            wechat_openid=open_id,
            phone_number=phone_number,
            phone_hash=phone_hash,
            nickname='测试用户',
            name='测试用户',
            role=role,
            status=1,
            password_salt='test_salt',
            password_hash=sha256(f"{password}:test_salt".encode('utf-8')).hexdigest()
        )
    
    def create_standard_test_community(self, creator_role=1):
        """创建标准的测试社区"""
        creator = self.create_standard_test_user(creator_role)
        return self.create_test_community(
            name=f'标准测试社区_{creator_role}',
            creator=creator
        )


@pytest.fixture(scope="class")
def test_base():
    """提供TestBase实例的fixture"""
    return TestBase


@pytest.fixture(scope="class")
def app():
    """创建Flask应用实例的fixture"""
    os.environ['ENV_TYPE'] = 'unit'
    
    from app import create_app
    from app.extensions import db
    
    application = create_app()
    
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    """为每个测试提供HTTP客户端"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """为每个测试提供数据库会话，支持自动回滚"""
    with app.app_context():
        from app.extensions import db
        
        # 开始嵌套事务
        savepoint = db.session.begin_nested()
        try:
            yield db.session
        finally:
            # 回滚到保存点，确保测试隔离
            savepoint.rollback()