#!/usr/bin/env python3
"""
DatabaseCore 到 Flask-SQLAlchemy 迁移扫描工具
扫描项目中所有使用 DatabaseCore 的代码，生成迁移报告
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def find_files_with_pattern(pattern: str, root_dir: Path) -> List[Path]:
    """查找包含指定模式的文件"""
    matches = []
    for ext in ['.py', '.md']:
        for file_path in root_dir.rglob(f'*{ext}'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if re.search(pattern, content, re.IGNORECASE):
                        matches.append(file_path)
                except UnicodeDecodeError:
                    # 跳过二进制文件
                    continue
    return matches

def analyze_databasecore_usage(file_path: Path) -> Dict:
    """分析文件中的 DatabaseCore 使用情况"""
    content = file_path.read_text(encoding='utf-8')
    
    patterns = {
        'import_get_database': r'from database import get_database|import.*get_database',
        'import_databasecore': r'from database.core import DatabaseCore|import.*DatabaseCore',
        'get_database_call': r'get_database\(\)',
        'get_session_call': r'\.get_session\(\)',
        'with_db_session': r'with .*get_session\(\) as session:',
        'db_core_attr': r'db_core\.|current_app\.db_core',
        'query_method': r'\.query\(|db\.query\(',
    }
    
    results = {
        'file': str(file_path.relative_to(Path.cwd())),
        'line_count': len(content.splitlines()),
        'patterns_found': {},
        'lines': []
    }
    
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        line_analysis = {}
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, line):
                line_analysis[pattern_name] = True
        
        if line_analysis:
            results['lines'].append({
                'line_number': i,
                'content': line.strip(),
                'patterns': list(line_analysis.keys())
            })
    
    # 统计模式发现情况
    for pattern_name in patterns.keys():
        count = sum(1 for line_info in results['lines'] 
                   if pattern_name in line_info['patterns'])
        if count > 0:
            results['patterns_found'][pattern_name] = count
    
    return results

def categorize_files_by_priority(analysis_results: List[Dict]) -> Dict[str, List[Dict]]:
    """按优先级分类文件"""
    categories = {
        'high_priority': [],  # 直接使用 DatabaseCore.get_session()
        'medium_priority': [],  # 混合使用或间接使用
        'low_priority': [],  # 仅导入或简单引用
    }
    
    for result in analysis_results:
        patterns = result['patterns_found']
        
        if 'with_db_session' in patterns or 'get_session_call' in patterns:
            # 直接使用 get_session()，高优先级
            categories['high_priority'].append(result)
        elif 'get_database_call' in patterns or 'db_core_attr' in patterns:
            # 使用 get_database() 或 db_core 属性，中优先级
            categories['medium_priority'].append(result)
        elif 'import_get_database' in patterns or 'import_databasecore' in patterns:
            # 仅导入，低优先级
            categories['low_priority'].append(result)
        else:
            # 其他情况，中优先级
            categories['medium_priority'].append(result)
    
    return categories

def generate_migration_report(categories: Dict[str, List[Dict]]) -> str:
    """生成迁移报告"""
    report_lines = []
    report_lines.append("# DatabaseCore 到 Flask-SQLAlchemy 迁移分析报告")
    report_lines.append("")
    report_lines.append(f"生成时间: {sys.argv[1] if len(sys.argv) > 1 else 'N/A'}")
    report_lines.append("")
    
    total_files = sum(len(files) for files in categories.values())
    report_lines.append(f"## 总体统计")
    report_lines.append(f"- 总文件数: {total_files}")
    report_lines.append(f"- 高优先级文件: {len(categories['high_priority'])}")
    report_lines.append(f"- 中优先级文件: {len(categories['medium_priority'])}")
    report_lines.append(f"- 低优先级文件: {len(categories['low_priority'])}")
    report_lines.append("")
    
    for priority, files in categories.items():
        if not files:
            continue
            
        report_lines.append(f"## {priority.replace('_', ' ').title()} 文件")
        report_lines.append("")
        
        for file_info in files:
            report_lines.append(f"### {file_info['file']}")
            report_lines.append(f"- 行数: {file_info['line_count']}")
            
            if file_info['patterns_found']:
                report_lines.append("- 发现的模式:")
                for pattern, count in file_info['patterns_found'].items():
                    report_lines.append(f"  - {pattern}: {count} 处")
            
            if file_info['lines']:
                report_lines.append("- 具体位置:")
                for line_info in file_info['lines'][:10]:  # 只显示前10行
                    patterns_str = ', '.join(line_info['patterns'])
                    report_lines.append(f"  - 第 {line_info['line_number']} 行: {line_info['content'][:100]}... [{patterns_str}]")
                if len(file_info['lines']) > 10:
                    report_lines.append(f"  - ... 还有 {len(file_info['lines']) - 10} 行")
            
            report_lines.append("")
    
    # 添加迁移建议
    report_lines.append("## 迁移建议")
    report_lines.append("")
    report_lines.append("### 高优先级文件（建议首先迁移）")
    report_lines.append("这些文件直接使用 `DatabaseCore.get_session()`，迁移后收益最大：")
    for file_info in categories['high_priority']:
        report_lines.append(f"- `{file_info['file']}`")
    report_lines.append("")
    
    report_lines.append("### 迁移步骤")
    report_lines.append("1. 为每个高优先级文件创建备份")
    report_lines.append("2. 替换 `with db.get_session() as session:` 为直接使用 `db.session`")
    report_lines.append("3. 更新事务处理：确保显式调用 `db.session.commit()` 和 `rollback()`")
    report_lines.append("4. 运行相关测试")
    report_lines.append("5. 重复步骤2-4直到所有高优先级文件完成")
    report_lines.append("")
    
    return "\n".join(report_lines)

def main():
    """主函数"""
    project_root = Path.cwd()
    src_dir = project_root / 'src'
    
    print("正在扫描 DatabaseCore 使用情况...")
    
    # 查找所有可能使用 DatabaseCore 的文件
    pattern = r'DatabaseCore|get_database|db_core'
    files = find_files_with_pattern(pattern, src_dir)
    
    print(f"找到 {len(files)} 个可能使用 DatabaseCore 的文件")
    
    # 分析每个文件
    analysis_results = []
    for file_path in files:
        print(f"分析: {file_path.relative_to(project_root)}")
        try:
            result = analyze_databasecore_usage(file_path)
            if result['lines']:  # 只保留有实际使用的文件
                analysis_results.append(result)
        except Exception as e:
            print(f"  分析失败: {e}")
    
    # 分类文件
    categories = categorize_files_by_priority(analysis_results)
    
    # 生成报告
    report = generate_migration_report(categories)
    
    # 保存报告
    report_path = project_root / 'databasecore_migration_report.md'
    report_path.write_text(report, encoding='utf-8')
    
    print(f"\n报告已生成: {report_path}")
    print(f"\n摘要:")
    print(f"  高优先级文件: {len(categories['high_priority'])}")
    print(f"  中优先级文件: {len(categories['medium_priority'])}")
    print(f"  低优先级文件: {len(categories['low_priority'])}")
    
    # 打印高优先级文件列表
    if categories['high_priority']:
        print("\n高优先级文件列表（建议首先迁移）:")
        for file_info in categories['high_priority']:
            print(f"  - {file_info['file']}")

if __name__ == '__main__':
    main()