#!/usr/bin/env python3
"""
清理测试数据脚本
用于清理模拟环境中创建的测试用户和相关数据
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量为 function 环境，使用文件数据库
os.environ['ENV_TYPE'] = 'function'

from wxcloudrun import db, app
from wxcloudrun.model import User, CheckinRule, CheckinRecord

def clean_test_data():
    """清理测试数据"""
    with app.app_context():
        try:
            # 查找所有模拟用户（openid以 mock_openid_ 开头的用户）
            mock_users = User.query.filter(User.wechat_openid.like('mock_openid_%')).all()
            
            print(f"找到 {len(mock_users)} 个模拟用户")
            
            # 删除这些用户的打卡记录
            for user in mock_users:
                # 删除打卡记录
                CheckinRecord.query.filter(CheckinRecord.solo_user_id == user.user_id).delete()
                print(f"删除用户 {user.user_id} 的打卡记录")
                
                # 删除打卡规则
                CheckinRule.query.filter(CheckinRule.solo_user_id == user.user_id).delete()
                print(f"删除用户 {user.user_id} 的打卡规则")
                
                # 删除用户
                db.session.delete(user)
                print(f"删除用户 {user.user_id} ({user.wechat_openid})")
            
            # 提交更改
            db.session.commit()
            print("✅ 测试数据清理完成")
            
        except Exception as e:
            print(f"❌ 清理测试数据失败: {e}")
            db.session.rollback()

def check_test_data():
    """检查现有测试数据"""
    with app.app_context():
        try:
            # 查找所有模拟用户
            mock_users = User.query.filter(User.wechat_openid.like('mock_openid_%')).all()
            
            print(f"当前有 {len(mock_users)} 个模拟用户:")
            for user in mock_users:
                print(f"  - 用户ID: {user.user_id}, OpenID: {user.wechat_openid}, 昵称: {user.nickname}")
                
                # 查看打卡规则数量
                rule_count = CheckinRule.query.filter(CheckinRule.solo_user_id == user.user_id).count()
                print(f"    打卡规则数量: {rule_count}")
                
                # 查看打卡记录数量
                record_count = CheckinRecord.query.filter(CheckinRecord.solo_user_id == user.user_id).count()
                print(f"    打卡记录数量: {record_count}")
                
        except Exception as e:
            print(f"❌ 检查测试数据失败: {e}")

if __name__ == '__main__':
    print("=== 检查现有测试数据 ===")
    check_test_data()
    
    print("\n=== 清理测试数据 ===")
    clean_test_data()
    
    print("\n=== 清理后检查 ===")
    check_test_data()