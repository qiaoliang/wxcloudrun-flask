# tests/unit/fixtures/user_builder.py
"""
User对象的Builder模式实现
提供链式调用接口创建特定配置的User对象
"""
from wxcloudrun.model import User


class UserBuilder:
    """User对象的Builder模式实现

    示例用法:
    user = UserBuilder()\
        .with_phone_number("13800138000")\
        .with_nickname("测试用户")\
        .as_solo_user()\
        .build()
    """

    def __init__(self):
        """初始化Builder，设置默认值"""
        self.user_data = {
            'wechat_openid': 'Original_openid_123456',
            'phone_number': '13200132000',
            'nickname': 'Original NickName',
            'avatar_url': 'https://example.com/original.jpg',
            'name': 'Original Name',
            'work_id': None,
            'is_solo_user': True,
            'is_supervisor': False,
            'is_community_worker': False,
            'role': 1,  # 默认是独居者
            'status': 1,  # 默认是正常状态
            'verification_status': 0,  # 默认是未申请
            'verification_materials': None,
            'community_id': None,
            'auth_type': 'phone',  # 默认是手机认证
            'linked_accounts': None,
            'refresh_token': None,
            'refresh_token_expire': None
        }

    def with_wechat_openid(self, openid):
        """设置微信OpenID

        Args:
            openid: 微信OpenID字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['wechat_openid'] = openid
        return self

    def with_phone_number(self, phone_number):
        """设置手机号码

        Args:
            phone_number: 手机号码字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['phone_number'] = phone_number
        return self

    def with_nickname(self, nickname):
        """设置用户昵称

        Args:
            nickname: 昵称字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['nickname'] = nickname
        return self

    def with_avatar_url(self, avatar_url):
        """设置用户头像URL

        Args:
            avatar_url: 头像URL字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['avatar_url'] = avatar_url
        return self

    def with_real_name(self, name):
        """设置用户真实姓名

        Args:
            name: 真实姓名字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['name'] = name
        return self

    def with_work_id(self, work_id):
        """设置工号或身份证号

        Args:
            work_id: 工号或身份证号字符串

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['work_id'] = work_id
        return self

    def as_solo_user(self):
        """设置为独居者

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['is_solo_user'] = True
        self.user_data['is_supervisor'] = False
        self.user_data['is_community_worker'] = False
        self.user_data['role'] = 1
        return self

    def as_supervisor(self):
        """设置为监护人

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['is_solo_user'] = False
        self.user_data['is_supervisor'] = True
        self.user_data['is_community_worker'] = False
        self.user_data['role'] = 2
        return self

    def as_community_worker(self):
        """设置为社区工作人员

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['is_solo_user'] = False
        self.user_data['is_supervisor'] = False
        self.user_data['is_community_worker'] = True
        self.user_data['role'] = 3
        return self

    def with_status(self, status):
        """设置用户状态

        Args:
            status: 状态值 (1-正常, 2-禁用)

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['status'] = status
        return self

    def with_verification_status(self, verification_status):
        """设置验证状态

        Args:
            verification_status: 验证状态值 (0-未申请, 1-待审核, 2-已通过, 3-已拒绝)

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['verification_status'] = verification_status
        return self

    def with_community_id(self, community_id):
        """设置所属社区ID

        Args:
            community_id: 社区ID整数

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['community_id'] = community_id
        return self

    def with_auth_type(self, auth_type):
        """设置认证类型

        Args:
            auth_type: 认证类型 ('wechat'/'phone'/'both')

        Returns:
            UserBuilder: 自身实例，支持链式调用
        """
        self.user_data['auth_type'] = auth_type
        return self

    def build(self):
        """构建User对象

        Returns:
            User: 创建的User对象
        """
        return User(**self.user_data)


# 便捷函数：创建默认独居者用户
def create_default_solo_user():
    """创建默认的独居者用户

    Returns:
        User: 默认配置的独居者用户
    """
    return UserBuilder()\
        .with_phone_number("13800138000")\
        .with_nickname("默认独居用户")\
        .as_solo_user()\
        .build()


# 便捷函数：创建默认监护人用户
def create_default_supervisor():
    """创建默认的监护人用户

    Returns:
        User: 默认配置的监护人用户
    """
    return UserBuilder()\
        .with_phone_number("13800138001")\
        .with_nickname("默认监护人")\
        .as_supervisor()\
        .build()
