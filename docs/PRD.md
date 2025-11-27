# 安全守护后端产品需求文档

## 1. 后端产品概述

### 1.1 后端服务定位

安全守护后端是基于 Flask 框架开发的 RESTful API 服务，为微信小程序前端提供完整的数据支持和业务逻辑处理。后端服务负责用户认证、数据存储、业务逻辑实现和与微信小程序生态的集成。

### 1.2 技术架构

*   **框架**: Flask 2.0.2
*   **数据库**: MySQL (使用 SQLAlchemy ORM)
*   **数据库连接**: PyMySQL 1.0.2
*   **身份验证**: JWT (PyJWT 2.4.0)
*   **微信小程序集成**: 微信小程序 code2Session API
*   **部署**: Docker 容器化部署

### 1.3 后端服务职责

*   提供用户认证和授权服务
*   管理用户数据和角色权限
*   处理打卡业务逻辑
*   管理监护关系和通知系统
*   提供社区数据看板支持
*   确保数据安全和系统稳定性

## 2. 后端功能规格

### 2.1 用户管理模块 (B-USER_001)

#### 2.1.1 用户认证

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/login | 微信小程序登录认证 | POST | P0 |
| /api/update_user_info | 更新用户基本信息 | POST | P0 |
| /api/validate_token | Token验证中间件 | - | P0 |

**接口详情**:

**POST /api/login**
- **功能**: 通过微信小程序 code 获取用户信息并返回 JWT token
- **请求参数**:
  ```json
  {
    "code": "微信小程序登录凭证"
  }
  ```
- **响应示例**:
  ```json
  {
    "code": 0,
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "openid": "用户微信openid",
      "session_key": "微信会话密钥"
    }
  }
  ```

**POST /api/update_user_info**
- **功能**: 更新用户头像和昵称信息
- **请求参数**:
  ```json
  {
    "token": "JWT令牌",
    "avatar_url": "用户头像URL",
    "nickname": "用户昵称"
  }
  ```

#### 2.1.2 用户角色管理

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/user/role | 设置用户角色 | POST | P0 |
| /api/user/profile | 获取用户完整信息 | GET | P0 |
| /api/community/verify | 社区工作人员身份验证 | POST | P1 |

### 2.2 打卡管理模块 (B-CHECKIN_001)

#### 2.2.1 打卡记录管理

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/checkin | 提交打卡记录 | POST | P0 |
| /api/checkin/list | 获取用户今日打卡列表 | GET | P0 |
| /api/checkin/history | 获取历史打卡记录 | GET | P0 |
| /api/checkin/revoke | 撤销打卡记录 | POST | P1 |
| /api/checkin/sync | 离线打卡数据同步 | POST | P0 |

#### 2.2.2 打卡规则管理

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/rules | 获取用户打卡规则 | GET | P0 |
| /api/rules/create | 创建打卡规则 | POST | P0 |
| /api/rules/update | 更新打卡规则 | PUT | P0 |
| /api/rules/delete | 删除打卡规则 | DELETE | P0 |
| /api/rules/default | 获取默认打卡规则 | GET | P1 |

### 2.3 监护关系管理模块 (B-SUPERVISOR_001)

#### 2.3.1 监护关系操作

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/supervisor/invite | 邀请监护人 | POST | P0 |
| /api/supervisor/apply | 申请成为监护人 | POST | P1 |
| /api/supervisor/accept | 同意监护人申请 | POST | P0 |
| /api/supervisor/reject | 拒绝监护人申请 | POST | P0 |
| /api/supervisor/list | 获取监护人列表 | GET | P0 |
| /api/supervisor/remove | 移除监护人关系 | DELETE | P0 |

#### 2.3.2 监护人功能

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/supervisor/dashboard | 监护人首页数据 | GET | P0 |
| /api/supervisor/detail | 获取被监护人详情 | GET | P0 |
| /api/supervisor/records | 获取被监护人打卡记录 | GET | P0 |
| /api/supervisor/settings | 监护人通知设置 | POST | P0 |

### 2.4 社区管理模块 (B-COMMUNITY_001)

#### 2.4.1 数据看板

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/community/dashboard | 社区数据看板 | GET | P0 |
| /api/community/unchecked | 获取未打卡独居者列表 | GET | P0 |
| /api/community/notify | 批量发送提醒 | POST | P0 |
| /api/community/mark_contacted | 标记已联系状态 | POST | P1 |

### 2.5 通知系统模块 (B-NOTIFICATION_001)

| API接口 | 功能描述 | 请求方法 | 优先级 |
|---------|---------|---------|--------|
| /api/notifications | 获取用户通知列表 | GET | P0 |
| /api/notifications/read | 标记通知已读 | POST | P0 |
| /api/notifications/send | 发送系统通知 | POST | P0 |
| /api/notifications/settings | 通知设置管理 | POST | P0 |

## 3. 数据库设计

### 3.1 数据库结构概述

根据产品需求文档，后端数据库设计包含以下核心实体：
- 用户系统（用户表、社区表）
- 监护关系系统（监督关系表）
- 打卡系统（打卡规则表、打卡记录表）
- 通知系统（通知表）

### 3.2 核心数据表

#### 3.2.1 用户表 (users)

存储系统中所有用户的基本信息和角色权限。

```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    wechat_openid VARCHAR(128) UNIQUE NOT NULL COMMENT '微信OpenID，唯一标识用户',
    phone_number VARCHAR(20) UNIQUE COMMENT '手机号码，可用于登录和联系',
    nickname VARCHAR(100) COMMENT '用户昵称',
    avatar_url VARCHAR(500) COMMENT '用户头像URL',
    role ENUM('solo', 'supervisor', 'community') NOT NULL COMMENT '用户角色：独居者/监护人/社区工作人员',
    community_id INT COMMENT '所属社区ID，仅社区工作人员需要',
    status ENUM('active', 'disabled') DEFAULT 'active' COMMENT '用户状态：正常/禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_openid (wechat_openid) COMMENT '微信OpenID索引，支持快速登录查询',
    INDEX idx_phone (phone_number) COMMENT '手机号索引，支持手机号登录',
    INDEX idx_role (role) COMMENT '角色索引，支持按角色查询',
    FOREIGN KEY (community_id) REFERENCES communities(community_id) ON DELETE SET NULL
);
```

#### 3.2.2 社区表 (communities)

存储社区工作人员所属的社区信息。

```sql
CREATE TABLE communities (
    community_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '社区ID',
    community_name VARCHAR(200) NOT NULL COMMENT '社区名称',
    address VARCHAR(500) COMMENT '社区地址',
    contact_person VARCHAR(100) COMMENT '社区联系人',
    contact_phone VARCHAR(20) COMMENT '社区联系电话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (community_name) COMMENT '社区名称索引，支持按名称查询'
);
```

#### 3.2.3 监督关系表 (supervision_relations)

管理独居者与监护人之间的监护关系。

```sql
CREATE TABLE supervision_relations (
    relation_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '关系ID',
    solo_user_id INT NOT NULL COMMENT '独居者用户ID',
    supervisor_user_id INT NOT NULL COMMENT '监护人用户ID',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '关系状态：待同意/已同意/已拒绝',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_solo (solo_user_id) COMMENT '独居者ID索引，支持查询独居者的所有监护人',
    INDEX idx_supervisor (supervisor_user_id) COMMENT '监护人ID索引，支持查询监护人监护的所有独居者',
    INDEX idx_status (status) COMMENT '状态索引，支持按状态筛选关系',
    FOREIGN KEY (solo_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

#### 3.2.4 打卡规则表 (checkin_rules)

存储独居者设置的打卡规则，支持自定义打卡事项。

```sql
CREATE TABLE checkin_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '规则ID',
    solo_user_id INT NOT NULL COMMENT '独居者用户ID',
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    icon_url VARCHAR(500) COMMENT '规则图标URL',
    frequency_type ENUM('daily', 'weekly', 'custom') DEFAULT 'daily' COMMENT '频率类型：每天/每周/自定义',
    frequency_details JSON COMMENT '频率详情，如具体的星期几',
    time_slot_type ENUM('period', 'exact') DEFAULT 'period' COMMENT '时间段类型：时段/精确时间',
    time_slot_details JSON COMMENT '时间段详情，如上午/下午/晚上或具体时间段',
    grace_period_minutes INT DEFAULT 30 COMMENT '宽限期（分钟），默认30分钟',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user (solo_user_id) COMMENT '用户ID索引，支持查询用户的所有打卡规则',
    INDEX idx_active (is_active) COMMENT '启用状态索引，支持筛选启用的规则',
    FOREIGN KEY (solo_user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

#### 3.2.5 打卡记录表 (checkin_records)

记录用户的打卡历史，包括已打卡、未打卡和已撤销状态。

```sql
CREATE TABLE checkin_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    solo_user_id INT NOT NULL COMMENT '独居者用户ID',
    rule_id INT NOT NULL COMMENT '打卡规则ID',
    checkin_time TIMESTAMP NULL COMMENT '实际打卡时间',
    status ENUM('checked', 'missed', 'revoked') DEFAULT 'missed' COMMENT '状态：已打卡/未打卡/已撤销',
    planned_time TIMESTAMP NOT NULL COMMENT '计划打卡时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_date (solo_user_id, planned_time) COMMENT '用户和日期复合索引，支持高效的日期范围查询',
    INDEX idx_rule (rule_id) COMMENT '规则ID索引，支持查询特定规则的打卡记录',
    INDEX idx_status (status) COMMENT '状态索引，支持按状态筛选',
    INDEX idx_planned_time (planned_time) COMMENT '计划时间索引，支持按时间查询',
    FOREIGN KEY (solo_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES checkin_rules(rule_id) ON DELETE CASCADE
);
```

#### 3.2.6 通知表 (notifications)

存储系统通知，包括未打卡提醒、规则更新、监护人申请等。

```sql
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '通知ID',
    user_id INT NOT NULL COMMENT '接收通知的用户ID',
    type ENUM('missed_checkin', 'rule_update', 'supervisor_request', 'system') NOT NULL COMMENT '通知类型',
    title VARCHAR(200) COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    related_id INT COMMENT '关联记录ID，如打卡记录ID、规则ID、监督关系ID',
    related_type VARCHAR(50) COMMENT '关联记录类型',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_unread (user_id, is_read) COMMENT '用户和已读状态复合索引，支持未读通知快速查询',
    INDEX idx_type (type) COMMENT '通知类型索引，支持按类型筛选',
    INDEX idx_created (created_at) COMMENT '创建时间索引，支持按时间排序',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

### 3.3 数据库关系图

```
users (用户表)
├── 1:N → communities (社区表) [community_id]
├── 1:N → supervision_relations (监督关系表) [solo_user_id]
├── 1:N → supervision_relations (监督关系表) [supervisor_user_id]
├── 1:N → checkin_rules (打卡规则表) [solo_user_id]
├── 1:N → checkin_records (打卡记录表) [solo_user_id]
└── 1:N → notifications (通知表) [user_id]

checkin_rules (打卡规则表)
└── 1:N → checkin_records (打卡记录表) [rule_id]

supervision_relations (监督关系表)
└── 1:N → notifications (通知表) [related_id, related_type='supervision']

checkin_records (打卡记录表)
└── 1:N → notifications (通知表) [related_id, related_type='checkin']
```

### 3.4 数据库索引策略

#### 3.4.1 主要索引设计

*   **用户表 (users)**:
    - `wechat_openid`: 唯一索引，支持微信登录快速查询
    - `phone_number`: 唯一索引，支持手机号登录
    - `role`: 普通索引，支持按角色筛选用户

*   **打卡记录表 (checkin_records)**:
    - `(solo_user_id, planned_time)`: 复合索引，支持用户历史记录高效查询
    - `rule_id`: 普通索引，支持特定规则的打卡记录查询
    - `planned_time`: 普通索引，支持按时间范围查询
    - `status`: 普通索引，支持按状态筛选

*   **监督关系表 (supervision_relations)**:
    - `solo_user_id`: 普通索引，支持查询独居者的所有监护人
    - `supervisor_user_id`: 普通索引，支持查询监护人监护的所有独居者
    - `status`: 普通索引，支持按状态筛选关系

*   **通知表 (notifications)**:
    - `(user_id, is_read)`: 复合索引，支持未读通知快速查询
    - `type`: 普通索引，支持按通知类型筛选
    - `created_at`: 普通索引，支持按时间排序

#### 3.4.2 查询优化策略

1. **分页查询**: 所有列表查询都使用LIMIT和OFFSET进行分页
2. **条件过滤**: 优先使用索引字段作为WHERE条件
3. **排序优化**: 使用索引字段进行ORDER BY排序
4. **JOIN优化**: 确保JOIN字段有适当的索引

### 3.5 数据完整性约束

#### 3.5.1 外键约束

*   用户表与社区表的外键关系，确保社区工作人员属于有效社区
*   监督关系表与用户表的外键关系，确保监护关系中的用户存在
*   打卡规则表与用户表的外键关系，确保规则属于有效用户
*   打卡记录表与用户表和规则表的外键关系，确保记录的完整性
*   通知表与用户表的外键关系，确保通知接收者存在

#### 3.5.2 业务约束

*   用户角色必须为预定义的三种角色之一
*   监护关系状态必须为预定义的三种状态之一
*   打卡记录状态必须为预定义的三种状态之一
* 通知类型必须为预定义的四种类型之一

### 3.6 数据初始化

#### 3.6.1 默认打卡规则

系统需要为独居者提供默认的打卡规则选项：

```sql
-- 可以通过配置表或代码初始化默认规则
INSERT INTO checkin_rules (solo_user_id, rule_name, icon_url, frequency_type, time_slot_type) 
VALUES 
    (1, '起床', 'icons/get_up.png', 'daily', 'period'),
    (1, '早餐', 'icons/breakfast.png', 'daily', 'period'),
    (1, '午餐', 'icons/lunch.png', 'daily', 'period'),
    (1, '晚餐', 'icons/dinner.png', 'daily', 'period'),
    (1, '服药', 'icons/medicine.png', 'daily', 'exact'),
    (1, '睡觉', 'icons/sleep.png', 'daily', 'period');
```

#### 3.6.2 系统配置

可以添加系统配置表存储全局配置：

```sql
CREATE TABLE system_configs (
    config_id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('default_grace_period', '30', '默认宽限期（分钟）'),
('daily_reminder_time', '18:00', '每日提醒时间'),
('max_supervisors_per_solo', '10', '每个独居者最大监护人数量');
```

## 4. 后端架构设计

### 4.1 分层架构

```
┌─────────────────────────────────────┐
│             API层                   │
│  (views.py - 路由和请求处理)        │
├─────────────────────────────────────┤
│           业务逻辑层                 │
│  (services/ - 业务服务模块)         │
├─────────────────────────────────────┤
│           数据访问层                 │
│  (dao.py - 数据库访问对象)          │
├─────────────────────────────────────┤
│           数据模型层                 │
│  (model.py - SQLAlchemy模型)        │
├─────────────────────────────────────┤
│           数据库层                   │
│  (MySQL数据库)                      │
└─────────────────────────────────────┘
```

### 4.2 模块组织

```
wxcloudrun/
├── __init__.py              # Flask应用初始化
├── views.py                 # API路由定义
├── dao.py                   # 数据访问对象
├── model.py                 # 数据模型定义
├── response.py              # 响应格式化
├── services/                # 业务服务层
│   ├── __init__.py
│   ├── auth_service.py      # 认证服务
│   ├── user_service.py      # 用户管理服务
│   ├── checkin_service.py   # 打卡业务服务
│   ├── supervisor_service.py # 监护关系服务
│   ├── community_service.py # 社区管理服务
│   └── notification_service.py # 通知服务
├── middleware/              # 中间件
│   ├── __init__.py
│   ├── auth_middleware.py   # 认证中间件
│   └── error_handler.py     # 错误处理中间件
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── jwt_utils.py         # JWT工具
│   ├── wechat_utils.py      # 微信API工具
│   └── notification_utils.py # 通知工具
└── templates/               # 模板文件
    └── index.html
```

### 4.3 关键服务设计

#### 4.3.1 认证服务 (auth_service.py)

```python
class AuthService:
    def login(self, code):
        """微信小程序登录"""
        # 1. 调用微信API获取openid
        # 2. 查询或创建用户记录
        # 3. 生成JWT token
        # 4. 返回用户信息和token
    
    def validate_token(self, token):
        """验证JWT token"""
        # 1. 解码token
        # 2. 验证token有效性
        # 3. 返回用户信息
```

#### 4.3.2 打卡服务 (checkin_service.py)

```python
class CheckinService:
    def checkin(self, user_id, rule_id):
        """提交打卡"""
        # 1. 验证打卡权限和时间
        # 2. 创建打卡记录
        # 3. 更新相关统计
        # 4. 触发通知
    
    def get_today_checkins(self, user_id):
        """获取今日打卡列表"""
        # 1. 查询用户今日打卡规则
        # 2. 查询已打卡记录
        # 3. 返回打卡状态列表
```

## 5. 安全设计

### 5.1 身份认证与授权

*   **JWT Token认证**: 所有需要认证的接口使用JWT token进行身份验证
*   **Token有效期**: Token有效期为7天，支持自动刷新机制
*   **权限控制**: 基于用户角色的访问控制，确保不同角色只能访问相应功能

### 5.2 数据安全

*   **敏感数据加密**: 用户手机号等敏感信息在数据库中加密存储
*   **HTTPS传输**: 所有API通信必须使用HTTPS协议
*   **SQL注入防护**: 使用参数化查询和ORM，防止SQL注入攻击
*   **输入验证**: 对所有用户输入进行严格验证和过滤

### 5.3 API安全

*   **请求频率限制**: 对关键接口实施请求频率限制，防止恶意调用
*   **CORS配置**: 严格的跨域资源共享配置，只允许信任的域名访问
*   **错误信息脱敏**: 生产环境中不暴露详细的错误信息和堆栈跟踪

## 6. 性能优化

### 6.1 数据库优化

*   **连接池配置**: 使用数据库连接池管理数据库连接
*   **查询优化**: 合理使用索引，避免全表扫描
*   **分页查询**: 大数据量查询使用分页机制
*   **缓存策略**: 对热点数据使用Redis缓存

### 6.2 API性能

*   **异步处理**: 耗时操作使用异步处理，不阻塞主线程
*   **数据压缩**: 对大数据响应启用压缩传输
*   **CDN加速**: 静态资源使用CDN分发

## 7. 监控与日志

### 7.1 日志管理

*   **分级日志**: 使用DEBUG、INFO、WARNING、ERROR四级日志
*   **结构化日志**: 使用JSON格式记录日志，便于分析
*   **日志轮转**: 实施日志文件轮转策略，防止日志文件过大
*   **敏感信息过滤**: 日志中不记录密码等敏感信息

### 7.2 监控指标

*   **API响应时间**: 监控各接口的平均响应时间和P95响应时间
*   **错误率**: 监控API错误率和异常类型分布
*   **数据库性能**: 监控数据库连接数、查询执行时间等
*   **系统资源**: 监控CPU、内存、磁盘使用率

## 8. 部署与运维

### 8.1 容器化部署

*   **Docker镜像**: 基于Alpine Linux构建轻量级Docker镜像
*   **多阶段构建**: 使用多阶段构建减少镜像体积
*   **健康检查**: 配置容器健康检查机制
*   **优雅关闭**: 实现应用的优雅关闭机制

### 8.2 环境配置

*   **环境变量**: 使用环境变量管理不同环境的配置
*   **配置管理**: 实施配置版本管理和变更控制
*   **密钥管理**: 安全管理数据库密码、JWT密钥等敏感信息

### 8.3 扩展性设计

*   **水平扩展**: 支持多实例部署，通过负载均衡分发请求
*   **数据库扩展**: 支持读写分离和分库分表
*   **微服务演进**: 为未来微服务化改造预留接口

## 9. 开发规范

### 9.1 代码规范

*   **PEP8规范**: 遵循Python PEP8代码风格指南
*   **类型注解**: 使用类型注解提高代码可读性
*   **文档字符串**: 为所有函数和类编写详细的文档字符串
*   **单元测试**: 关键业务逻辑必须有对应的单元测试

### 9.2 API设计规范

*   **RESTful风格**: 遵循RESTful API设计原则
*   **统一响应格式**: 所有API使用统一的响应格式
*   **版本控制**: API版本通过URL路径进行管理
*   **错误处理**: 统一的错误码和错误信息处理

### 9.3 数据库规范

*   **命名规范**: 表名使用小写字母和下划线，字段名使用小写字母和下划线
*   **主键设计**: 统一使用自增整数主键
*   **时间戳**: 所有表包含created_at和updated_at字段
*   **外键约束**: 使用外键约束保证数据完整性

## 10. 测试策略

### 10.1 测试类型

*   **单元测试**: 对业务逻辑和工具函数进行单元测试
*   **集成测试**: 测试各模块间的接口和交互
*   **API测试**: 对所有API接口进行功能和性能测试
*   **端到端测试**: 模拟完整业务流程进行测试

### 10.2 测试环境

*   **开发环境**: 开发人员本地测试环境
*   **测试环境**: 自动化测试和QA测试环境
*   **预生产环境**: 生产前最后验证环境
*   **生产环境**: 正式运行环境

