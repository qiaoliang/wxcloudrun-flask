# 社区管理 API 文档

> **重要约定**: 
> - HTTP 状态码统一返回 200 (除非服务器内部错误返回 500 或路由不存在返回 404)
> - 业务状态通过响应体中的 `code` 字段判断: `code=1` 表示成功, `code=0` 表示失败
> - 失败时 `msg` 字段包含具体错误信息, `data` 可为空对象 `{}` 或包含必要的提示数据

---

## 1. 社区 CRUD 相关接口

### 1.1 获取社区列表

**状态**: ✅ 已实现

- **路径**: `GET /api/community/list`
- **认证**: Bearer Token (super_admin)
- **请求参数**:
  ```json
  {
    "page": 1,           // 可选, 页码, 默认1
    "page_size": 20,     // 可选, 每页数量, 默认20
    "status": "active"   // 可选, 筛选状态: active/inactive/all, 默认all
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "communities": [
        {
          "id": "uuid-string",
          "name": "阳光社区",
          "location": "北京市朝阳区XX街道",
          "location_lat": 39.9042,
          "location_lon": 116.4074,
          "status": "active",           // active: 启用, inactive: 停用
          "manager_id": "user-uuid",
          "manager_name": "张主管",
          "description": "社区描述信息",
          "created_at": "2025-12-10T10:00:00Z",
          "updated_at": "2025-12-10T10:00:00Z"
        }
      ],
      "total": 50,
      "has_more": true,
      "current_page": 1
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "权限不足，需要超级管理员权限",
    "data": {}
  }
  ```

- **示例代码**:
  ```python
  import requests
  
  url = "http://localhost:9999/api/community/list"
  headers = {"Authorization": "Bearer your_token"}
  params = {"page": 1, "page_size": 20}
  
  response = requests.get(url, params=params, headers=headers)
  print(response.json())
  ```

---

### 1.2 创建社区

**状态**: ✅ 已实现

- **路径**: `POST /api/community/create`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "name": "新社区名称",              // 必填, 2-50字符
    "location": "北京市朝阳区XX街道",   // 必填
    "location_lat": 39.9042,          // 可选, 纬度
    "location_lon": 116.4074,         // 可选, 经度
    "manager_id": "user-uuid",        // 可选, 社区主管ID
    "description": "社区描述"          // 可选, 最多200字符
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "社区创建成功",
    "data": {
      "community_id": "new-uuid",
      "name": "新社区名称",
      "location": "北京市朝阳区XX街道",
      "status": "active",
      "created_at": "2025-12-12T10:00:00Z"
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "社区名称已存在",
    "data": {}
  }
  ```

---

### 1.3 更新社区信息

**状态**: ✅ 已实现

- **路径**: `POST /api/community/update`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",     // 必填
    "name": "更新后的名称",             // 可选
    "location": "新地址",               // 可选
    "location_lat": 39.9042,           // 可选
    "location_lon": 116.4074,          // 可选
    "manager_id": "user-uuid",         // 可选
    "description": "更新描述"           // 可选
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "更新成功",
    "data": {
      "community_id": "uuid-string",
      "updated_at": "2025-12-12T10:00:00Z"
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "社区不存在",
    "data": {}
  }
  ```

---

### 1.4 切换社区状态

**状态**: ✅ 已实现

- **路径**: `POST /api/community/toggle-status`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",
    "status": "inactive"  // active 或 inactive
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "状态更新成功",
    "data": {
      "community_id": "uuid-string",
      "status": "inactive"
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "该社区有未处理的申请，无法停用",
    "data": {
      "pending_applications": 5
    }
  }
  ```

---

### 1.5 删除社区

**状态**: ✅ 已实现

- **路径**: `POST /api/community/delete`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string"
  }
  ```

- **前置条件**: 
  - 社区必须已停用 (status = inactive)
  - 社区内无用户

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "删除成功",
    "data": {}
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "请先停用社区",
    "data": {}
  }
  ```
  或
  ```json
  {
    "code": 0,
    "msg": "社区内还有用户，无法删除",
    "data": {
      "user_count": 10
    }
  }
  ```

---

### 1.6 合并社区

**状态**: ✅ 已实现

- **路径**: `POST /api/community/merge`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "source_community_ids": ["uuid-1", "uuid-2"],  // 至少2个
    "target_community_id": "target-uuid"
  }
  ```

- **业务逻辑**:
  - 将源社区的所有用户和工作人员转移到目标社区
  - 源社区状态设为 inactive
  - 记录合并历史

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "合并成功",
    "data": {
      "merged_communities": 2,
      "transferred_users": 25,
      "transferred_staff": 3
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "至少需要选择2个社区进行合并",
    "data": {}
  }
  ```

---

### 1.7 拆分社区

**状态**: ✅ 已实现

- **路径**: `POST /api/community/split`
- **认证**: Bearer Token (super_admin)
- **请求体**:
  ```json
  {
    "source_community_id": "uuid-string",
    "sub_communities": [
      {
        "name": "子社区1",
        "location": "地址1",
        "location_lat": 39.9042,
        "location_lon": 116.4074
      },
      {
        "name": "子社区2",
        "location": "地址2"
      }
    ]
  }
  ```

- **业务逻辑**:
  - 创建多个新社区
  - 源社区状态设为 inactive
  - 用户需要重新分配到新社区

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "拆分成功",
    "data": {
      "created_communities": [
        {
          "id": "new-uuid-1",
          "name": "子社区1"
        },
        {
          "id": "new-uuid-2",
          "name": "子社区2"
        }
      ]
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "社区不存在",
    "data": {}
  }
  ```

---

## 2. 工作人员管理相关接口

### 2.1 获取工作人员列表

**状态**: ✅ 已实现

- **路径**: `GET /api/community/staff/list`
- **认证**: Bearer Token (super_admin, community_manager)
- **请求参数**:
  ```json
  {
    "community_id": "uuid-string",     // 必填
    "role": "all",                     // 可选: manager/staff/all, 默认all
    "sort_by": "time"                  // 可选: name/role/time, 默认time
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "staff_members": [
        {
          "user_id": "uuid",
          "nickname": "张三",
          "avatar_url": "https://example.com/avatar.jpg",
          "phone_number": "138****5678",
          "role": "manager",             // manager: 主管, staff: 专员
          "communities": [                // 所属的所有社区
            {
              "id": "community-uuid",
              "name": "阳光社区",
              "location": "北京市朝阳区"
            }
          ],
          "scope": "负责XX区域",         // 仅 staff 角色有此字段
          "added_time": "2025-12-10T10:00:00Z"
        }
      ]
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "社区不存在",
    "data": {}
  }
  ```

---

### 2.2 添加工作人员

**状态**: ✅ 已实现

- **路径**: `POST /api/community/add-staff`
- **认证**: Bearer Token (super_admin, community_manager)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",
    "user_ids": ["user-uuid-1", "user-uuid-2"],
    "role": "staff"  // manager 或 staff
  }
  ```

- **业务规则**:
  - 主管 (manager) 只能添加一个
  - 检查用户是否已是工作人员
  - 检查用户是否存在

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "添加成功",
    "data": {
      "added_count": 2,
      "failed": []
    }
  }
  ```

- **部分成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "部分添加成功",
    "data": {
      "added_count": 1,
      "failed": [
        {
          "user_id": "uuid",
          "reason": "用户已是工作人员"
        }
      ]
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "主管只能添加一个",
    "data": {}
  }
  ```

---

### 2.3 移除工作人员

**状态**: ✅ 已实现

- **路径**: `POST /api/community/remove-staff`
- **认证**: Bearer Token (super_admin, community_manager)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",
    "user_id": "user-uuid"
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "移除成功",
    "data": {}
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "工作人员不存在",
    "data": {}
  }
  ```

---

### 2.4 搜索用户

**状态**: ✅ 已实现

- **路径**: `GET /api/user/search`
- **认证**: Bearer Token (super_admin, community_manager, community_staff)
- **请求参数**:
  ```json
  {
    "keyword": "张三",              // 必填, 搜索关键词 (昵称或手机号)
    "community_id": "uuid-string"  // 可选, 用于标记已在社区的用户
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "users": [
        {
          "user_id": "uuid",
          "nickname": "张三",
          "avatar_url": "https://example.com/avatar.jpg",
          "phone_number": "138****5678",
          "is_staff": false,                    // 是否已是任何社区的工作人员
          "already_in_community": false         // 是否已在指定社区 (仅当传了community_id时)
        }
      ]
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "搜索关键词不能为空",
    "data": {}
  }
  ```

---

## 3. 社区用户管理相关接口

### 3.1 获取社区用户列表

**状态**: ✅ 已实现

- **路径**: `GET /api/community/users`
- **认证**: Bearer Token (super_admin, community_manager, community_staff)
- **请求参数**:
  ```json
  {
    "community_id": "uuid-string",  // 必填
    "page": 1,                      // 可选, 默认1
    "page_size": 20                 // 可选, 默认20
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "users": [
        {
          "user_id": "uuid",
          "nickname": "张三",
          "avatar_url": "https://example.com/avatar.jpg",
          "phone_number": "138****5678",
          "join_time": "2025-12-10T10:00:00Z",
          "unchecked_count": 2,           // 未完成打卡数
          "unchecked_items": [            // 未完成打卡详情
            {
              "rule_id": "rule-uuid",
              "rule_name": "晨跑",
              "planned_time": "07:00:00"
            }
          ]
        }
      ],
      "total": 50,
      "has_more": true,
      "current_page": 1
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "社区不存在",
    "data": {}
  }
  ```

---

### 3.2 添加社区用户

**状态**: ✅ 已实现

- **路径**: `POST /api/community/add-users`
- **认证**: Bearer Token (super_admin, community_manager, community_staff)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",
    "user_ids": ["user-uuid-1", "user-uuid-2"]  // 最多50个
  }
  ```

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "添加成功",
    "data": {
      "added_count": 2,
      "failed": []
    }
  }
  ```

- **部分成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "部分添加成功",
    "data": {
      "added_count": 1,
      "failed": [
        {
          "user_id": "uuid",
          "reason": "用户已在社区"
        }
      ]
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "最多只能添加50个用户",
    "data": {}
  }
  ```

---

### 3.3 移除社区用户

**状态**: ✅ 已实现

- **路径**: `POST /api/community/remove-user`
- **认证**: Bearer Token (super_admin, community_manager, community_staff)
- **请求体**:
  ```json
  {
    "community_id": "uuid-string",
    "user_id": "user-uuid"
  }
  ```

- **业务逻辑**:
  - 如果是从"安卡大家庭"移除,则移入"黑屋"
  - 如果是从普通社区移除:
    - 若用户还属于其他普通社区,仅从当前社区移除
    - 若用户不属于任何其他普通社区,则移入"安卡大家庭"

- **成功响应** (200):
  ```json
  {
    "code": 1,
    "msg": "移除成功",
    "data": {
      "moved_to": "安卡大家庭"  // 或 "黑屋" 或 null
    }
  }
  ```

- **失败响应** (200):
  ```json
  {
    "code": 0,
    "msg": "用户不在该社区",
    "data": {}
  }
  ```

---

## 4. 特殊社区说明

### 4.1 安卡大家庭

- **特性**: 系统默认社区,新注册用户自动加入
- **规则**: 
  - 不能删除
  - 不能停用
  - 用户从普通社区移除且不属于其他社区时,自动移入此社区

### 4.2 黑屋

- **特性**: 特殊管理社区
- **规则**:
  - 不能删除
  - 不能停用
  - 从"安卡大家庭"移除的用户移入此社区
  - 用户在此社区时,功能受限

---

## 5. 权限说明

| 角色 | 社区CRUD | 工作人员管理 | 用户管理 |
|------|---------|------------|---------|
| super_admin | ✅ | ✅ | ✅ |
| community_manager | ❌ | ✅ | ✅ |
| community_staff | ❌ | ❌ | ✅ |

---

## 6. 错误码说明

| code | 说明 |
|------|------|
| 1 | 成功 |
| 0 | 失败 (具体原因见 msg 字段) |

**常见错误消息**:
- "权限不足"
- "社区不存在"
- "用户不存在"
- "社区名称已存在"
- "请先停用社区"
- "社区内还有用户，无法删除"
- "主管只能添加一个"
- "用户已是工作人员"
- "用户已在社区"

---

## 7. 实现优先级

1. **高优先级** (核心功能):
   - ✅ 获取社区列表
   - ⏳ 获取工作人员列表
   - ⏳ 获取社区用户列表
   - ⏳ 添加/移除工作人员
   - ⏳ 添加/移除社区用户

2. **中优先级** (管理功能):
   - ⏳ 创建/更新/删除社区
   - ⏳ 切换社区状态
   - ⏳ 搜索用户

3. **低优先级** (高级功能):
   - ⏳ 合并社区
   - ⏳ 拆分社区

---

## 8. 测试建议

### 8.1 单元测试
- 权限验证
- 业务规则验证
- 边界条件测试

### 8.2 集成测试
- 完整用户流程
- 特殊社区逻辑
- 并发操作

### 8.3 性能测试
- 大量用户列表加载
- 批量操作性能

---

**文档版本**: v1.0  
**最后更新**: 2025-12-12  
**维护者**: SafeGuard 开发团队
