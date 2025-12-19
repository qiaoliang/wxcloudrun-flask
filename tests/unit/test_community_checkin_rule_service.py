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
        # 创建多个社区
        communities_data = [
            {'name': f'普通社区1{uuid_str(8)}', 'is_default': False},
            {'name': DEFUALT_COMMUNITY_NAME, 'is_default': True},
            {'name': f'普通社区2{uuid_str(8)}', 'is_default': False},
        ]
        # Arrange - 只有openid 和 nickname, avatar_url
        new_user = User(
            wechat_openid="test_openid_new",
            nickname="微信新用户",
            avatar_url="https://example.com/1.jpg"
        )

        # Act - 执行被测试的方法
        a_user = UserService.create_user(new_user)
        cumm_name, description, creator_id = random_str(8), random_str(16), a_user.user_id

        cumm = CommunityService.create_community(cumm_name, description,a_user.user_id, None, None, a_user.user_id, None, None, test_session)
        test_session.commit()

        # 查找默认社区
        default_community = test_session.query(Community).filter_by(
            name=cumm["name"]
        ).first()
        assert default_community.name == cumm["name"]
        result = CommunityCheckinRuleService.create_community_rule(
            rule_data={
                'rule_name': '默认社区签到规则',
                'community_id': default_community.community_id,
                'start_time': '08:00:00',
                'end_time': '18:00:00',
                'checkin_days': [1, 2, 3, 4, 5],
                'checkin_times': [
                    {'start_time': '08:00:00',}
                ]
            },
            community_id=default_community.community_id,
            created_by=1
        )
        assert result.community_rule_id == 1

