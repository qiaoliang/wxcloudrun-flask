import os
import random
import string
from abc import ABC, abstractmethod


class SMSProvider(ABC):
    @abstractmethod
    def send(self, phone: str, content: str) -> bool:
        pass


class MockSMSProvider(SMSProvider):
    def send(self, phone: str, content: str) -> bool:
        print(f"[MockSMS] to {phone}: {content}")
        return True


def create_sms_provider() -> SMSProvider:
    env = os.getenv('ENV_TYPE', 'unit')
    return MockSMSProvider()


def generate_code(n: int = 6) -> str:
    env = os.getenv('ENV_TYPE', 'unit')
    if env != 'prod':
        return '123456'
    return ''.join(random.choice(string.digits) for _ in range(n))
