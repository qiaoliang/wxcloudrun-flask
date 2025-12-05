"""
打卡规则软删除功能测试
"""
import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wxcloudrun import app, db
from wxcloudrun.model import CheckinRule, CheckinRecord, User
from wxcloudrun.dao import delete_checkin_rule_by_id, query_checkin_rules_by_user_id


class TestCheckinRuleSoftDelete:
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.app_context = app.app_context()
        self.app_context.push()
        
        # 创建测试用户
        self.test_user = User(
            wechat_openid="test_openid_123",
            nickname="测试用户",
            role=1  # 独居者
        )
        db.session.add(self.test_user)
        db.session.commit()
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        # 清理测试数据
        CheckinRecord.query.filter_by(solo_user_id=self.test_user.user_id).delete()
        CheckinRule.query.filter_by(solo_user_id=self.test_user.user_id).delete()
        User.query.filter_by(user_id=self.test_user.user_id).delete()
        db.session.commit()
        
        self.app_context.pop()
    
    def test_soft_delete_rule_with_records(self):
        """测试有打卡记录的规则软删除"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="测试规则",
            status=1
        )
        db.session.add(rule)
        db.session.commit()
        
        # 添加打卡记录
        record = CheckinRecord(
            rule_id=rule.rule_id,
            solo_user_id=self.test_user.user_id,
            status=1,
            planned_time=datetime.now()
        )
        db.session.add(record)
        db.session.commit()
        
        # 执行软删除
        result = delete_checkin_rule_by_id(rule.rule_id)
        
        # 验证结果
        assert result is True
        assert rule.status == 2  # 已删除状态
        assert rule.deleted_at is not None
        
        # 验证记录仍然存在
        assert CheckinRecord.query.filter_by(rule_id=rule.rule_id).count() == 1
    
    def test_soft_delete_rule_without_records(self):
        """测试无打卡记录的规则软删除"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="测试规则",
            status=1
        )
        db.session.add(rule)
        db.session.commit()
        
        # 执行软删除
        result = delete_checkin_rule_by_id(rule.rule_id)
        
        # 验证结果
        assert result is True
        assert rule.status == 2
        assert rule.deleted_at is not None
    
    def test_delete_nonexistent_rule(self):
        """测试删除不存在的规则"""
        with pytest.raises(ValueError, match="没有找到 id 为 999 的打卡规则"):
            delete_checkin_rule_by_id(999)
    
    def test_query_rules_exclude_deleted(self):
        """测试查询规则时排除已删除的规则"""
        # 创建正常规则
        active_rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="正常规则",
            status=1
        )
        
        # 创建已删除规则
        deleted_rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="已删除规则",
            status=2,
            deleted_at=datetime.now()
        )
        
        # 创建禁用规则
        disabled_rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="禁用规则",
            status=0
        )
        
        db.session.add(active_rule)
        db.session.add(deleted_rule)
        db.session.add(disabled_rule)
        db.session.commit()
        
        # 查询规则
        rules = query_checkin_rules_by_user_id(self.test_user.user_id)
        
        # 验证只返回正常和禁用的规则，不包括已删除的
        assert len(rules) == 2
        rule_names = [rule.rule_name for rule in rules]
        assert "正常规则" in rule_names
        assert "禁用规则" in rule_names
        assert "已删除规则" not in rule_names
    
    def test_soft_delete_preserves_data_integrity(self):
        """测试软删除保持数据完整性"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=self.test_user.user_id,
            rule_name="数据完整性测试规则",
            status=1
        )
        db.session.add(rule)
        db.session.commit()
        
        # 添加多条打卡记录
        for i in range(3):
            record = CheckinRecord(
                rule_id=rule.rule_id,
                solo_user_id=self.test_user.user_id,
                status=1 if i < 2 else 0,  # 前两条已打卡，第三条未打卡
                planned_time=datetime.now()
            )
            db.session.add(record)
        db.session.commit()
        
        # 执行软删除
        delete_checkin_rule_by_id(rule.rule_id)
        
        # 验证所有打卡记录仍然存在
        records = CheckinRecord.query.filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 3
        
        # 验证记录状态保持不变
        checked_count = sum(1 for r in records if r.status == 1)
        missed_count = sum(1 for r in records if r.status == 0)
        assert checked_count == 2
        assert missed_count == 1


if __name__ == '__main__':
    pytest.main([__file__])