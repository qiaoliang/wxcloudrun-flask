"""
测试社区用户管理的单元测试
验证同一用户不能被添加到同一社区两次的功能
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.model_community_extensions import CommunityMember
from wxcloudrun.views.community import add_community_users
from wxcloudrun.model import User, Community
from wxcloudrun import db
from wxcloudrun.response import make_err_response, make_succ_response


class TestCommunityUserManagement:
    """测试社区用户管理功能"""

    def test_same_user_cannot_be_added_twice_to_same_community(self):
        """
        RED阶段：测试同一用户不能被添加到同一社区两次
        这个测试应该先失败，然后我们编写代码使其通过
        """
        # 准备测试数据
        community_id = 1
        user_id = 123
        user_ids = [user_id]
        
        # 模拟已存在的社区成员
        existing_member = CommunityMember(
            community_id=community_id,
            user_id=user_id
        )
        
        # 模拟数据库查询
        with patch('wxcloudrun.views.community.verify_token') as mock_verify:
            with patch('wxcloudrun.views.community.User') as mock_user_model:
                with patch('wxcloudrun.views.community.Community') as mock_community_model:
                    with patch('wxcloudrun.views.community.CommunityMember') as mock_member_model:
                        with patch('wxcloudrun.views.community.request') as mock_request:
                            with patch('wxcloudrun.views.community.db.session') as mock_session:
                                # 设置模拟返回值
                                mock_verify.return_value = ({'user_id': 456}, None)  # 当前操作用户
                                
                                # 模拟当前用户（有权限的管理员）
                                current_user = MagicMock()
                                current_user.role = 4  # super_admin
                                mock_user_model.query.get.return_value = current_user
                                
                                # 模拟社区存在
                                community = MagicMock()
                                mock_community_model.query.get.return_value = community
                                
                                # 模拟请求参数
                                mock_request.get_json.return_value = {
                                    'community_id': community_id,
                                    'user_ids': user_ids
                                }
                                
                                # 模拟目标用户存在
                                target_user = MagicMock()
                                mock_user_model.query.get.side_effect = [
                                    current_user,  # 第一次返回当前用户
                                    target_user     # 第二次返回目标用户
                                ]
                                
                                # 关键：模拟已存在的成员记录
                                mock_member_model.query.filter_by.return_value.first.return_value = existing_member
                                
                                # 执行添加用户操作
                                response = add_community_users()
                                
                                # 验证响应
                                assert response[1] == 200
                                data = response[0].get_json()
                                assert data['code'] == 0  # 应该返回错误，因为有用户已在社区
                                assert 'added_count' in data['data']
                                assert data['data']['added_count'] == 0  # 没有添加任何用户
                                
                                # 验证失败列表
                                failed = data['data']['failed']
                                assert len(failed) == 1
                                assert failed[0]['user_id'] == user_id
                                assert failed[0]['reason'] == '用户已在社区'
                                
                                # 验证没有尝试添加重复的用户
                                mock_session.add.assert_not_called()
                                mock_session.commit.assert_called_once()

    def test_can_add_different_users_to_same_community(self):
        """
        测试不同用户可以被添加到同一社区
        这是正面测试用例，确保正常功能不受影响
        """
        # 准备测试数据
        community_id = 1
        user_ids = [123, 456]  # 两个不同的用户
        
        with patch('wxcloudrun.views.community.verify_token') as mock_verify:
            with patch('wxcloudrun.views.community.User') as mock_user_model:
                with patch('wxcloudrun.views.community.Community') as mock_community_model:
                    with patch('wxcloudrun.views.community.CommunityMember') as mock_member_model:
                        with patch('wxcloudrun.views.community.request') as mock_request:
                            with patch('wxcloudrun.views.community.db.session') as mock_session:
                                # 设置模拟返回值
                                mock_verify.return_value = ({'user_id': 789}, None)
                                
                                # 模拟当前用户
                                current_user = MagicMock()
                                current_user.role = 4
                                mock_user_model.query.get.return_value = current_user
                                
                                # 模拟社区存在
                                community = MagicMock()
                                mock_community_model.query.get.return_value = community
                                
                                # 模拟请求参数
                                mock_request.get_json.return_value = {
                                    'community_id': community_id,
                                    'user_ids': user_ids
                                }
                                
                                # 模拟目标用户存在
                                user1 = MagicMock()
                                user2 = MagicMock()
                                mock_user_model.query.get.side_effect = [
                                    current_user,  # 当前用户
                                    user1,          # 第一个目标用户
                                    user2           # 第二个目标用户
                                ]
                                
                                # 模拟没有已存在的成员记录
                                mock_member_model.query.filter_by.return_value.first.return_value = None
                                
                                # 执行添加用户操作
                                response = add_community_users()
                                
                                # 验证响应
                                assert response[1] == 200
                                data = response[0].get_json()
                                assert data['code'] == 1  # 应该成功
                                assert data['data']['added_count'] == 2  # 两个用户都添加成功
                                assert len(data['data']['failed']) == 0
                                
                                # 验证确实调用了添加操作
                                assert mock_session.add.call_count == 2
                                mock_session.commit.assert_called_once()

    def test_can_add_same_user_to_different_communities(self):
        """
        测试同一用户可以被添加到不同的社区
        确保约束只在同一社区内生效
        """
        # 准备测试数据
        community_id_1 = 1
        community_id_2 = 2
        user_id = 123
        
        # 第一次添加到社区1
        with patch('wxcloudrun.views.community.verify_token') as mock_verify:
            with patch('wxcloudrun.views.community.User') as mock_user_model:
                with patch('wxcloudrun.views.community.Community') as mock_community_model:
                    with patch('wxcloudrun.views.community.CommunityMember') as mock_member_model:
                        with patch('wxcloudrun.views.community.request') as mock_request:
                            with patch('wxcloudrun.views.community.db.session') as mock_session:
                                # 设置模拟返回值
                                mock_verify.return_value = ({'user_id': 456}, None)
                                
                                current_user = MagicMock()
                                current_user.role = 4
                                mock_user_model.query.get.return_value = current_user
                                
                                community = MagicMock()
                                mock_community_model.query.get.return_value = community
                                
                                # 第一次添加到社区1
                                mock_request.get_json.return_value = {
                                    'community_id': community_id_1,
                                    'user_ids': [user_id]
                                }
                                
                                target_user = MagicMock()
                                mock_user_model.query.get.side_effect = [
                                    current_user,
                                    target_user
                                ]
                                
                                # 社区1中没有该用户
                                mock_member_model.query.filter_by.return_value.first.return_value = None
                                
                                response1 = add_community_users()
                                assert response1[0].get_json()['code'] == 1
                                
                                # 第二次添加到社区2
                                mock_request.get_json.return_value = {
                                    'community_id': community_id_2,
                                    'user_ids': [user_id]
                                }
                                
                                # 社区2中也没有该用户
                                mock_member_model.query.filter_by.return_value.first.return_value = None
                                
                                response2 = add_community_users()
                                assert response2[0].get_json()['code'] == 1
                                
                                # 两次都应该成功
                                assert mock_session.add.call_count == 2