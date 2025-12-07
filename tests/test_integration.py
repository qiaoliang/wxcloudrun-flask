#!/usr/bin/env python3
"""
微信与手机注册流程优化 - 集成测试
验证前后端修改的正确性
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import unittest
from datetime import datetime, timedelta
from flask import Flask
from wxcloudrun import db, app
from wxcloudrun.model import User, CheckinRule, CheckinRecord, SupervisionRuleRelation
from wxcloudrun.views import _format_user_login_response, _merge_accounts_by_time
from hashlib import sha256

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """清理测试环境"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_client(self):
        """创建测试客户端"""
        return app.test_client()
    
    def test_phone_register_rejects_existing_phone(self):
        """测试1：手机注册拒绝已存在的手机号"""
        with app.app_context():
            # 创建测试客户端
            client = self._create_test_client()
            
            # 1. 先注册一个手机号用户
            phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
            phone = "13800138000"
            phone_hash = sha256(f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
            
            # 创建用户
            user1 = User(
                wechat_openid="test_wx_1",
                phone_hash=phone_hash,
                phone_number="138****8000",
                nickname="User1",
                role=1,
                status=1,
                password_hash="test_hash",
                password_salt="test_salt"
            )
            db.session.add(user1)
            db.session.commit()
            
            # 2. 尝试用相同手机号注册
            response = client.post('/api/auth/register_phone', 
                json={
                    'phone': phone,
                    'code': 'test_code',
                    'password': 'test123456'
                }
            )
            
            # 3. 验证返回错误
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['code'], 0)  # 错误响应
            self.assertEqual(data['data']['code'], 'PHONE_EXISTS')
            self.assertIn('该手机号已注册', data['msg'])
            
            print("✅ 测试1通过：手机注册正确拒绝已存在的手机号")
    
    def test_account_merge_functionality(self):
        """测试2：账号合并功能"""
        with app.app_context():
            # 创建两个用户，一个较早有微信，一个较晚有手机
            earlier_user = User(
                wechat_openid="early_wx",
                phone_hash=None,
                nickname="Early User",
                role=1,
                status=1,
                created_at=datetime.now() - timedelta(days=2)
            )
            later_user = User(
                wechat_openid="later_wx_temp",
                phone_hash="late_phone",
                phone_number="138****0001",
                nickname="Later User",
                role=1,
                status=1,
                created_at=datetime.now() - timedelta(days=1)
            )
            
            db.session.add(earlier_user)
            db.session.add(later_user)
            db.session.commit()
            
            # 为两个用户添加一些数据
            rule1 = CheckinRule(
                solo_user_id=earlier_user.user_id,
                rule_name="Morning Check",
                status=1
            )
            rule2 = CheckinRule(
                solo_user_id=later_user.user_id,
                rule_name="Evening Check",
                status=1
            )
            db.session.add(rule1)
            db.session.add(rule2)
            db.session.commit()
            
            # 执行合并
            primary = _merge_accounts_by_time(earlier_user, later_user)
            
            # 验证结果
            self.assertEqual(primary.user_id, earlier_user.user_id)
            self.assertEqual(primary.wechat_openid, "early_wx")
            self.assertEqual(primary.phone_hash, "late_phone")
            self.assertEqual(primary.phone_number, "138****0001")
            
            # 验证数据迁移
            rules = CheckinRule.query.filter_by(solo_user_id=primary.user_id).all()
            self.assertEqual(len(rules), 2)
            
            # 验证较晚用户被禁用
            disabled_user = User.query.filter_by(user_id=later_user.user_id).first()
            self.assertEqual(disabled_user.status, 2)
            
            print("✅ 测试2通过：账号合并功能正常工作")
    
    def test_unified_login_response_format(self):
        """测试3：统一登录响应格式"""
        with app.app_context():
            # 创建测试用户
            user = User(
                wechat_openid="test_wx",
                phone_number="138****0002",
                phone_hash="test_phone",
                nickname="Test User",
                avatar_url="http://test.com/avatar.jpg",
                role=1,
                status=1
            )
            db.session.add(user)
            db.session.commit()
            
            # 测试新用户响应
            response_new = _format_user_login_response(
                user, "test_token", "test_refresh_token", is_new_user=True
            )
            
            # 测试老用户响应
            response_existing = _format_user_login_response(
                user, "test_token", "test_refresh_token", is_new_user=False
            )
            
            # 验证新用户响应
            self.assertEqual(response_new['token'], "test_token")
            self.assertEqual(response_new['refresh_token'], "test_refresh_token")
            self.assertEqual(response_new['user_id'], user.user_id)
            self.assertEqual(response_new['wechat_openid'], "test_wx")
            self.assertEqual(response_new['phone_number'], "138****0002")
            self.assertEqual(response_new['nickname'], "Test User")
            self.assertEqual(response_new['avatar_url'], "http://test.com/avatar.jpg")
            self.assertEqual(response_new['role'], "solo")
            self.assertEqual(response_new['login_type'], "new_user")
            
            # 验证老用户响应
            self.assertEqual(response_existing['login_type'], "existing_user")
            
            print("✅ 测试3通过：统一登录响应格式正确")
    
    def test_data_migration_integrity(self):
        """测试4：数据迁移完整性"""
        with app.app_context():
            # 创建源用户和目标用户
            src_user = User(
                wechat_openid="src_wx_test",
                phone_hash="src_phone_test",
                nickname="Source User",
                role=1,
                status=1
            )
            dst_user = User(
                wechat_openid="dst_wx_test",
                nickname="Dest User",
                role=1,
                status=1
            )
            
            db.session.add(src_user)
            db.session.add(dst_user)
            db.session.commit()
            
            # 为源用户添加各种数据
            # 打卡规则
            rule = CheckinRule(
                solo_user_id=src_user.user_id,
                rule_name="Test Rule",
                status=1
            )
            db.session.add(rule)
            db.session.commit()  # 确保rule_id被生成
            
            # 打卡记录
            record = CheckinRecord(
                solo_user_id=src_user.user_id,
                rule_id=rule.rule_id,  # 使用实际的rule_id
                status=1,  # 已打卡
                planned_time=datetime.now()  # 添加必需的planned_time
            )
            db.session.add(record)
            
            # 监护关系（作为被监护人）
            supervision1 = SupervisionRuleRelation(
                solo_user_id=src_user.user_id,
                supervisor_user_id=999,
                status=1
            )
            db.session.add(supervision1)
            
            # 监护关系（作为监护人）
            supervision2 = SupervisionRuleRelation(
                solo_user_id=888,
                supervisor_user_id=src_user.user_id,
                status=1
            )
            db.session.add(supervision2)
            db.session.commit()
            
            # 执行合并
            primary = _merge_accounts_by_time(dst_user, src_user)
            
            # 验证所有数据都迁移到了目标用户
            rules = CheckinRule.query.filter_by(solo_user_id=primary.user_id).all()
            self.assertEqual(len(rules), 1)
            self.assertEqual(rules[0].rule_name, "Test Rule")
            
            records = CheckinRecord.query.filter_by(solo_user_id=primary.user_id).all()
            self.assertEqual(len(records), 1)
            
            # 验证监护关系迁移
            rels_as_solo = SupervisionRuleRelation.query.filter_by(
                solo_user_id=primary.user_id
            ).all()
            self.assertEqual(len(rels_as_solo), 1)
            self.assertEqual(rels_as_solo[0].supervisor_user_id, 999)
            
            rels_as_supervisor = SupervisionRuleRelation.query.filter_by(
                supervisor_user_id=primary.user_id
            ).all()
            self.assertEqual(len(rels_as_supervisor), 1)
            self.assertEqual(rels_as_supervisor[0].solo_user_id, 888)
            
            print("✅ 测试4通过：数据迁移完整且正确")
    
    def test_frontend_error_handling(self):
        """测试5：前端错误处理（模拟）"""
        # 这个测试主要验证前端代码中是否正确处理了PHONE_EXISTS错误
        # 由于是前后端分离，我们验证后端返回的错误格式是否符合前端预期
        
        with app.app_context():
            client = self._create_test_client()
            
            # 创建已存在的用户
            phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
            phone = "13800138001"
            phone_hash = sha256(f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
            
            existing_user = User(
                wechat_openid="existing_wx",
                phone_hash=phone_hash,
                phone_number="138****8001",
                nickname="Existing User",
                role=1,
                status=1
            )
            db.session.add(existing_user)
            db.session.commit()
            
            # 尝试注册相同手机号
            response = client.post('/api/auth/register_phone',
                json={
                    'phone': phone,
                    'code': 'test_code',
                    'password': 'test123456'
                }
            )
            
            # 验证错误响应格式
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # 前端期望的错误格式
            self.assertEqual(data['code'], 0)  # 错误标识
            self.assertIn('data', data)  # 错误详情
            self.assertEqual(data['data']['code'], 'PHONE_EXISTS')  # 错误码
            self.assertIn('msg', data)  # 错误消息
            
            print("✅ 测试5通过：错误响应格式符合前端预期")
    
    def test_binding_with_merge(self):
        """测试6：绑定功能与账号合并"""
        with app.app_context():
            # 创建两个用户
            user1 = User(
                wechat_openid="user1_wx_bind",
                nickname="User1",
                role=1,
                status=1,
                created_at=datetime.now() - timedelta(days=2)
            )
            user2 = User(
                wechat_openid="user2_wx_bind_temp",
                phone_hash="user2_phone_bind",
                phone_number="139****0002",
                nickname="User2",
                role=1,
                status=1,
                created_at=datetime.now() - timedelta(days=1)
            )
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # 模拟绑定手机号的请求（需要token认证）
            # 这里只验证合并逻辑，不测试完整的认证流程
            
            # 执行合并
            primary = _merge_accounts_by_time(user1, user2)
            
            # 验证合并结果
            self.assertEqual(primary.user_id, user1.user_id)  # 保留较早的用户
            self.assertEqual(primary.wechat_openid, "user1_wx_bind")  # 保留原有微信
            self.assertEqual(primary.phone_hash, "user2_phone_bind")  # 继承手机号
            self.assertEqual(primary.phone_number, "139****0002")  # 继承手机号
            
            # 验证较晚用户被禁用
            disabled_user = User.query.filter_by(user_id=user2.user_id).first()
            self.assertEqual(disabled_user.status, 2)
            
            print("✅ 测试6通过：绑定功能正确触发账号合并")

if __name__ == '__main__':
    print("=" * 60)
    print("开始微信与手机注册流程优化 - 集成测试")
    print("=" * 60)
    
    # 运行测试
    unittest.main(verbosity=2)