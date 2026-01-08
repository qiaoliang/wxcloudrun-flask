# 用户批量转移API文档

## 概述

本文档描述用户批量转移API，允许社区主管批量转移普通用户到其他社区。

## 接口信息

- **接口路径**: `/api/community/transfer-users`
- **请求方法**: POST
- **需要认证**: 是
- **权限要求**: 社区主管（role=3）或超级管理员（role=4）

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| source_community_id | number | 是 | 源社区ID |
| target_community_id | number | 是 | 目标社区ID |
| user_ids | number[] | 是 | 用户ID列表（最多10个） |

### 请求示例

```json
{
  "source_community_id": 1,
  "target_community_id": 2,
  "user_ids": [101, 102, 103]
}
```

## 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | number | 状态码（0-成功，1-失败） |
| message | string | 状态消息 |
| data | object | 响应数据 |

### data参数说明

| 参数名 | 类型 | 说明 |
|--------|------|------|
| success_count | number | 成功转移数量 |
| skipped_count | number | 静默跳过数量 |
| failed | array | 失败列表 |
| failed[].user_id | number | 失败的用户ID |
| failed[].reason | string | 失败原因 |
| transferred_users | array | 成功用户信息列表 |
| transferred_users[].user_id | number | 用户ID |
| transferred_users[].nickname | string | 用户昵称 |
| transferred_users[].phone_number | string | 用户手机号 |
| events_transferred | number | 转移的事件数 |
| rules_updated | number | 规则更新数 |

### 响应示例

**成功响应**:
```json
{
  "code": 0,
  "message": "转移成功",
  "data": {
    "success_count": 2,
    "skipped_count": 1,
    "failed": [],
    "transferred_users": [
      {
        "user_id": 101,
        "nickname": "张三",
        "phone_number": "138****1234"
      },
      {
        "user_id": 102,
        "nickname": "李四",
        "phone_number": "139****5678"
      }
    ],
    "events_transferred": 3,
    "rules_updated": 4
  }
}
```

**失败响应**:
```json
{
  "code": 1,
  "message": "权限不足：您不是源社区的主管",
  "data": null
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 1 | 权限不足 |
| 1 | 参数错误 |
| 1 | 用户数量超过限制 |
| 1 | 源社区和目标社区相同 |
| 1 | 社区不存在 |
| 1 | 用户不存在 |
| 1 | 只能转移普通用户 |

## 业务规则

1. **权限验证**
   - 操作者必须是源社区的主管
   - 操作者必须是目标社区的主管
   - 超级管理员可以跳过上述检查

2. **用户限制**
   - 只能转移普通用户（role=1）
   - 不能转移工作人员（role=2,3）
   - 一次最多转移10个用户

3. **社区限制**
   - 目标社区必须与源社区不同
   - 目标社区必须存在

4. **数据更新**
   - 更新用户的社区归属
   - 更新用户的加入时间
   - 停用源社区的所有打卡规则
   - 激活目标社区的所有打卡规则
   - 转移未完成的事件（status=1）
   - 保留已完成或已取消的事件（status=2,3）

5. **错误处理**
   - 用户已离开源社区：静默跳过
   - 用户不存在：记录失败，继续处理
   - 用户不是普通用户：记录失败，继续处理
   - 权限不足：立即终止并回滚
   - 参数错误：立即终止并回滚

## 使用示例

### cURL示例

```bash
curl -X POST http://localhost:9999/api/community/transfer-users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "source_community_id": 1,
    "target_community_id": 2,
    "user_ids": [101, 102, 103]
  }'
```

### JavaScript示例

```javascript
import { transferUsersBatch } from '@/api/community'

const result = await transferUsersBatch(1, 2, [101, 102, 103])

if (result.code === 0) {
  console.log('转移成功:', result.data)
  console.log('成功转移:', result.data.success_count, '个用户')
  console.log('转移事件:', result.data.events_transferred, '个')
} else {
  console.error('转移失败:', result.message)
}
```

## 注意事项

1. 所有操作在一个数据库事务中完成，确保数据一致性
2. 转移操作会记录审计日志
3. 转移是静默的，不会通知被转移用户
4. 已完成的事件保留在源社区，不会转移
5. 建议在低峰期执行大批量转移操作

## 相关文档

- [后端架构指南](../AGENTS.md)
- [代码风格指南](../docs/code-style-guide.md)
- [集成测试指南](../docs/integration-test-writing-guide.md)
- [用户批量转移功能设计文档](../../docs/plans/2026-01-08-user-batch-transfer-design.md)