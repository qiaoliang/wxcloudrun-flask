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
    使用时间戳+随机数确保跨进程唯一性
    """
    import random
    # 使用当前时间的微妙部分 + 随机数确保唯一性
    current_time = int(time.time() * 1000000)  # 微妙时间戳
    random_part = random.randint(10000, 99999)  # 5位随机数
    # 组合时间戳和随机数的后几位，确保总共是11位数字
    # 139开头，总共11位，所以后面需要9位数字
    # 使用时间戳的后7位 + 2位随机数组成9位数字
    time_part = int(str(current_time)[-7:])  # 取时间戳后7位
    if time_part < 1000000:  # 确保至少是7位数
        time_part += 1000000
    random_part = random.randint(10, 99)  # 2位随机数
    phone = f"139{time_part:07d}{random_part:02d}"
    
    # 确保手机号是11位
    if len(phone) > 11:
        phone = phone[:11]
    elif len(phone) < 11:
        # 如果长度不足11位，用随机数字补足
        while len(phone) < 11:
            phone += str(random.randint(0, 9))
    
    # 确保不会生成超级管理员的手机号
    if phone == SUPER_ADMIN_PHONE:
        # 如果冲突，增加一个随机偏移
        offset = random.randint(1, 99)
        phone = f"139{int(phone[3:]) + offset:08d}"
        if len(phone) > 11:
            phone = phone[:11]
    
    return phone