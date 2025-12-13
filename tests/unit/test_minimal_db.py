"""
测试最小化Flask依赖的数据库初始化
验证与生产环境的兼容性
"""
import pytest
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import User, Community, CheckinRule, CheckinRecord, SupervisionRuleRelation
from datetime import datetime


class TestMinimalDBInit:
    """测试最小化Flask依赖的数据库初始化"""

    def test_database_creation(self, test_session):
        """测试数据库创建和基础数据"""
        # 创建默认社区
        default_community = Community(
            name="安卡大家庭",
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(default_community)
        test_session.commit()
        
        # 验证默认社区存在
        found_community = test_session.query(Community).filter_by(
            name="安卡大家庭"
        ).first()
        
        assert found_community is not None
        assert found_community.is_default is True
        assert found_community.status == 1
        
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_test",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1
        )
        test_session.add(super_admin)
        test_session.commit()
        
        # 验证超级管理员存在
        found_admin = test_session.query(User).filter_by(
            wechat_openid="super_admin_test"
        ).first()
        
        assert found_admin is not None
        assert found_admin.role == 4
        assert found_admin.status == 1

    def test_model_operations(self, test_session):
        """测试模型操作（与生产环境相同）"""
        # 创建用户
        user = User(
            wechat_openid="test_user_1",
            nickname="测试用户1",
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()  # 获取ID但不提交
        
        # 创建打卡规则
        rule = CheckinRule(
            solo_user_id=user.user_id,
            rule_name="测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()
        
        # 创建打卡记录
        record = CheckinRecord(
            rule_id=rule.rule_id,
            solo_user_id=user.user_id,
            status=1,
            planned_time=datetime.now()
        )
        test_session.add(record)
        test_session.commit()
        
        # 验证数据创建成功
        assert user.user_id is not None
        assert rule.rule_id is not None
        assert record.record_id is not None
        
        # 测试查询
        found_user = test_session.query(User).filter_by(
            wechat_openid="test_user_1"
        ).first()
        assert found_user is not None
        assert found_user.nickname == "测试用户1"
        
        # 测试关联查询
        user_rules = test_session.query(CheckinRule).filter_by(
            solo_user_id=user.user_id
        ).all()
        assert len(user_rules) == 1

    def test_supervision_relation(self, test_session):
        """测试监督关系（使用生产环境的模型方法）"""
        # 创建用户
        solo_user = User(
            wechat_openid="solo_user_test",
            nickname="独居用户",
            role=1,
            status=1
        )
        supervisor_user = User(
            wechat_openid="supervisor_test",
            nickname="监督员",
            role=2,
            status=1
        )
        test_session.add_all([solo_user, supervisor_user])
        test_session.flush()
        
        # 创建打卡规则
        rule = CheckinRule(
            solo_user_id=solo_user.user_id,
            rule_name="监督测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()
        
        # 创建监督关系
        supervision = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor_user.user_id,
            rule_id=rule.rule_id,
            status=1
        )
        test_session.add(supervision)
        test_session.commit()
        
        # 验证监督关系创建成功
        assert supervision.relation_id is not None
        
        # 测试查询监督关系
        found_supervision = test_session.query(SupervisionRuleRelation).filter_by(
            solo_user_id=solo_user.user_id
        ).first()
        assert found_supervision is not None
        assert found_supervision.supervisor_user_id == supervisor_user.user_id

    def test_database_constraints(self, test_session):
        """测试数据库约束"""
        # 创建用户
        user = User(
            wechat_openid="constraint_test_user",
            nickname="约束测试用户",
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.commit()
        
        # 尝试创建相同OpenID的用户
        duplicate_user = User(
            wechat_openid="constraint_test_user",  # 相同的OpenID
            nickname="重复用户",
            role=1,
            status=1
        )
        test_session.add(duplicate_user)
        
        # 应该抛出异常
        with pytest.raises(Exception) as exc_info:
            test_session.commit()
        
        # 验证是唯一约束错误
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚
        test_session.rollback()

    def test_database_transaction_rollback(self, test_session):
        """测试数据库事务回滚"""
        # 创建用户
        user = User(
            wechat_openid="rollback_test_user",
            nickname="回滚测试用户",
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.commit()
        
        # 开始新事务
        user_count_before = test_session.query(User).count()
        
        # 尝试添加数据但回滚
        try:
            new_user = User(
                wechat_openid="will_be_rolled_back",
                nickname="将被回滚",
                role=1,
                status=1
            )
            test_session.add(new_user)
            
            # 模拟错误
            raise ValueError("测试回滚")
        except ValueError:
            test_session.rollback()
        
        # 验证数据没有被保存
        user_count_after = test_session.query(User).count()
        assert user_count_before == user_count_after
        
        # 验证新用户不存在
        rolled_back_user = test_session.query(User).filter_by(
            wechat_openid="will_be_rolled_back"
        ).first()
        assert rolled_back_user is None

    def test_database_connection_lifecycle(self, test_session):
        """测试数据库连接生命周期"""
        # 验证会话是活跃的
        assert test_session.is_active
        
        # 执行简单查询
        user_count = test_session.query(User).count()
        assert isinstance(user_count, int)
        
        # 会话会在上下文管理器退出时自动关闭