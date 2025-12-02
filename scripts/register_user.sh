#!/bin/bash

# 安全守护项目 - 手机号注册用户脚本
# 使用说明：
# 1. 首先运行脚本发送验证码
# 2. 然后使用返回的验证码注册用户

# 服务器地址
SERVER_URL="http://localhost:8080"

# 手机号码（可通过参数指定，否则使用默认值）
PHONE_NUMBER="${1:-13800138000}"

# 用户昵称（可选）
NICKNAME="测试用户"

# 头像URL（可选）
AVATAR_URL="https://example.com/avatar.jpg"

echo "=== 安全守护项目 - 手机号注册用户 ==="
echo "服务器地址: $SERVER_URL"
echo "手机号码: $PHONE_NUMBER"
echo ""
echo "使用方法:"
echo "  ./register_user.sh [手机号码]"
echo "  例如: ./register_user.sh 13912345678"
echo "  不提供参数时使用默认手机号: 13800138000"
echo ""

# 步骤1: 发送验证码
echo "步骤1: 发送验证码..."

# 先获取原始响应
RAW_SMS_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/send_sms" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE_NUMBER\"}")

# 检查响应是否为空
if [ -z "$RAW_SMS_RESPONSE" ]; then
    echo "❌ 错误：服务器未返回响应，请检查服务器是否运行"
    exit 1
fi

# 尝试格式化JSON响应
SMS_RESPONSE=$(echo "$RAW_SMS_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))" 2>/dev/null)

# 如果JSON解析失败，显示原始响应
if [ $? -ne 0 ]; then
    echo "❌ 错误：服务器返回的不是有效的JSON格式"
    echo "原始响应："
    echo "$RAW_SMS_RESPONSE"
    exit 1
fi

echo "发送验证码响应:"
echo "$SMS_RESPONSE"

# 从响应中提取验证码（仅开发环境）
VERIFICATION_CODE=$(echo "$SMS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('verification_code', ''))" 2>/dev/null)

if [ -n "$VERIFICATION_CODE" ]; then
    echo "✅ 开发环境验证码: $VERIFICATION_CODE"
else
    # 尝试从Redis获取验证码（开发环境）
    REDIS_CODE=$(docker exec redis redis-cli get "sms_verification:+86$PHONE_NUMBER" 2>/dev/null | tr -d '\r\n')
    
    if [ -n "$REDIS_CODE" ] && [ "$REDIS_CODE" != "(nil)" ]; then
        echo "✅ 从Redis获取验证码: $REDIS_CODE"
        VERIFICATION_CODE="$REDIS_CODE"
    else
        # 检查是否是Redis未配置的问题
        ERROR_MSG=$(echo "$SMS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('message', ''))" 2>/dev/null)
        
        if [[ "$ERROR_MSG" == *"验证码存储失败"* ]] || [[ "$ERROR_MSG" == *"Redis"* ]]; then
            echo "⚠️  检测到Redis未配置，使用默认验证码: 123456"
            VERIFICATION_CODE="123456"
        else
            echo "请检查手机短信获取验证码"
            echo "请手动输入验证码:"
            read VERIFICATION_CODE
        fi
    fi
fi

echo ""

# 步骤2: 注册用户
echo "步骤2: 使用验证码注册用户..."

# 先获取原始响应
RAW_REGISTER_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/register_phone" \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE_NUMBER\", \"code\": \"$VERIFICATION_CODE\", \"nickname\": \"$NICKNAME\", \"avatar_url\": \"$AVATAR_URL\"}")

# 检查响应是否为空
if [ -z "$RAW_REGISTER_RESPONSE" ]; then
    echo "❌ 错误：服务器未返回响应，请检查服务器是否运行"
    exit 1
fi

# 尝试格式化JSON响应
REGISTER_RESPONSE=$(echo "$RAW_REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))" 2>/dev/null)

# 如果JSON解析失败，显示原始响应
if [ $? -ne 0 ]; then
    echo "❌ 错误：服务器返回的不是有效的JSON格式"
    echo "原始响应："
    echo "$RAW_REGISTER_RESPONSE"
    exit 1
fi

echo "注册用户响应:"
echo "$REGISTER_RESPONSE"

# 检查注册是否成功
SUCCESS_CODE=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('code', 0))" 2>/dev/null)
if [ "$SUCCESS_CODE" = "1" ]; then
    echo ""
    echo "✅ 用户注册成功！"
    
    # 提取用户ID和令牌
    USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('user_id', ''))" 2>/dev/null)
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('tokens', {}).get('access_token', ''))" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('tokens', {}).get('refresh_token', ''))" 2>/dev/null)
    
    echo "用户ID: $USER_ID"
    echo "访问令牌: $ACCESS_TOKEN"
    echo "刷新令牌: $REFRESH_TOKEN"
    
    # 保存令牌到文件
    echo "ACCESS_TOKEN=$ACCESS_TOKEN" > tokens.env
    echo "REFRESH_TOKEN=$REFRESH_TOKEN" >> tokens.env
    echo "USER_ID=$USER_ID" >> tokens.env
    echo ""
    echo "令牌已保存到 tokens.env 文件"
else
    echo ""
    echo "❌ 用户注册失败，请检查错误信息"
fi

echo ""
echo "=== 脚本执行完成 ==="