# wechat_di_demo.py
from abc import ABC, abstractmethod
from typing import Dict, Optional
import os
import requests
from dotenv import load_dotenv

# --------------------------
# 1. 统一抽象接口（核心：业务逻辑仅依赖此接口）
# --------------------------
class WeChatAPI(ABC):
    @abstractmethod
    def send_template_msg(self, openid: str, template_id: str, data: Dict) -> Dict:
        """发送模板消息（抽象方法，子类必须实现）"""
        pass

    @abstractmethod
    def get_user_info(self, openid: str) -> Optional[Dict]:
        """获取用户信息（抽象方法）"""
        pass

# --------------------------
# 2. 具体实现（模拟 + 真实）
# --------------------------
class MockWeChatAPI(WeChatAPI):
    """模拟微信 API（dev/test 环境用）"""
    def send_template_msg(self, openid: str, template_id: str, data: Dict) -> Dict:
        print(f"\n[模拟微信API] 环境：{os.getenv('ENV')}")
        print(f"[模拟发送] 接收者 openid：{openid}")
        print(f"[模拟发送] 模板ID：{template_id}")
        print(f"[模拟发送] 消息数据：{data}")
        # 模拟微信官方返回格式（确保和真实接口一致）
        return {"errcode": 0, "errmsg": "success", "msgid": f"mock_{openid[:8]}"}

    def get_user_info(self, openid: str) -> Optional[Dict]:
        print(f"\n[模拟微信API] 环境：{os.getenv('ENV')}")
        print(f"[模拟获取] 用户 openid：{openid}")
        # 模拟用户信息返回（严格遵循微信官方字段）
        return {
            "openid": openid,
            "nickname": "测试用户_模拟",
            "sex": 1,
            "language": "zh_CN",
            "city": "深圳",
            "province": "广东",
            "country": "中国",
            "headimgurl": "https://thirdwx.qlogo.cn/mmopen/vi_32/Q0j4TwGTfTLibriaibiaibiaibiaibiaibiaibiaibiaibicg/132",
            "privilege": [],
            "unionid": f"mock_unionid_{openid}"
        }

class RealWeChatAPI(WeChatAPI):
    """真实微信 API（prod 环境用）"""
    def __init__(self, appid: str, appsecret: str):
        self.appid = appid
        self.appsecret = appsecret
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """获取微信 Access Token（真实接口调用）"""
        url = (
            f"https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential"
            f"&appid={self.appid}"
            f"&secret={self.appsecret}"
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 抛出 HTTP 错误
            result = response.json()
            if result.get("errcode"):
                raise Exception(f"获取 Access Token 失败：{result['errmsg']}（错误码：{result['errcode']}）")
            print(f"[真实微信API] Access Token 获取成功")
            return result["access_token"]
        except Exception as e:
            raise RuntimeError(f"微信 API 初始化失败：{str(e)}") from e

    def send_template_msg(self, openid: str, template_id: str, data: Dict) -> Dict:
        """调用真实微信模板消息接口"""
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.access_token}"
        payload = {
            "touser": openid,
            "template_id": template_id,
            "data": data
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            print(f"\n[真实微信API] 模板消息发送结果：{result}")
            return result
        except Exception as e:
            print(f"[真实微信API] 发送失败：{str(e)}")
            return {"errcode": -1, "errmsg": str(e)}

    def get_user_info(self, openid: str) -> Optional[Dict]:
        """调用真实微信用户信息接口"""
        url = (
            f"https://api.weixin.qq.com/cgi-bin/user/info"
            f"?access_token={self.access_token}"
            f"&openid={openid}"
            f"&lang=zh_CN"
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode"):
                print(f"[真实微信API] 获取用户信息失败：{result['errmsg']}")
                return None
            print(f"\n[真实微信API] 用户信息获取成功：{result}")
            return result
        except Exception as e:
            print(f"[真实微信API] 获取用户信息失败：{str(e)}")
            return None

# --------------------------
# 3. 依赖工厂（按环境动态创建实例）
# --------------------------

def create_wechat_api() -> WeChatAPI:
    """依赖工厂：根据环境创建微信 API 实例"""
    env = os.getenv("ENV_TYPE", "unit")
    if env == "prod":
        # 生产环境：从环境变量读取真实配置
        appid = os.getenv("WECHAT_APPID")
        appsecret = os.getenv("WECHAT_APPSECRET")
        if not appid or not appsecret:
            raise ValueError("生产环境必须配置 WECHAT_APPID 和 WECHAT_APPSECRET 环境变量")
        return RealWeChatAPI(appid=appid, appsecret=appsecret)
    elif env in ("unit", "function"):
        return MockWeChatAPI()
    else:
        raise ValueError(f"不支持的环境类型：{env}（仅支持 dev/test/prod）")

# --------------------------
# 4. 业务逻辑（依赖抽象接口，不关心具体实现）
# --------------------------
class UserNotificationService:
    """用户通知业务服务（消费者）"""
    def __init__(self, wechat_api: WeChatAPI):
        """构造函数注入依赖（仅依赖 WeChatAPI 抽象接口）"""
        self.wechat_api = wechat_api

    def send_welcome_notification(self, openid: str) -> Dict:
        """发送欢迎通知（业务逻辑示例）"""
        template_id = os.getenv("WECHAT_TEMPLATE_ID", "MOCK_TEMPLATE_ID")
        welcome_data = {
            "first": {"value": "🎉 欢迎关注我们的公众号！", "color": "#173177"},
            "keyword1": {"value": "新用户注册", "color": "#333333"},
            "keyword2": {"value": "2025-12-04", "color": "#333333"},
            "remark": {"value": "点击下方按钮完善个人信息～", "color": "#173177"}
        }
        print("\n=== 开始执行发送欢迎通知 ===")
        return self.wechat_api.send_template_msg(
            openid=openid,
            template_id=template_id,
            data=welcome_data
        )

    def fetch_user_profile(self, openid: str) -> Optional[Dict]:
        """获取用户资料（业务逻辑示例）"""
        print("\n=== 开始获取用户资料 ===")
        return self.wechat_api.get_user_info(openid=openid)

# --------------------------
# 5. 主函数（程序入口）
# --------------------------
if __name__ == "__main__":
    try:
        # 步骤2：按环境创建依赖实例（依赖注入核心）
        wechat_api = create_wechat_api()

        # 步骤3：注入依赖到业务服务
        notification_service = UserNotificationService(wechat_api=wechat_api)

        # 步骤4：执行业务逻辑（环境不同，行为自动区分）
        test_openid = os.getenv("TEST_OPENID", "o6_bmjrPTlm6_2sgVt7hMZOPfL2M")  # 测试用 openid

        # 发送欢迎通知
        notify_result = notification_service.send_welcome_notification(test_openid)
        print(f"\n📊 通知发送最终结果：{notify_result}")

        # 获取用户资料
        user_profile = notification_service.fetch_user_profile(test_openid)
        print(f"\n📋 用户资料最终结果：{user_profile}")

    except Exception as e:
        print(f"\n❌ 程序执行失败：{str(e)}")