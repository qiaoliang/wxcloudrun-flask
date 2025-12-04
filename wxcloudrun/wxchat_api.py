from abc import ABC, abstractmethod
from typing import Dict, Optional
import os
import requests
from config import WX_APPID, WX_SECRET


# --------------------------
# 1. 统一抽象接口（核心：业务逻辑仅依赖此接口）
# --------------------------
class WeChatAPI(ABC):
    @abstractmethod
    def get_user_info_by_code(self, code: str) -> Dict:
        """通过code获取用户openid和session_key（抽象方法，子类必须实现）"""
        pass


# --------------------------
# 2. 具体实现（模拟 + 真实）
# --------------------------
class MockWeChatAPI(WeChatAPI):
    """模拟微信 API（非prod环境用）"""
    def get_user_info_by_code(self, code: str) -> Dict:
        # 对于模拟API，我们返回模拟的openid和session_key
        # 使用code的前8位作为模拟的openid后缀，确保不同code得到不同的openid
        mock_openid = f"mock_openid_{code[:8]}" if code else "mock_openid_default"
        mock_session_key = f"mock_session_key_{code[:8]}" if code else "mock_session_key_default"
        
        print(f"[模拟微信API] 获取用户信息成功")
        print(f"[模拟微信API] 返回openid: {mock_openid}")
        
        # 模拟微信官方返回格式（确保和真实接口一致）
        return {
            "openid": mock_openid,
            "session_key": mock_session_key,
            "unionid": f"mock_unionid_{code[:8]}" if code else None
        }


class RealWeChatAPI(WeChatAPI):
    """真实微信 API（prod 环境用）"""
    def __init__(self, appid: str, appsecret: str):
        self.appid = appid
        self.appsecret = appsecret

    def get_user_info_by_code(self, code: str) -> Dict:
        """调用真实微信API获取用户openid和session_key"""
        if not code:
            raise ValueError("code参数不能为空")
        
        # 构建微信API请求URL
        wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={self.appid}&secret={self.appsecret}&js_code={code}&grant_type=authorization_code'
        
        try:
            # 发送请求到微信API
            wx_response = requests.get(wx_url, timeout=30, verify=True)
            
            # 检查HTTP状态码
            if wx_response.status_code != 200:
                raise Exception(f"请求微信API失败，HTTP状态码: {wx_response.status_code}")
            
            wx_data = wx_response.json()
            
            # 检查微信API返回的错误
            if 'errcode' in wx_data:
                errcode = wx_data.get('errcode')
                errmsg = wx_data.get('errmsg', '未知错误')
                raise Exception(f"微信API返回错误 - errcode: {errcode}, errmsg: {errmsg}")
            
            print(f"[真实微信API] 获取用户信息成功")
            print(f"[真实微信API] 返回数据: {wx_data}")
            
            return wx_data
            
        except requests.exceptions.Timeout:
            raise Exception("请求微信API超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求微信API时发生网络错误: {str(e)}")
        except ValueError:
            raise Exception("微信API返回的数据格式错误")


# --------------------------
# 3. 依赖工厂（按环境动态创建实例）
# --------------------------
def create_wechat_api() -> WeChatAPI:
    """依赖工厂：根据环境创建微信 API 实例"""
    env = os.getenv("ENV_TYPE", "unit")
    
    if env == "prod":
        # 生产环境：使用真实的微信配置
        if not WX_APPID or not WX_SECRET:
            raise ValueError("生产环境必须配置WX_APPID和WX_SECRET环境变量")
        print(f"[真实微信API] 使用真实的微信配置，ENV_TYPE={env}")
        return RealWeChatAPI(appid=WX_APPID, appsecret=WX_SECRET)
    else:
        # 非生产环境：使用模拟的微信API
        print(f"[模拟微信API] 使用模拟的微信API，ENV_TYPE={env}")
        return MockWeChatAPI()


# --------------------------
# 4. 全局API实例（供其他模块使用）
# --------------------------
# 根据环境创建微信API实例
wechat_api = create_wechat_api()


# --------------------------
# 5. 便捷函数（供其他模块调用）
# --------------------------
def get_user_info_by_code(code: str) -> Dict:
    """
    通过code获取用户信息的便捷函数
    :param code: 微信登录code
    :return: 包含openid和session_key的字典
    """
    return wechat_api.get_user_info_by_code(code)