import jwt
from datetime import datetime, timezone, timedelta
import os

def create_jwt_token(test_user_id):
    """创建一个有效的 JWT token 用于测试"""
    token = jwt.encode({
        'user_id': test_user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')
    return token