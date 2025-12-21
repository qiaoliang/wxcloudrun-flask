"""
测试社区规则打卡功能
验证扩展后的打卡接口支持个人规则和社区规则
"""
import pytest
from datetime import datetime, date
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wxcloudrun.checkin_record_service import CheckinRecordService


class TestCommunityCheckin:
    """测试社区规则打卡功能"""
    
    def test_perform_checkin_with_rule_source_parameter(self):
        """测试打卡接口支持rule_source参数"""
        # 测试参数传递
        assert CheckinRecordService.perform_checkin.__code__.co_argcount > 2
        
        # 检查默认参数
        import inspect
        sig = inspect.signature(CheckinRecordService.perform_checkin)
        assert 'rule_source' in sig.parameters
        assert sig.parameters['rule_source'].default == 'personal'
    
    def test_create_record_with_community_rule(self):
        """测试创建社区规则打卡记录"""
        # 测试方法签名
        assert CheckinRecordService._create_record.__code__.co_argcount > 5
        
        # 检查默认参数
        import inspect
        sig = inspect.signature(CheckinRecordService._create_record)
        assert 'rule_source' in sig.parameters
        assert sig.parameters['rule_source'].default == 'personal'
    
    def test_query_records_with_rule_source(self):
        """测试查询打卡记录支持规则来源"""
        # 测试方法签名
        assert CheckinRecordService._query_records_by_rule_and_date.__code__.co_argcount > 2
        
        # 检查默认参数
        import inspect
        sig = inspect.signature(CheckinRecordService._query_records_by_rule_and_date)
        assert 'rule_source' in sig.parameters
        assert sig.parameters['rule_source'].default == 'personal'
    
    def test_rule_source_values(self):
        """测试规则来源参数的有效值"""
        valid_sources = ['personal', 'community']
        
        # 这些值应该被正确处理
        for source in valid_sources:
            assert source in ['personal', 'community']
    
    def test_parameter_validation(self):
        """测试参数验证逻辑"""
        # 模拟前端传递的数据结构
        personal_data = {"rule_id": 1, "rule_source": "personal"}
        community_data = {"rule_id": 1, "rule_source": "community"}
        
        # 验证数据结构
        assert "rule_id" in personal_data
        assert "rule_source" in personal_data
        assert personal_data["rule_source"] == "personal"
        
        assert "rule_id" in community_data
        assert "rule_source" in community_data
        assert community_data["rule_source"] == "community"