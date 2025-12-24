"""
手机号登录API快照对比集成测试
验证 /api/auth/login_phone 端点返回的数据与预期快照的一致性
"""

import pytest
import json
import sys
import os
from datetime import datetime

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community, CommunityStaff


class TestAuthLoginPhoneSnapshot:
    """手机号登录API快照对比测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置，创建应用实例和测试数据"""
        # 设置测试环境
        os.environ['ENV_TYPE'] = 'unit'
        
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
            cls._create_snapshot_test_data()
            
            # 定义预期响应快照
            cls.expected_snapshots = cls._define_expected_snapshots()
    
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
    
    def get_test_client(self):
        """获取测试客户端"""
        return self.app.test_client()
    
    @classmethod
    def _create_snapshot_test_data(cls):
        """创建快照测试所需的用户数据"""
        # 创建超级管理员
        cls.super_admin = User(
            wechat_openid='super_admin_snapshot',
            phone_number='13900007997',
            nickname='系统超级管理员',
            name='系统超级管理员',
            role=4,  # 超级系统管理员
            status=1,
            password_salt='test_salt',
            password_hash='test_hash'  # 在测试中会被替换
        )
        cls.db.session.add(cls.super_admin)
        
        # 创建社区主管
        cls.community_manager = User(
            wechat_openid='manager_snapshot',
            phone_number='13900007998',
            nickname='社区主管',
            name='社区主管',
            role=3,  # 社区主管
            status=1,
            password_salt='test_salt',
            password_hash='test_hash'
        )
        cls.db.session.add(cls.community_manager)
        
        # 创建普通用户
        cls.normal_user = User(
            wechat_openid='normal_snapshot',
            phone_number='13900007999',
            nickname='普通用户',
            name='普通用户',
            role=1,  # 普通用户
            status=1,
            password_salt='test_salt',
            password_hash='test_hash'
        )
        cls.db.session.add(cls.normal_user)
        
        # 创建测试社区
        cls.test_community = Community(
            name='测试社区快照',
            description='用于快照测试的社区',
            creator_id=cls.super_admin.user_id
        )
        cls.db.session.add(cls.test_community)
        
        cls.db.session.flush()  # 获取ID
        
        # 建立用户-社区关系
        cls.super_admin.community_id = cls.test_community.community_id
        cls.community_manager.community_id = cls.test_community.community_id
        cls.normal_user.community_id = cls.test_community.community_id
        
        # 创建社区工作人员关系
        cls.manager_staff = CommunityStaff(
            community_id=cls.test_community.community_id,
            user_id=cls.community_manager.user_id,
            role=3  # 主管
        )
        cls.db.session.add(cls.manager_staff)
        
        cls.db.session.commit()
        
        # 设置密码哈希（模拟Firefox0820密码）
        cls._set_test_passwords()
    
    @classmethod
    def _set_test_passwords(cls):
        """设置测试用户的密码哈希"""
        from hashlib import sha256
        
        test_password = "Firefox0820"
        for user in [cls.super_admin, cls.community_manager, cls.normal_user]:
            user.password_hash = sha256(f"{test_password}:{user.password_salt}".encode('utf-8')).hexdigest()
        
        cls.db.session.commit()
    
    @classmethod
    def _define_expected_snapshots(cls):
        """定义预期响应快照模板"""
        return {
            'super_admin': {
                'code': 1,
                'msg': 'success',
                'data': {
                    'user_id': cls.super_admin.user_id,
                    'wechat_openid': 'super_admin_snapshot',
                    'phone_number': '13900007997',
                    'nickname': '系统超级管理员',
                    'name': '系统超级管理员',
                    'avatar_url': None,
                    'role': '超级系统管理员',
                    'community_id': cls.test_community.community_id,
                    'community_name': '测试社区快照',
                    'login_type': 'existing_user'
                }
            },
            'community_manager': {
                'code': 1,
                'msg': 'success',
                'data': {
                    'user_id': cls.community_manager.user_id,
                    'wechat_openid': 'manager_snapshot',
                    'phone_number': '13900007998',
                    'nickname': '社区主管',
                    'name': '社区主管',
                    'avatar_url': None,
                    'role': '社区主管',
                    'community_id': cls.test_community.community_id,
                    'community_name': '测试社区快照',
                    'login_type': 'existing_user'
                }
            },
            'normal_user': {
                'code': 1,
                'msg': 'success',
                'data': {
                    'user_id': cls.normal_user.user_id,
                    'wechat_openid': 'normal_snapshot',
                    'phone_number': '13900007999',
                    'nickname': '普通用户',
                    'name': '普通用户',
                    'avatar_url': None,
                    'role': '普通用户',
                    'community_id': cls.test_community.community_id,
                    'community_name': '测试社区快照',
                    'login_type': 'existing_user'
                }
            }
        }
    
    def _prepare_response_for_comparison(self, response_data):
        """准备响应数据用于对比，移除时间敏感字段"""
        data = response_data.copy()
        
        # 移除时间敏感的字段
        if 'token' in data.get('data', {}):
            data['data'].pop('token')
        if 'refresh_token' in data.get('data', {}):
            data['data'].pop('refresh_token')
        
        return data
    
    def _compare_with_snapshot(self, actual_response, expected_snapshot, test_name):
        """将实际响应与预期快照进行对比"""
        prepared_actual = self._prepare_response_for_comparison(actual_response)
        
        # 手动对比关键字段
        assert prepared_actual['code'] == expected_snapshot['code'], f"{test_name}: code不匹配"
        assert prepared_actual['msg'] == expected_snapshot['msg'], f"{test_name}: msg不匹配"
        
        # 对比data字段
        actual_data = prepared_actual['data']
        expected_data = expected_snapshot['data']
        
        for key in expected_data:
            assert key in actual_data, f"{test_name}: 缺少字段 {key}"
            assert actual_data[key] == expected_data[key], f"{test_name}: 字段 {key} 不匹配: 期望 {expected_data[key]}, 实际 {actual_data[key]}"
        
        print(f"✅ {test_name} 快照对比通过")
    
    def test_super_admin_login_snapshot(self):
        """测试超级管理员登录的快照对比"""
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
        actual_response = json.loads(response.data)
        
        # 与快照对比
        self._compare_with_snapshot(
            actual_response,
            self.expected_snapshots['super_admin'],
            '超级管理员登录'
        )
    
    def test_community_manager_login_snapshot(self):
        """测试社区主管登录的快照对比"""
        client = self.get_test_client()
        
        login_data = {
            'phone': '13900007998',
            'code': '123456',
            'password': 'Firefox0820'
        }
        
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        actual_response = json.loads(response.data)
        
        # 与快照对比
        self._compare_with_snapshot(
            actual_response,
            self.expected_snapshots['community_manager'],
            '社区主管登录'
        )
    
    def test_normal_user_login_snapshot(self):
        """测试普通用户登录的快照对比"""
        client = self.get_test_client()
        
        login_data = {
            'phone': '13900007999',
            'code': '123456',
            'password': 'Firefox0820'
        }
        
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        actual_response = json.loads(response.data)
        
        # 与快照对比
        self._compare_with_snapshot(
            actual_response,
            self.expected_snapshots['normal_user'],
            '普通用户登录'
        )
    
    def test_snapshot_data_integrity(self):
        """验证快照数据本身的完整性"""
        # 确保所有快照都包含必要的字段
        required_fields = ['code', 'msg', 'data']
        required_data_fields = [
            'user_id', 'wechat_openid', 'phone_number', 'nickname',
            'name', 'avatar_url', 'role', 'community_id', 
            'community_name', 'login_type'
        ]
        
        for snapshot_name, snapshot in self.expected_snapshots.items():
            # 检查顶级字段
            for field in required_fields:
                assert field in snapshot, f"快照 {snapshot_name} 缺少字段 {field}"
            
            # 检查data字段
            for field in required_data_fields:
                assert field in snapshot['data'], f"快照 {snapshot_name}.data 缺少字段 {field}"
        
        print("✅ 快照数据完整性验证通过")
    
    def test_role_mapping_consistency(self):
        """验证角色映射的一致性"""
        expected_roles = {
            1: '普通用户',
            2: '社区专员',
            3: '社区主管',
            4: '超级系统管理员'
        }
        
        for snapshot_name, snapshot in self.expected_snapshots.items():
            actual_role = snapshot['data']['role']
            
            # 从用户数据获取role值
            if snapshot_name == 'super_admin':
                expected_role = expected_roles[4]
            elif snapshot_name == 'community_manager':
                expected_role = expected_roles[3]
            elif snapshot_name == 'normal_user':
                expected_role = expected_roles[1]
            
            assert actual_role == expected_role, f"{snapshot_name} 角色映射不一致: 期望 {expected_role}, 实际 {actual_role}"
        
        print("✅ 角色映射一致性验证通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])