# 删除CommunityMember表设计文档

## 概述
本设计旨在删除冗余的CommunityMember表，将社区成员关系信息整合到User表中。每个用户只属于一个社区，通过User表的`community_id`和新增的`community_joined_at`字段记录用户当前社区及加入时间。

## 设计决策
**选择方案一**：在User表中添加`community_joined_at`字段
- 简单直接，符合业务模型
- 无需复杂的数据迁移
- 可以满足"需要历史时间"的基本需求

## 数据库变更

### 1. 添加新字段到users表
```sql
ALTER TABLE users ADD COLUMN community_joined_at DATETIME;
```

### 2. 设置现有数据的默认值
```sql
-- 对于已有社区的用户，使用created_at作为加入时间
UPDATE users SET community_joined_at = created_at WHERE community_id IS NOT NULL;

-- 对于没有社区的用户，设置为NULL
UPDATE users SET community_joined_at = NULL WHERE community_id IS NULL;
```

### 3. 删除community_members表（最后执行）
```sql
DROP TABLE community_members;
```

## 代码变更清单

### 核心模型文件
1. **`src/database/models.py`**
   - 在User类中添加`community_joined_at`字段
   - 从导出列表中移除CommunityMember

### 服务层文件
2. **`src/wxcloudrun/user_service.py`**
   - 用户注册时设置`community_joined_at = datetime.now()`
   - 更新用户信息时处理社区变更

3. **`src/wxcloudrun/community_service.py`**
   - 所有使用CommunityMember的查询改为使用User表
   - 添加用户到社区时设置`community_joined_at`
   - 从社区移除用户时清空`community_id`和`community_joined_at`
   - 用户更换社区时更新`community_joined_at`

4. **`src/wxcloudrun/community_staff_service.py`**
   - 确保工作人员逻辑不受影响

### API层文件
5. **`src/wxcloudrun/views/community.py`**
   - `/api/community/members/list`：改为查询User表
   - `/api/community/members/add`：改为更新User表
   - `/api/community/members/remove`：改为更新User表
   - 所有社区成员相关的API响应更新

6. **`src/wxcloudrun/views/user.py`**
   - 用户信息响应包含`community_joined_at`字段
   - 更新用户社区时更新`community_joined_at`

### 其他文件
7. **`src/wxcloudrun/__init__.py`**
   - 从导入列表中移除CommunityMember

8. **`AGENTS.md`**
   - 更新文档，移除CommunityMember相关描述

## API变更

### 用户信息响应格式
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "user_id": 1,
    "nickname": "张三",
    "community_id": 1,
    "community_joined_at": "2025-12-18T10:30:00",
    // ... 其他字段
  }
}
```

### 社区成员列表响应格式
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "members": [
      {
        "user_id": 1,
        "nickname": "张三",
        "avatar_url": "...",
        "joined_at": "2025-12-18T10:30:00",
        // ... 其他字段
      }
    ],
    "total": 10
  }
}
```

## 实施步骤

### 第一阶段：准备
1. 创建设计文档（本文件）
2. 备份数据库

### 第二阶段：代码修改
1. 修改数据库模型，添加`community_joined_at`字段
2. 更新用户注册逻辑
3. 更新社区服务层代码
4. 更新API层代码
5. 更新测试代码

### 第三阶段：测试验证
1. 运行单元测试
2. 运行集成测试
3. 运行端到端测试
4. 手动测试关键用户旅程

### 第四阶段：部署
1. 执行数据库变更
2. 部署代码更新
3. 监控系统运行

## 风险与缓解措施

### 风险1：数据不一致
- **缓解**：先添加字段并更新代码，验证无误后再删除旧表
- **回滚方案**：如果出现问题，可以回退到使用CommunityMember表

### 风险2：API兼容性
- **缓解**：确保API响应格式向后兼容
- **测试**：充分测试所有API端点

### 风险3：性能影响
- **缓解**：社区成员查询改为基于User表的查询，性能应该更好
- **监控**：部署后监控查询性能

## 测试策略

### 单元测试
- 测试用户注册时的`community_joined_at`设置
- 测试社区成员添加/移除逻辑
- 测试社区成员查询逻辑

### 集成测试
- 测试完整的用户旅程：注册→加入社区→更换社区
- 测试社区工作人员管理
- 测试社区合并/拆分功能

### 端到端测试
- 测试前端与后端的完整交互
- 测试权限验证逻辑

## 成功标准
1. 所有现有功能正常工作
2. 社区成员管理功能正常
3. 用户社区变更历史正确记录
4. 所有测试通过
5. 系统性能不受影响

## 相关文档
- 数据库模型：`src/database/models.py`
- 社区服务：`src/wxcloudrun/community_service.py`
- 社区API：`src/wxcloudrun/views/community.py`
- 用户服务：`src/wxcloudrun/user_service.py`

---
*文档创建时间：2025-12-18*
*设计确认：✓*