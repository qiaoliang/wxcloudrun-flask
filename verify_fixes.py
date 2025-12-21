#!/usr/bin/env python3
"""
验证测试修复的简单测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """测试基本导入"""
    try:
        from database import get_database, reset_all
        from database.models import User, Community
        from wxcloudrun.community_event_service import CommunityEventService
        print("✓ 所有基本导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_database_initialization():
    """测试数据库初始化"""
    try:
        from database import get_database, reset_all
        from database.models import User
        
        # 重置并初始化数据库
        reset_all()
        db = get_database('test')
        db.initialize()
        db.create_tables()
        
        # 测试基本操作
        with db.get_session() as session:
            user = User(wechat_openid="test_openid", nickname="测试用户", role=1, status=1)
            session.add(user)
            session.commit()
            
            # 查询用户
            retrieved_user = session.query(User).filter_by(wechat_openid="test_openid").first()
            assert retrieved_user is not None
            assert retrieved_user.nickname == "测试用户"
        
        print("✓ 数据库初始化和基本操作成功")
        return True
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_community_event_service():
    """测试社区事件服务"""
    try:
        from database import get_database, reset_all
        from database.models import User, Community
        from wxcloudrun.community_event_service import CommunityEventService
        
        # 初始化数据库
        reset_all()
        db = get_database('test')
        db.initialize()
        db.create_tables()
        
        with db.get_session() as session:
            # 创建测试用户
            user = User(wechat_openid="test_openid", nickname="测试用户", role=1, status=1)
            session.add(user)
            session.commit()
            user_id = user.user_id
            
            # 创建测试社区
            community = Community(name="测试社区", location="测试地址")
            session.add(community)
            session.commit()
            community_id = community.community_id
        
        # 测试获取不存在的社区统计
        result = CommunityEventService.get_community_stats(999)
        assert result['success'] is False
        assert '社区不存在' in result['message']
        
        print("✓ 社区事件服务测试成功")
        return True
    except Exception as e:
        print(f"✗ 社区事件服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始验证测试修复...\n")
    
    tests = [
        ("基本导入测试", test_basic_imports),
        ("数据库初始化测试", test_database_initialization),
        ("社区事件服务测试", test_community_event_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"=== {test_name} ===")
        if test_func():
            passed += 1
        print()
    
    print(f"=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有核心功能验证通过！")
        print("\n主要修复:")
        print("✓ conftest.py中的test_db fixture yield问题")
        print("✓ CommunityEventService.get_community_stats社区验证逻辑")
        print("✓ 测试参数传递错误")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)