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

# 导入测试常量
# 添加上级目录到路径以导入test_constants
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from test_constants import TEST_CONSTANTS

# 添加当前目录到路径以导入test_data_generator
sys.path.insert(0, os.path.dirname(__file__))
from test_data_generator import generate_unique_phone_number


# ==================== Pytest Fixtures ====================

@pytest.fixture(scope='class')
def app():
    """创建并返回 Flask 应用实例"""
    # 设置测试环境
    os.environ['ENV_TYPE'] = 'unit'
    os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
    os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'

    # 导入并创建Flask应用
    from app import create_app
    from app.extensions import db

    app = create_app()

    # 在应用上下文中初始化数据库
    with app.app_context():
        # 创建所有表
        db.create_all()

        # 创建初始数据
        _create_initial_data(db)

    yield app

    # 清理
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """
    为每个测试函数创建一个新的数据库会话和事务
    使用 commit 而不是 begin_nested，确保数据可以被 test_client 访问
    """
    from app.extensions import db

    with app.app_context():
        # 开始事务
        db.session.begin()

        yield db

        # 回滚事务，确保测试隔离
        db.session.rollback()


@pytest.fixture(scope='function')
def test_client(app):
    """创建测试客户端"""
    return app.test_client()


# ==================== 测试基类 ====================

class TestBase:
    """测试基类，封装Flask-SQLAlchemy测试上下文管理"""

    @classmethod
    def setup_class(cls):
        """类级别的设置，创建应用实例"""
        # 设置测试环境
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
        # 在应用上下文中开始外层事务
        with self.app.app_context():
            self.db.session.begin()

    def teardown_method(self, method):
        """每个测试方法后的清理"""
        # 回滚外层事务，确保测试隔离
        with self.app.app_context():
            self.db.session.rollback()

    @classmethod
    def _create_initial_data(cls):
        """创建测试所需的初始数据"""
        from database.flask_models import User, Community
        import time

        # 创建测试用户
        test_user = User(
            wechat_openid='test_openid_123',
            phone_hash='test_phone_hash',
            nickname='测试用户',
            avatar_url='https://example.com/avatar.jpg',
            role=1  # 普通用户角色
        )
        cls.db.session.add(test_user)

        # 创建测试社区（使用时间戳确保唯一性）
        community_name = f'测试社区_{int(time.time() * 1000)}'
        test_community = Community(
            name=community_name,
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
        phone_secret = TEST_CONSTANTS.PHONE_ENC_SECRET
        return sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()

    @staticmethod
    def generate_password_hash(password, salt):
        """生成密码哈希"""
        return sha256(f"{password}:{salt}".encode('utf-8')).hexdigest()

    @classmethod
    def create_test_user(cls, phone_number=None, role=1, suffix=None, test_context=None, **kwargs):
        """创建测试用户的增强方法（向后兼容）"""
        # 导入统一的测试工具
        from test_utils import TestUserFactory

        return TestUserFactory.create_user(
            session=cls.db.session,
            role=role,
            phone_number=phone_number,
            test_context=test_context,
            **kwargs
        )

    @classmethod
    def create_test_community(cls, name=None, creator=None, **kwargs):
        """创建测试社区的增强方法"""
        from database.flask_models import Community
        import time

        if name is None:
            # 使用时间戳确保唯一性
            suffix = kwargs.get("suffix", f"default_{int(time.time() * 1000)}")
            name = f'测试社区_{suffix}'

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
        cls.db.session.refresh(community)  # 刷新对象以确保状态正确
        return community

    # ==================== API 测试工具 ====================

    def get_jwt_token(self, phone_number=None, password=None):
        """获取JWT token的标准方法"""
        if phone_number is None:
            # 使用数据生成器生成唯一手机号
            from test_data_generator import generate_unique_phone_number
            phone_number = generate_unique_phone_number('get_jwt_token')

        if password is None:
            password = TEST_CONSTANTS.DEFAULT_PASSWORD

        client = self.get_test_client()

        login_data = {
            'phone': phone_number,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,  # 测试验证码
            'password': password
        }

        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        return data['data']['token']

    def make_authenticated_request(self, method, endpoint, data=None, phone_number=None, password=None):
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

    # 不再需要覆盖 setup_class，直接继承父类的实现
    # 父类的 setup_class 已经包含了创建初始数据的逻辑

    @classmethod
    def create_standard_test_user(cls, role=1, phone_number=None, password=None, open_id=None, test_context=None):
        """创建标准测试用户（自动生成唯一手机号码）"""
        from hashlib import sha256
        import sys
        import os

        # 使用默认密码如果没有提供
        if password is None:
            password = TEST_CONSTANTS.DEFAULT_PASSWORD

        # 导入测试数据生成器（从测试目录）
        from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname, generate_unique_username

        # 如果没有指定手机号码，生成唯一的
        if phone_number is None:
            phone_number = generate_unique_phone_number(test_context or 'create_standard_test_user')

        # 设置phone_secret以匹配UserService中的哈希算法
        phone_secret = TEST_CONSTANTS.PHONE_ENC_SECRET
        phone_hash = sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()

        # 如果没有指定open_id，生成唯一的
        if not open_id:
            open_id = generate_unique_openid(phone_number, test_context or 'create_standard_test_user')

        # 生成唯一的昵称和用户名
        nickname = generate_unique_nickname(test_context or 'create_standard_test_user')
        username = generate_unique_username(test_context or 'create_standard_test_user')

        # 生成密码盐和哈希（与auth/routes.py保持一致）
        password_salt = TEST_CONSTANTS.generate_password_salt()
        password_hash = sha256(f"{password}:{password_salt}".encode('utf-8')).hexdigest()

        # 生成phone_hash（与UserService中的算法保持一致）
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(f"{phone_secret}:{phone_number}".encode('utf-8')).hexdigest()

        # 使用现有的create_test_user方法，但传递所有必需的参数
        return cls.create_test_user(
            wechat_openid=open_id,
            phone_number=phone_number,
            phone_hash=phone_hash,
            nickname=nickname,
            name=username,  # 用户名使用uname_前缀
            role=role,
            status=1,
            password_salt=password_salt,
            password_hash=password_hash
        )

    def create_standard_test_community(self, creator_role=1):
        """创建标准的测试社区"""
        creator = self.create_standard_test_user(creator_role)
        return self.create_test_community(
            name=f'标准测试社区_{creator_role}',
            creator=creator
        )

    @classmethod
    def get_super_admin(cls, test_context=None):
        """创建或获取超级管理员（确保系统中只有一个超级管理员）

        超级管理员特征：
        - role=4 (超级系统管理员)
        - 手机号: 13900007997 (固定)
        - 昵称: 系统超级管理员

        Returns:
            dict: 超级管理员信息字典，包含user_id, phone_number等关键字段
        """
        from database.flask_models import User
        from hashlib import sha256
        import secrets

        with cls.app.app_context():
            # 检查超级管理员是否已存在
            existing_admin = cls.db.session.query(User).filter_by(
                phone_number=TEST_CONSTANTS.SUPER_ADMIN_PHONE
            ).first()

            if existing_admin:
                cls.db.session.refresh(existing_admin)  # 确保获取最新数据
                return {
                    'user_id': existing_admin.user_id,
                    'phone_number': existing_admin.phone_number,
                    'nickname': existing_admin.nickname,
                    'name': existing_admin.name,
                    'role': existing_admin.role,
                    'wechat_openid': existing_admin.wechat_openid
                }

            # 创建新的超级管理员
            salt = TEST_CONSTANTS.generate_password_salt()
            password_hash = sha256(f"{TEST_CONSTANTS.DEFAULT_PASSWORD}:{salt}".encode('utf-8')).hexdigest()

            # 使用与auth.py完全相同的手机号哈希方法
            phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
            phone_hash = sha256(f"{phone_secret}:{TEST_CONSTANTS.SUPER_ADMIN_PHONE}".encode('utf-8')).hexdigest()

            super_admin = User(
                wechat_openid=f"super_admin_{secrets.token_hex(16)}",
                phone_number=TEST_CONSTANTS.SUPER_ADMIN_PHONE,
                phone_hash=phone_hash,
                nickname=TEST_CONSTANTS.SUPER_ADMIN_NICKNAME,
                name=TEST_CONSTANTS.SUPER_ADMIN_NAME,
                password_hash=password_hash,
                password_salt=salt,
                role=TEST_CONSTANTS.SUPER_ADMIN_ROLE,  # 超级管理员角色
                status=1,  # 正常状态
                verification_status=2,  # 已通过验证
                _is_community_worker=True
            )

            cls.db.session.add(super_admin)
            cls.db.session.commit()

            return {
                'user_id': super_admin.user_id,
                'phone_number': super_admin.phone_number,
                'nickname': super_admin.nickname,
                'name': super_admin.name,
                'role': super_admin.role,
                'wechat_openid': super_admin.wechat_openid
            }

    @classmethod
    def add_community_staff(cls, community_id, user_id, role='staff', operator_id=None):
        """为社区添加社区专员或主管

        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            role (str): 角色，'staff'（专员）或 'manager'（主管），默认为 'staff'
            operator_id (int): 操作者ID，如果未提供则使用超级管理员

        Returns:
            CommunityStaff: 创建的社区工作人员记录

        Raises:
            ValueError: 当参数无效或操作失败时
        """
        from wxcloudrun.community_staff_service import CommunityStaffService

        # 如果没有提供操作者ID，使用超级管理员
        if operator_id is None:
            super_admin = cls.get_super_admin('add_community_staff')
            operator_id = super_admin['user_id']

        # 调用服务层方法添加工作人员
        try:
            staff_record = CommunityStaffService.add_staff_single(
                community_id=community_id,
                user_id=user_id,
                role=role,
                operator_id=operator_id
            )
            return staff_record
        except ValueError as e:
            # 重新抛出业务异常
            raise ValueError(f"添加社区工作人员失败: {str(e)}")
        except Exception as e:
            # 包装其他异常
            raise ValueError(f"添加社区工作人员时发生未知错误: {str(e)}")


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