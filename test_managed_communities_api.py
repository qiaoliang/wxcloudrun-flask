#!/usr/bin/env python3
"""
测试管理社区API的功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from wxcloudrun import app, db
from wxcloudrun.model import User, Community, CommunityAdmin
from wxcloudrun.views.community import get_managed_communities
from flask import Flask
import json

def create_test_data():
    """创建测试数据"""
    print("=== 创建测试数据 ===")
    
    # 创建测试用户
    # 超级管理员
    super_admin = User(
        wechat_openid="super_admin_test",
        nickname="超级管理员",
        role=4,  # 超级管理员
        phone_number="+8613900007997"
    )
    db.session.add(super_admin)
    
    # 社区主管
    primary_admin = User(
        wechat_openid="primary_admin_test", 
        nickname="社区主管",
        role=3,  # 社区管理员
        phone_number="+8613900007998"
    )
    db.session.add(primary_admin)
    
    # 普通管理员
    normal_admin = User(
        wechat_openid="normal_admin_test",
        nickname="普通管理员", 
        role=3,  # 社区管理员
        phone_number="+8613900007999"
    )
    db.session.add(normal_admin)
    
    db.session.commit()
    
    # 创建测试社区
    community1 = Community(
        name="测试社区1",
        description="第一个测试社区",
        location="北京市朝阳区"
    )
    db.session.add(community1)
    
    community2 = Community(
        name="测试社区2", 
        description="第二个测试社区",
        location="上海市浦东新区"
    )
    db.session.add(community2)
    
    db.session.commit()
    
    # 分配管理员到社区
    # 主管管理社区1
    admin_role1 = CommunityAdmin(
        community_id=community1.community_id,
        user_id=primary_admin.user_id,
        role=1  # 主管
    )
    db.session.add(admin_role1)
    
    # 普通管理员管理社区1和社区2
    admin_role2 = CommunityAdmin(
        community_id=community1.community_id,
        user_id=normal_admin.user_id,
        role=2  # 普通管理员
    )
    db.session.add(admin_role2)
    
    admin_role3 = CommunityAdmin(
        community_id=community2.community_id,
        user_id=normal_admin.user_id,
        role=2  # 普通管理员
    )
    db.session.add(admin_role3)
    
    db.session.commit()
    
    print(f"✅ 创建用户: 超级管理员({super_admin.user_id}), 主管({primary_admin.user_id}), 普通管理员({normal_admin.user_id})")
    print(f"✅ 创建社区: {community1.name}({community1.community_id}), {community2.name}({community2.community_id})")
    print(f"✅ 分配管理员角色完成")
    
    return {
        'super_admin': super_admin,
        'primary_admin': primary_admin, 
        'normal_admin': normal_admin,
        'community1': community1,
        'community2': community2
    }

def test_api_with_user(user, expected_role, expected_communities):
    """测试指定用户的API响应"""
    print(f"\n=== 测试用户: {user.nickname} (角色: {expected_role}) ===")
    
    # 模拟API调用环境
    with app.test_request_context():
        # 模拟token验证
        import wxcloudrun.views.community as community_views
        
        # 临时替换verify_token函数来模拟认证
        original_verify = community_views.verify_token
        def mock_verify_token():
            return {'user_id': user.user_id}, None
        community_views.verify_token = mock_verify_token
        
        try:
            # 调用API
            response = get_managed_communities()
            
            # 检查响应
            if hasattr(response, 'data'):
                data = json.loads(response.data)
                if data['code'] == 1:
                    communities = data['data']['communities']
                    user_role = data['data']['user_role']
                    
                    print(f"✅ API调用成功")
                    print(f"✅ 用户角色: {user_role}")
                    print(f"✅ 社区数量: {len(communities)}")
                    
                    # 验证社区数量
                    if len(communities) == expected_communities:
                        print(f"✅ 社区数量正确: {len(communities)}")
                    else:
                        print(f"❌ 社区数量错误: 期望{expected_communities}, 实际{len(communities)}")
                    
                    # 显示社区列表
                    for community in communities:
                        print(f"   - {community['name']} (用户角色: {community['user_role']})")
                        
                else:
                    print(f"❌ API返回错误: {data['msg']}")
            else:
                print(f"❌ API响应格式错误")
                
        except Exception as e:
            print(f"❌ API调用异常: {str(e)}")
        finally:
            # 恢复原始函数
            community_views.verify_token = original_verify

def main():
    """主测试函数"""
    print("🚀 开始测试管理社区API功能")
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建测试数据
        test_data = create_test_data()
        
        # 测试超级管理员
        test_api_with_user(
            test_data['super_admin'], 
            'super_admin', 
            2  # 应该看到所有社区
        )
        
        # 测试社区主管
        test_api_with_user(
            test_data['primary_admin'],
            'community_admin', 
            1  # 应该只看到自己管理的社区
        )
        
        # 测试普通管理员
        test_api_with_user(
            test_data['normal_admin'],
            'community_admin',
            2  # 应该看到自己管理的两个社区
        )
        
        print("\n🎉 测试完成!")

if __name__ == '__main__':
    main()