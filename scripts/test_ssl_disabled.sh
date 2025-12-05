#!/bin/bash
# 测试禁用SSL验证后的微信API连接

set -e

echo "=== 测试禁用SSL验证的微信API连接 ==="
echo ""

cd "$(dirname "$0")/../"

# 激活虚拟环境
source venv_py312/bin/activate

echo "1. 测试微信API连接（禁用SSL验证）..."

python3 -c "
import requests
import sys

print('测试微信API SSL连接（verify=False）...')
try:
    response = requests.get(
        'https://api.weixin.qq.com/sns/jscode2session?appid=test&secret=test&js_code=test&grant_type=authorization_code',
        timeout=10,
        verify=False  # 禁用SSL验证
    )
    print('✅ SSL连接成功！（验证已禁用）')
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text[:100]}...')
except Exception as e:
    print(f'❌ SSL连接失败: {str(e)}')
    sys.exit(1)
"

echo ""
echo "2. 测试微信API模块..."

python3 -c "
import os
os.environ['ENV_TYPE'] = 'prod'  # 设置为生产环境
os.environ['WX_APPID'] = 'test_appid'
os.environ['WX_SECRET'] = 'test_secret'

from wxcloudrun.wxchat_api import get_user_info_by_code

print('测试微信API模块（禁用SSL验证）...')
try:
    result = get_user_info_by_code('test_code')
    print('✅ 微信API模块调用成功！')
    print(f'返回结果: {result}')
except Exception as e:
    print(f'❌ 微信API模块调用失败: {str(e)}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "3. 安全提醒..."
echo "⚠️  注意：SSL验证已被禁用，这会带来安全风险："
echo "   - 数据可能被中间人攻击拦截"
echo "   - 无法验证服务器身份真实性"
echo "   - 建议仅在测试环境中使用此配置"
echo "   - 生产环境应考虑更新CA证书的解决方案"

echo ""
echo "✅ 禁用SSL验证测试完成！"