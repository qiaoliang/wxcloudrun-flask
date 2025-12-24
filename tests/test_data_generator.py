"""
线程安全的测试数据生成器
用于在多线程测试环境下生成唯一的测试数据
"""

import threading
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime


class TestDataManager:
    """线程安全的测试数据管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    # 手机号码计数器
                    self._phone_counter = 8000  # 从13900008000开始
                    self._phone_counter_lock = threading.Lock()
                    
                    # 测试会话ID, 用于区分不同的测试运行
                    self._session_id = f"test_{int(time.time() * 1000)}"
                    
                    # 已分配的手机号码记录（用于调试）
                    self._allocated_phones = {}
                    self._allocated_phones_lock = threading.Lock()
                    
                    # 避免的系统手机号码
                    self._reserved_phones = {
                        '13900007997',  # 超级管理员
                        '13900007998',  # 其他系统用户
                        '13900007999',
                        '13900007996',
                        '13900007995',
                    }
                    
                    self._initialized = True
    
    def generate_unique_phone_number(self, test_context: Optional[str] = None) -> str:
        """
        生成唯一的测试手机号码
        
        Args:
            test_context: 测试上下文信息, 用于调试追踪
            
        Returns:
            唯一的手机号码字符串, 格式: 1390000XXXX
        """
        with self._phone_counter_lock:
            phone_number = f"1390000{self._phone_counter}"
            self._phone_counter += 1
            
            # 确保不会与保留号码冲突
            while phone_number in self._reserved_phones:
                phone_number = f"1390000{self._phone_counter}"
                self._phone_counter += 1
        
        # 记录分配信息（用于调试）
        with self._allocated_phones_lock:
            self._allocated_phones[phone_number] = {
                'test_context': test_context or 'unknown',
                'thread_id': threading.current_thread().ident,
                'timestamp': datetime.now().isoformat(),
                'session_id': self._session_id
            }
        
        return phone_number
    
    def generate_unique_openid(self, phone_number: str, test_context: Optional[str] = None) -> str:
        """
        生成唯一的微信OpenID
        
        Args:
            phone_number: 关联的手机号码
            test_context: 测试上下文信息
            
        Returns:
            唯一的OpenID字符串
        """
        thread_id = threading.current_thread().ident
        timestamp = int(time.time() * 1000)
        context_suffix = test_context[:8] if test_context else 'unknown'
        
        return f"test_{self._session_id}_{context_suffix}_{phone_number[-4:]}_{thread_id}_{timestamp}"
    
    def generate_unique_nickname(self, test_context: Optional[str] = None) -> str:
        """
        生成唯一的昵称
        
        Args:
            test_context: 测试上下文信息
            
        Returns:
            唯一的昵称字符串
        """
        with self._phone_counter_lock:
            # 使用共享计数器确保唯一性
            counter = self._phone_counter
            self._phone_counter += 1
        
        thread_id = threading.current_thread().ident
        context_suffix = test_context[:8] if test_context else 'unknown'
        
        return f"nickname_{context_suffix}_{thread_id}_{counter}"
    
    def generate_unique_username(self, test_context: Optional[str] = None) -> str:
        """
        生成唯一的用户名
        
        Args:
            test_context: 测试上下文信息
            
        Returns:
            唯一的用户名字符串
        """
        with self._phone_counter_lock:
            # 使用共享计数器确保唯一性
            counter = self._phone_counter
            self._phone_counter += 1
        
        thread_id = threading.current_thread().ident
        context_suffix = test_context[:8] if test_context else 'unknown'
        
        return f"uname_{context_suffix}_{thread_id}_{counter}"
    
    def get_allocation_info(self) -> Dict[str, Any]:
        """
        获取号码分配信息（用于调试）
        
        Returns:
            分配信息字典
        """
        with self._allocated_phones_lock:
            return {
                'session_id': self._session_id,
                'total_allocated': len(self._allocated_phones),
                'current_counter': self._phone_counter,
                'allocated_phones': dict(self._allocated_phones)
            }
    
    def reset_session(self):
        """重置会话（主要用于测试）"""
        with self._phone_counter_lock:
            self._phone_counter = 8000
        
        with self._allocated_phones_lock:
            self._allocated_phones.clear()
        
        self._session_id = f"test_{int(time.time() * 1000)}"


# 全局实例
_test_data_manager = TestDataManager()


def get_test_data_manager() -> TestDataManager:
    """获取测试数据管理器实例"""
    return _test_data_manager


def generate_unique_phone_number(test_context: Optional[str] = None) -> str:
    """
    生成唯一测试手机号码的便捷函数
    
    Args:
        test_context: 测试上下文, 建议使用测试方法名
        
    Returns:
        唯一的手机号码
    """
    return _test_data_manager.generate_unique_phone_number(test_context)


def generate_unique_openid(phone_number: str, test_context: Optional[str] = None) -> str:
    """
    生成唯一OpenID的便捷函数
    
    Args:
        phone_number: 关联的手机号码
        test_context: 测试上下文
        
    Returns:
        唯一的OpenID
    """
    return _test_data_manager.generate_unique_openid(phone_number, test_context)


def generate_unique_nickname(test_context: Optional[str] = None) -> str:
    """
    生成唯一昵称的便捷函数
    
    Args:
        test_context: 测试上下文
        
    Returns:
        唯一的昵称
    """
    return _test_data_manager.generate_unique_nickname(test_context)


def generate_unique_username(test_context: Optional[str] = None) -> str:
    """
    生成唯一用户名的便捷函数
    
    Args:
        test_context: 测试上下文
        
    Returns:
        唯一的用户名
    """
    return _test_data_manager.generate_unique_username(test_context)


if __name__ == "__main__":
    # 简单的测试
    import concurrent.futures
    
    def worker(worker_id):
        phone = generate_unique_phone_number(f"worker_{worker_id}")
        openid = generate_unique_openid(phone, f"worker_{worker_id}")
        nickname = generate_unique_nickname(f"worker_{worker_id}")
        return f"Worker {worker_id}: {phone}, {openid}, {nickname}"
    
    # 并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(20)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    for result in sorted(results):
        print(result)
    
    # 打印分配信息
    manager = get_test_data_manager()
    info = manager.get_allocation_info()
    print(f"\n分配信息: {info['total_allocated']} 个号码")
    print(f"会话ID: {info['session_id']}")