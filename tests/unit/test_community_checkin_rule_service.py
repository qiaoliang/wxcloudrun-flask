import pytest
import sys
import os
import re

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import User, Community,CommunityCheckinRule
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.community_service import CommunityService
from wxcloudrun.user_service import UserService
from wxcloudrun.utils.strutil import random_str,uuid_str

class TestCommunityCheckinRulesService:

    def test_create_community_rule(self, test_session):
        """测试默认社区识别"""

        # Arrange - 创建一个用户
        new_user = User(
            wechat_openid="test_openid_new",
            nickname="微信新用户",
            avatar_url="https://example.com/1.jpg"
        )
        a_user = UserService.create_user(new_user)

        # Arrange - 创建一个社区
        cumm_name, description = random_str(8), random_str(16)
        cumm = CommunityService.create_community(cumm_name, description,a_user.user_id, None, None, a_user.user_id, None, None, test_session)
        test_session.commit()

        # Act - 创建一个社区签到规则
        result = CommunityCheckinRuleService.create_community_rule(
            rule_data={
                'rule_name': '默认社区签到规则',
                'community_id': cumm['community_id'],
                'start_time': '08:00:00',
                'end_time': '18:00:00',
                'checkin_days': [1, 2, 3, 4, 5],
                'checkin_times': [
                    {'start_time': '08:00:00',}
                ]
            },
            community_id=cumm['community_id'],
            created_by=a_user.user_id
        )
        assert result.community_rule_id == 1

