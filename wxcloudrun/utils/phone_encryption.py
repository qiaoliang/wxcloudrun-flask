"""
手机号码加密工具
提供手机号码的加密和解密功能，确保敏感信息安全存储
"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib
import os

# 用于区分默认参数和显式传入的None
_USE_CONFIG = object()

# 配置日志
logger = logging.getLogger(__name__)


class PhoneEncryption:
    """手机号码加密类"""

    def __init__(self, encryption_key=_USE_CONFIG):
        """
        初始化加密器

        Args:
            encryption_key: 加密密钥，如果不提供则从配置文件获取
        """
        # 如果显式传入了None或空字符串，则认为是无效密钥
        if encryption_key is None or encryption_key == "":
            raise ValueError("手机号码加密密钥无效")
        
        # 如果使用默认值，则从配置文件获取
        if encryption_key is _USE_CONFIG:
            encryption_key = os.environ.get('PHONE_ENCRYPTION_KEY')

        if not encryption_key:
            raise ValueError("手机号码加密密钥未配置")

        # 使用PBKDF2从密钥派生加密密钥
        self.fernet = self._create_fernet(encryption_key)

    def _create_fernet(self, key: str) -> Fernet:
        """从字符串密钥创建Fernet加密器"""
        # 使用PBKDF2派生32字节的密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'safeguard_phone_salt',  # 固定盐值，实际应用中应该每个用户不同
            iterations=100000,
        )
        key_bytes = kdf.derive(key.encode())
        return Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt_phone(self, phone_number: str) -> str:
        """
        加密手机号码

        Args:
            phone_number: 原始手机号码

        Returns:
            str: 加密后的手机号码（Base64编码）
        """
        try:
            # 转换为字节并加密
            phone_bytes = phone_number.encode('utf-8')
            encrypted_bytes = self.fernet.encrypt(phone_bytes)
            # 返回Base64编码的字符串
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"手机号码加密失败: {str(e)}")
            raise ValueError(f"手机号码加密失败: {str(e)}")

    def decrypt_phone(self, encrypted_phone: str) -> str:
        """
        解密手机号码

        Args:
            encrypted_phone: 加密后的手机号码（Base64编码）

        Returns:
            str: 原始手机号码
        """
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_phone.encode('utf-8'))
            # 解密
            phone_bytes = self.fernet.decrypt(encrypted_bytes)
            return phone_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"手机号码解密失败: {str(e)}")
            raise ValueError(f"手机号码解密失败: {str(e)}")

    def encrypt_phone_hash(self, phone_number: str) -> str:
        """
        生成手机号码的哈希值（用于索引和搜索）

        Args:
            phone_number: 手机号码

        Returns:
            str: 手机号码的SHA256哈希值
        """
        try:
            # 使用SHA256生成哈希值
            hash_object = hashlib.sha256(phone_number.encode('utf-8'))
            return hash_object.hexdigest()
        except Exception as e:
            logger.error(f"手机号码哈希生成失败: {str(e)}")
            raise ValueError(f"手机号码哈希生成失败: {str(e)}")

    def mask_phone(self, phone_number: str, mask_char: str = '*', visible_digits: int = 4) -> str:
        """
        手机号码脱敏显示

        Args:
            phone_number: 原始手机号码
            mask_char: 脱敏字符
            visible_digits: 保留可见的数字位数（从末尾开始）

        Returns:
            str: 脱敏后的手机号码
        """
        if len(phone_number) <= visible_digits:
            return phone_number

        masked_part = mask_char * (len(phone_number) - visible_digits)
        visible_part = phone_number[-visible_digits:]
        return masked_part + visible_part


class PhoneValidator:
    """手机号码验证器"""

    @staticmethod
    def validate_phone_number(phone_number: str) -> tuple[bool, str]:
        """
        验证手机号码格式

        Args:
            phone_number: 待验证的手机号码

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not phone_number:
            return False, "手机号码不能为空"

        # 去除空格和特殊字符
        cleaned_phone = ''.join(c for c in phone_number if c.isdigit())

        # 如果包含+86前缀，则去除前缀后再验证
        if phone_number.startswith('+86'):
            cleaned_phone = cleaned_phone[2:]  # 去除86

        # 检查长度
        if len(cleaned_phone) != 11:
            return False, "手机号码必须是11位数字"

        # 检查是否以1开头
        if not cleaned_phone.startswith('1'):
            return False, "手机号码必须以1开头"

        # 检查第二位（运营商号段）
        second_digit = cleaned_phone[1]
        valid_second_digits = ['3', '4', '5', '6', '7', '8', '9']
        if second_digit not in valid_second_digits:
            return False, "无效的手机号码号段"

        return True, ""

    @staticmethod
    def normalize_phone_number(phone_number: str) -> str:
        """
        标准化手机号码格式

        Args:
            phone_number: 原始手机号码

        Returns:
            str: 标准化后的手机号码
        """
        # 去除所有非数字字符
        cleaned_phone = ''.join(c for c in phone_number if c.isdigit())

        # 添加国际区号（如果需要）
        if not cleaned_phone.startswith('86'):
            cleaned_phone = '86' + cleaned_phone

        return '+' + cleaned_phone


# 全局加密器实例
_phone_encryption = None


def get_phone_encryption() -> PhoneEncryption:
    """获取手机号码加密器实例"""
    global _phone_encryption
    if _phone_encryption is None:
        _phone_encryption = PhoneEncryption()
    return _phone_encryption


def encrypt_phone_number(phone_number: str) -> str:
    """加密手机号码（便捷函数）"""
    return get_phone_encryption().encrypt_phone(phone_number)


def decrypt_phone_number(encrypted_phone: str) -> str:
    """解密手机号码（便捷函数）"""
    return get_phone_encryption().decrypt_phone(encrypted_phone)


def get_phone_hash(phone_number: str) -> str:
    """获取手机号码哈希值（便捷函数）"""
    return get_phone_encryption().encrypt_phone_hash(phone_number)


def mask_phone_number(phone_number: str, mask_char: str = '*', visible_digits: int = 4) -> str:
    """手机号码脱敏显示（便捷函数）"""
    return get_phone_encryption().mask_phone(phone_number, mask_char, visible_digits)


def validate_and_normalize_phone(phone_number: str) -> tuple[bool, str, str]:
    """
    验证并标准化手机号码

    Args:
        phone_number: 原始手机号码

    Returns:
        tuple[bool, str, str]: (是否有效, 错误信息, 标准化后的手机号码)
    """
    # 验证手机号码
    is_valid, error_msg = PhoneValidator.validate_phone_number(phone_number)
    if not is_valid:
        return False, error_msg, ""

    # 标准化手机号码
    normalized_phone = PhoneValidator.normalize_phone_number(phone_number)

    return True, "", normalized_phone