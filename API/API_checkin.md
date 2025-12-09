# API 名称：获取今日打卡事项
- 路径：GET /api/checkin/today
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "date": "2025-12-09",
    "checkin_items": [
      {
        "rule_id": 1,
        "record_id": 123,
        "rule_name": "晨练",
        "icon_url": "https://example.com/exercise.png",
        "planned_time": "09:00:00",
        "status": "checked",
        "checkin_time": "08:45:30"
      },
      {
        "rule_id": 2,
        "record_id": null,
        "rule_name": "服药",
        "icon_url": "https://example.com/medicine.png",
        "planned_time": "14:00:00",
        "status": "unchecked",
        "checkin_time": null
      }
    ]
  }
}
```
- 错误：401（token无效）、404（用户不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/checkin/today"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：执行打卡
- 路径：POST /api/checkin
- 认证：Bearer Token
- 请求参数：
  - rule_id（必填，int，打卡规则ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "rule_id": 2,
    "record_id": 124,
    "checkin_time": "2025-12-09 14:05:30",
    "message": "打卡成功"
  }
}
```
- 错误：400（缺少rule_id参数、今日已打卡）、401（token无效）、404（规则不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/checkin"
data = {
    "rule_id": 2
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：标记为missed
- 路径：POST /api/checkin/miss
- 认证：Bearer Token
- 请求参数：
  - rule_id（必填，int，打卡规则ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "record_id": 125,
    "message": "已标记为miss"
  }
}
```
- 错误：400（缺少rule_id参数、今日已打卡）、401（token无效）、404（规则不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/checkin/miss"
data = {
    "rule_id": 3
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：撤销打卡
- 路径：POST /api/checkin/cancel
- 认证：Bearer Token
- 请求参数：
  - record_id（必填，int，打卡记录ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "record_id": 124,
    "message": "撤销打卡成功"
  }
}
```
- 错误：400（缺少record_id参数、超过30分钟撤销时限）、401（token无效）、404（记录不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/checkin/cancel"
data = {
    "record_id": 124
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：获取打卡历史
- 路径：GET /api/checkin/history
- 认证：Bearer Token
- 请求参数：
  - start_date（可选，string，开始日期，默认7天前，格式：YYYY-MM-DD）
  - end_date（可选，string，结束日期，默认今天，格式：YYYY-MM-DD）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "start_date": "2025-12-02",
    "end_date": "2025-12-09",
    "history": [
      {
        "record_id": 120,
        "rule_id": 1,
        "rule_name": "晨练",
        "icon_url": "https://example.com/exercise.png",
        "planned_time": "2025-12-09 09:00:00",
        "checkin_time": "2025-12-09 08:45:30",
        "status": "已打卡",
        "created_at": "2025-12-09 08:45:30"
      },
      {
        "record_id": 121,
        "rule_id": 2,
        "rule_name": "服药",
        "icon_url": "https://example.com/medicine.png",
        "planned_time": "2025-12-08 14:00:00",
        "checkin_time": null,
        "status": "未打卡",
        "created_at": "2025-12-08 14:00:00"
      }
    ]
  }
}
```
- 错误：400（日期格式错误）、401（token无效）、404（用户不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/checkin/history"
params = {
    "start_date": "2025-12-01",
    "end_date": "2025-12-09"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

---

# API 名称：打卡规则管理
- 路径：GET/POST/PUT/DELETE /api/checkin/rules
- 认证：Bearer Token
- 请求参数：
  - GET：无参数
  - POST：
    - rule_name（必填，string，规则名称）
    - icon_url（可选，string，图标URL）
    - frequency_type（可选，int，频率类型：0-每天，1-每周，2-工作日，3-自定义）
    - time_slot_type（可选，int，时间段类型：1-上午，2-下午，3-晚上，4-自定义）
    - custom_time（可选，string，自定义时间，格式：HH:MM或HH:MM:SS）
    - week_days（可选，int，周几，位掩码：1-周一，2-周二，4-周三，8-周四，16-周五，32-周六，64-周日）
    - custom_start_date（可选，string，自定义开始日期，格式：YYYY-MM-DD）
    - custom_end_date（可选，string，自定义结束日期，格式：YYYY-MM-DD）
    - status（可选，int，状态：1-启用，2-禁用）
  - PUT：
    - rule_id（必填，int，规则ID）
    - 其他参数同POST（均为可选）
  - DELETE：
    - rule_id（必填，int，规则ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "rules": [
      {
        "rule_id": 1,
        "rule_name": "晨练",
        "icon_url": "https://example.com/exercise.png",
        "frequency_type": 0,
        "time_slot_type": 1,
        "custom_time": null,
        "week_days": 127,
        "custom_start_date": null,
        "custom_end_date": null,
        "status": 1,
        "created_at": "2025-12-01 10:00:00",
        "updated_at": "2025-12-01 10:00:00"
      }
    ]
  }
}
```
- 错误：400（参数缺失/无效）、401（token无效）、404（规则不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

# 获取规则列表
url = "http://localhost:8080/api/checkin/rules"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())

# 创建新规则
create_data = {
    "rule_name": "服药提醒",
    "icon_url": "https://example.com/medicine.png",
    "frequency_type": 0,
    "time_slot_type": 4,
    "custom_time": "14:00",
    "status": 1
}
response = requests.post(url, json=create_data, headers=headers)
print(response.json())

# 更新规则
update_data = {
    "rule_id": 1,
    "rule_name": "晨练（更新）",
    "custom_time": "08:30"
}
response = requests.put(url, json=update_data, headers=headers)
print(response.json())

# 删除规则
delete_data = {
    "rule_id": 2
}
response = requests.delete(url, json=delete_data, headers=headers)
print(response.json())
```