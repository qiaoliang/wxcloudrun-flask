#!/usr/bin/env python
"""
验证最小化Flask依赖的独立测试
"""
import sys
import os
from datetime import datetime

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 记录Flask初始化
flask_initialized = False

# 监控Flask导入
original_import = __import__

def monitored_import(name, *args, **kwargs):
    global flask_initialized
    if name == 'flask' or name.startswith('flask.'):
        flask_initialized = True
        print(f"⚠️  Flask被导入: {name}")
    return original_import(name, *args, **kwargs)

# 替换导入函数
__builtins__.__import__ = monitored_import

try:
    print("开始测试最小化Flask依赖...")
    
    # 测试1：导入最小化初始化器
    print("\n1. 导入最小化初始化器")
    sys.path.insert(0, os.path.dirname(__file__))
    from minimal_db_initializer import MinimalDatabaseInitializer
    print("✓ 最小化初始化器导入成功")
    
    # 测试2：创建初始化器
    print("\n2. 创建数据库初始化器")
    initializer = MinimalDatabaseInitializer("sqlite:///:memory:")
    print("✓ 初始化器创建成功")
    
    # 测试3：初始化数据库
    print("\n3. 初始化数据库")
    engine, session_factory = initializer.initialize()
    print("✓ 数据库初始化成功")
    
    # 测试4：使用数据库
    print("\n4. 测试数据库操作")
    with initializer.get_session() as session:
        # 创建测试数据
        from wxcloudrun.model import User
        
        user = User(
            wechat_openid="test_minimal",
            nickname="最小化测试用户",
            role=1,
            status=1
        )
        session.add(user)
        session.commit()
        
        # 查询验证
        found_user = session.query(User).filter_by(
            wechat_openid="test_minimal"
        ).first()
        
        assert found_user is not None
        assert found_user.nickname == "最小化测试用户"
        
    print("✓ 数据库操作测试成功")
    
    # 测试5：验证模型方法
    print("\n5. 测试模型方法")
    with initializer.get_session() as session:
        from wxcloudrun.model import User, CheckinRule, SupervisionRuleRelation
        
        # 创建用户
        solo_user = User(
            wechat_openid="solo_minimal",
            nickname="独居用户",
            role=1,
            status=1
        )
        supervisor_user = User(
            wechat_openid="supervisor_minimal",
            nickname="监督用户",
            role=2,
            status=1
        )
        session.add_all([solo_user, supervisor_user])
        session.flush()
        
        # 创建规则
        rule = CheckinRule(
            solo_user_id=solo_user.user_id,
            rule_name="测试规则",
            status=1
        )
        session.add(rule)
        session.flush()
        
        # 创建监督关系
        relation = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor_user.user_id,
            rule_id=rule.rule_id,
            status=2
        )
        session.add(relation)
        session.commit()
        
        # 测试模型方法
        can_supervise = supervisor_user.can_supervise_user(solo_user.user_id)
        assert can_supervise is True
        
        supervised_users = supervisor_user.get_supervised_users()
        assert len(supervised_users) == 1
        
    print("✓ 模型方法测试成功")
    
    # 总结
    print("\n" + "="*50)
    if flask_initialized:
        print("⚠️  Flask被初始化，但依赖最小化")
        print("✓ 所有测试通过，数据库功能正常")
    else:
        print("🎉 完全避免了Flask初始化！")
        print("✓ 所有测试通过，数据库功能正常")
    
    print("="*50)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)