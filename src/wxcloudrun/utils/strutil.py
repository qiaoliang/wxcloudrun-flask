import uuid
import time
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