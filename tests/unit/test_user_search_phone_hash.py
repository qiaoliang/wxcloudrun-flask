"""
测试用户搜索API的单元测试
专门测试通过完整手机号hash搜索用户的功能
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.views.user import search_users
from wxcloudrun.model import User
from wxcloudrun import dao, db
from hashlib import sha256

class TestUserSearchByPhoneHash:
    """测试通过手机号hash搜索用户的功能"""

    @pytest.fixture
    def mock_current_user(self):
        """创建模拟的当前用户（超级管理员）"""
        user = MagicMock()
        user.user_id = 1
        user.role = 4  # 超级管理员
        user.can_manage_community = MagicMock(return_value=True)
        return user

    @pytest.fixture
    def mock_target_user(self):
        """创建模拟的目标用户"""
        user = MagicMock()
        user.user_id = 2
        user.nickname = "测试用户"
        user.phone_number = "138****8888"
        user.phone_hash = sha256(
            f"default_secret:13888888888".encode('utf-8')).hexdigest()
        user.avatar_url = "https://example.com/avatar.jpg"
        user.updated_at = "2025-12-12"
        return user

    def test_search_by_full_phone_number_hash(self, mock_current_user, mock_target_user):
        """
        RED阶段：测试通过完整手机号hash搜索用户
        这个测试应该先失败，因为功能还未实现
        """
        # 准备测试数据
        full_phone = "13888888888"
        expected_hash = sha256(
            f"default_secret:{full_phone}".encode('utf-8')).hexdigest()
        
        # 确保目标用户的phone_hash匹配
        assert mock_target_user.phone_hash == expected_hash
        
        # 模拟数据库查询
        with patch('wxcloudrun.views.user.User') as mock_user_model:
            with patch('wxcloudrun.views.user.query_user_by_openid') as mock_query:
                # 设置模拟返回值
                mock_query.return_value = mock_current_user
                mock_user_model.query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_target_user]
                
                # 模拟请求参数
                with patch('wxcloudrun.views.user.request') as mock_request:
                    mock_request.args = {
                        'keyword': full_phone,
                        'scope': 'all',
                        'limit': '10'
                    }
                    
                    # 执行搜索
                    decoded = {'openid': 'test_openid'}
                    response = search_users(decoded)
                    
                    # 验证响应
                    assert response[1] == 200
                    data = response[0].get_json()
                    assert data['code'] == 1
                    assert len(data['data']['users']) == 1
                    assert data['data']['users'][0]['user_id'] == 2
                    assert data['data']['users'][0]['nickname'] == "测试用户"
                    
                    # 验证使用了正确的查询条件
                    # 这里应该验证查询中使用了phone_hash匹配
                    # 但由于当前实现可能不正确，这个测试会失败
                    mock_user_model.query.filter.assert_called_once()
                    filter_call_args = mock_user_model.query.filter.call_args[0][0]
                    
                    # 验证查询条件包含phone_hash匹配
                    # 这个断言可能会失败，因为当前实现可能不正确
                    assert hasattr(filter_call_args, 'right')  # 应该是一个比较表达式
                    assert filter_call_args.right.value == expected_hash

    def test_search_by_partial_phone_should_not_use_hash(self, mock_current_user, mock_target_user):
        """
        测试使用部分手机号搜索时不应使用hash匹配
        """
        partial_phone = "138****8888"
        
        with patch('wxcloudrun.views.user.User') as mock_user_model:
            with patch('wxcloudrun.views.user.query_user_by_openid') as mock_query:
                mock_query.return_value = mock_current_user
                mock_user_model.query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_target_user]
                
                with patch('wxcloudrun.views.user.request') as mock_request:
                    mock_request.args = {
                        'keyword': partial_phone,
                        'scope': 'all',
                        'limit': '10'
                    }
                    
                    decoded = {'openid': 'test_openid'}
                    response = search_users(decoded)
                    
                    # 验证响应
                    assert response[1] == 200
                    data = response[0].get_json()
                    assert data['code'] == 1
                    
                    # 验证使用了模糊匹配而不是hash匹配
                    mock_user_model.query.filter.assert_called_once()
                    filter_call_args = mock_user_model.query.filter.call_args[0][0]
                    
                    # 应该是ILIKE模糊匹配，不是hash精确匹配
                    assert "ilike" in str(filter_call_args).lower()

    def test_search_by_nickname_should_not_use_hash(self, mock_current_user, mock_target_user):
        """
        测试使用昵称搜索时不应使用hash匹配
        """
        nickname = "测试用户"
        
        with patch('wxcloudrun.views.user.User') as mock_user_model:
            with patch('wxcloudrun.views.user.query_user_by_openid') as mock_query:
                mock_query.return_value = mock_current_user
                mock_user_model.query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_target_user]
                
                with patch('wxcloudrun.views.user.request') as mock_request:
                    mock_request.args = {
                        'keyword': nickname,
                        'scope': 'all',
                        'limit': '10'
                    }
                    
                    decoded = {'openid': 'test_openid'}
                    response = search_users(decoded)
                    
                    # 验证响应
                    assert response[1] == 200
                    data = response[0].get_json()
                    assert data['code'] == 1
                    
                    # 验证使用了昵称模糊匹配
                    mock_user_model.query.filter.assert_called_once()