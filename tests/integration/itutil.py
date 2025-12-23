
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

from src.hashutil import phone_hash, pwd_hash, sms_code_hash, uuid_str, random_str, PWD_SALT

def get_headers_by_creating_phone_user(base_url, phone, nickname="DO_NOT_CARE", password=TEST_DEFAULT_PWD,sms_code =TEST_DEFAULT_SMS_CODE):
        user_data = create_phone_user(base_url, phone, nickname, password,sms_code)
        user_token = user_data['token']
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        return headers,user_data

def create_phone_user(base_url, phone, nickname="DO_NOT_CARE", password=TEST_DEFAULT_PWD,sms_code =TEST_DEFAULT_SMS_CODE):
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
def create_wx_user(base_url, wxchat_code, nickname="DO_NOT_CARE", avatal_url=TEST_DEFAULT_AVATAR):
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