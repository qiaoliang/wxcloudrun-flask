# 测试隔离设计方案

## 概述

设计一个测试隔离机制，确保每个测试类使用完全独立的数据库实例，避免测试数据互相污染。

## 需求分析

- **隔离级别**: 每个测试类重建数据库（类级别隔离）
- **数据初始化**: 完全空数据库，只有schema
- **数据管理**: 每个测试类完全自主管理其需要的测试数据

## 核心设计

### 1. 数据库隔离策略

使用SQLite内存数据库，为每个测试类创建独立的数据库实例：

```python
@pytest.fixture(scope="class")
def isolated_db():
    """为每个测试类提供独立的数据库实例"""
    # 创建唯一的数据库标识
    db_id = f"test_db_{id(uuid.uuid4())}"
    
    # 创建独立的内存数据库
    app = original_app
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///:memory:'
    app.config['SQLALCHEMY_BINDS'] = {db_id: f'sqlite:///:memory:'}
    
    with app.app_context():
        # 只创建表结构，不插入数据
        db.create_all()
        yield
        
        # 清理：删除所有表
        db.drop_all()
```

### 2. 测试类基类

创建一个基类，提供便捷的数据创建方法：

```python
class IsolatedBaseTest:
    """测试隔离基类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        # 确保使用隔离的数据库
        pass
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理可能残留的数据
        self.cleanup_all_data()
    
    def cleanup_all_data(self):
        """清理所有测试数据"""
        # 按依赖关系删除数据
        from wxcloudrun.model import RuleSupervision, CheckinRecord, CheckinRule, User, Counters
        RuleSupervision.query.delete()
        CheckinRecord.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        Counters.query.delete()
        db.session.commit()
```

### 3. 测试数据工厂

提供便捷的测试数据创建方法：

```python
class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_user(**kwargs):
        """创建测试用户"""
        defaults = {
            'phone_number': '13800000001',
            'nickname': '测试用户',
            'is_solo_user': True,
            'is_supervisor': False,
            'status': 1,
            'auth_type': 'phone'
        }
        defaults.update(kwargs)
        return User(**defaults)
    
    @staticmethod
    def create_checkin_rule(**kwargs):
        """创建打卡规则"""
        from datetime import time
        defaults = {
            'rule_name': '测试打卡',
            'icon_url': '🌅',
            'frequency_type': 0,
            'time_slot_type': 4,
            'custom_time': time(8, 0, 0),
            'week_days': 127,
            'status': 1
        }
        defaults.update(kwargs)
        return CheckinRule(**defaults)
```

## 实现细节

### 1. 修改 conftest.py

添加新的隔离数据库fixture：

```python
@pytest.fixture(scope="class")
def isolated_database():
    """为每个测试类提供完全隔离的数据库"""
    import uuid
    from wxcloudrun import db
    
    # 生成唯一的数据库标识
    db_identifier = f"test_{uuid.uuid4().hex[:8]}"
    
    # 配置应用使用内存数据库
    app = original_app
    original_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    
    try:
        # 设置内存数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            # 只创建表结构
            db.create_all()
            yield app
            
            # 清理：删除所有数据
            db.drop_all()
            
    finally:
        # 恢复原始配置
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
```

### 2. 更新测试基类

```python
# tests/base_test.py
import pytest
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision, Counters


@pytest.mark.usefixtures("isolated_database")
class BaseTest:
    """测试基类，提供数据库隔离"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        pass
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 确保数据库是空的
        self.ensure_clean_database()
    
    def ensure_clean_database(self):
        """确保数据库是空的"""
        # 删除所有可能残留的数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        User.query.delete()
        Counters.query.delete()
        db.session.commit()
    
    # 便捷的数据创建方法
    def create_user(self, **kwargs):
        """创建测试用户"""
        user = User(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user
    
    def create_checkin_rule(self, solo_user_id, **kwargs):
        """创建打卡规则"""
        from datetime import time
        defaults = {
            'solo_user_id': solo_user_id,
            'rule_name': '测试打卡',
            'icon_url': '🌅',
            'frequency_type': 0,
            'time_slot_type': 4,
            'custom_time': time(8, 0, 0),
            'week_days': 127,
            'status': 1
        }
        defaults.update(kwargs)
        rule = CheckinRule(**defaults)
        db.session.add(rule)
        db.session.commit()
        return rule
    
    def create_supervision(self, rule_id, solo_user_id, supervisor_user_id, **kwargs):
        """创建监护关系"""
        defaults = {
            'rule_id': rule_id,
            'solo_user_id': solo_user_id,
            'supervisor_user_id': supervisor_user_id,
            'status': 0,
            'invitation_message': '请监督我'
        }
        defaults.update(kwargs)
        supervision = RuleSupervision(**defaults)
        db.session.add(supervision)
        db.session.commit()
        return supervision
```

### 3. 测试类示例

```python
class TestUserManagement(BaseTest):
    """用户管理测试 - 每个测试类使用独立的数据库"""
    
    def test_create_user(self):
        """测试创建用户"""
        # 数据库是空的，可以安全创建数据
        user = self.create_user(
            phone_number='13800000001',
            nickname='测试用户1'
        )
        
        assert user.user_id is not None
        assert User.query.count() == 1
    
    def test_update_user(self):
        """测试更新用户"""
        # 每个测试方法开始时数据库都是空的
        user = self.create_user(
            phone_number='13800000002',
            nickname='测试用户2'
        )
        
        user.nickname = '更新后的昵称'
        db.session.commit()
        
        updated_user = User.query.get(user.user_id)
        assert updated_user.nickname == '更新后的昵称'

class TestCheckinRules(BaseTest):
    """打卡规则测试 - 独立的数据库实例"""
    
    def test_create_rule(self):
        """测试创建打卡规则"""
        # 这个测试类有完全独立的数据库
        user = self.create_user(
            phone_number='13800000003',
            nickname='用户3'
        )
        
        rule = self.create_checkin_rule(
            solo_user_id=user.user_id,
            rule_name='起床打卡'
        )
        
        assert rule.rule_id is not None
        assert CheckinRule.query.count() == 1
```

## 迁移指南

### 1. 更新现有测试

1. 让所有测试类继承 `BaseTest`
2. 移除对 `setup_test_data` fixture 的依赖
3. 在每个测试方法中创建所需的数据

### 2. 示例迁移

**迁移前：**
```python
def test_user_creation(client, setup_test_data):
    users, _, _ = setup_test_data
    user = users[0]
    # 测试逻辑
```

**迁移后：**
```python
class TestUserCreation(BaseTest):
    def test_user_creation(self):
        # 创建测试数据
        user = self.create_user(
            phone_number='13800000001',
            nickname='测试用户'
        )
        # 测试逻辑
```

## 优势

1. **完全隔离**: 每个测试类使用独立的数据库实例
2. **清晰的数据管理**: 测试类明确负责自己的数据
3. **性能平衡**: 避免了每个测试方法重建的开销
4. **易于维护**: 基类提供了便捷的数据创建方法
5. **向后兼容**: 现有测试可以逐步迁移

## 注意事项

1. 确保所有测试类都继承自 `BaseTest`
2. 测试方法之间不要共享数据
3. 使用便捷方法创建测试数据，而不是直接操作数据库
4. 复杂的测试数据可以在 `setup_method` 中创建