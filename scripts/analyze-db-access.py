#!/usr/bin/env python3
"""
UseCase层DB访问分析工具

扫描所有UseCase文件，识别直接访问数据库的代码片段，
生成需要重构的文件清单。
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class DBAccessAnalyzer:
    """数据库访问分析器"""

    # 需要检测的违规模式
    PATTERNS = {
        'direct_db_import': r'from\s+database\.flask_models\s+import.*\b(db\b|User\b|Community\b)',
        'db_session_get': r'db\.session\.get\(',
        'db_session_execute': r'db\.session\.execute\(',
        'db_session_add': r'db\.session\.add\(',
        'db_session_commit': r'db\.session\.commit\(',
        'db_session_flush': r'db\.session\.flush\(',
        'db_session_delete': r'db\.session\.delete\(',
        'db_session_rollback': r'db\.session\.rollback\(',
    }

    def __init__(self, use_case_dir: str):
        self.use_case_dir = Path(use_case_dir)
        self.results = defaultdict(lambda: defaultdict(list))

    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个UseCase文件"""
        violations = defaultdict(list)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern_name, pattern in self.PATTERNS.items():
                for match in re.finditer(pattern, content):
                    # 找到匹配的行号
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1].strip()
                    violations[pattern_name].append({
                        'line': line_num,
                        'content': line_content
                    })

        except Exception as e:
            violations['_error'] = str(e)

        return dict(violations)

    def scan_all(self) -> Dict[str, Dict]:
        """扫描所有UseCase文件"""
        use_case_files = list(self.use_case_dir.rglob('*_use_case.py'))

        for file_path in use_case_files:
            relative_path = file_path.relative_to(self.use_case_dir)
            violations = self.analyze_file(file_path)

            if violations and '_error' not in violations:
                self.results[str(relative_path)] = violations

        return dict(self.results)

    def generate_report(self) -> str:
        """生成分析报告"""
        results = self.scan_all()

        report = ["=" * 80]
        report.append("UseCase层数据库直接访问分析报告")
        report.append("=" * 80)
        report.append("")

        total_files = len(results)
        report.append(f"发现 {total_files} 个文件需要重构")
        report.append("")

        # 按优先级分组
        critical_files = []
        high_files = []
        medium_files = []

        for file_path, violations in results.items():
            violation_count = sum(len(v) for v in violations.values())

            # 包含db.session.get或直接导入db的为Critical
            if 'direct_db_import' in violations or 'db_session_get' in violations:
                critical_files.append((file_path, violations, violation_count))
            elif violation_count > 5:
                high_files.append((file_path, violations, violation_count))
            else:
                medium_files.append((file_path, violations, violation_count))

        # 输出Critical级别
        report.append("=" * 80)
        report.append("CRITICAL (必须立即重构):")
        report.append("=" * 80)
        for file_path, violations, count in sorted(critical_files, key=lambda x: x[2], reverse=True):
            report.append(f"\n📁 {file_path} ({count} 处违规)")
            for pattern, items in violations.items():
                report.append(f"   - {pattern}: {len(items)} 处")
                for item in items[:3]:  # 只显示前3个
                    report.append(f"      Line {item['line']}: {item['content'][:60]}...")
                if len(items) > 3:
                    report.append(f"      ... 还有 {len(items) - 3} 处")

        # 输出High级别
        report.append("\n" + "=" * 80)
        report.append("HIGH (本周内重构):")
        report.append("=" * 80)
        for file_path, violations, count in sorted(high_files, key=lambda x: x[2], reverse=True):
            report.append(f"\n📁 {file_path} ({count} 处违规)")

        # 输出Medium级别
        report.append("\n" + "=" * 80)
        report.append("MEDIUM (本月内重构):")
        report.append("=" * 80)
        for file_path, violations, count in sorted(medium_files, key=lambda x: x[2], reverse=True)[:10]:
            report.append(f"\n📁 {file_path} ({count} 处违规)")

        report.append("\n" + "=" * 80)
        report.append(f"总计: {len(critical_files)} Critical, {len(high_files)} High, {len(medium_files)} Medium")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_file_list(self) -> str:
        """生成需要重构的文件列表（用于脚本）"""
        results = self.scan_all()

        lines = []
        lines.append("# UseCase文件重构清单")
        lines.append("")
        lines.append("## Critical Priority")
        lines.append("")

        for file_path, violations in sorted(results.items()):
            violation_count = sum(len(v) for v in violations.values())
            if 'direct_db_import' in violations or 'db_session_get' in violations:
                lines.append(f"- [ ] {file_path} ({violation_count} violations)")

        lines.append("")
        lines.append("## High Priority")
        lines.append("")

        for file_path, violations in sorted(results.items()):
            violation_count = sum(len(v) for v in violations.values())
            if violation_count > 5 and 'direct_db_import' not in violations:
                lines.append(f"- [ ] {file_path} ({violation_count} violations)")

        return "\n".join(lines)


def main():
    """主函数"""
    use_case_dir = "src/app/application/use_cases"

    if not os.path.exists(use_case_dir):
        print(f"错误: 找不到目录 {use_case_dir}")
        return

    analyzer = DBAccessAnalyzer(use_case_dir)

    # 生成并打印报告
    report = analyzer.generate_report()
    print(report)

    # 保存报告到文件
    report_file = "usecase-db-access-analysis-report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ 报告已保存到: {report_file}")

    # 生成文件清单
    checklist = analyzer.generate_file_list()
    checklist_file = "usecase-refactor-checklist.md"
    with open(checklist_file, 'w', encoding='utf-8') as f:
        f.write(checklist)
    print(f"✅ 重构清单已保存到: {checklist_file}")


if __name__ == '__main__':
    main()
