#!/usr/bin/env python3
"""
修复集成测试文件中的CommunityEventService使用
"""
import re

def fix_events_operations_file():
    """修复test_events_operations.py"""
    file_path = "/Users/qiaoliang/working/code/safeGuard/backend/tests/integration/test_events_operations.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除import语句
    content = re.sub(
        r"from wxcloudrun\.community_event_service import CommunityEventService\n",
        "",
        content
    )
    
    # 添加UseCase import
    if "CreateEventUseCase" not in content:
        import_line = "from app.application.use_cases.events.create_event_use_case import CreateEventUseCase\n"
        content = import_line + content
    
    # 替换CommunityEventService.create_event调用
    # 模式: CommunityEventService.create_event(\s*(.*?))
    def replace_create_event(match):
        params = match.group(1)
        # 提取参数
        return f"use_case = CreateEventUseCase()\n            use_case.execute({params})"
    
    content = re.sub(
        r"CommunityEventService\.create_event\(\s*(.*?)\)",
        replace_create_event,
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_close_event_file():
    """修复test_close_event.py"""
    file_path = "/Users/qiaoliang/working/code/safeGuard/backend/tests/integration/test_close_event.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除import语句
    content = re.sub(
        r"from wxcloudrun\.community_event_service import CommunityEventService\n",
        "",
        content
    )
    
    # 添加UseCase import
    if "CreateEventUseCase" not in content:
        import_line = "from app.application.use_cases.events.create_event_use_case import CreateEventUseCase\n"
        import_line += "from app.application.use_cases.events.close_event_use_case import CloseEventUseCase\n"
        content = import_line + content
    
    # 替换CommunityEventService.create_event调用
    def replace_create_event(match):
        params = match.group(1)
        return f"use_case = CreateEventUseCase()\n            use_case.execute({params})"
    
    content = re.sub(
        r"event = CommunityEventService\.create_event\(\s*(.*?)\)",
        replace_create_event,
        content,
        flags=re.DOTALL
    )
    
    # 替换CommunityEventService.close_event调用
    def replace_close_event(match):
        params = match.group(1)
        return f"use_case = CloseEventUseCase()\nclose_result = use_case.execute({params})"
    
    content = re.sub(
        r"close_result = CommunityEventService\.close_event\(\s*(.*?)\)",
        replace_close_event,
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    print("============================================================")
    print("修复集成测试文件中的CommunityEventService使用")
    print("============================================================")
    
    if fix_events_operations_file():
        print("✅ 已修复: test_events_operations.py")
    else:
        print("❌ 修复失败: test_events_operations.py")
    
    if fix_close_event_file():
        print("✅ 已修复: test_close_event.py")
    else:
        print("❌ 修复失败: test_close_event.py")
    
    print("============================================================")
    print("修复完成！")
    print("============================================================")

if __name__ == "__main__":
    main()