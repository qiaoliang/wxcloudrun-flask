# SafeGuard 后端 API 文档总览

本文档总结了 SafeGuard 后端项目中所有生产环境的 RESTful API 接口，按业务领域分类整理。

## 目录

-   [1. 认证与授权 (Authentication & Authorization)](#1-认证与授权-authentication--authorization)
-   [2. 用户管理 (User Management)](#2-用户管理-user-management)
-   [3. 社区管理 (Community Management)](#3-社区管理-community-management)
-   [4. 社区工作人员管理 (Community Staff Management)](#4-社区工作人员管理-community-staff-management)
-   [5. 社区申请管理 (Community Application Management)](#5-社区申请管理-community-application-management)
-   [6. 打卡功能 (Check-in Management)](#6-打卡功能-check-in-management)
-   [7. 打卡规则管理 (Check-in Rules Management)](#7-打卡规则管理-check-in-rules-management)
-   [8. 监督功能 (Supervision Management)](#8-监督功能-supervision-management)
-   [9. 分享功能 (Share Management)](#9-分享功能-share-management)
-   [10. 短信服务 (SMS Service)](#10-短信服务-sms-service)
-   [11. 系统功能 (System Functions)](#11-系统功能-system-functions)

---

## 1. 认证与授权 (Authentication & Authorization)

### 1.1 微信登录

-   **路径**: `POST /api/login`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 通过微信小程序 code 获取用户信息并返回 token
-   **权限**: 公开
-   **请求参数**:
    -   `code` (string, required): 微信小程序登录凭证
    -   `nickname` (string, required): 用户昵称
    -   `avatar_url` (string, required): 用户头像 URL
-   **响应数据**:
    -   `token`: JWT access token
    -   `refresh_token`: 刷新令牌
    -   `user_id`: 用户 ID
    -   `login_type`: 登录类型（new_user/existing_user）
-   **自动化测试**: 
    -   `test_wechat_login_success` (tests/e2e/test_auth_api.py)
    -   `test_wechat_login_missing_code` (tests/e2e/test_auth_api.py)
    -   `test_wechat_login_invalid_code` (tests/e2e/test_auth_api.py)
    -   `test_register_wechat_user_via_login_and_find_in_db` (tests/e2e/test_wechat_user_registration.py)
    -   `test_register_same_wechat_user_twice_returns_existing_user` (tests/e2e/test_wechat_user_registration.py)
    -   `test_register_wechat_user_with_minimal_data` (tests/e2e/test_wechat_user_registration.py)
    -   `test_register_wechat_user_missing_code_returns_error` (tests/e2e/test_wechat_user_registration.py)
    -   `test_register_wechat_user_with_empty_code_returns_error` (tests/e2e/test_wechat_user_registration.py)

### 1.2 Token 刷新

-   **路径**: `POST /api/refresh_token`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 使用 refresh token 获取新的 access token
-   **权限**: 公开
-   **请求参数**:
    -   `refresh_token` (string, required): 刷新令牌
-   **自动化测试**:
    -   `test_refresh_token_success` (tests/e2e/test_auth_api.py)
    -   `test_refresh_token_missing_token` (tests/e2e/test_auth_api.py)
    -   `test_refresh_token_invalid_token` (tests/e2e/test_auth_api.py)

### 1.3 用户登出

-   **路径**: `POST /api/logout`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 清除用户的 refresh token
-   **权限**: 需要认证
-   **自动化测试**:
    -   `test_logout_without_token` (tests/e2e/test_auth_api.py)
    -   `test_logout_invalid_token` (tests/e2e/test_auth_api.py)

### 1.4 手机号注册

-   **路径**: `POST /api/auth/register_phone`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 通过手机号和验证码注册新用户
-   **权限**: 公开
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `code` (string, required): 验证码
    -   `nickname` (string, optional): 昵称
    -   `avatar_url` (string, optional): 头像 URL
    -   `password` (string, optional): 密码
-   **自动化测试**:
    -   `test_phone_register_success` (tests/e2e/test_auth_api.py)
    -   `test_phone_register_missing_phone` (tests/e2e/test_auth_api.py)
    -   `test_phone_register_missing_code` (tests/e2e/test_auth_api.py)
    -   `test_phone_register_invalid_sms_code` (tests/e2e/test_auth_api.py)
    -   `test_phone_register_weak_password` (tests/e2e/test_auth_api.py)
    -   `test_phone_register_existing_phone` (tests/e2e/test_auth_api.py)

### 1.5 手机号登录（多种方式）

#### ⚠️ **功能重复说明**

以下三个接口都提供手机号登录功能，但验证方式不同：

#### 1.5.1 验证码登录

-   **路径**: `POST /api/auth/login_phone_code`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 仅使用手机号和验证码登录
-   **权限**: 公开
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `code` (string, required): 验证码
-   **自动化测试**:
    -   `test_login_phone_code_success` (tests/e2e/test_auth_api.py)
    -   `test_login_phone_code_missing_phone` (tests/e2e/test_auth_api.py)
    -   `test_login_phone_code_user_not_exists` (tests/e2e/test_auth_api.py)

#### 1.5.2 密码登录

-   **路径**: `POST /api/auth/login_phone_password`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 仅使用手机号和密码登录
-   **权限**: 公开
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `password` (string, required): 密码
-   **自动化测试**:
    -   `test_login_phone_password_success` (tests/e2e/test_auth_api.py)
    -   `test_login_phone_password_wrong_password` (tests/e2e/test_auth_api.py)

#### 1.5.3 验证码+密码登录

-   **路径**: `POST /api/auth/login_phone`
-   **文件**: `src/wxcloudrun/views/auth.py`
-   **功能**: 同时验证手机号、验证码和密码登录（双重验证）
-   **权限**: 公开
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `code` (string, required): 验证码
    -   `password` (string, required): 密码
-   **自动化测试**:
    -   `test_login_phone_success` (tests/e2e/test_auth_api.py)

---

## 2. 用户管理 (User Management)

### 2.1 获取用户信息

-   **路径**: `GET /api/user/profile`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 获取当前登录用户的详细信息
-   **权限**: 需要认证
-   **响应数据**:
    -   `user_id`: 用户 ID
    -   `wechat_openid`: 微信 OpenID
    -   `phone_number`: 手机号（脱敏）
    -   `nickname`: 昵称
    -   `avatar_url`: 头像 URL
    -   `role`: 角色名称
    -   `community_id`: 所属社区 ID
    -   `status`: 状态名称

### 2.2 更新用户信息

-   **路径**: `POST /api/user/profile`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 更新当前用户的个人信息
-   **权限**: 需要认证
-   **请求参数**:
    -   `nickname` (string, optional): 昵称
    -   `avatar_url` (string, optional): 头像 URL
    -   `phone_number` (string, optional): 手机号
    -   `role` (int/string, optional): 角色
    -   `community_id` (int, optional): 社区 ID
    -   `status` (int/string, optional): 状态
    -   `is_community_worker` (boolean, optional): 是否社区工作人员

### 2.3 搜索用户

-   **路径**: `GET /api/users/search`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 根据昵称或手机号搜索用户（支持范围限制）
-   **权限**: 需要认证
-   **请求参数**:
    -   `keyword` (string, required): 搜索关键词（昵称或完整手机号）
    -   `scope` (string, optional): 搜索范围（all/community，默认 all）
    -   `community_id` (int, optional): 社区 ID（scope=community 时必需）
    -   `limit` (int, optional): 返回数量限制（默认 10）
-   **权限要求**:
    -   `scope=all`: 需要超级管理员权限
    -   `scope=community`: 需要该社区的管理权限
-   **自动化测试**:
    -   `test_search_users_success` (tests/e2e/test_user_api.py)
    -   `test_search_users_by_phone_number` (tests/e2e/test_user_api.py)
    -   `test_search_phone_logic` (tests/e2e/test_phone_hash_search.py)
    -   `test_phone_hash_calculation` (tests/e2e/test_phone_hash_search.py)

### 2.4 绑定手机号

-   **路径**: `POST /api/user/bind_phone`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 为当前用户绑定手机号（支持账号合并）
-   **权限**: 需要认证
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `code` (string, required): 验证码

### 2.5 绑定微信

-   **路径**: `POST /api/user/bind_wechat`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 为当前用户绑定微信（支持账号合并）
-   **权限**: 需要认证
-   **请求参数**:
    -   `code` (string, required): 微信登录 code
    -   `phone` (string, optional): 手机号
    -   `phone_code` (string, optional): 手机验证码

### 2.6 社区工作人员身份验证

-   **路径**: `POST /api/community/verify`
-   **文件**: `src/wxcloudrun/views/user.py`
-   **功能**: 提交社区工作人员身份验证申请
-   **权限**: 需要认证
-   **请求参数**:
    -   `name` (string, required): 真实姓名
    -   `workId` (string, required): 工号
    -   `workProof` (string, required): 工作证明照片 URL

---

## 3. 社区管理 (Community Management)

### 3.1 获取社区列表（多个接口）

#### ⚠️ **功能重复说明**

以下两个接口都用于获取社区列表，但适用场景不同：

#### 3.1.1 获取社区列表（旧版，超级管理员专用）

-   **路径**: `GET /api/communities`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取所有社区列表（用于应用初始化测试）
-   **权限**: 超级管理员
-   **响应数据**: 社区数组，包含完整社区信息
-   **自动化测试**:
    -   `test_default_community_and_super_admin_created_after_startup` (tests/e2e/test_application_initialization.py)

#### 3.1.2 获取社区列表（新版，支持分页筛选）

-   **路径**: `GET /api/community/list`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取社区列表，支持分页和状态筛选
-   **权限**: 超级管理员
-   **请求参数**:
    -   `page` (int, optional): 页码（默认 1）
    -   `page_size` (int, optional): 每页数量（默认 20）
    -   `status_filter` (string, optional): 状态筛选（all/active/inactive，默认 all）
-   **响应数据**:
    -   `communities`: 社区数组
    -   `total`: 总数
    -   `has_more`: 是否有更多
    -   `current_page`: 当前页码

### 3.2 获取社区用户列表

-   **路径**: `GET /api/communities/<int:community_id>/users`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取指定社区的用户列表（非管理员）
-   **权限**: 社区管理员
-   **请求参数**:
    -   `page` (int, optional): 页码（默认 1）
    -   `per_page` (int, optional): 每页数量（默认 20）
    -   `keyword` (string, optional): 搜索关键词

### 3.3 从社区移除用户

-   **路径**: `DELETE /api/communities/<int:community_id>/users/<int:target_user_id>`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 从社区中移除用户（移至默认社区）
-   **权限**: 超级管理员

### 3.4 获取当前用户的社区信息

-   **路径**: `GET /api/user/community`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取当前用户所属的社区信息
-   **权限**: 需要认证
-   **响应数据**:
    -   `community`: 社区信息
    -   `is_admin`: 是否为管理员
    -   `is_primary_admin`: 是否为主管

### 3.5 获取用户管理的社区列表

-   **路径**: `GET /api/user/managed-communities`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取当前用户有管理权限的社区列表
-   **权限**: 需要认证（社区工作人员或超级管理员）
-   **响应数据**:
    -   `communities`: 社区数组
    -   `total`: 总数
    -   `user_role`: 用户角色（super_admin/community_staff）

### 3.6 获取可申请的社区列表

-   **路径**: `GET /api/communities/available`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取所有可以申请加入的社区列表
-   **权限**: 需要认证

---

## 4. 社区工作人员管理 (Community Staff Management)

### 4.1 获取社区工作人员列表

-   **路径**: `GET /api/community/staff/list`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取指定社区的工作人员列表
-   **权限**: 超级管理员或社区工作人员
-   **请求参数**:
    -   `community_id` (int, required): 社区 ID
    -   `role` (string, optional): 角色筛选（all/manager/staff，默认 all）
    -   `sort_by` (string, optional): 排序方式（name/role/time，默认 time）
-   **响应数据**:
    -   `staff_members`: 工作人员数组
-   **自动化测试**:
    -   `test_default_community_and_super_admin_created_after_startup` (tests/e2e/test_application_initialization.py)
    -   `test_multi_community_role_assignment_basic_flow` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_user_permission_based_on_community_role` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_user_can_be_removed_from_individual_communities` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_get_managed_communities_api_returns_correct_roles` (tests/e2e/test_multi_community_role_e2e.py)

### 4.2 添加社区工作人员

-   **路径**: `POST /api/community/add-staff`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 为社区添加工作人员（主管或专员）
-   **权限**: 超级管理员或社区主管
-   **请求参数**:
    -   `community_id` (int, required): 社区 ID
    -   `user_ids` (array, required): 用户 ID 列表
    -   `role` (string, required): 角色（manager/staff）
-   **注意事项**:
    -   主管只能添加一个
    -   用户不能在同一社区重复任职
-   **自动化测试**:
    -   `test_multi_community_role_assignment_basic_flow` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_user_permission_based_on_community_role` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_user_can_be_removed_from_individual_communities` (tests/e2e/test_multi_community_role_e2e.py)
    -   `test_get_managed_communities_api_returns_correct_roles` (tests/e2e/test_multi_community_role_e2e.py)

---

## 5. 社区申请管理 (Community Application Management)

### 5.1 获取社区申请列表

-   **路径**: `GET /api/community/applications`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 获取待处理的社区申请列表
-   **权限**: 社区管理员
-   **响应数据**: 申请数组，包含申请人、目标社区、申请原因等信息

### 5.2 提交社区申请

-   **路径**: `POST /api/community/applications`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 提交加入社区的申请
-   **权限**: 需要认证
-   **请求参数**:
    -   `community_id` (int, required): 目标社区 ID
    -   `reason` (string, optional): 申请理由

### 5.3 批准社区申请

-   **路径**: `PUT /api/community/applications/<int:application_id>/approve`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 批准用户的社区申请
-   **权限**: 社区管理员

### 5.4 拒绝社区申请

-   **路径**: `PUT /api/community/applications/<int:application_id>/reject`
-   **文件**: `src/wxcloudrun/views/community.py`
-   **功能**: 拒绝用户的社区申请
-   **权限**: 社区管理员
-   **请求参数**:
    -   `rejection_reason` (string, required): 拒绝理由

---

## 6. 打卡功能 (Check-in Management)

### 6.1 获取今日打卡事项

-   **路径**: `GET /api/checkin/today`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 获取用户今日的所有打卡事项列表
-   **权限**: 需要认证
-   **响应数据**:
    -   `date`: 日期
    -   `checkin_items`: 打卡事项数组（包含规则信息、计划时间、状态等）

### 6.2 执行打卡

-   **路径**: `POST /api/checkin`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 执行打卡操作
-   **权限**: 需要认证
-   **请求参数**:
    -   `rule_id` (int, required): 打卡规则 ID
-   **响应数据**:
    -   `rule_id`: 规则 ID
    -   `record_id`: 打卡记录 ID
    -   `checkin_time`: 打卡时间

### 6.3 标记为 Missed

-   **路径**: `POST /api/checkin/miss`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 标记当天规则为 missed（超过宽限期）
-   **权限**: 需要认证
-   **请求参数**:
    -   `rule_id` (int, required): 打卡规则 ID

### 6.4 撤销打卡

-   **路径**: `POST /api/checkin/cancel`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 撤销打卡操作（仅限 30 分钟内）
-   **权限**: 需要认证
-   **请求参数**:
    -   `record_id` (int, required): 打卡记录 ID

### 6.5 获取打卡历史

-   **路径**: `GET /api/checkin/history`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 获取用户的打卡历史记录
-   **权限**: 需要认证
-   **请求参数**:
    -   `start_date` (string, optional): 开始日期（默认 7 天前）
    -   `end_date` (string, optional): 结束日期（默认今天）
-   **响应数据**:
    -   `start_date`: 开始日期
    -   `end_date`: 结束日期
    -   `history`: 打卡记录数组

---

## 7. 打卡规则管理 (Check-in Rules Management)

### 7.1 打卡规则管理（统一接口）

-   **路径**: `GET/POST/PUT/DELETE /api/checkin/rules`
-   **文件**: `src/wxcloudrun/views/checkin.py`
-   **功能**: 打卡规则的 CRUD 操作
-   **权限**: 需要认证

#### 7.1.1 获取打卡规则列表

-   **方法**: `GET`
-   **响应数据**:
    -   `rules`: 规则数组（包含规则名称、图标、频率类型、时间等）

#### 7.1.2 创建打卡规则

-   **方法**: `POST`
-   **请求参数**:
    -   `rule_name` (string, required): 规则名称
    -   `icon_url` (string, optional): 图标 URL
    -   `frequency_type` (int, optional): 频率类型（0-每天/1-每周/2-工作日/3-自定义）
    -   `time_slot_type` (int, optional): 时间段类型（1-上午/2-下午/3-晚上/4-自定义）
    -   `custom_time` (string, optional): 自定义时间（HH:MM 格式）
    -   `week_days` (int, optional): 星期掩码（默认 127，周一到周日）
    -   `custom_start_date` (string, optional): 自定义开始日期
    -   `custom_end_date` (string, optional): 自定义结束日期
    -   `status` (int, optional): 状态（默认 1-启用）

#### 7.1.3 更新打卡规则

-   **方法**: `PUT`
-   **请求参数**:
    -   `rule_id` (int, required): 规则 ID
    -   其他字段同创建接口（可选）

#### 7.1.4 删除打卡规则

-   **方法**: `DELETE`
-   **请求参数**:
    -   `rule_id` (int, required): 规则 ID

---

## 8. 监督功能 (Supervision Management)

### 8.1 邀请监督者

-   **路径**: `POST /api/rules/supervision/invite`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 邀请特定用户监督特定规则
-   **权限**: 需要认证
-   **请求参数**:
    -   `invite_type` (string, optional): 邀请类型（默认 wechat）
    -   `rule_ids` (array, optional): 规则 ID 列表（空表示监督所有规则）
    -   `target_openid` (string, required): 被邀请用户的 openid

### 8.2 生成监督邀请链接

-   **路径**: `POST /api/rules/supervision/invite_link`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 生成监督邀请链接（无需指定目标用户）
-   **权限**: 需要认证
-   **请求参数**:
    -   `rule_ids` (array, optional): 规则 ID 列表
    -   `expire_hours` (int, optional): 过期时间（小时，默认 72）
-   **响应数据**:
    -   `invite_token`: 邀请令牌
    -   `mini_path`: 小程序路径
    -   `expire_at`: 过期时间

### 8.3 解析邀请链接

-   **路径**: `GET /api/rules/supervision/invite/resolve`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 解析邀请链接，将当前登录用户绑定为监督者
-   **权限**: 需要认证
-   **请求参数**:
    -   `token` (string, required): 邀请令牌
-   **响应数据**:
    -   `relation_id`: 监督关系 ID
    -   `status`: 关系状态
    -   `solo_user_id`: 被监督用户 ID
    -   `rule_id`: 规则 ID

### 8.4 获取监督邀请列表

-   **路径**: `GET /api/rules/supervision/invitations`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 获取当前用户收到或发出的监督邀请
-   **权限**: 需要认证
-   **请求参数**:
    -   `type` (string, optional): 类型（received-收到/sent-发出，默认 received）
-   **响应数据**:
    -   `type`: 类型
    -   `invitations`: 邀请数组

### 8.5 接受监督邀请

-   **路径**: `POST /api/rules/supervision/accept`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 接受监督邀请
-   **权限**: 需要认证
-   **请求参数**:
    -   `relation_id` (int, required): 监督关系 ID

### 8.6 拒绝监督邀请

-   **路径**: `POST /api/rules/supervision/reject`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 拒绝监督邀请
-   **权限**: 需要认证
-   **请求参数**:
    -   `relation_id` (int, required): 监督关系 ID

### 8.7 获取我监督的用户列表

-   **路径**: `GET /api/rules/supervision/my_supervised`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 获取当前用户监督的用户列表及其今日打卡状态
-   **权限**: 需要认证
-   **响应数据**:
    -   `supervised_users`: 被监督用户数组（包含规则列表、今日打卡状态）

### 8.8 获取我的监护人列表

-   **路径**: `GET /api/rules/supervision/my_guardians`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 获取监督当前用户的监护人列表
-   **权限**: 需要认证
-   **响应数据**:
    -   `guardians`: 监护人数组

### 8.9 获取被监督用户的打卡记录

-   **路径**: `GET /api/rules/supervision/records`
-   **文件**: `src/wxcloudrun/views/supervision.py`
-   **功能**: 获取被监督用户的打卡记录
-   **权限**: 需要认证
-   **请求参数**:
    -   `solo_user_id` (int, required): 被监督用户 ID
    -   `rule_id` (int, optional): 规则 ID（可选，不指定则查所有）
    -   `start_date` (string, optional): 开始日期（默认 7 天前）
    -   `end_date` (string, optional): 结束日期（默认今天）
-   **响应数据**:
    -   `start_date`: 开始日期
    -   `end_date`: 结束日期
    -   `history`: 打卡记录数组

---

## 9. 分享功能 (Share Management)

### 9.1 创建分享链接

-   **路径**: `POST /api/share/checkin/create`
-   **文件**: `src/wxcloudrun/views/share.py`
-   **功能**: 创建可分享的打卡邀请链接（opaque token）
-   **权限**: 需要认证
-   **请求参数**:
    -   `rule_id` (int, required): 打卡规则 ID
    -   `expire_hours` (int, optional): 过期时间（小时，默认 168）
-   **响应数据**:
    -   `token`: 分享令牌
    -   `url`: 分享 URL
    -   `mini_path`: 小程序路径
    -   `expire_at`: 过期时间

### 9.2 解析分享链接

-   **路径**: `GET /api/share/checkin/resolve`
-   **文件**: `src/wxcloudrun/views/share.py`
-   **功能**: 解析分享链接并建立监督关系
-   **权限**: 需要认证
-   **请求参数**:
    -   `token` (string, required): 分享令牌
-   **响应数据**:
    -   `rule`: 规则信息
    -   `solo_user_id`: 被监督用户 ID

### 9.3 分享链接的 Web 入口

-   **路径**: `GET /share/check-in`
-   **文件**: `src/wxcloudrun/views/share.py`
-   **功能**: 分享链接的 Web 页面入口（记录访问日志、提示小程序路径）
-   **权限**: 公开
-   **请求参数**:
    -   `token` (string, required): 分享令牌

---

## 10. 短信服务 (SMS Service)

### 10.1 发送验证码

-   **路径**: `POST /api/sms/send_code`
-   **文件**: `src/wxcloudrun/views/sms.py`
-   **功能**: 发送短信验证码
-   **权限**: 公开
-   **请求参数**:
    -   `phone` (string, required): 手机号
    -   `purpose` (string, optional): 用途（register/login/bind_phone/bind_wechat，默认 register）
-   **响应数据**:
    -   `message`: 提示消息
    -   `debug_code` (optional): 调试用验证码（仅在调试模式下返回）

---

## 11. 系统功能 (System Functions)

### 11.1 主页

-   **路径**: `GET /`
-   **文件**: `src/wxcloudrun/views/misc.py`
-   **功能**: 返回主页面
-   **权限**: 公开

### 11.2 环境配置查看器

-   **路径**: `GET /env`
-   **文件**: `src/wxcloudrun/views/misc.py`
-   **功能**: 返回环境配置查看器页面
-   **权限**: 公开

### 11.3 计数器操作

-   **路径**: `POST /api/count`
-   **文件**: `src/wxcloudrun/views/misc.py`
-   **功能**: 计数器操作（自增、清零、清理用户数据）
-   **权限**: 公开
-   **请求参数**:
    -   `action` (string, required): 操作类型（inc/clear/clear_users）
-   **自动化测试**:
    -   `test_post_count_clear` (tests/e2e/test_count_api.py)
    -   `test_post_count_invalid_action` (tests/e2e/test_count_api.py)
    -   `test_post_count_missing_action` (tests/e2e/test_count_api.py)
    -   `test_post_count_invalid_json` (tests/e2e/test_count_api.py)

### 11.4 获取计数值

-   **路径**: `GET /api/count`
-   **文件**: `src/wxcloudrun/views/misc.py`
-   **功能**: 获取计数器的当前值
-   **权限**: 公开
-   **自动化测试**:
    -   `test_get_count_initial_value` (tests/e2e/test_count_api.py)
    -   `test_default_community_and_super_admin_created_after_startup` (tests/e2e/test_application_initialization.py)

### 11.5 获取环境配置信息

-   **路径**: `GET /api/get_envs`
-   **文件**: `src/wxcloudrun/views/misc.py`
-   **功能**: 获取环境配置详细信息（支持 JSON 和 TOML 格式）
-   **权限**: 公开
-   **请求参数**:
    -   `format` (string, optional): 响应格式（txt/toml/json，默认 json）
-   **响应数据**:
    -   `environment`: 环境类型
    -   `config_source`: 配置文件来源
    -   `variables`: 环境变量详情
    -   `external_systems`: 外部系统状态

---

## API 命名规范说明

### RESTful 设计原则

本项目的 API 设计遵循以下原则：

-   使用 HTTP 方法表示操作类型（GET/POST/PUT/DELETE）
-   使用名词复数形式表示资源（如 `/api/users`, `/api/communities`）
-   使用路径参数表示资源 ID（如 `/api/communities/<id>`）
-   使用查询参数进行过滤和分页

### 统一响应格式

所有 API 返回统一的响应格式：

```json
{
  "code": 1,          // 1-成功，0-失败
  "msg": "success",   // 状态消息
  "data": {...}       // 响应数据
}
```

### 认证方式

需要认证的接口使用 Bearer Token 方式：

```
Authorization: Bearer <token>
```

---

## 注意事项

### 功能重复的 API

项目中存在以下功能重复或相似的 API：

1. **社区列表查询**:

    - `/api/communities` (旧版，无分页)
    - `/api/community/list` (新版，支持分页和筛选) ✅ **推荐使用**

2. **手机号登录**:
    - `/api/auth/login_phone_code` (仅验证码)
    - `/api/auth/login_phone_password` (仅密码)
    - `/api/auth/login_phone` (验证码+密码) ✅ **最安全，推荐使用**

### 权限分级

-   **公开**: 无需认证
-   **需要认证**: 需要有效的 JWT token
-   **社区管理员**: 需要社区管理权限
-   **超级管理员**: 需要超级管理员权限（role=4）

### 版本说明

当前文档版本：v1.0.0
最后更新时间：2025-12-15

---

## 相关文档链接

-   [认证 API 详细文档](./API_auth.md)
-   [用户 API 详细文档](./API_user.md)
-   [社区 API 详细文档](./API_community.md)
-   [打卡 API 详细文档](./API_checkin.md)
-   [监督 API 详细文档](./API_supervision.md)
-   [分享 API 详细文档](./API_share.md)
-   [短信 API 详细文档](./API_sms.md)
-   [其他 API 详细文档](./API_misc.md)
