# SafeGuard 后端代码规范

## 1. 概述

本文档定义了 SafeGuard 后端项目的代码规范，确保代码一致性、可维护性和可读性。所有开发者必须遵循这些规范。

## 2. 技术栈

- **Python 版本**: Python 3.12
- **Web 框架**: Flask 3.1.2
- **ORM**: SQLAlchemy 2.0 + Flask-SQLAlchemy 3.0.5
- **数据库迁移**: Alembic 1.13.1
- **认证**: JWT (PyJWT 2.4.0)
- **测试框架**: pytest 7.4.3

## 3. 数据库操作规范

### 3.1 使用 `db.session` 进行所有数据库操作

**原则**: 所有数据库操作必须通过 `db.session` 进行，禁止直接使用 SQLAlchemy 的 `Session` 或其他方式。

```python
# ✅ 正确：使用 db.session
from database.flask_models import db

# 查询单个对象
user = db.session.get(User, user_id)

# 查询多个对象
users = db.session.query(User).filter(User.status == 1).all()

# 创建新对象
new_user = User(
    phone_number='13800138000',
    nickname='测试用户'
)
db.session.add(new_user)
db.session.commit()

# 更新对象
user.nickname = '新昵称'
db.session.commit()

# 删除对象（软删除）
user.is_deleted = True
db.session.commit()

# 删除对象（硬删除）
db.session.delete(user)
db.session.commit()

# ❌ 错误：禁止直接使用 SQLAlchemy Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///test.db')
Session = sessionmaker(bind=engine)
session = Session()  # 禁止这样做！
```

### 3.2 SQLAlchemy 2.0 API 使用规范

**原则**: 使用 SQLAlchemy 2.0 的 API，禁止使用 1.x 的 API。

```python
# ✅ 正确：SQLAlchemy 2.0 API
# 使用 db.session.get() 替代 Query.get()
user = db.session.get(User, user_id)

# 使用 select() 进行复杂查询
from sqlalchemy import select
stmt = select(User).where(User.status == 1)
users = db.session.execute(stmt).scalars().all()

# 使用 func.date() 进行日期比较
from sqlalchemy import func
records = db.session.query(CheckinRecord).filter(
    func.date(CheckinRecord.planned_time) >= start_date
).all()

# ❌ 错误：SQLAlchemy 1.x API
# 禁止使用 Query.get()
user = db.session.query(User).get(user_id)  # 禁止这样做！

# 禁止使用旧的 filter 方式
users = db.session.query(User).filter_by(status=1).all()  # 不推荐
```

### 3.3 数据库操作最佳实践

#### 3.3.1 查询操作

**原则**: 查询操作应该高效、安全，避免 N+1 查询问题。

```python
# ✅ 最佳实践 1: 使用 db.session.get() 查询单个对象
def get_user(user_id):
    """根据用户ID获取用户"""
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError('用户不存在')
    return user

# ✅ 最佳实践 2: 使用 filter() 进行条件查询
def get_active_users():
    """获取所有活跃用户"""
    users = db.session.query(User).filter(
        User.status == 1,
        User.is_deleted == False
    ).all()
    return users

# ✅ 最佳实践 3: 使用 join() 进行关联查询
def get_users_with_community():
    """获取用户及其社区信息"""
    from sqlalchemy.orm import joinedload
    
    users = db.session.query(User).options(
        joinedload(User.community)
    ).filter(
        User.is_deleted == False
    ).all()
    return users

# ✅ 最佳实践 4: 使用 func.date() 进行日期比较
def get_records_by_date_range(user_id, start_date, end_date):
    """根据日期范围获取记录"""
    from sqlalchemy import func
    
    records = db.session.query(CheckinRecord).filter(
        CheckinRecord.user_id == user_id,
        func.date(CheckinRecord.planned_time) >= start_date,
        func.date(CheckinRecord.planned_time) <= end_date
    ).order_by(CheckinRecord.planned_time.desc()).all()
    return records

# ✅ 最佳实践 5: 使用 in_() 进行批量查询
def get_users_by_ids(user_ids):
    """根据用户ID列表获取用户"""
    users = db.session.query(User).filter(
        User.user_id.in_(user_ids)
    ).all()
    return users

# ❌ 错误示例 1: 循环查询（N+1 问题）
def get_users_with_community_bad():
    """❌ 错误：N+1 查询问题"""
    users = db.session.query(User).all()
    for user in users:
        print(user.community.name)  # 每次访问都会触发一次查询
    return users

# ❌ 错误示例 2: 查询后不检查是否存在
def get_user_bad(user_id):
    """❌ 错误：不检查是否存在"""
    user = db.session.get(User, user_id)
    return user.nickname  # 如果 user 为 None，会抛出 AttributeError

# ❌ 错误示例 3: 使用字符串拼接（SQL 注入风险）
def get_user_by_phone_bad(phone_number):
    """❌ 错误：SQL 注入风险"""
    query = f"SELECT * FROM users WHERE phone_number = '{phone_number}'"
    user = db.session.execute(query).first()
    return user
```

#### 3.3.2 创建操作

**原则**: 创建操作应该验证数据、使用事务、处理异常。

```python
# ✅ 最佳实践 1: 完整的创建流程
def create_user(user_data):
    """
    创建新用户
    
    Args:
        user_data (dict): 用户数据
        
    Returns:
        User: 创建的用户对象
        
    Raises:
        ValueError: 当数据验证失败时
    """
    try:
        # 1. 数据验证
        if not user_data.get('phone_number'):
            raise ValueError('手机号不能为空')
        
        if not user_data.get('password'):
            raise ValueError('密码不能为空')
        
        # 2. 检查手机号是否已存在
        existing_user = db.session.query(User).filter(
            User.phone_number == user_data['phone_number']
        ).first()
        
        if existing_user:
            raise ValueError('手机号已被注册')
        
        # 3. 创建用户对象
        user = User(
            phone_number=user_data['phone_number'],
            nickname=user_data.get('nickname', '用户'),
            password_hash=generate_password_hash(user_data['password'])
        )
        
        # 4. 添加到会话
        db.session.add(user)
        
        # 5. 提交事务
        db.session.commit()
        
        logger.info(f"创建用户成功，用户ID: {user.user_id}")
        return user
        
    except Exception as e:
        # 6. 回滚事务
        db.session.rollback()
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        raise e

# ✅ 最佳实践 2: 批量创建
def create_users_batch(users_data):
    """批量创建用户"""
    try:
        users = []
        for user_data in users_data:
            user = User(**user_data)
            users.append(user)
        
        db.session.add_all(users)
        db.session.commit()
        
        logger.info(f"批量创建用户成功，数量: {len(users)}")
        return users
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量创建用户失败: {str(e)}", exc_info=True)
        raise e

# ❌ 错误示例 1: 没有事务处理
def create_user_bad(user_data):
    """❌ 错误：没有事务处理"""
    user = User(**user_data)
    db.session.add(user)
    db.session.commit()
    # 如果后续操作失败，无法回滚

# ❌ 错误示例 2: 没有数据验证
def create_user_bad2(user_data):
    """❌ 错误：没有数据验证"""
    user = User(**user_data)  # 可能缺少必要字段
    db.session.add(user)
    db.session.commit()

# ❌ 错误示例 3: 没有异常处理
def create_user_bad3(user_data):
    """❌ 错误：没有异常处理"""
    user = User(**user_data)
    db.session.add(user)
    db.session.commit()  # 如果失败，没有回滚
```

#### 3.3.3 更新操作

**原则**: 更新操作应该先查询、验证权限、使用事务。

```python
# ✅ 最佳实践 1: 完整的更新流程
def update_user(user_id, update_data):
    """
    更新用户信息
    
    Args:
        user_id (int): 用户ID
        update_data (dict): 更新数据
        
    Returns:
        User: 更新后的用户对象
        
    Raises:
        ValueError: 当用户不存在或无权限时
    """
    try:
        # 1. 查询用户
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        
        # 2. 更新字段
        if 'nickname' in update_data:
            user.nickname = update_data['nickname']
        
        if 'avatar_url' in update_data:
            user.avatar_url = update_data['avatar_url']
        
        # 3. 更新时间戳
        user.updated_at = datetime.now()
        
        # 4. 提交事务
        db.session.commit()
        
        logger.info(f"更新用户成功，用户ID: {user_id}")
        return user
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户失败: {str(e)}", exc_info=True)
        raise e

# ✅ 最佳实践 2: 批量更新
def update_users_status(user_ids, status):
    """批量更新用户状态"""
    try:
        db.session.query(User).filter(
            User.user_id.in_(user_ids)
        ).update({
            'status': status,
            'updated_at': datetime.now()
        }, synchronize_session=False)
        
        db.session.commit()
        
        logger.info(f"批量更新用户状态成功，数量: {len(user_ids)}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量更新用户状态失败: {str(e)}", exc_info=True)
        raise e

# ❌ 错误示例 1: 不检查对象是否存在
def update_user_bad(user_id, update_data):
    """❌ 错误：不检查对象是否存在"""
    user = db.session.get(User, user_id)
    user.nickname = update_data['nickname']  # 如果 user 为 None，会抛出 AttributeError
    db.session.commit()

# ❌ 错误示例 2: 直接修改数据库字段
def update_user_bad2(user_id, nickname):
    """❌ 错误：直接修改数据库字段"""
    db.session.execute(
        "UPDATE users SET nickname = ? WHERE user_id = ?",
        (nickname, user_id)
    )
    db.session.commit()
```

#### 3.3.4 删除操作

**原则**: 删除操作应该使用软删除，禁止物理删除。

```python
# ✅ 最佳实践 1: 软删除
def delete_user(user_id):
    """
    删除用户（软删除）
    
    Args:
        user_id (int): 用户ID
        
    Raises:
        ValueError: 当用户不存在时
    """
    try:
        # 1. 查询用户
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')
        
        # 2. 软删除
        user.is_deleted = True
        user.deleted_at = datetime.now()
        
        # 3. 提交事务
        db.session.commit()
        
        logger.info(f"删除用户成功，用户ID: {user_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败: {str(e)}", exc_info=True)
        raise e

# ✅ 最佳实践 2: 批量软删除
def delete_users_batch(user_ids):
    """批量删除用户（软删除）"""
    try:
        db.session.query(User).filter(
            User.user_id.in_(user_ids)
        ).update({
            'is_deleted': True,
            'deleted_at': datetime.now()
        }, synchronize_session=False)
        
        db.session.commit()
        
        logger.info(f"批量删除用户成功，数量: {len(user_ids)}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量删除用户失败: {str(e)}", exc_info=True)
        raise e

# ❌ 错误示例 1: 物理删除
def delete_user_bad(user_id):
    """❌ 错误：物理删除"""
    user = db.session.get(User, user_id)
    db.session.delete(user)  # 禁止物理删除！
    db.session.commit()

# ❌ 错误示例 2: 不检查对象是否存在
def delete_user_bad2(user_id):
    """❌ 错误：不检查对象是否存在"""
    user = db.session.get(User, user_id)
    user.is_deleted = True  # 如果 user 为 None，会抛出 AttributeError
    db.session.commit()
```

#### 3.3.5 事务处理

**原则**: 所有写操作必须使用事务，确保数据一致性。

```python
# ✅ 最佳实践 1: 简单事务
def create_user(user_data):
    """创建用户"""
    try:
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        raise e

# ✅ 最佳实践 2: 复杂事务（多个操作）
def create_user_with_profile(user_data, profile_data):
    """创建用户和用户档案"""
    try:
        # 1. 创建用户
        user = User(**user_data)
        db.session.add(user)
        db.session.flush()  # 获取 user_id 但不提交
        
        # 2. 创建用户档案
        profile = UserProfile(
            user_id=user.user_id,
            **profile_data
        )
        db.session.add(profile)
        
        # 3. 创建默认社区
        community = Community(
            name=f"{user.nickname}的社区",
            creator_id=user.user_id
        )
        db.session.add(community)
        
        # 4. 提交事务
        db.session.commit()
        
        logger.info(f"创建用户和档案成功，用户ID: {user.user_id}")
        return user
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建用户和档案失败: {str(e)}", exc_info=True)
        raise e

# ✅ 最佳实践 3: 嵌套事务（使用 savepoint）
def create_user_with_optional_profile(user_data, profile_data=None):
    """创建用户，可选创建用户档案"""
    try:
        # 1. 创建用户
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        
        # 2. 如果提供了档案数据，创建档案
        if profile_data:
            try:
                profile = UserProfile(
                    user_id=user.user_id,
                    **profile_data
                )
                db.session.add(profile)
                db.session.commit()
            except Exception as e:
                # 档案创建失败，不影响用户创建
                db.session.rollback()
                logger.warning(f"创建用户档案失败: {str(e)}")
        
        return user
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        raise e

# ❌ 错误示例 1: 没有事务
def create_user_bad(user_data):
    """❌ 错误：没有事务"""
    user = User(**user_data)
    db.session.add(user)
    db.session.commit()
    # 如果后续操作失败，无法回滚

# ❌ 错误示例 2: 异常处理不完整
def create_user_bad2(user_data):
    """❌ 错误：异常处理不完整"""
    try:
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        # 没有回滚！
        raise e
```

### 3.4 软删除规范

**原则**: 删除操作使用软删除，通过 `is_deleted` 字段标记，禁止直接物理删除。

```python
# ✅ 正确：软删除
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValueError('用户不存在')
    
    user.is_deleted = True
    user.deleted_at = datetime.now()
    db.session.commit()

# ❌ 错误：物理删除
def delete_user_hard(user_id):
    user = db.session.get(User, user_id)
    db.session.delete(user)  # 禁止物理删除！
    db.session.commit()
```

### 3.5 查询优化规范

**原则**: 使用 `select_related` 和 `joinedload` 进行关联查询优化，避免 N+1 查询问题。

```python
# ✅ 正确：使用 joinedload 优化关联查询
from sqlalchemy.orm import joinedload

# 一次性加载用户和社区信息
users = db.session.query(User).options(
    joinedload(User.community)
).all()

# ❌ 错误：N+1 查询问题
users = db.session.query(User).all()
for user in users:
    print(user.community.name)  # 每次访问都会触发一次查询
```

## 4. 代码结构规范

### 4.1 Blueprint 模块化规范

**原则**: 每个功能域一个 Blueprint，包含 `__init__.py` 和 `routes.py`。

```
src/app/modules/
├── auth/
│   ├── __init__.py          # Blueprint 定义
│   └── routes.py            # 路由定义
├── user/
│   ├── __init__.py
│   └── routes.py
└── ...
```

**Blueprint 定义规范**:

```python
# __init__.py
"""
认证模块蓝图定义
"""
from flask import Blueprint

# 定义认证模块蓝图
auth_bp = Blueprint(
    name='auth',
    import_name=__name__,
    url_prefix='/auth'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes
```

**路由定义规范**:

```python
# routes.py
from flask import request, jsonify
from app.shared.response import make_succ_response, make_err_response
from database.flask_models import db
from app.modules.auth import auth_bp

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        # 参数验证
        phone_number = request.json.get('phone_number')
        password = request.json.get('password')
        
        if not phone_number or not password:
            return make_err_response({}, '缺少必要参数')
        
        # 业务逻辑
        from wxcloudrun.user_service import UserService
        user = UserService.authenticate(phone_number, password)
        
        return make_succ_response({
            'user_id': user.user_id,
            'nickname': user.nickname
        })
        
    except Exception as e:
        return make_err_response({}, f'登录失败: {str(e)}')
```

### 4.2 Service 层规范

**原则**: 业务逻辑放在 Service 层，不放在路由层。

```python
# ✅ 正确：Service 层处理业务逻辑
# wxcloudrun/user_service.py

class UserService:
    @staticmethod
    def create_user(user_data):
        """创建用户"""
        # 验证数据
        if not user_data.get('phone_number'):
            raise ValueError('手机号不能为空')
        
        # 创建用户
        user = User(**user_data)
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def authenticate(phone_number, password):
        """用户认证"""
        user = db.session.query(User).filter(
            User.phone_number == phone_number
        ).first()
        
        if not user:
            raise ValueError('用户不存在')
        
        if not user.check_password(password):
            raise ValueError('密码错误')
        
        return user

# routes.py - 路由只负责参数验证和响应
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        phone_number = request.json.get('phone_number')
        password = request.json.get('password')
        
        user = UserService.authenticate(phone_number, password)
        
        return make_succ_response({'user_id': user.user_id})
        
    except Exception as e:
        return make_err_response({}, str(e))

# ❌ 错误：业务逻辑放在路由层
@auth_bp.route('/login', methods=['POST'])
def login():
    phone_number = request.json.get('phone_number')
    password = request.json.get('password')
    
    # 业务逻辑不应该在这里！
    user = db.session.query(User).filter(
        User.phone_number == phone_number
    ).first()
    
    if not user:
        return make_err_response({}, '用户不存在')
    
    if not user.check_password(password):
        return make_err_response({}, '密码错误')
    
    return make_succ_response({'user_id': user.user_id})
```

### 4.3 响应格式规范

**原则**: 统一使用 `make_succ_response` 和 `make_err_response` 返回响应。

```python
# ✅ 正确：使用统一响应格式
from app.shared.response import make_succ_response, make_err_response

# 成功响应
return make_succ_response({
    'user_id': user.user_id,
    'nickname': user.nickname
})

# 失败响应
return make_err_response({}, '用户不存在')

# ❌ 错误：直接返回 jsonify
from flask import jsonify
return jsonify({'code': 1, 'data': user_data, 'msg': 'success'})  # 不推荐
```

## 5. 命名规范

### 5.1 文件命名

- Python 文件：使用小写字母和下划线，如 `user_service.py`
- 测试文件：使用 `test_` 前缀，如 `test_user_service.py`

### 5.2 变量命名

- 普通变量：使用小写字母和下划线，如 `user_id`, `phone_number`
- 常量：使用大写字母和下划线，如 `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE`
- 私有变量：使用单下划线前缀，如 `_internal_method`

### 5.3 函数命名

- 普通函数：使用小写字母和下划线，如 `create_user`, `get_user_by_id`
- 私有函数：使用单下划线前缀，如 `_validate_user_data`

### 5.4 类命名

- 类名：使用驼峰命名法，如 `UserService`, `CheckinRecord`
- 私有类：使用单下划线前缀，如 `_InternalHelper`

### 5.5 数据库字段命名

- 数据库字段：使用小写字母和下划线，如 `user_id`, `phone_number`, `created_at`
- 外键字段：使用 `{table}_id` 格式，如 `user_id`, `community_id`

## 6. 注释规范

### 6.1 文档字符串

**原则**: 所有公共函数和类必须包含文档字符串。

```python
def create_user(user_data):
    """
    创建新用户
    
    Args:
        user_data (dict): 用户数据字典，包含以下字段：
            - phone_number (str): 手机号
            - nickname (str): 昵称
            - password (str): 密码
    
    Returns:
        User: 创建的用户对象
    
    Raises:
        ValueError: 当手机号已存在或数据验证失败时
    """
    # 实现代码
    pass
```

### 6.2 行内注释

**原则**: 复杂逻辑必须添加注释，简单逻辑不需要注释。

```python
# ✅ 正确：复杂逻辑添加注释
# 检查用户是否已存在
existing_user = db.session.query(User).filter(
    User.phone_number == phone_number
).first()

if existing_user:
    raise ValueError('手机号已被注册')

# ❌ 错误：简单逻辑不需要注释
# 获取用户
user = db.session.get(User, user_id)  # 这里的注释是多余的
```

## 7. 错误处理规范

### 7.1 异常处理

**原则**: 使用 try-except 捕获异常，并记录日志。

```python
# ✅ 正确：完整的异常处理
import logging

logger = logging.getLogger(__name__)

def process_checkin(rule_id, user_id):
    try:
        # 业务逻辑
        record = CheckinRecordService.perform_checkin(rule_id, user_id)
        logger.info(f"用户 {user_id} 打卡成功，规则ID: {rule_id}")
        return record
        
    except ValueError as e:
        # 业务异常
        logger.warning(f"打卡失败: {str(e)}")
        raise e
        
    except Exception as e:
        # 系统异常
        logger.error(f"打卡时发生系统错误: {str(e)}", exc_info=True)
        raise e

# ❌ 错误：没有异常处理
def process_checkin(rule_id, user_id):
    record = CheckinRecordService.perform_checkin(rule_id, user_id)
    return record  # 如果抛出异常，没有日志记录
```

### 7.2 错误响应

**原则**: 统一使用 `make_err_response` 返回错误响应。

```python
# ✅ 正确：返回错误响应
try:
    user = UserService.create_user(user_data)
    return make_succ_response({'user_id': user.user_id})
    
except ValueError as e:
    return make_err_response({}, str(e))
    
except Exception as e:
    logger.error(f"创建用户失败: {str(e)}", exc_info=True)
    return make_err_response({}, '系统错误，请稍后重试')
```

## 8. 测试规范

### 8.1 测试文件组织

```
tests/
├── unit/              # 单元测试
│   ├── conftest.py    # 单元测试配置
│   ├── test_user_service.py
│   └── ...
├── integration/       # 集成测试
│   ├── conftest.py    # 集成测试配置
│   ├── test_user_integration.py
│   └── ...
└── e2e/              # 端到端测试
    ├── conftest.py    # E2E 测试配置
    └── ...
```

### 8.2 测试数据生成

**原则**: 使用统一的测试数据生成器，确保测试数据唯一性和隔离性。

```python
# ✅ 正确：使用测试数据生成器
from wxcloudrun.test_data_generator import TestDataManager

def test_create_user():
    """测试创建用户"""
    # 生成唯一测试数据
    test_data = TestDataManager.get_instance()
    phone_number = test_data.generate_phone()
    nickname = test_data.generate_nickname()
    
    user = UserService.create_user({
        'phone_number': phone_number,
        'nickname': nickname,
        'password': 'password123'
    })
    
    assert user.phone_number == phone_number
    assert user.nickname == nickname

# ❌ 错误：硬编码测试数据
def test_create_user():
    """测试创建用户"""
    user = UserService.create_user({
        'phone_number': '13800138000',  # 硬编码，可能冲突
        'nickname': '测试用户',
        'password': 'password123'
    })
    
    assert user.phone_number == '13800138000'
```

### 8.3 测试隔离

**原则**: 每个测试使用不同的测试数据，保持测试用例之间的独立性。

```python
# ✅ 正确：每个测试使用不同的测试数据
def test_create_user_1():
    test_data = TestDataManager.get_instance()
    phone_number = test_data.generate_phone()
    user = UserService.create_user({'phone_number': phone_number, ...})
    assert user.phone_number == phone_number

def test_create_user_2():
    test_data = TestDataManager.get_instance()
    phone_number = test_data.generate_phone()  # 生成不同的手机号
    user = UserService.create_user({'phone_number': phone_number, ...})
    assert user.phone_number == phone_number

# ❌ 错误：多个测试使用相同的测试数据
def test_create_user_1():
    user = UserService.create_user({'phone_number': '13800138000', ...})
    assert user.phone_number == '13800138000'

def test_create_user_2():
    user = UserService.create_user({'phone_number': '13800138000', ...})  # 冲突！
    assert user.phone_number == '13800138000'
```

## 9. 日志规范

### 9.1 日志级别

- **DEBUG**: 详细的调试信息，用于开发阶段
- **INFO**: 一般信息，记录重要的业务流程
- **WARNING**: 警告信息，记录潜在问题
- **ERROR**: 错误信息，记录错误和异常
- **CRITICAL**: 严重错误，记录系统崩溃级别的错误

### 9.2 日志格式

```python
# ✅ 正确：使用结构化日志
logger.info(f"用户 {user_id} 登录成功，IP: {ip_address}")
logger.warning(f"用户 {user_id} 登录失败，原因: {reason}")
logger.error(f"创建用户失败: {str(e)}", exc_info=True)

# ❌ 错误：日志信息不清晰
logger.info("登录成功")
logger.error("出错了")
```

## 10. 安全规范

### 10.1 密码处理

**原则**: 密码必须使用哈希存储，禁止明文存储。

```python
# ✅ 正确：使用密码哈希
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(user_data):
    user = User(
        phone_number=user_data['phone_number'],
        password_hash=generate_password_hash(user_data['password'])
    )
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(phone_number, password):
    user = db.session.query(User).filter(
        User.phone_number == phone_number
    ).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        raise ValueError('用户名或密码错误')
    
    return user

# ❌ 错误：明文存储密码
def create_user(user_data):
    user = User(
        phone_number=user_data['phone_number'],
        password=user_data['password']  # 禁止明文存储！
    )
    db.session.add(user)
    db.session.commit()
    return user
```

### 10.2 SQL 注入防护

**原则**: 使用 ORM 参数化查询，禁止字符串拼接 SQL。

```python
# ✅ 正确：使用 ORM 参数化查询
user = db.session.query(User).filter(
    User.phone_number == phone_number  # 自动参数化
).first()

# ❌ 错误：字符串拼接 SQL
query = f"SELECT * FROM users WHERE phone_number = '{phone_number}'"  # SQL 注入风险！
user = db.session.execute(query).first()
```

### 10.3 敏感信息处理

**原则**: 日志中禁止记录敏感信息（密码、token 等）。

```python
# ✅ 正确：不记录敏感信息
def login(phone_number, password):
    logger.info(f"用户登录请求: {phone_number}")  # 不记录密码
    user = authenticate_user(phone_number, password)
    logger.info(f"用户 {user.user_id} 登录成功")
    return user

# ❌ 错误：记录敏感信息
def login(phone_number, password):
    logger.info(f"用户登录请求: {phone_number}, 密码: {password}")  # 禁止记录密码！
    user = authenticate_user(phone_number, password)
    return user
```

## 11. 性能优化规范

### 11.1 查询优化

**原则**: 避免在循环中执行查询，使用批量查询。

```python
# ✅ 正确：批量查询
user_ids = [1, 2, 3, 4, 5]
users = db.session.query(User).filter(
    User.user_id.in_(user_ids)
).all()

# ❌ 错误：循环查询
user_ids = [1, 2, 3, 4, 5]
users = []
for user_id in user_ids:
    user = db.session.get(User, user_id)  # N 次查询
    users.append(user)
```

### 11.2 分页查询

**原则**: 大数据量查询必须使用分页。

```python
# ✅ 正确：使用分页
def get_users(page=1, per_page=20):
    query = db.session.query(User)
    pagination = query.paginate(page=page, per_page=per_page)
    
    return {
        'users': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }

# ❌ 错误：一次性加载所有数据
def get_users():
    users = db.session.query(User).all()  # 可能加载大量数据
    return [user.to_dict() for user in users]
```

## 12. 代码审查清单

在提交代码前，请检查以下项目：

- [ ] 所有数据库操作使用 `db.session`
- [ ] 使用 SQLAlchemy 2.0 API
- [ ] 所有写操作使用事务
- [ ] 删除操作使用软删除
- [ ] 业务逻辑放在 Service 层
- [ ] 使用统一响应格式
- [ ] 遵循命名规范
- [ ] 公共函数包含文档字符串
- [ ] 异常处理完整且记录日志
- [ ] 测试使用不同的测试数据
- [ ] 日志不包含敏感信息
- [ ] 查询优化（避免 N+1 查询）
- [ ] 大数据量查询使用分页

## 13. 工具和命令

### 13.1 代码格式化

```bash
# 使用 autopep8 格式化代码
autopep8 --in-place --aggressive --aggressive src/

# 使用 black 格式化代码
black src/
```

### 13.2 代码检查

```bash
# 使用 pylint 检查代码
pylint src/

# 使用 flake8 检查代码
flake8 src/
```

### 13.3 测试

```bash
# 运行所有测试
make test-all

# 运行单元测试
make ut

# 运行集成测试
make it

# 运行 E2E 测试
make e2e
```

## 14. 参考资源

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Flask-SQLAlchemy 文档](https://flask-sqlalchemy.palletsprojects.com/)
- [Python PEP 8 代码风格指南](https://peps.python.org/pep-0008/)
- [Python PEP 257 文档字符串约定](https://peps.python.org/pep-0257/)

---

**最后更新**: 2025-12-28
**版本**: 1.0
**维护者**: SafeGuard 开发团队