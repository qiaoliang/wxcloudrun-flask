import uuid
import time
import pytest
import requests
import time
from datetime import datetime


TEST_DEFAULT_SMS_CODE = 'wx_auth_123456'
TEST_DEFAULT_PWD ='TEST_DEFAULT_PWD_123456'
TEST_DEFAULT_AVATAR ="/avatar/TEST_DEFAULT_AVATAR"
TEST_DEFAULT_WXCAHT_CODE = '123456'

def uuid_str(length:int) ->str:
    if not isinstance(length, int) or length < 1 or length > 32:
        raise ValueError("长度必须是1-32之间的整数")

    # 生成uuid4并去掉所有'-'符号（原始uuid4格式如：f81d4fae-7dec-11d0-a765-00a0c91e6bf6）
    uuid_str = uuid.uuid4().hex  # hex属性直接返回无'-'的32位16进制字符串

    # 截取指定长度的字符串
    result = uuid_str[:length]

    return result

def random_str(length:int) -> str:
    # 最多 16 位数字
    length = length if length < 16 else 16
    timestamp = str(int(time.time() * 1000000))
    result = f"{timestamp}"
    return result[:length]

def create_phone_user(base_url, phone, nickname, password=TEST_DEFAULT_PWD,sms_code =TEST_DEFAULT_SMS_CODE):
        """创建测试用户"""
        register_response = requests.post(f"{base_url}/api/auth/register_phone", json={
            'phone': phone,
            'code': sms_code,
            'password': password,
            'nickname': nickname
        })
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert register_data.get('code') == 1, f"注册失败: {register_data.get('msg')}"
        print(f"注册成功: {register_data.get('msg')}")
        return register_data['data']
def create_wx_user(base_url, wxchat_code, nickname, avatal_url=TEST_DEFAULT_AVATAR):
        """创建测试用户"""
        data ={
        "code": wxchat_code,
        "nickname": nickname,
        "avatar_url": avatal_url
        }
        response = requests.post(f"{base_url}/api/auth/login_wechat", json=data)
        assert response.status_code == 200
        register_data = response.json()
        assert register_data.get('code') == 1
        return register_data['data']