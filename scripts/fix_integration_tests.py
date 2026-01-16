#!/usr/bin/env python3
"""
修复集成测试文件中的CommunityEventService使用
"""
import re
import sys

def fix_integration_test_file(file_path):
    """修复单个集成测试文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 删除CommunityEventService的import语句
        content = re.sub(
            r"from wxcloudrun\.community_event_service import CommunityEventService\n",
            "",
            content
        )
        
        # 替换CommunityEventService.create_event为UseCase调用
        # 模式1: event = CommunityEventService.create_event(...)
        content = re.sub(
            r"event = CommunityEventService\.create_event\((.*?)\)",
            lambda m: f"use_case = CreateEventUseCase()\nresult = use_case.execute({m.group(1)})\nevent = result.data['event']",
            content
        )
        
        # 模式2: CommunityEventService.create_event(...)
        content = re.sub(
            r"CommunityEventService\.create_event\((.*?)\)",
            lambda m: f"use_case = CreateEventUseCase()\nuse_case.execute({m.group(1)})",
            content
        )
        
        # 替换CommunityEventService.close_event为UseCase调用
        content = re.sub(
            r"close_result = CommunityEventService\.close_event\((.*?)\)",
            lambda m: f"use_case = CloseEventUseCase()\nclose_result = use_case.execute({m.group(1)})",
            content
        )
        
        # 在文件开头添加UseCase import
        if "from wxcloudrun.community_event_service" in original_content and "CreateEventUseCase" not in content:
            import_line = "from app.application.use_cases.events.create_event_use_case import CreateEventUseCase\n"
            import_line += "from app.application.use_cases.events.close_event_use_case import CloseEventUseCase\n"
            content = import_line + content
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def main():
    """主函数"""
    import os
    
    test_dir = "/Users/qiaoliang/working/code/safeGuard/backend/tests/integration"
    test_files = [
        "test_events_operations.py",
        "test_close_event.py"
    ]
    
    print("============================================================")
    print("修复集成测试文件中的CommunityEventService使用")
    print("============================================================")
    
    for test_file in test_files:
        file_path = os.path.join(test_dir, test_file)
        if fix_integration_test_file(file_path):
            print(f"✅ 已修复: {test_file}")
        else:
            print(f"ℹ️  无需修改: {test_file}")
    
    print("============================================================")
    print("修复完成！")
    print("============================================================")

if __name__ == "__main__":
    main()