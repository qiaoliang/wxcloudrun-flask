from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import date, datetime
from wxcloudrun.model import User, CheckinRule, CheckinRecord


class BaseService(ABC):
    """
    服务层基类，定义基本规范
    """
    
    @abstractmethod
    def get_model_class(self):
        """获取服务对应的数据模型"""
        pass


class UserService(BaseService):
    """
    用户服务类
    """
    
    def get_model_class(self):
        return User

    def get_user_by_openid(self, openid: str) -> Optional[User]:
        """根据OpenID获取用户"""
        from wxcloudrun.dao import query_user_by_openid
        return query_user_by_openid(openid)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        from wxcloudrun.dao import query_user_by_id
        return query_user_by_id(user_id)

    def create_user(self, openid: str, nickname: str = None, avatar_url: str = None) -> User:
        """创建新用户"""
        from wxcloudrun.dao import insert_user
        from wxcloudrun.model import User as UserModel
        
        user = UserModel(
            wechat_openid=openid,
            nickname=nickname,
            avatar_url=avatar_url,
            role=1,  # 默认为独居者角色
            status=1  # 默认为正常状态
        )
        insert_user(user)
        return user

    def update_user(self, user: User, **kwargs) -> User:
        """更新用户信息"""
        from wxcloudrun.dao import update_user_by_id
        
        # 更新用户信息
        if 'nickname' in kwargs and kwargs['nickname'] is not None:
            user.nickname = kwargs['nickname']
        if 'avatar_url' in kwargs and kwargs['avatar_url'] is not None:
            user.avatar_url = kwargs['avatar_url']
        if 'phone_number' in kwargs and kwargs['phone_number'] is not None:
            user.phone_number = kwargs['phone_number']
        if 'role' in kwargs and kwargs['role'] is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(kwargs['role'], str):
                role_value = User.get_role_value(kwargs['role'])
                if role_value is not None:
                    user.role = role_value
            elif isinstance(kwargs['role'], int):
                user.role = kwargs['role']
        if 'community_id' in kwargs and kwargs['community_id'] is not None:
            user.community_id = kwargs['community_id']
        if 'status' in kwargs and kwargs['status'] is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(kwargs['status'], str):
                status_value = User.get_status_value(kwargs['status'])
                if status_value is not None:
                    user.status = status_value
            elif isinstance(kwargs['status'], int):
                user.status = kwargs['status']
        user.updated_at = datetime.now()
        
        update_user_by_id(user)
        return user

    def verify_community_user(self, user: User, name: str, work_id: str, work_proof: str) -> Dict[str, Any]:
        """社区工作人员身份验证"""
        from wxcloudrun.dao import update_user_by_id
        
        # 更新用户信息，设置验证状态
        user.name = name
        user.work_id = work_id
        user.verification_status = 1  # 设置为待审核状态
        user.verification_materials = work_proof  # 保存验证材料
        user.updated_at = datetime.now()
        
        update_user_by_id(user)
        
        return {
            'message': '身份验证申请已提交，请耐心等待审核',
            'verification_status': 'pending'
        }


class CheckinRuleService(BaseService):
    """
    打卡规则服务类
    """
    
    def get_model_class(self):
        return CheckinRule

    def get_rules_by_user_id(self, user_id: int) -> List[CheckinRule]:
        """根据用户ID获取打卡规则列表"""
        from wxcloudrun.dao import query_checkin_rules_by_user_id
        return query_checkin_rules_by_user_id(user_id)

    def get_rule_by_id(self, rule_id: int) -> Optional[CheckinRule]:
        """根据规则ID获取打卡规则"""
        from wxcloudrun.dao import query_checkin_rule_by_id
        return query_checkin_rule_by_id(rule_id)

    def create_rule(self, user_id: int, rule_data: Dict[str, Any]) -> CheckinRule:
        """创建打卡规则"""
        from wxcloudrun.dao import insert_checkin_rule
        from wxcloudrun.model import CheckinRule as CheckinRuleModel
        from datetime import datetime as dt
        
        new_rule = CheckinRuleModel(
            solo_user_id=user_id,
            rule_name=rule_data.get('rule_name'),
            icon_url=rule_data.get('icon_url', ''),
            frequency_type=rule_data.get('frequency_type', 0),
            time_slot_type=rule_data.get('time_slot_type', 4),
            custom_time=dt.strptime(rule_data['custom_time'], '%H:%M:%S').time() if rule_data.get('custom_time') else None,
            week_days=rule_data.get('week_days', 127),
            status=rule_data.get('status', 1)
        )
        
        insert_checkin_rule(new_rule)
        return new_rule

    def update_rule(self, rule: CheckinRule, rule_data: Dict[str, Any]) -> CheckinRule:
        """更新打卡规则"""
        from wxcloudrun.dao import update_checkin_rule_by_id
        
        if 'rule_name' in rule_data:
            rule.rule_name = rule_data['rule_name']
        if 'icon_url' in rule_data:
            rule.icon_url = rule_data['icon_url']
        if 'frequency_type' in rule_data:
            rule.frequency_type = rule_data['frequency_type']
        if 'time_slot_type' in rule_data:
            rule.time_slot_type = rule_data['time_slot_type']
        if 'custom_time' in rule_data:
            from datetime import datetime as dt
            rule.custom_time = dt.strptime(rule_data['custom_time'], '%H:%M:%S').time() if rule_data['custom_time'] else None
        if 'week_days' in rule_data:
            rule.week_days = rule_data['week_days']
        if 'status' in rule_data:
            rule.status = rule_data['status']
        
        update_checkin_rule_by_id(rule)
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        """删除打卡规则"""
        from wxcloudrun.dao import delete_checkin_rule_by_id
        delete_checkin_rule_by_id(rule_id)
        return True


class CheckinRecordService(BaseService):
    """
    打卡记录服务类
    """
    
    def get_model_class(self):
        return CheckinRecord

    def get_today_checkin_items(self, user_id: int, target_date: date = None) -> List[Dict[str, Any]]:
        """获取用户今日打卡事项"""
        from wxcloudrun.dao import query_checkin_rules_by_user_id, query_checkin_records_by_rule_id_and_date
        from datetime import date as dt_date, time
        import datetime
        
        if target_date is None:
            target_date = dt_date.today()
        
        # 获取用户的打卡规则
        checkin_rules = query_checkin_rules_by_user_id(user_id)
        
        # 生成今天的打卡计划
        checkin_items = []
        for rule in checkin_rules:
            # 根据规则频率类型判断今天是否需要打卡
            should_checkin_today = True
            
            if rule.frequency_type == 1:  # 每周
                # 根据week_days位掩码判断今天是否需要打卡
                today_weekday = target_date.weekday()  # 0是周一，6是周日
                if not (rule.week_days & (1 << today_weekday)):
                    should_checkin_today = False
            elif rule.frequency_type == 2:  # 工作日
                if target_date.weekday() >= 5:  # 周六日
                    should_checkin_today = False
            
            if should_checkin_today:
                # 查询今天该规则的打卡记录
                today_records = query_checkin_records_by_rule_id_and_date(rule.rule_id, target_date)
                
                # 计算计划打卡时间
                if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                    planned_time = datetime.datetime.combine(target_date, rule.custom_time)
                elif rule.time_slot_type == 1:  # 上午
                    planned_time = datetime.datetime.combine(target_date, time(9, 0))  # 默认上午9点
                elif rule.time_slot_type == 2:  # 下午
                    planned_time = datetime.datetime.combine(target_date, time(14, 0))  # 默认下午2点
                else:  # 晚上，默认晚上8点
                    planned_time = datetime.datetime.combine(target_date, time(20, 0))
                
                # 确定打卡状态
                checkin_status = 'unchecked'
                checkin_time = None
                record_id = None
                
                for record in today_records:
                    if record.status == 1:  # 已打卡
                        checkin_status = 'checked'
                        checkin_time = record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else None
                        record_id = record.record_id
                        break
                    elif record.status == 2:  # 已撤销
                        checkin_status = 'unchecked'
                        checkin_time = None
                        record_id = record.record_id
                        break
                
                checkin_items.append({
                    'rule_id': rule.rule_id,
                    'record_id': record_id,
                    'rule_name': rule.rule_name,
                    'icon_url': rule.icon_url,
                    'planned_time': planned_time.strftime('%H:%M:%S'),
                    'status': checkin_status,  # unchecked, checked
                    'checkin_time': checkin_time
                })
        
        return checkin_items

    def perform_checkin(self, rule_id: int, user_id: int) -> Dict[str, Any]:
        """执行打卡操作"""
        from wxcloudrun.dao import query_checkin_rule_by_id, query_checkin_records_by_rule_id_and_date, insert_checkin_record, update_checkin_record_by_id
        from datetime import datetime, date, time as dt_time
        import datetime as dt_module
        
        # 验证打卡规则是否存在且属于当前用户
        rule = query_checkin_rule_by_id(rule_id)
        if not rule or rule.solo_user_id != user_id:
            raise ValueError('打卡规则不存在或无权限')
        
        # 检查今天是否已有打卡记录（防止重复打卡）
        today = date.today()
        existing_records = query_checkin_records_by_rule_id_and_date(rule_id, today)
        
        # 查找当天已有的打卡记录（状态为已打卡）
        existing_checkin = None
        for record in existing_records:
            if record.status == 1:  # 已打卡
                # 不允许重复打卡
                raise ValueError('今日该事项已打卡，请勿重复打卡')
            elif record.status == 0:  # 未打卡状态的记录，可以更新为已打卡
                existing_checkin = record
                break
            elif record.status == 2:  # 已撤销的记录，可以重新打卡
                # 创建新的打卡记录
                existing_checkin = None
                break
        
        # 记录打卡时间
        checkin_time = datetime.now()
        
        if existing_checkin:
            # 更新已有记录的打卡时间和状态
            existing_checkin.checkin_time = checkin_time
            existing_checkin.status = 1  # 已打卡
            update_checkin_record_by_id(existing_checkin)
            record_id = existing_checkin.record_id
        else:
            # 计算计划打卡时间
            if rule.time_slot_type == 4 and rule.custom_time:  # 自定义时间
                planned_time = dt_module.datetime.combine(today, rule.custom_time)
            elif rule.time_slot_type == 1:  # 上午
                planned_time = dt_module.datetime.combine(today, dt_time(9, 0))  # 默认上午9点
            elif rule.time_slot_type == 2:  # 下午
                planned_time = dt_module.datetime.combine(today, dt_time(14, 0))  # 默认下午2点
            else:  # 晚上，默认晚上8点
                planned_time = dt_module.datetime.combine(today, dt_time(20, 0))
            
            # 创建新的打卡记录
            new_record = CheckinRecord(
                rule_id=rule_id,
                solo_user_id=user_id,
                checkin_time=checkin_time,
                status=1,  # 已打卡
                planned_time=planned_time
            )
            insert_checkin_record(new_record)
            record_id = new_record.record_id
        
        return {
            'rule_id': rule_id,
            'record_id': record_id,
            'checkin_time': checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
            'message': '打卡成功'
        }

    def cancel_checkin(self, record_id: int, user_id: int) -> Dict[str, Any]:
        """撤销打卡操作"""
        from wxcloudrun.dao import query_checkin_record_by_id, update_checkin_record_by_id
        from datetime import datetime
        
        # 验证打卡记录是否存在且属于当前用户
        record = query_checkin_record_by_id(record_id)
        if not record or record.solo_user_id != user_id:
            raise ValueError('打卡记录不存在或无权限')
        
        # 检查打卡时间是否在30分钟内（防止撤销过期打卡）
        if record.checkin_time:
            time_diff = datetime.now() - record.checkin_time
            if time_diff.total_seconds() > 30 * 60:  # 30分钟
                raise ValueError('只能撤销30分钟内的打卡记录')
        
        # 更新记录状态为已撤销
        record.status = 2  # 已撤销
        record.checkin_time = None  # 清除打卡时间
        update_checkin_record_by_id(record)
        
        return {
            'record_id': record_id,
            'message': '撤销打卡成功'
        }

    def get_checkin_history(self, user_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取打卡历史记录"""
        from wxcloudrun.dao import query_checkin_records_by_user_and_date_range
        
        # 获取打卡记录
        records = query_checkin_records_by_user_and_date_range(user_id, start_date, end_date)
        
        # 转换为响应格式
        history_data = []
        for record in records:
            history_data.append({
                'record_id': record.record_id,
                'rule_id': record.rule_id,
                'rule_name': record.rule.rule_name,
                'icon_url': record.rule.icon_url,
                'planned_time': record.planned_time.strftime('%Y-%m-%d %H:%M:%S'),
                'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                'status': record.status_name,  # 使用模型中的状态名称
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return history_data