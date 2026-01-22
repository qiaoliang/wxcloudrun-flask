# API 契约测试实现计划

## 概述

本文档记录了 SafeGuard 后端 API 契约测试的实现状态和待完成任务。

**创建日期**: 2026-01-21  
**最后更新**: 2026-01-21

## 整体统计

- **契约定义的 API 端点总数**: 117
- **测试方法总数**: 116
- **被跳过的测试**: 59
- **实际实现的测试**: 57
- **真实覆盖率**: 48.7%

## 模块详细状态

### ✅ 完全实现的模块（2个）

#### 1. COMMUNITY 模块
- **契约端点数**: 28
- **测试方法数**: 13
- **跳过数**: 0
- **实现数**: 13
- **实现率**: 100%

**已实现的测试**:
- test_community_create_contract
- test_community_update_contract
- test_community_toggle_status_activate_contract
- test_community_toggle_status_deactivate_contract
- test_community_toggle_status_missing_parameters_contract
- test_community_add_users_contract
- test_community_add_users_missing_parameters_contract
- test_community_remove_user_contract
- test_community_remove_user_missing_parameters_contract
- test_community_list_contract
- test_community_list_with_pagination_contract
- test_community_users_contract
- test_community_users_missing_community_id_contract

**未覆盖的 API 端点**（15个）:
- GET /api/communities
- GET /api/communities/available
- GET /api/community/communities/manage/list
- GET /api/communities/manage/search
- GET /api/communities/{community_id}
- POST /api/community/delete
- GET /api/communities/{community_id}/users
- DELETE /api/communities/{community_id}/users/{target_user_id}
- GET /api/community/staff/list-enhanced
- POST /api/community/add-staff
- POST /api/community/remove-staff
- POST /api/community/set-super-admin
- GET /api/community/admin-list
- GET /api/community/applications
- POST /api/community/applications
- PUT /api/community/applications/{application_id}/approve
- PUT /api/community/applications/{application_id}/reject
- POST /api/transfer-users
- GET /api/communities/{community_id}/events
- GET /api/communities/{community_id}/stats
- GET /api/communities/{community_id}/pending-events

#### 2. USER 模块
- **契约端点数**: 20
- **测试方法数**: 27
- **跳过数**: 0
- **实现数**: 27
- **实现率**: 100%

**已实现的测试**:
- test_user_profile_contract
- test_user_update_profile_contract
- test_user_update_profile_missing_parameters_contract
- test_user_upload_avatar_contract
- test_user_change_password_contract
- test_user_change_password_wrong_old_password_contract
- test_user_change_password_missing_parameters_contract
- test_user_search_contract
- test_user_search_missing_keyword_contract
- test_user_bind_phone_contract
- test_user_bind_phone_missing_parameters_contract
- test_user_bind_wechat_contract
- test_user_bind_wechat_missing_code_contract
- test_user_community_verify_contract
- test_user_community_verify_missing_community_id_contract
- test_user_active_events_contract
- test_user_event_messages_contract
- test_user_event_history_contract
- test_user_medical_history_list_contract
- test_user_medical_history_add_contract
- test_user_medical_history_update_contract
- test_user_medical_history_delete_contract
- test_user_medical_history_common_conditions_contract
- test_user_log_profile_view_contract
- test_user_log_view_guardian_contract
- test_user_profile_view_logs_contract
- test_user_managed_communities_contract

### ⚠️ 部分实现的模块（1个）

#### 1. AUTH 模块
- **契约端点数**: 7
- **测试方法数**: 20
- **跳过数**: 3
- **实现数**: 17
- **实现率**: 85%

**已实现的测试**（17个）:
- test_login_phone_password_contract
- test_login_phone_password_field_types_100_percent
- test_login_phone_password_wrong_password_contract
- test_login_phone_password_missing_field_contract
- test_login_phone_code_contract
- test_login_phone_code_field_types_100_percent
- test_login_phone_code_wrong_code_contract
- test_login_phone_code_missing_field_contract
- test_login_phone_with_code_contract
- test_login_phone_field_types_100_percent
- test_login_phone_with_password_only_contract
- test_login_phone_without_auth_method_contract
- test_login_wechat_contract
- test_login_wechat_field_types_100_percent
- test_login_wechat_with_optional_fields_contract
- test_login_wechat_missing_code_contract
- test_register_phone_contract
- test_register_phone_field_types_100_percent
- test_register_phone_with_optional_fields_contract
- test_register_phone_missing_required_field_contract
- test_refresh_token_contract
- test_refresh_token_field_types_100_percent
- test_refresh_token_invalid_contract
- test_refresh_token_missing_field_contract

**被跳过的测试**（3个）:
- test_logout_contract - 原因: "无法获取认证 token"
- test_logout_without_auth_contract - 原因: "无法获取认证 token"
- test_refresh_token_contract (部分) - 原因: "无法获取 refresh_token"
- test_refresh_token_field_types_100_percent (部分) - 原因: "无法获取 refresh_token"

### ❌ 完全未实现的模块（9个）

#### 1. CHECKIN 模块
- **契约端点数**: 9
- **测试方法数**: 6
- **跳过数**: 6
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（6个）:
- test_checkin_today_contract - 原因: "待实现：需要准备测试数据"
- test_checkin_create_contract - 原因: "待实现：需要准备测试数据"
- test_checkin_miss_contract - 原因: "待实现：需要准备测试数据"
- test_checkin_cancel_contract - 原因: "待实现：需要准备测试数据"
- test_checkin_history_contract - 原因: "待实现：需要准备测试数据"
- test_checkin_rules_contract - 原因: "待实现：需要准备测试数据"

**未覆盖的 API 端点**（3个）:
- POST /api/checkin/rules
- PUT /api/checkin/rules
- DELETE /api/checkin/rules

**需要的测试数据**:
- 用户
- 打卡规则
- 打卡记录

#### 2. COMMUNITY-CHECKIN 模块
- **契约端点数**: 9
- **测试方法数**: 6
- **跳过数**: 6
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（6个）:
- test_community_checkin_rules_list_contract - 原因: "待实现：需要准备测试数据（社区、打卡规则）"
- test_community_checkin_rule_create_contract - 原因: "待实现：需要准备测试数据"
- test_community_checkin_rule_update_contract - 原因: "待实现：需要准备测试数据"
- test_community_checkin_rule_delete_contract - 原因: "待实现：需要准备测试数据"
- test_community_checkin_records_contract - 原因: "待实现：需要准备测试数据"
- test_community_checkin_statistics_contract - 原因: "待实现：需要准备测试数据"

**未覆盖的 API 端点**（3个）:
- POST /api/community_checkin/rules/{rule_id}/enable
- POST /api/community_checkin/rules/{rule_id}/disable
- GET /api/community_checkin/stats/{community_id}/daily-stats
- GET /api/community_checkin/stats/{community_id}/checkin-stats

**需要的测试数据**:
- 社区
- 社区打卡规则
- 打卡记录

#### 3. COMMUNITY-DASHBOARD 模块
- **契约端点数**: 5
- **测试方法数**: 5
- **跳过数**: 5
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（5个）:
- test_community_overview_contract - 原因: "待实现：需要准备测试数据（社区、用户、打卡记录、事件）"
- test_community_user_statistics_contract - 原因: "待实现：需要准备测试数据"
- test_community_checkin_statistics_contract - 原因: "待实现：需要准备测试数据"
- test_community_event_statistics_contract - 原因: "待实现：需要准备测试数据"
- test_community_supervision_statistics_contract - 原因: "待实现：需要准备测试数据"

**需要的测试数据**:
- 社区
- 用户
- 打卡记录
- 事件
- 监护关系

#### 4. EVENTS 模块
- **契约端点数**: 8
- **测试方法数**: 9
- **跳过数**: 9
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（9个）:
- test_event_help_create_contract - 原因: "待实现：需要准备测试数据（用户、社区）"
- test_event_help_list_contract - 原因: "待实现：需要准备测试数据"
- test_event_support_create_contract - 原因: "待实现：需要准备测试数据"
- test_event_support_list_contract - 原因: "待实现：需要准备测试数据"
- test_event_detail_contract - 原因: "待实现：需要准备测试数据（事件）"
- test_event_close_contract - 原因: "待实现：需要准备测试数据"
- test_event_messages_contract - 原因: "待实现：需要准备测试数据"
- test_event_add_message_contract - 原因: "待实现：需要准备测试数据"
- test_my_events_contract - 原因: "待实现：需要准备测试数据"

**需要的测试数据**:
- 用户
- 社区
- 事件
- 事件消息

#### 5. MISC 模块
- **契约端点数**: 6
- **测试方法数**: 4
- **跳过数**: 4
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（4个）:
- test_health_check_contract - 原因: "待实现：健康检查端点"
- test_version_info_contract - 原因: "待实现：版本信息端点"
- test_config_info_contract - 原因: "待实现：需要准备测试数据"
- test_file_upload_contract - 原因: "待实现：需要准备测试文件"

**需要的测试数据**:
- 测试文件（用于文件上传测试）

#### 6. SHARE 模块
- **契约端点数**: 3
- **测试方法数**: 5
- **跳过数**: 5
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（5个）:
- test_share_link_create_contract - 原因: "待实现：需要准备测试数据（事件、社区等）"
- test_share_content_get_contract - 原因: "待实现：需要准备测试数据（分享链接）"
- test_share_links_list_contract - 原因: "待实现：需要准备测试数据"
- test_share_link_revoke_contract - 原因: "待实现：需要准备测试数据"
- test_share_access_contract - 原因: "待实现：需要准备测试数据"

**需要的测试数据**:
- 事件
- 社区
- 分享链接

#### 7. SMS 模块
- **契约端点数**: 1
- **测试方法数**: 3
- **跳过数**: 3
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（3个）:
- test_sms_send_code_contract - 原因: "待实现：需要配置 mock SMS"
- test_sms_verify_code_contract - 原因: "待实现：需要准备测试数据和 mock 验证码"
- test_sms_code_status_contract - 原因: "待实现：需要准备测试数据"

**需要的配置**:
- Mock SMS 服务配置

#### 8. SUPERVISION 模块
- **契约端点数**: 15
- **测试方法数**: 10
- **跳过数**: 10
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（10个）:
- test_supervision_create_contract - 原因: "待实现：需要准备测试数据（监护人、被监护人、社区）"
- test_supervision_list_contract - 原因: "待实现：需要准备测试数据"
- test_supervision_detail_contract - 原因: "待实现：需要准备测试数据（监护关系）"
- test_supervision_update_contract - 原因: "待实现：需要准备测试数据"
- test_supervision_delete_contract - 原因: "待实现：需要准备测试数据"
- test_my_supervisions_contract - 原因: "待实现：需要准备测试数据"
- test_my_supervisors_contract - 原因: "待实现：需要准备测试数据"
- test_supervision_invite_contract - 原因: "待实现：需要准备测试数据"
- test_supervision_accept_invite_contract - 原因: "待实现：需要准备测试数据（邀请）"
- test_supervision_reject_invite_contract - 原因: "待实现：需要准备测试数据"

**未覆盖的 API 端点**（5个）:
- POST /api/supervision/invite/internal
- POST /api/supervision/invite_link
- GET /api/supervision/invite/resolve
- DELETE /api/supervision/invitations/{invitation_id}
- POST /api/supervision/invitations/batch-accept
- GET /api/supervision/records
- GET /api/supervision/today
- POST /api/supervision/send_reminder

**需要的测试数据**:
- 监护人用户
- 被监护人用户
- 社区
- 监护关系
- 监护邀请

#### 9. USER-CHECKIN 模块
- **契约端点数**: 6
- **测试方法数**: 8
- **跳过数**: 8
- **实现数**: 0
- **实现率**: 0%

**被跳过的测试**（8个）:
- test_user_checkin_rules_list_contract - 原因: "待实现：需要准备测试数据（用户、打卡规则）"
- test_user_checkin_rule_create_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_rule_update_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_rule_delete_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_records_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_today_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_calendar_contract - 原因: "待实现：需要准备测试数据"
- test_user_checkin_statistics_contract - 原因: "待实现：需要准备测试数据"

**需要的测试数据**:
- 用户
- 用户打卡规则
- 打卡记录

## 优先级排序

### 高优先级（核心功能）
1. **SUPERVISION** - 10个测试（监护关系是核心功能）
2. **EVENTS** - 9个测试（事件处理是核心功能）
3. **USER-CHECKIN** - 8个测试（用户打卡是核心功能）

### 中优先级（重要功能）
4. **CHECKIN** - 6个测试（打卡功能）
5. **COMMUNITY-CHECKIN** - 6个测试（社区打卡）
6. **COMMUNITY-DASHBOARD** - 5个测试（社区仪表板）
7. **SHARE** - 5个测试（分享功能）

### 低优先级（辅助功能）
8. **MISC** - 4个测试（辅助功能）
9. **SMS** - 3个测试（短信验证）

## 实施建议

### 1. 通用测试数据准备
创建通用的测试数据生成器，用于：
- 用户创建（包括不同角色）
- 社区创建
- 打卡规则创建
- 事件创建
- 监护关系创建

### 2. Mock 服务配置
- SMS Mock 服务配置
- 文件上传 Mock 配置

### 3. 测试数据隔离
确保每个测试使用独立的测试数据，避免测试间相互影响。

### 4. 认证 Token 获取
修复 AUTH 模块中因无法获取 token 而跳过的测试。

## 实施步骤

### 第一阶段：基础设施（1-2天）
1. 创建测试数据生成器
2. 配置 Mock SMS 服务
3. 准备测试文件

### 第二阶段：核心功能（3-5天）
1. 实现 SUPERVISION 模块测试
2. 实现 EVENTS 模块测试
3. 实现 USER-CHECKIN 模块测试

### 第三阶段：重要功能（2-3天）
1. 实现 CHECKIN 模块测试
2. 实现 COMMUNITY-CHECKIN 模块测试
3. 实现 COMMUNITY-DASHBOARD 模块测试
4. 实现 SHARE 模块测试

### 第四阶段：辅助功能（1天）
1. 实现 MISC 模块测试
2. 实现 SMS 模块测试

### 第五阶段：完善与验证（1-2天）
1. 修复 AUTH 模块的跳过测试
2. 补充 COMMUNITY 模块缺失的测试
3. 运行所有契约测试，确保通过

## 注意事项

1. **测试数据隔离**: 每个测试应该使用独立的测试数据，避免测试间相互影响
2. **Mock 配置**: 确保 Mock 服务配置正确，特别是 SMS 服务
3. **认证处理**: 需要认证的测试应该正确处理 token 获取
4. **错误场景**: 除了正常场景，还需要测试错误场景和边界条件
5. **响应验证**: 严格验证响应结构、字段类型和字段值

## 参考资料

- 契约文件位置: `backend/api-contract/`
- 测试文件位置: `backend/tests/contract/`
- 集成测试指南: `backend/docs/integration-test-writing-guide.md`
- 测试数据生成器: `backend/tests/conftest.py`

## 更新日志

- 2026-01-21: 创建初始文档，记录所有模块的测试实现状态