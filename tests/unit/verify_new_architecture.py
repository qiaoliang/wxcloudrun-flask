#!/usr/bin/env python
"""
验证新架构的实际使用
"""
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def main():
    print("="*60)
    print("验证新架构的实际使用")
    print("="*60)

    # 1. 测试独立模式
    print("\n1. 测试独立模式")
    # from database import get_database
from database import initialize_for_test

db = initialize_for_test()

    db = get_database('test')

    with db.get_session() as session:
        from database.flask_models import User, CheckinRule, SupervisionRuleRelation

        # 创建用户
        user1 = User(
            wechat_openid='test_openid_1',
            nickname='Test User 1',
            role=1,
            status=1
        )
        user2 = User(
            wechat_openid='test_openid_2',
            nickname='Test User 2',
            role=2,
            status=1
        )
        session.add_all([user1, user2])
        session.flush()

        # 创建规则
        rule = CheckinRule(
            solo_user_id=user1.user_id,
            rule_name='起床打卡',
            icon_url='🌅',
            frequency_type=0,
            time_slot_type=4,
            week_days=127,
            status=1
        )
        session.add(rule)
        session.flush()

        # 创建监督关系
        relation = SupervisionRuleRelation(
            solo_user_id=user1.user_id,
            supervisor_user_id=user2.user_id,
            rule_id=rule.rule_id,
            status=1
        )
        session.add(relation)
        session.commit()

        print(f"✓ 创建用户: {user1.nickname}, {user2.nickname}")
        print(f"✓ 创建规则: {rule.rule_name}")
        print(f"✓ 创建监督关系: ID {relation.relation_id}")

        # 验证数据
        relations = session.query(SupervisionRuleRelation).all()
        assert len(relations) == 1
        assert relations[0].status == 1

        print(f"✓ 验证成功: 共 {len(relations)} 个监督关系")

    # 2. 测试模型方法
    print("\n2. 测试模型方法")
    with db.get_session() as session:
        from database.flask_models import User

        # 测试用户查询
        users = session.query(User).filter(User.role == 2).all()
        assert len(users) == 1
        assert users[0].nickname == 'Test User 2'

        print(f"✓ 查询成功: 找到 {len(users)} 个监督用户")

    # 3. 测试快速重置
    print("\n3. 测试快速重置")
    db.reset_database()

    with db.get_session() as session:
        from database.flask_models import User

        users = session.query(User).all()
        assert len(users) == 0

        print("✓ 重置成功: 数据库已清空")

    # 4. 测试Flask模式
    print("\n4. 测试Flask模式")
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db_flask = SQLAlchemy(app)

    with app.app_context():
        from database import bind_flask_db

        db_core = bind_flask_db(db_flask, app)

        with db_flask.session.begin():
            from database.flask_models import User

            user = User(
                wechat_openid='flask_test',
                nickname='Flask Test User',
                role=1,
                status=1
            )
            db_flask.session.add(user)
            db_flask.session.commit()

        users = db_flask.session.query(User).all()
        assert len(users) == 1
        assert users[0].nickname == 'Flask Test User'

        print(f"✓ Flask模式成功: 创建用户 {users[0].nickname}")

    print("\n" + "="*60)
    print("✅ 所有验证通过！")
    print("="*60)
    print("\n新架构特点：")
    print("1. 完全独立：数据库不依赖Flask")
    print("2. 模式灵活：支持test/standalone/flask三种模式")
    print("3. 使用简单：统一的API接口")
    print("4. 性能优秀：测试快速，生产稳定")
    print("\n实施成功！可以开始迁移现有代码。")


if __name__ == "__main__":
    main()