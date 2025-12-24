#!/usr/bin/env python3
"""
智能测试运行器
根据测试规模自动选择最佳并行配置
"""
import subprocess
import sys
import os
import glob
import argparse
from pathlib import Path

def count_test_files(test_path):
    """统计测试文件数量"""
    if os.path.isfile(test_path):
        return 1
    
    if os.path.isdir(test_path):
        pattern = os.path.join(test_path, "**", "test_*.py")
        return len(glob.glob(pattern, recursive=True))
    
    return 0

def get_optimal_config(test_path, force_parallel=False, max_workers=None):
    """根据测试规模获取最佳配置"""
    file_count = count_test_files(test_path)
    
    config = {
        'args': [test_path],
        'description': f"智能配置 ({file_count} 个文件)"
    }
    
    # 强制并行模式
    if force_parallel:
        if max_workers:
            config['args'].extend(['-n', str(max_workers)])
        else:
            config['args'].extend(['-n', 'auto', '--dist', 'loadscope'])
        return config
    
    # 智能选择策略
    if file_count == 1:
        # 单个文件：串行执行
        pass
    elif file_count <= 5:
        # 小规模：2个进程
        config['args'].extend(['-n', '2'])
    elif file_count <= 20:
        # 中等规模：自动检测
        config['args'].extend(['-n', 'auto'])
    else:
        # 大规模：自动检测 + 负载均衡
        config['args'].extend(['-n', 'auto', '--dist', 'loadscope'])
    
    return config

def run_tests_with_smart_config(test_path, verbose=False, force_parallel=False, max_workers=None):
    """使用智能配置运行测试"""
    
    config = get_optimal_config(test_path, force_parallel, max_workers)
    
    # 构建完整命令
    cmd = [sys.executable, '-m', 'pytest']
    cmd.extend(config['args'])
    
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    # 添加常用参数
    cmd.extend(['--tb=short', '--maxfail=10'])
    
    print(f"=== {config['description']} ===")
    print(f"命令: {' '.join(cmd)}")
    
    # 设置环境变量
    env = os.environ.copy()
    if max_workers:
        env['PYTEST_XDIST_AUTO_NUM_WORKERS'] = str(max_workers)
    
    try:
        # 执行测试
        result = subprocess.run(cmd, env=env)
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return False
    except Exception as e:
        print(f"执行失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='智能测试运行器')
    parser.add_argument('test_path', nargs='?', default='tests/', 
                       help='测试路径 (默认: tests/)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')
    parser.add_argument('-p', '--parallel', action='store_true',
                       help='强制并行执行')
    parser.add_argument('-n', '--max-workers', type=int,
                       help='最大并行进程数')
    parser.add_argument('--dry-run', action='store_true',
                       help='显示配置但不执行')
    
    args = parser.parse_args()
    
    # 检查测试路径
    if not os.path.exists(args.test_path):
        print(f"错误: 测试路径不存在: {args.test_path}")
        return 1
    
    # 获取配置
    config = get_optimal_config(args.test_path, args.parallel, args.max_workers)
    
    print(f"智能测试运行器")
    print(f"测试路径: {args.test_path}")
    print(f"文件数量: {count_test_files(args.test_path)}")
    print(f"推荐配置: {config['description']}")
    
    if args.dry_run:
        print(f" dry-run 模式，不执行测试")
        return 0
    
    # 运行测试
    success = run_tests_with_smart_config(
        args.test_path, 
        args.verbose, 
        args.parallel, 
        args.max_workers
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
