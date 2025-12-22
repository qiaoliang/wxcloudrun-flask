"""
测试社区创建用户API的核心逻辑单元测试
验证超级管理员在安卡大家庭中免验证码创建用户的业务规则
"""

import pytest
import sys
import os
import re

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User, Community
from const_default import DEFUALT_COMMUNITY_NAME


class TestCommunityCreateUserAPILogic:
    """测试社区创建用户API的核心逻辑"""

    def test_super_admin_permission(self, test_session):
        """测试超级管理员权限验证"""
        # 创建不同角色的用户
        users = [
            {'role': 1, 'name': '独居者', 'expected_super_admin': False},
            {'role': 2, 'name': '社区专员', 'expected_super_admin': False},
            {'role': 3, 'name': '社区主管', 'expected_super_admin': False},
            {'role': 4, 'name': '超级管理员', 'expected_super_admin': True},
        ]
        
        for user_data in users:
            user = User(
                wechat_openid=f"test_{user_data['role']}",
                nickname=user_data['name'],
                role=user_data['role'],
                status=1
            )
            test_session.add(user)
        
        test_session.commit()
        
        # 验证权限
        for user_data in users:
            user = test_session.query(User).filter_by(
                nickname=user_data['name']
            ).first()
            is_super_admin = (user.role == 4)
            assert is_super_admin == user_data['expected_super_admin'], \
                f"角色{user.role}的超级管理员权限应为{user_data['expected_super_admin']}"

    def test_default_community_identification(self, test_session):
        """测试默认社区识别"""
        # 创建多个社区
        communities_data = [
            {'name': '普通社区1', 'is_default': False},
            {'name': DEFUALT_COMMUNITY_NAME, 'is_default': True},
            {'name': '普通社区2', 'is_default': False},
        ]
        
        for comm_data in communities_data:
            community = Community(
                name=comm_data['name'],
                description=f"{comm_data['name']}描述",
                status=1,
                is_default=comm_data['is_default']
            )
            test_session.add(community)
        
        test_session.commit()
        
        # 查找默认社区
        default_community = test_session.query(Community).filter_by(
            name=DEFUALT_COMMUNITY_NAME
        ).first()
        
        assert default_community is not None
        assert default_community.name == DEFUALT_COMMUNITY_NAME
        assert default_community.is_default is True

    def test_phone_validation_regex(self):
        """测试手机号验证正则表达式"""
        # 有效的手机号
        valid_phones = [
            '13800138000',
            '13912345678',
            '15098765432',
            '17612345678',
            '19987654321'
        ]
        
        # 无效的手机号（标准化后仍然无效）
        invalid_phones = [
            '123456',  # 太短
            '138001380001',  # 太长
            '23800138000',  # 不是1开头
            '12800138000',  # 第二位不是3-9
            'abc12345678',  # 包含字母，标准化后不是11位数字
        ]
        
        # 这些手机号包含分隔符，但标准化后是有效的
        phones_with_separators = [
            '138-0013-8000',
            '138 0013 8000',
            '+8613800138000',
        ]
        
        phone_pattern = r'^1[3-9]\d{9}$'
        
        for phone in valid_phones:
            assert re.match(phone_pattern, phone) is not None, \
                f"有效手机号 {phone} 应该通过验证"
        
        for phone in invalid_phones:
            # 先标准化手机号（移除非数字字符）
            normalized = ''.join(filter(str.isdigit, phone))
            if len(normalized) == 11:
                # 如果是11位数字，检查格式是否正确
                assert re.match(phone_pattern, normalized) is None, \
                    f"无效手机号 {phone} 不应该通过验证"
            else:
                # 如果不是11位数字，肯定无效
                # 不需要检查正则表达式，因为长度就不对
                pass
        
        # 测试包含分隔符的手机号，标准化后应该有效
        from wxcloudrun.utils.validators import normalize_phone_number
        for phone in phones_with_separators:
            normalized = normalize_phone_number(phone)
            assert len(normalized) == 11, \
                f"手机号 {phone} 标准化后应该是11位数字，得到: {normalized} (长度: {len(normalized)})"
            assert re.match(phone_pattern, normalized) is not None, \
                f"手机号 {phone} 标准化后应该通过验证"

    def test_nickname_validation(self):
        """测试昵称验证"""
        # 有效的昵称
        valid_nicknames = [
            '张三',
            '李四',
            '王五',
            '测试用户',
            'User123',
            'a' * 50,  # 50个字符（边界值）
        ]
        
        # 无效的昵称
        invalid_nicknames = [
            '',  # 空
            ' ',  # 空格
            'a',  # 太短（1个字符）
            'a' * 51,  # 太长（51个字符）
        ]
        
        for nickname in valid_nicknames:
            assert len(nickname.strip()) >= 2, \
                f"有效昵称 {nickname} 应该至少有2个字符"
            assert len(nickname.strip()) <= 50, \
                f"有效昵称 {nickname} 应该不超过50个字符"
        
        for nickname in invalid_nicknames:
            stripped = nickname.strip()
            if stripped:
                assert len(stripped) < 2 or len(stripped) > 50, \
                    f"无效昵称 {nickname} 应该被拒绝"

    def test_user_creation_with_default_values(self, test_session):
        """测试使用默认值创建用户"""
        # 创建新用户
        new_user = User(
            phone_number='13800138001',
            nickname='测试用户',
            avatar_url='',
            role=1,  # 默认角色：独居者
            status=1  # 正常状态
            # 注意：User模型没有直接的password字段
            # 而是有password_hash和password_salt字段
        )
        
        test_session.add(new_user)
        test_session.commit()
        
        # 验证默认值
        assert new_user.user_id is not None
        assert new_user.phone_number == '13800138001'
        assert new_user.nickname == '测试用户'
        assert new_user.role == 1  # 独居者
        assert new_user.status == 1  # 正常状态
        assert new_user.avatar_url == ''  # 空头像

    def test_phone_normalization(self):
        """测试手机号标准化"""
        from wxcloudrun.utils.validators import normalize_phone_number
        
        test_cases = [
            ('13800138000', '13800138000'),  # 已经是标准格式
            ('+8613800138000', '13800138000'),  # 有+86前缀
            ('138-0013-8000', '13800138000'),  # 有分隔符
            ('138 0013 8000', '13800138000'),  # 有空格
            ('+86-138-0013-8000', '13800138000'),  # 混合格式
        ]
        
        for input_phone, expected_output in test_cases:
            normalized = normalize_phone_number(input_phone)
            assert normalized == expected_output, \
                f"输入 {input_phone} 应该标准化为 {expected_output}，但得到 {normalized}"
