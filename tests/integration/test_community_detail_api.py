"""
社区详情API集成测试
测试 GET /api/communities/{community_id} API
"""

import pytest
import json
from tests.integration.conftest import test_app, test_db
import jwt
import time

@pytest.fixture
def client(test_app):
    """创建测试客户端"""
    return test_app.test_client()

def create_auth_headers(user_id):
    """创建认证头"""
    # 创建测试token
    payload = {
        'user_id': user_id,
        'exp': time.time() + 3600
    }
    token = jwt.encode(payload, 'test_secret', algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}

def test_get_community_detail_success(client, test_db):
    """测试成功获取社区详情"""
    # 创建测试社区
    from database.models import Community, User, CommunityStaff
    
    # 创建测试用户（超级管理员）
    user = User(
        nickname="测试管理员",
        role=4,  # 超级管理员
        phone_number="13800138000"
    )
    test_db.session.add(user)
    test_db.session.commit()
    
    # 创建测试社区
    community = Community(
        name="测试社区详情",
        description="这是一个测试社区",
        location="测试地点",
        creator_user_id=user.user_id,
        status=1  # 启用
    )
    test_db.session.add(community)
    test_db.session.commit()
    
    # 设置用户为社区主管
    staff = CommunityStaff(
        community_id=community.community_id,
        user_id=user.user_id,
        role='manager'
    )
    test_db.session.add(staff)
    test_db.session.commit()
    
    # 获取社区详情
    response = client.get(
        f'/api/communities/{community.community_id}',
        headers=create_auth_headers(user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证响应格式
    assert data['code'] == 1
    assert data['msg'] == 'success'
    assert 'community' in data['data']
    
    # 验证社区数据
    community_data = data['data']['community']
    assert community_data['id'] == community.community_id
    assert community_data['name'] == '测试社区详情'
    assert community_data['description'] == '这是一个测试社区'
    assert community_data['location'] == '测试地点'
    assert community_data['status'] == 'active'
    
    # 验证统计信息
    assert 'stats' in community_data
    stats = community_data['stats']
    assert stats['admin_count'] >= 0
    assert stats['user_count'] >= 0
    assert stats['staff_count'] >= 0
    
    # 验证创建者信息
    assert 'creator' in community_data
    if community_data['creator']:
        assert community_data['creator']['user_id'] == user.user_id
        assert community_data['creator']['nickname'] == '测试管理员'

def test_get_community_detail_not_found(client, test_db):
    """测试获取不存在的社区详情"""
    from database.models import User
    
    # 创建测试用户
    user = User(
        nickname="测试用户",
        role=4,  # 超级管理员
        phone_number="13800138001"
    )
    test_db.session.add(user)
    test_db.session.commit()
    
    # 尝试获取不存在的社区
    response = client.get(
        '/api/communities/999999',
        headers=create_auth_headers(user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证错误响应
    assert data['code'] == 0
    assert '社区不存在' in data['msg']

def test_get_community_detail_permission_denied(client, test_db):
    """测试无权限获取社区详情"""
    from database.models import Community, User
    
    # 创建测试社区
    community = Community(
        name="权限测试社区",
        description="权限测试",
        location="测试地点",
        status=1
    )
    test_db.session.add(community)
    test_db.session.commit()
    
    # 创建普通用户（非社区工作人员）
    user = User(
        nickname="普通用户",
        role=1,  # 普通用户
        phone_number="13800138002"
    )
    test_db.session.add(user)
    test_db.session.commit()
    
    # 尝试获取社区详情（应该被拒绝）
    response = client.get(
        f'/api/communities/{community.community_id}',
        headers=create_auth_headers(user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证权限错误
    assert data['code'] == 0
    assert '权限不足' in data['msg']

def test_get_community_detail_as_community_staff(client, test_db):
    """测试社区工作人员获取自己管理的社区详情"""
    from database.models import Community, User, CommunityStaff
    
    # 创建测试社区
    community = Community(
        name="工作人员测试社区",
        description="工作人员测试",
        location="测试地点",
        status=1
    )
    test_db.session.add(community)
    test_db.session.commit()
    
    # 创建社区工作人员用户
    user = User(
        nickname="社区工作人员",
        role=3,  # 社区工作人员
        phone_number="13800138003"
    )
    test_db.session.add(user)
    test_db.session.commit()
    
    # 设置用户为社区工作人员
    staff = CommunityStaff(
        community_id=community.community_id,
        user_id=user.user_id,
        role='staff'  # 专员
    )
    test_db.session.add(staff)
    test_db.session.commit()
    
    # 获取社区详情（应该有权限）
    response = client.get(
        f'/api/communities/{community.community_id}',
        headers=create_auth_headers(user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证成功响应
    assert data['code'] == 1
    assert data['msg'] == 'success'
    assert data['data']['community']['id'] == community.community_id

def test_get_community_detail_invalid_id_format(client, test_db):
    """测试无效的社区ID格式"""
    from database.models import User
    
    # 创建测试用户
    user = User(
        nickname="测试用户",
        role=4,  # 超级管理员
        phone_number="13800138004"
    )
    test_db.session.add(user)
    test_db.session.commit()
    
    # 测试有效的整数但为负数
    response = client.get(
        '/api/communities/-1',
        headers=create_auth_headers(user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证错误响应
    assert data['code'] == 0
    assert '社区ID必须为正整数' in data['msg'] or '社区不存在' in data['msg']

def test_get_community_detail_stats_calculation(client, test_db):
    """测试社区统计信息计算"""
    from database.models import Community, User, CommunityStaff
    
    # 创建测试用户（超级管理员）
    admin_user = User(
        nickname="超级管理员",
        role=4,
        phone_number="13800138005"
    )
    test_db.session.add(admin_user)
    test_db.session.commit()
    
    # 创建测试社区
    community = Community(
        name="统计测试社区",
        description="统计测试",
        location="测试地点",
        creator_user_id=admin_user.user_id,
        status=1
    )
    test_db.session.add(community)
    test_db.session.commit()
    
    # 创建几个测试用户并添加到社区
    users = []
    for i in range(3):
        user = User(
            nickname=f"测试用户{i}",
            role=1,
            phone_number=f"1380013800{i+6}",
            community_id=community.community_id
        )
        test_db.session.add(user)
        users.append(user)
    
    test_db.session.commit()
    
    # 添加一个专员
    staff_user = User(
        nickname="社区专员",
        role=3,
        phone_number="13800138009"
    )
    test_db.session.add(staff_user)
    test_db.session.commit()
    
    staff = CommunityStaff(
        community_id=community.community_id,
        user_id=staff_user.user_id,
        role='admin'  # 专员
    )
    test_db.session.add(staff)
    test_db.session.commit()
    
    # 获取社区详情
    response = client.get(
        f'/api/communities/{community.community_id}',
        headers=create_auth_headers(admin_user.user_id)
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # 验证统计信息
    community_data = data['data']['community']
    stats = community_data['stats']
    
    # 应该有1个专员（admin_count）
    assert stats['admin_count'] == 1
    # 应该有4个用户（3个普通用户 + 1个专员）
    assert stats['user_count'] == 4
    # 应该有2个工作人员（1个主管 + 1个专员）
    assert stats['staff_count'] == 2