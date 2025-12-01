from typing import Any, Dict
from flask import request
import logging
import jwt
from functools import wraps
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.services.user_service import UserService, CheckinRuleService, CheckinRecordService
from wxcloudrun.services.auth_service import AuthService


class BaseController:
    """
    控制器基类
    """
    @staticmethod
    def verify_token():
        """
        验证JWT token并返回解码后的用户信息
        """
        # 验证token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            header_token = auth_header[7:]  # 去掉 'Bearer ' 前缀
            header_token = header_token.strip()  # 确保去除可能的空白字符
            # 去除可能存在的引号
            if header_token.startswith('"') and header_token.endswith('"'):
                header_token = header_token[1:-1]
            elif header_token.startswith("'") and header_token.endswith("'"):
                header_token = header_token[1:-1]
        else:
            header_token = auth_header.strip()
            # 去除可能存在的引号
            if header_token.startswith('"') and header_token.endswith('"'):
                header_token = header_token[1:-1]
            elif header_token.startswith("'") and header_token.endswith("'"):
                header_token = header_token[1:-1]
        # 优先使用header中的token，只有当header_token非空时才使用它
        token = header_token if header_token else params.get('token')
        
        if not token:
            logging.warning('请求中缺少token参数')
            return None, make_err_response({}, '缺少token参数')

        try:
            import config
            # 使用配置文件中的TOKEN_SECRET进行解码
            token_secret = config.TOKEN_SECRET
            
            # 解码token
            decoded = jwt.decode(
                token,
                token_secret,
                algorithms=['HS256']
            )
            openid = decoded.get('openid')

            if not openid:
                logging.error('解码后的token中未找到openid')
                return None, make_err_response({}, 'token无效')

            return decoded, None
        except jwt.ExpiredSignatureError:
            return None, make_err_response({}, 'token已过期')
        except jwt.InvalidSignatureError:
            return None, make_err_response({}, 'token签名无效')
        except jwt.DecodeError as e:
            logging.error(f'token解码失败: {str(e)}')
            logging.error(f'尝试解码的token (前50字符): {token[:50] if token else "None"}')
            logging.error(f'token总长度: {len(token) if token else 0}')
            if token:
                token_parts = token.split('.')
                logging.error(f'token段数: {len(token_parts)}')
                for i, part in enumerate(token_parts):
                    logging.error(f'第{i+1}段长度: {len(part)}')
            return None, make_err_response({}, 'token格式错误')
        except jwt.InvalidTokenError:
            return None, make_err_response({}, 'token无效')
        except Exception as e:
            logging.error(f'JWT验证时发生错误: {str(e)}', exc_info=True)
            return None, make_err_response({}, f'JWT验证失败: {str(e)}')


def login_required(f):
    """
    统一的登录认证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, error_response = BaseController.verify_token()
        if error_response:
            return error_response
        # 将解码后的用户信息传递给被装饰的函数
        return f(decoded, *args, **kwargs)

    return decorated_function


def permission_required(permission):
    """
    权限验证装饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 先验证token
            decoded, error_response = BaseController.verify_token()
            if error_response:
                return error_response
            
            # 获取用户信息并检查权限
            from wxcloudrun.dao import query_user_by_openid
            openid = decoded.get('openid')
            user = query_user_by_openid(openid)
            
            if not user:
                return make_err_response({}, '用户不存在')
            
            # 检查权限
            if not user.has_permission(permission):
                return make_err_response({}, '权限不足')
            
            # 将解码后的用户信息和用户对象传递给被装饰的函数
            return f(decoded, user, *args, **kwargs)
        return decorated_function
    return decorator


def community_required(f):
    """
    社区工作人员权限验证装饰器
    """
    return permission_required('community_worker')(f)


def supervisor_required(f):
    """
    监护人权限验证装饰器
    """
    return permission_required('supervisor')(f)


class UserController:
    """
    用户控制器
    """
    def __init__(self):
        self.user_service = UserService()
        self.auth_service = AuthService()

    def login(self):
        """
        登录接口，通过code获取用户信息并返回token
        """
        from flask import request
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行登录接口 ===')

        try:
            # 在日志中打印登录请求
            request_params = request.get_json()
            app_logger.info(f'login 请求参数: {request_params}')

            # 获取请求体参数
            params = request.get_json()
            if not params:
                app_logger.warning('登录请求缺少请求体参数')
                return make_err_response({},'缺少请求体参数')

            app_logger.info('成功获取请求参数，开始检查code参数')

            code = params.get('code')
            if not code:
                app_logger.warning('登录请求缺少code参数')
                return make_err_response({},'缺少code参数')

            # 打印code用于调试
            app_logger.info(f'获取到的code: {code}')

            # 获取可能传递的用户信息（首次登录时会包含这些信息）
            nickname = params.get('nickname')
            avatar_url = params.get('avatar_url')

            app_logger.info(f'获取到的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}')

            app_logger.info('开始调用微信API获取用户openid和session_key')

            # 调用微信API获取用户信息
            import config
            app_logger.info(f'从配置中获取WX_APPID: {config.WX_APPID[:10]}...' if hasattr(config, 'WX_APPID') and config.WX_APPID else 'WX_APPID未配置')
            app_logger.info(f'从配置中获取WX_SECRET: {config.WX_SECRET[:10]}...' if hasattr(config, 'WX_SECRET') and config.WX_SECRET else 'WX_SECRET未配置')

            import requests
            wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={config.WX_APPID}&secret={config.WX_SECRET}&js_code={code}&grant_type=authorization_code'
            app_logger.info(f'请求微信API的URL: {wx_url[:100]}...')  # 只打印URL前100个字符以避免敏感信息泄露

            # 发送请求到微信API，禁用SSL验证以解决证书问题（仅用于开发测试环境）
            app_logger.info('正在发送请求到微信API...')
            wx_response = requests.get(wx_url, timeout=30, verify=False)  # 增加超时时间到30秒
            app_logger.info(f'微信API响应状态码: {wx_response.status_code}')

            wx_data = wx_response.json()
            app_logger.info(f'微信API响应数据类型: {type(wx_data)}')
            app_logger.info(f'微信API响应内容: {wx_data}')

            # 检查微信API返回的错误
            if 'errcode' in wx_data:
                app_logger.error(f'微信API返回错误 - errcode: {wx_data.get("errcode")}, errmsg: {wx_data.get("errmsg")}')
                return make_err_response({}, f'微信API错误: {wx_data.get("errmsg", "未知错误")}')

            # 获取openid和session_key
            app_logger.info('正在从微信API响应中提取openid和session_key')
            openid = wx_data.get('openid')
            session_key = wx_data.get('session_key')

            app_logger.info(f'提取到的openid: {openid}')
            app_logger.info(f'提取到的session_key: {"*" * 10}')  # 隐藏session_key的实际值

            if not openid or not session_key:
                app_logger.error(f'微信API返回数据不完整 - openid存在: {bool(openid)}, session_key存在: {bool(session_key)}')
                return make_err_response({}, '微信API返回数据不完整')

            app_logger.info('成功获取openid和session_key，开始查询数据库中的用户信息')

            # 检查用户是否已存在
            existing_user = self.user_service.get_user_by_openid(openid)
            is_new = not bool(existing_user)
            app_logger.info(f'用户查询结果 - 是否为新用户: {is_new}, openid: {openid}')

            if not existing_user:
                app_logger.info('用户不存在，创建新用户...')
                # 创建新用户，根据是否提供了用户信息来决定初始角色
                user = self.user_service.create_user(openid, nickname, avatar_url)
                app_logger.info(f'新用户创建成功，用户ID: {user.user_id}, openid: {openid}')
            else:
                app_logger.info('用户已存在，检查是否需要更新用户信息...')
                # 更新现有用户信息（如果提供了新的头像或昵称）
                user = existing_user
                updated = False
                if nickname and user.nickname != nickname:
                    app_logger.info(f'更新用户昵称: {user.nickname} -> {nickname}')
                    user.nickname = nickname
                    updated = True
                if avatar_url and user.avatar_url != avatar_url:
                    app_logger.info(f'更新用户头像: {user.avatar_url} -> {avatar_url}')
                    user.avatar_url = avatar_url
                    updated = True
                if updated:
                    app_logger.info('保存用户信息更新到数据库...')
                    self.user_service.update_user(user, nickname=user.nickname, avatar_url=user.avatar_url)
                    app_logger.info(f'用户信息更新成功，openid: {openid}')
                else:
                    app_logger.info('用户信息无变化，无需更新')

            app_logger.info('开始生成JWT token和refresh token...')

            import datetime
            import secrets
            
            # 生成JWT token (access token)，设置2小时过期时间
            token_payload = {
                'openid': openid,
                'user_id': user.user_id,  # 添加用户ID到token中
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)  # 设置2小时过期时间
            }
            app_logger.info(f'JWT token payload: {token_payload}')

            # 使用配置文件中的TOKEN_SECRET进行编码
            token_secret = config.TOKEN_SECRET
            app_logger.info(f'使用的TOKEN_SECRET: {token_secret[:10]}...')  # 只记录部分信息用于调试

            token = jwt.encode(token_payload, token_secret, algorithm='HS256')

            # 生成refresh token
            refresh_token = secrets.token_urlsafe(32)
            app_logger.info(f'生成的refresh_token: {refresh_token[:20]}...')

            # 设置refresh token过期时间为7天
            refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)

            # 更新用户信息，保存refresh token
            from wxcloudrun.dao import update_user_by_id
            user.refresh_token = refresh_token
            user.refresh_token_expire = refresh_token_expire
            update_user_by_id(user)

            # 打印生成的token用于调试（只打印前50个字符）
            app_logger.info(f'生成的token前50字符: {token[:50]}...')
            app_logger.info(f'生成的token总长度: {len(token)}')

            app_logger.info('JWT token和refresh token生成成功')

        except requests.exceptions.Timeout as e:
            app_logger.error(f'请求微信API超时: {str(e)}')
            return make_err_response({}, f'调用微信API超时: {str(e)}')
        except requests.exceptions.RequestException as e:
            app_logger.error(f'请求微信API时发生网络错误: {str(e)}')
            return make_err_response({}, f'调用微信API失败: {str(e)}')
        except jwt.PyJWTError as e:
            app_logger.error(f'JWT处理错误: {str(e)}')
            return make_err_response({}, f'JWT处理失败: {str(e)}')
        except Exception as e:
            app_logger.error(f'登录过程中发生未预期的错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'登录失败: {str(e)}')

        app_logger.info('登录流程完成，开始构造响应数据')

        # 构造返回数据，包含用户的 token 和 refresh token
        # 根据登录流程图，返回格式应该与登录流程图一致
        response_data = {
            'token': token,
            'refresh_token': refresh_token,  # 添加refresh token
            'user_id': user.user_id,
            'is_new_user': is_new,  # 标识是否为新用户，符合登录流程图要求
            'role': user.role_name,  # 返回用户角色名称
            'is_verified': user.verification_status == 2,  # 返回验证状态（仅对社区工作人员有意义）
            'expires_in': 7200  # 2小时（秒）
        }

        app_logger.info(f'返回的用户ID: {user.user_id}')
        app_logger.info(f'是否为新用户: {is_new}')
        app_logger.info(f'返回的token长度: {len(token)}')
        app_logger.info(f'返回的refresh_token长度: {len(refresh_token)}')
        app_logger.info('=== 登录接口执行完成 ===')

        # 返回自定义格式的响应，符合统一响应格式
        return make_succ_response(response_data)

    def get_or_update_profile(self, decoded: Dict[str, Any]):
        """
        获取或更新用户信息
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行用户信息接口 ===')
        app_logger.info(f'请求方法: {request.method}')
        app_logger.info(f'请求头信息: {dict(request.headers)}')
        app_logger.info(f'请求URL: {request.url}')
        app_logger.info(f'Content-Type: {request.content_type}')

        try:
            # 获取请求体参数，增加对不同Content-Type的处理
            params = {}
            if request.method == 'POST' and request.content_type and 'application/json' in request.content_type:
                params = request.get_json() or {}
            elif request.method == 'POST':
                # 如果不是JSON格式，尝试解析为form data（虽然不太可能从前端发送）
                params = dict(request.form) or {}
            else:
                params = {}
            
            app_logger.info(f'解析后的请求体参数: {params}')

            openid = decoded.get('openid')

            if not openid:
                app_logger.error('解码后的token中未找到openid')
                return make_err_response({}, 'token无效')

            # 根据HTTP方法决定操作
            if request.method == 'GET':
                app_logger.info(f'GET请求 - 查询用户信息，openid: {openid}')
                # 查询用户信息
                user = self.user_service.get_user_by_openid(openid)
                if not user:
                    app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
                    return make_err_response({}, '用户不存在')

                # 返回用户信息
                user_data = {
                    'user_id': user.user_id,
                    'wechat_openid': user.wechat_openid,
                    'phone_number': user.phone_number,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'role': user.role_name,  # 返回字符串形式的角色名
                    'community_id': user.community_id,
                    'status': user.status_name,  # 返回字符串形式的状态名
                    'is_verified': user.verification_status == 2  # 返回验证状态（仅对社区工作人员有意义）
                }

                app_logger.info(f'成功查询到用户信息，用户ID: {user.user_id}')
                return make_succ_response(user_data)

            elif request.method == 'POST':
                app_logger.info(f'POST请求 - 更新用户信息，openid: {openid}')
                # 查询用户
                user = self.user_service.get_user_by_openid(openid)
                if not user:
                    app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
                    return make_err_response({}, '用户不存在')

                # 获取可更新的用户信息（只更新非空字段）
                nickname = params.get('nickname')
                avatar_url = params.get('avatar_url')
                phone_number = params.get('phone_number')
                role = params.get('role')
                community_id = params.get('community_id')
                status = params.get('status')

                app_logger.info(f'待更新的用户信息 - nickname: {nickname}, avatar_url: {avatar_url}, phone_number: {phone_number}, role: {role}')

                # 更新用户信息到数据库
                update_kwargs = {}
                if nickname is not None:
                    app_logger.info(f'更新nickname: {user.nickname} -> {nickname}')
                    update_kwargs['nickname'] = nickname
                if avatar_url is not None:
                    app_logger.info(f'更新avatar_url: {user.avatar_url} -> {avatar_url}')
                    update_kwargs['avatar_url'] = avatar_url
                if phone_number is not None:
                    app_logger.info(f'更新phone_number: {user.phone_number} -> {phone_number}')
                    update_kwargs['phone_number'] = phone_number
                if role is not None:
                    app_logger.info(f'更新role: {user.role} -> {role}')
                    update_kwargs['role'] = role
                if community_id is not None:
                    app_logger.info(f'更新community_id: {user.community_id} -> {community_id}')
                    update_kwargs['community_id'] = community_id
                if status is not None:
                    app_logger.info(f'更新status: {user.status} -> {status}')
                    update_kwargs['status'] = status

                # 保存到数据库
                self.user_service.update_user(user, **update_kwargs)

                app_logger.info(f'用户 {openid} 信息更新成功')

                return make_succ_response({'message': '用户信息更新成功'})

        except jwt.ExpiredSignatureError as e:
            app_logger.error(f'token已过期: {str(e)}')
            return make_err_response({}, 'token已过期')
        except jwt.InvalidSignatureError as e:
            error_subclass = type(e).__name__
            app_logger.error(f"❌  InvalidSignatureError 实际异常子类：{error_subclass}")
            app_logger.error(f"InvalidSignatureError 详细描述：{str(e)}")
            app_logger.error(f'token签名验证失败: {str(e)}')
            app_logger.error('可能原因：TOKEN_SECRET配置不一致、token被篡改或格式错误')
            return make_err_response({}, 'token签名无效')
        except jwt.DecodeError as e:
            # 捕获更详细的 DecodeError 的子类错误，打印详细信息
            # 关键代码：获取实际子类名称
            error_subclass = type(e).__name__
            app_logger.error(f"❌ 实际异常子类：{error_subclass}")
            app_logger.error(f"详细描述：{str(e)}")

            app_logger.error(f'token解码失败: {str(e)}')
            app_logger.error('可能原因：token格式错误（非标准JWT格式）、token被截断或包含非法字符')
            # 额外调试信息
            token = decoded.get('token', '')  # 从decoded获取token用于调试
            app_logger.info(f'尝试解析的token长度: {len(token) if token else 0}')
            if token:
                token_parts = token.split('.')
                app_logger.info(f'token段数: {len(token_parts)}')
                if len(token_parts) >= 2:
                    import base64
                    try:
                        # 尝试解码header部分查看格式
                        header_part = token_parts[0]
                        # 补齐Base64 padding
                        missing_padding = len(header_part) % 4
                        if missing_padding:
                            header_part += '=' * (4 - missing_padding)
                        header_decoded = base64.urlsafe_b64decode(header_part)
                        app_logger.info(f'token header解码成功: {header_decoded.decode("utf-8")}')
                    except Exception as decode_err:
                        app_logger.error(f'token header解码失败: {str(decode_err)}')
            return make_err_response({}, 'token格式错误')
        except jwt.InvalidTokenError as e:
            app_logger.error(f'token无效: {str(e)}')
            return make_err_response({}, 'token无效')
        except Exception as e:
            app_logger.error(f'JWT处理时发生未知错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'JWT处理失败: {str(e)}')

        app_logger.info('=== 用户信息接口执行完成 ===')

    def refresh_token(self):
        """
        刷新token接口
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行刷新Token接口 ===')
        
        try:
            # 获取请求体参数
            params = request.get_json()
            if not params:
                app_logger.warning('刷新Token请求缺少请求体参数')
                return make_err_response({}, '缺少请求体参数')
            
            refresh_token = params.get('refresh_token')
            if not refresh_token:
                app_logger.warning('刷新Token请求缺少refresh_token参数')
                return make_err_response({}, '缺少refresh_token参数')
            
            app_logger.info('开始验证refresh token...')
            
            result = self.auth_service.refresh_token(refresh_token)
            
            app_logger.info('成功刷新token')
            return make_succ_response(result)
            
        except ValueError as e:
            app_logger.error(f'刷新token时发生错误: {str(e)}')
            return make_err_response({}, str(e))
        except Exception as e:
            app_logger.error(f'刷新Token过程中发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'刷新Token失败: {str(e)}')

    def logout(self, decoded: dict):
        """
        用户登出接口
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行登出接口 ===')
        
        try:
            openid = decoded.get('openid')
            if not openid:
                return make_err_response({}, 'token无效')
            
            result = self.auth_service.logout(openid)
            
            app_logger.info('成功登出')
            return make_succ_response(result)
            
        except Exception as e:
            app_logger.error(f'登出过程中发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'登出失败: {str(e)}')


class CheckinController:
    """
    打卡控制器
    """
    def __init__(self):
        self.checkin_rule_service = CheckinRuleService()
        self.checkin_record_service = CheckinRecordService()
        self.user_service = UserService()

    def get_today_checkin_items(self, decoded: Dict[str, Any]):
        """
        获取用户今日打卡事项列表
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行获取今日打卡事项接口 ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            checkin_items = self.checkin_record_service.get_today_checkin_items(user.user_id)
            
            from datetime import date
            response_data = {
                'date': date.today().strftime('%Y-%m-%d'),
                'checkin_items': checkin_items
            }
            
            app_logger.info(f'成功获取今日打卡事项，用户ID: {user.user_id}, 事项数量: {len(checkin_items)}')
            return make_succ_response(response_data)
            
        except Exception as e:
            app_logger.error(f'获取今日打卡事项时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'获取今日打卡事项失败: {str(e)}')

    def perform_checkin(self, decoded: Dict[str, Any]):
        """
        执行打卡操作
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行打卡接口 ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            # 获取请求参数
            params = request.get_json()
            rule_id = params.get('rule_id')
            
            if not rule_id:
                return make_err_response({}, '缺少rule_id参数')
            
            result = self.checkin_record_service.perform_checkin(rule_id, user.user_id)
            
            app_logger.info(f'用户 {user.user_id} 打卡成功，规则ID: {rule_id}')
            return make_succ_response(result)
            
        except ValueError as e:
            return make_err_response({}, str(e))
        except Exception as e:
            app_logger.error(f'打卡时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'打卡失败: {str(e)}')

    def cancel_checkin(self, decoded: Dict[str, Any]):
        """
        撤销打卡操作
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行撤销打卡接口 ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            # 获取请求参数
            params = request.get_json()
            record_id = params.get('record_id')
            
            if not record_id:
                return make_err_response({}, '缺少record_id参数')
            
            result = self.checkin_record_service.cancel_checkin(record_id, user.user_id)
            
            app_logger.info(f'用户 {user.user_id} 撤销打卡成功，记录ID: {record_id}')
            return make_succ_response(result)
            
        except ValueError as e:
            return make_err_response({}, str(e))
        except Exception as e:
            app_logger.error(f'撤销打卡时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'撤销打卡失败: {str(e)}')

    def get_checkin_history(self, decoded: Dict[str, Any]):
        """
        获取打卡历史记录
        """
        import logging
        from datetime import datetime, date, timedelta
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行获取打卡历史接口 ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            # 获取查询参数
            params = request.args
            start_date_str = params.get('start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
            end_date_str = params.get('end_date', date.today().strftime('%Y-%m-%d'))
            
            # 解析日期
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            history_data = self.checkin_record_service.get_checkin_history(user.user_id, start_date, end_date)
            
            response_data = {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'history': history_data
            }
            
            app_logger.info(f'成功获取打卡历史，用户ID: {user.user_id}, 记录数量: {len(history_data)}')
            return make_succ_response(response_data)
            
        except Exception as e:
            app_logger.error(f'获取打卡历史时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'获取打卡历史失败: {str(e)}')

    def manage_checkin_rules(self, decoded: Dict[str, Any]):
        """
        打卡规则管理接口
        """
        import logging
        from datetime import datetime as dt
        app_logger = logging.getLogger('log')
        app_logger.info(f'=== 开始执行打卡规则管理接口: {request.method} ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            if request.method == 'GET':
                # 获取用户的所有打卡规则
                rules = self.checkin_rule_service.get_rules_by_user_id(user.user_id)
                
                rules_data = []
                for rule in rules:
                    rules_data.append({
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'icon_url': rule.icon_url,
                        'frequency_type': rule.frequency_type,
                        'time_slot_type': rule.time_slot_type,
                        'custom_time': rule.custom_time.strftime('%H:%M:%S') if rule.custom_time else None,
                        'week_days': rule.week_days,
                        'status': rule.status,
                        'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                response_data = {
                    'rules': rules_data
                }
                
                app_logger.info(f'成功获取打卡规则列表，用户ID: {user.user_id}, 规则数量: {len(rules_data)}')
                return make_succ_response(response_data)
                
            elif request.method == 'POST':
                # 创建打卡规则
                params = request.get_json()
                
                rule_name = params.get('rule_name')
                if not rule_name:
                    return make_err_response({}, '缺少rule_name参数')
                
                # 创建新的打卡规则
                new_rule = self.checkin_rule_service.create_rule(user.user_id, params)
                
                # 返回完整的规则信息
                response_data = {
                    'rule_id': new_rule.rule_id,
                    'rule_name': new_rule.rule_name,
                    'icon_url': new_rule.icon_url,
                    'frequency_type': new_rule.frequency_type,
                    'time_slot_type': new_rule.time_slot_type,
                    'custom_time': new_rule.custom_time.strftime('%H:%M:%S') if new_rule.custom_time else None,
                    'week_days': new_rule.week_days,
                    'status': new_rule.status,
                    'created_at': new_rule.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': new_rule.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': '创建打卡规则成功'
                }
                
                app_logger.info(f'成功创建打卡规则，用户ID: {user.user_id}, 规则ID: {new_rule.rule_id}')
                return make_succ_response(response_data)
                
            elif request.method == 'PUT':
                # 更新打卡规则
                params = request.get_json()
                
                rule_id = params.get('rule_id')
                if not rule_id:
                    return make_err_response({}, '缺少rule_id参数')
                
                # 验证规则是否存在且属于当前用户
                rule = self.checkin_rule_service.get_rule_by_id(rule_id)
                if not rule or rule.solo_user_id != user.user_id:
                    return make_err_response({}, '打卡规则不存在或无权限')
                
                # 更新规则
                updated_rule = self.checkin_rule_service.update_rule(rule, params)
                
                response_data = {
                    'rule_id': updated_rule.rule_id,
                    'message': '更新打卡规则成功'
                }
                
                app_logger.info(f'成功更新打卡规则，用户ID: {user.user_id}, 规则ID: {updated_rule.rule_id}')
                return make_succ_response(response_data)
                
            elif request.method == 'DELETE':
                # 删除打卡规则
                params = request.get_json()
                
                rule_id = params.get('rule_id')
                if not rule_id:
                    return make_err_response({}, '缺少rule_id参数')
                
                # 验证规则是否存在且属于当前用户
                rule = self.checkin_rule_service.get_rule_by_id(rule_id)
                if not rule or rule.solo_user_id != user.user_id:
                    return make_err_response({}, '打卡规则不存在或无权限')
                
                self.checkin_rule_service.delete_rule(rule_id)
                
                response_data = {
                    'rule_id': rule_id,
                    'message': '删除打卡规则成功'
                }
                
                app_logger.info(f'成功删除打卡规则，用户ID: {user.user_id}, 规则ID: {rule_id}')
                return make_succ_response(response_data)
                
        except Exception as e:
            app_logger.error(f'打卡规则管理时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'打卡规则管理失败: {str(e)}')


class CommunityController:
    """
    社区控制器
    """
    def __init__(self):
        self.user_service = UserService()
        self.auth_service = AuthService()

    def community_verify(self, decoded: Dict[str, Any]):
        """
        社区工作人员身份验证接口
        """
        import logging
        app_logger = logging.getLogger('log')
        app_logger.info('=== 开始执行社区工作人员身份验证接口 ===')
        
        openid = decoded.get('openid')
        user = self.user_service.get_user_by_openid(openid)
        if not user:
            app_logger.error(f'数据库中未找到openid为 {openid} 的用户')
            return make_err_response({}, '用户不存在')

        try:
            # 获取请求参数
            params = request.get_json()
            name = params.get('name')
            work_id = params.get('workId')  # 注意：前端使用驼峰命名
            work_proof = params.get('workProof')  # 工作证明照片URL或base64
            
            if not name or not work_id or not work_proof:
                return make_err_response({}, '缺少必要参数：姓名、工号或工作证明')
            
            result = self.user_service.verify_community_user(user, name, work_id, work_proof)
            
            app_logger.info(f'用户 {user.user_id} 身份验证申请已提交')
            return make_succ_response(result)
            
        except Exception as e:
            app_logger.error(f'身份验证时发生错误: {str(e)}', exc_info=True)
            return make_err_response({}, f'身份验证失败: {str(e)}')