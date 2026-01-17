"""
社区移除用户集成测试
Happy path: 成功从社区中移除用户
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.integration.conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS
from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase


class TestCommunityRemoveUser(IntegrationTestBase):
    """社区移除用户集成测试"""

    def test_remove_community_user_success(self):
        """测试成功从社区中移除用户"""
        with self.app.app_context():
            # 创建社区主管（用于操作）
            manager = self.create_standard_test_user(role=3, test_context='remove_user_manager')

            # 创建测试社区
            community = self.create_test_community(
                name='测试社区_remove_user',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 创建普通用户
            member = self.create_standard_test_user(role=1, test_context='remove_user_member')

            # 将用户添加到社区（使用 UseCase 替代 Service）
            add_users_use_case = AddUsersToCommunityUseCase()
            result = add_users_use_case.execute(community.community_id, [member.user_id])

            # 验证用户添加成功
            assert result.is_success

            # 重新查询用户以获取更新后的 community_id
            from database.flask_models import User
            updated_member = self.db.session.get(User, member.user_id)
            assert updated_member.community_id == community.community_id

            # 提交数据到外层事务
            self.db.session.commit()

            # 获取主管的token
            manager_phone = manager.phone_number
            community_id = community.community_id
            member_id = member.user_id

        # 获取主管的token
        client = self.get_test_client()
        token = self.get_jwt_token(manager_phone)

        # 发送移除用户请求
        response = client.delete(
            f'/api/communities/{community_id}/users/{member_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['message'])
        assert data['data']['message'] == '移除成功'

        # 验证用户已从社区中移除
        from database.flask_models import User
        with self.app.app_context():
            updated_member = self.db.session.get(User, member_id)
            assert updated_member.community_id is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])