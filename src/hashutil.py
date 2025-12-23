import secrets
import os
from hashlib import sha256
import uuid
import time
import threading

# 全局计数器，用于生成唯一的测试手机号
_phone_counter = 0
_phone_counter_lock = threading.Lock()

# 超级管理员手机号，需要避免生成这个号码
SUPER_ADMIN_PHONE = '13900007997'

PWD_SALT = secrets.token_hex(8)
PHONE_SALT = os.getenv('PHONE_ENC_SECRET', 'default_secret')
def pwd_hash(pwd):
    return sha256(f"{pwd}:{PWD_SALT}".encode('utf-8')).hexdigest()

def phone_hash(phone_number):
    return sha256(f"{PHONE_SALT}:{phone_number}".encode('utf-8')).hexdigest()

def sms_code_hash(phone, code, salt):
    """
    生成验证码哈希值
    """
    return sha256(f"{phone}:{code}:{salt}".encode('utf-8')).hexdigest()


def uuid_str(len:int) -> str:
    """生成UUID字符串（两种常用格式）"""
    len = len if len < 29 else 29
    # 1. UUID4（随机生成，最常用）
    uuid_str = str(uuid.uuid4())  # 格式：xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    # 2. 去掉横线，更简洁
    uuid_simple = uuid_str.replace('-', '')
    timestamp = str(int(time.time() * 1000000))
    return uuid_simple[:len]

def random_str(len:int) -> str:
    # 最多 16 位数字
    len = len if len < 16 else 16
    timestamp = str(int(time.time() * 1000000))
    result = f"{timestamp}"
    return result[:len]

def generate_unique_phone() -> str:
    """
    生成唯一的测试手机号
    确保手机号符合11位数字格式，且不与超级管理员号码冲突
    """
    global _phone_counter
    with _phone_counter_lock:
        _phone_counter += 1
        # 生成格式：139 + 1000 + 递增数字 (确保11位)
        # 例如: 139100000001, 139100000002, ...
        phone = f"139100{_phone_counter:06d}"
        
        # 确保不会生成超级管理员的手机号
        if phone == SUPER_ADMIN_PHONE:
            _phone_counter += 1
            phone = f"139100{_phone_counter:06d}"
    
    return phone