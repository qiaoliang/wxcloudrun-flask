# tests/test_rule_supervision_model.py
import pytest
from datetime import datetime
from wxcloudrun.model import RuleSupervision, CheckinRule, User


def test_rule_supervision_model_creation():
    """Test creating a RuleSupervision model instance."""
    supervision = RuleSupervision()
    supervision.rule_id = 1
    supervision.solo_user_id = 1
    supervision.supervisor_user_id = 2
    supervision.invited_by_user_id = 1
    supervision.status = 0
    supervision.invitation_message = "请监督我打卡"
    supervision.created_at = datetime.now()
    supervision.updated_at = datetime.now()
    
    assert supervision.rule_id == 1
    assert supervision.solo_user_id == 1
    assert supervision.supervisor_user_id == 2
    assert supervision.invited_by_user_id == 1
    assert supervision.status == 0
    assert supervision.invitation_message == "请监督我打卡"
    assert supervision.created_at is not None
    assert supervision.updated_at is not None
    assert supervision.__tablename__ == 'rule_supervisions'


def test_rule_supervision_status_mapping():
    """Test status mapping functionality."""
    supervision = RuleSupervision()
    
    # Test status mapping
    supervision.status = 0
    assert supervision.status_name == 'pending'
    
    supervision.status = 1
    assert supervision.status_name == 'confirmed'
    
    supervision.status = 2
    assert supervision.status_name == 'rejected'
    
    supervision.status = 3
    assert supervision.status_name == 'cancelled'
    
    # Test invalid status
    supervision.status = 99
    assert supervision.status_name == 'unknown'


def test_rule_supervision_is_active():
    """Test is_active property."""
    supervision = RuleSupervision()
    
    # Test active status
    supervision.status = 1
    assert supervision.is_active is True
    
    # Test inactive statuses
    supervision.status = 0
    assert supervision.is_active is False
    
    supervision.status = 2
    assert supervision.is_active is False
    
    supervision.status = 3
    assert supervision.is_active is False


def test_rule_supervision_to_dict():
    """Test to_dict method."""
    supervision = RuleSupervision()
    supervision.rule_supervision_id = 1
    supervision.rule_id = 1
    supervision.solo_user_id = 1
    supervision.supervisor_user_id = 2
    supervision.invited_by_user_id = 1
    supervision.status = 0
    supervision.invitation_message = "请监督我打卡"
    supervision.created_at = datetime.now()
    supervision.updated_at = datetime.now()
    
    result = supervision.to_dict()
    
    assert isinstance(result, dict)
    assert result['rule_supervision_id'] == 1
    assert result['rule_id'] == 1
    assert result['solo_user_id'] == 1
    assert result['supervisor_user_id'] == 2
    assert result['invited_by_user_id'] == 1
    assert result['status'] == 0
    assert result['status_name'] == 'pending'
    assert result['invitation_message'] == "请监督我打卡"
    assert 'created_at' in result
    assert 'updated_at' in result


def test_get_status_value():
    """Test get_status_value class method."""
    assert RuleSupervision.get_status_value('pending') == 0
    assert RuleSupervision.get_status_value('confirmed') == 1
    assert RuleSupervision.get_status_value('rejected') == 2
    assert RuleSupervision.get_status_value('cancelled') == 3
    assert RuleSupervision.get_status_value('invalid') is None