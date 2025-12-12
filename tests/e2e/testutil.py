import uuid
import time
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