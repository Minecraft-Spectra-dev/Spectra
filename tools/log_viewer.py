"""
日志查看工具

使用方法：
    python tools/log_viewer.py                    # 查看日志统计
    python tools/log_viewer.py --tail app.log    # 查看日志文件末尾
    python tools/log_viewer.py --clean            # 清理旧日志
    python tools/log_viewer.py --help             # 查看帮助
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from managers.log_manager import LogManager


def show_stats(log_manager):
    """显示日志统计信息"""
    print("\n" + "=" * 60)
    print("日志统计信息")
    print("=" * 60)
    stats = log_manager.get_log_stats()
    print(f"日志目录: {stats['log_directory']}")
    print(f"日志文件数量: {stats['total_files']}")
    print(f"日志总大小: {stats['total_size_mb']:.2f} MB")
    
    if stats['total_files'] > 0:
        print("\n日志文件列表:")
        for log_file in stats['log_files'][:10]:  # 只显示前10个
            file_path = Path(log_file)
            file_size = file_path.stat().st_size / 1024  # KB
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"  - {file_path.name:<20} {file_size:>8.1f} KB  {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if len(stats['log_files']) > 10:
            print(f"  ... 还有 {len(stats['log_files']) - 10} 个文件")
    
    print("=" * 60)


def tail_log(file_path: str, lines: int = 50):
    """查看日志文件末尾"""
    log_file = Path("logs") / file_path
    if not log_file.exists():
        print(f"错误: 日志文件不存在: {log_file}")
        return
    
    print(f"\n{'=' * 60}")
    print(f"查看日志文件: {file_path}")
    print(f"{'=' * 60}\n")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            print(line.rstrip())


def clean_logs(log_manager, days: int = 30):
    """清理旧日志"""
    print(f"\n正在清理 {days} 天前的日志文件...")
    log_manager.clean_old_logs(days=days)
    print("清理完成！")
    show_stats(log_manager)


def show_recent_logs(log_manager, hours: int = 1):
    """显示最近小时的日志"""
    log_files = log_manager.get_log_files()
    if not log_files:
        print("没有找到日志文件")
        return
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    print(f"\n{'=' * 60}")
    print(f"最近 {hours} 小时的日志")
    print(f"{'=' * 60}\n")
    
    for log_file in log_files:
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_time >= cutoff_time:
            print(f"\n--- {log_file.name} ({file_time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:  # 显示每个文件的最后20行
                    print(line.rstrip())


def main():
    parser = argparse.ArgumentParser(description='日志查看工具')
    parser.add_argument('--tail', metavar='FILE', help='查看日志文件末尾')
    parser.add_argument('--lines', type=int, default=50, help='显示的行数（用于 --tail）')
    parser.add_argument('--clean', action='store_true', help='清理旧日志')
    parser.add_argument('--days', type=int, default=30, help='清理多少天前的日志（用于 --clean）')
    parser.add_argument('--recent', type=int, default=0, help='显示最近N小时的日志')
    parser.add_argument('--stats', action='store_true', help='显示日志统计信息')
    
    args = parser.parse_args()
    
    # 初始化日志管理器
    log_manager = LogManager(log_dir="logs")
    
    # 如果没有指定任何选项，显示统计信息
    if not any([args.tail, args.clean, args.recent, args.stats]):
        show_stats(log_manager)
        return
    
    if args.tail:
        tail_log(args.tail, args.lines)
    
    if args.clean:
        clean_logs(log_manager, args.days)
    
    if args.recent > 0:
        show_recent_logs(log_manager, args.recent)
    
    if args.stats:
        show_stats(log_manager)


if __name__ == "__main__":
    main()
