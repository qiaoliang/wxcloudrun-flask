#!/usr/bin/env python3
"""
测试专员数量统计修复
"""

import sys
import os
sys.path.insert(0, 'src')

# 设置环境变量
os.environ['ENV_TYPE'] = 'function'

from sqlalchemy import create_engine, text

def get_database_url():
    """获取数据库URL"""
    # 从环境变量或配置文件获取
    # 这里使用默认的SQLite数据库
    return 'sqlite:///src/data/function.db'

def test_staff_statistics():
    """测试专员统计"""
    engine = create_engine(get_database_url())
    
    with engine.connect() as connection:
        print("=== 测试专员数量统计 ===")
        
        # 查询所有社区的统计信息
        result = connection.execute(text('''
            SELECT c.community_id, c.name, 
                   COUNT(cs.id) as total_staff,
                   SUM(CASE WHEN cs.role = 'staff' THEN 1 ELSE 0 END) as staff_only_count,
                   SUM(CASE WHEN cs.role = 'manager' THEN 1 ELSE 0 END) as manager_count
            FROM communities c
            LEFT JOIN community_staff cs ON c.community_id = cs.community_id
            GROUP BY c.community_id, c.name
            ORDER BY c.community_id
        '''))
        
        print("\n社区统计信息:")
        for row in result:
            print(f"\n社区ID: {row.community_id}, 名称: {row.name}")
            print(f"  工作人员总数: {row.total_staff}")
            print(f"  专员数量(staff): {row.staff_only_count}")
            print(f"  主管数量(manager): {row.manager_count}")
            
            # 验证计算
            calculated_staff_only = row.total_staff - row.manager_count
            print(f"  计算验证: total_staff({row.total_staff}) - manager_count({row.manager_count}) = {calculated_staff_only}")
            
            if row.staff_only_count != calculated_staff_only:
                print(f"  ⚠️ 警告: 数据库中的staff_only_count({row.staff_only_count})与计算结果({calculated_staff_only})不一致!")
            else:
                print(f"  ✅ 验证通过: staff_only_count计算正确")
        
        # 查询具体的专员和主管
        print("\n=== 详细工作人员列表 ===")
        staff_result = connection.execute(text('''
            SELECT cs.community_id, c.name, cs.user_id, u.nickname, cs.role
            FROM community_staff cs
            JOIN communities c ON cs.community_id = c.community_id
            JOIN users u ON cs.user_id = u.user_id
            ORDER BY cs.community_id, cs.role
        '''))
        
        staff_list = list(staff_result)
        if staff_list:
            print(f"\n共有 {len(staff_list)} 名工作人员:")
            for staff in staff_list:
                role_display = "主管" if staff.role == 'manager' else "专员"
                print(f"  - 社区: {staff.name}, 用户: {staff.nickname}, 角色: {role_display}({staff.role})")
        else:
            print("\n没有工作人员记录")

if __name__ == '__main__':
    test_staff_statistics()
