"""
契约测试配置文件
为 schemathesis 提供认证和测试环境
"""
import pytest
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)


@pytest.fixture(scope="module")
def app():
    """创建 Flask 测试应用"""
    # 设置测试环境
    os.environ['ENV_TYPE'] = 'unit'
    os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
    os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'
    os.environ['PHONE_ENC_SECRET'] = 'test_secret_key_for_testing'
    os.environ['SMS_PROVIDER'] = 'mock'

    from app import create_app
    from app.extensions import db

    app = create_app()
    app.config['TESTING'] = True

    # 在应用上下文中初始化数据库
    with app.app_context():
        db.create_all()
        # 创建超级管理员测试用户
        _create_super_admin(db)

    yield app

    # 清理
    with app.app_context():
        db.drop_all()


def _create_super_admin(db):
    """创建超级管理员测试用户"""
    from database.flask_models import User, Community, CommunityStaff
    import secrets
    from hashlib import sha256
    from datetime import datetime, timezone
    from wxcloudrun.utils.validators import generate_phone_hash, normalize_phone_number

    # 检查超级管理员是否已存在
    admin = db.session.query(User).filter_by(phone_number='13141516171').first()
    if not admin:
        # 创建默认社区 - 安卡大家庭
        default_community = Community(
            name='安卡大家庭',
            description='系统默认社区，新注册用户自动加入',
            creator_id=None,
            manager_id=None,
            status=1,
            is_default=True,
            is_blackhouse=False,
            location='北京市朝阳区柳芳南里29号',
            location_lat=39.901213,
            location_lon=116.527067,
            province='北京市',
            city='北京市',
            district='朝阳区',
            street='柳芳南里',
            settings='{"checkin_enabled": true, "event_notifications": true}',
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        db.session.add(default_community)
        db.session.flush()

        # 创建黑屋社区
        blackhouse_community = Community(
            name='黑屋社区',
            description='特殊管理社区，用户在此社区时功能受限',
            creator_id=None,
            manager_id=None,
            status=1,
            is_default=False,
            is_blackhouse=True,
            location='北京市海淀区中关村大街1号',
            location_lat=39.956073,
            location_lon=116.307079,
            province='北京市',
            city='北京市',
            district='海淀区',
            street='中关村大街',
            settings='{"checkin_enabled": false, "event_notifications": false, "restricted_mode": true}',
            created_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, 18, 30, 0, tzinfo=timezone.utc)
        )
        db.session.add(blackhouse_community)
        db.session.flush()

        # 创建超级管理员（使用与 initialization.py 一致的默认值）
        salt = secrets.token_hex(8)
        password_hash = sha256(f"F1234567:{salt}".encode('utf-8')).hexdigest()
        # 使用正确的 phone_hash 生成方式
        normalized_phone = normalize_phone_number('13141516171')
        phone_hash = generate_phone_hash(normalized_phone)

        admin = User(
            phone_number='13141516171',
            phone_hash=phone_hash,
            nickname='系统超级系统管理员',
            name='系统超级系统管理员',
            avatar_url='https://example.com/avatar/superadmin.png',
            work_id='SA0000001',
            address='北京市朝阳区柳芳南里29号',
            motto='守护每一位用户的安全与健康',
            emergency_contact_name='系统管理员',
            emergency_contact_phone='13800000000',
            emergency_contact_address='北京市朝阳区柳芳南里29号',
            password_hash=password_hash,
            password_salt=salt,
            role=4,  # SUPER_ADMIN
            status=1,
            verification_status=2,
            _is_community_worker=True,
            community_id=default_community.community_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        db.session.add(admin)
        db.session.flush()

        # 更新社区的创建者和主管为超级管理员
        default_community.creator_id = admin.user_id
        default_community.manager_id = admin.user_id
        blackhouse_community.creator_id = admin.user_id
        blackhouse_community.manager_id = admin.user_id

        # 创建 CommunityStaff 关系（超级管理员是两个社区的 manager）
        staff_ankaji = CommunityStaff(
            community_id=default_community.community_id,
            user_id=admin.user_id,
            role='manager'
        )
        db.session.add(staff_ankaji)

        staff_blackhouse = CommunityStaff(
            community_id=blackhouse_community.community_id,
            user_id=admin.user_id,
            role='manager'
        )
        db.session.add(staff_blackhouse)

        db.session.commit()


@pytest.fixture(scope="module")
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(scope="module")
def auth_headers(client):
    """获取认证 token（用于需要认证的 API）"""
    response = client.post('/api/auth/login_phone_password', json={
        'phone': '13141516171',
        'password': 'F1234567'
    })
    data = response.get_json()
    if data.get('code') == 1:
        token = data['data']['token']
        return {'Authorization': f'Bearer {token}'}
    return {}


@pytest.fixture(scope="module")
def base_client(app):
    """基础测试客户端（别名，与现有测试保持一致）"""
    return app.test_client()
