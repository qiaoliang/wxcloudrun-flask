import os
import random
import string
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any
from config_manager import should_use_real_sms


class SMSProvider(ABC):
    @abstractmethod
    def send(self, phone: str, content: str) -> bool:
        pass


class MockSMSProvider(SMSProvider):
    """模拟短信服务提供商"""
    def send(self, phone: str, content: str) -> bool:
        print(f"[MockSMS] to {phone}: {content}")
        return True


class RealSMSProvider(SMSProvider):
    """真实短信服务提供商"""
    def __init__(self):
        self.api_key = os.getenv('SMS_API_KEY', '')
        self.api_secret = os.getenv('SMS_API_SECRET', '')
        self.api_url = os.getenv('SMS_API_URL', 'https://api.sms-service.com/send')
    
    def send(self, phone: str, content: str) -> bool:
        """发送真实短信"""
        if not self.api_key or not self.api_secret:
            raise ValueError("真实短信服务需要配置 SMS_API_KEY 和 SMS_API_SECRET 环境变量")
        
        try:
            # 构建请求数据
            payload = {
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'phone': phone,
                'content': content
            }
            
            # 发送请求
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    print(f"[RealSMS] 短信发送成功 to {phone}")
                    return True
                else:
                    print(f"[RealSMS] 短信发送失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"[RealSMS] HTTP请求失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[RealSMS] 请求超时")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[RealSMS] 请求异常: {str(e)}")
            return False
        except Exception as e:
            print(f"[RealSMS] 发送短信时发生错误: {str(e)}")
            return False


def create_sms_provider() -> SMSProvider:
    """根据环境创建短信服务提供商实例"""
    if should_use_real_sms():
        print(f"[RealSMS] 使用真实短信服务，ENV_TYPE={os.getenv('ENV_TYPE', 'unit')}")
        return RealSMSProvider()
    else:
        print(f"[MockSMS] 使用模拟短信服务，ENV_TYPE={os.getenv('ENV_TYPE', 'unit')}")
        return MockSMSProvider()


def generate_code(n: int = 6) -> str:
    """生成验证码"""
    if should_use_real_sms():
        # uat 和 prod 环境生成随机验证码
        return ''.join(random.choice(string.digits) for _ in range(n))
    else:
        # unit 和 function 环境使用固定验证码
        return '123456'
