"""
SYSMIND Disk CLI Commands

Command handlers for disk analysis and management.
"""

import argparse
import os
from typing import Optional

from ..modules.disk.analyzer import DiskAnalyzer
from ..modules.disk.duplicates import DuplicateFinder
from ..modules.disk.cleaner import DiskCleaner
from ..modules.disk.quarantine import QuarantineManager
from ..utils.formatters import Formatter, Colors
from ..utils.validators import validate_path, parse_size
from ..core.database import Database


def register_disk_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register disk subcommands."""
    
    disk = subparsers.add_parser(
        'disk',
        help='Disk space analysis and management',
        description='Analyze disk usage, find duplicates, and clean up'
    )
    
    disk_sub = disk.add_subparsers(dest='disk_command', help='Disk commands')
    
    # Usage command
    usage = disk_sub.add_parser('usage', help='Show disk usage')
    usage.add_argument('path', nargs='?', default='.', help='Path to analyze')
    usage.add_argument('--depth', type=int, default=1, help='Directory depth')
    
    # Analyze command
    analyze = disk_sub.add_parser('analyze', help='Analyze directory')
    analyze.add_argument('path', nargs='?', default='.', help='Path to analyze')
    analyze.add_argument('--limit', type=int, default=20, help='Number of results')
    
    # Large files command
    large = disk_sub.add_parser('large', help='Find large files')
    large.add_argument('path', nargs='?', default='.', help='Path to search')
    large.add_argument('--min-size', type=str, default='100MB', help='Minimum file size')
    large.add_argument('--limit', type=int, default=20, help='Maximum results')
    
    # Old files command
    old = disk_sub.add_parser('old', help='Find old files')
    old.add_argument('path', nargs='?', default='.', help='Path to search')
    old.add_argument('--days', type=int, default=365, help='Minimum age in days')
    old.add_argument('--limit', type=int, default=20, help='Maximum results')
    
    # Duplicates command
    duplicates = disk_sub.add_parser('duplicates', help='Find duplicate files')
    duplicates.add_argument('path', nargs='?', default='.', help='Path to search')
    duplicates.add_argument('--min-size', type=str, default='1KB', help='Minimum file size')
    duplicates.add_argument('--limit', type=int, default=10, help='Maximum groups')
    
    # Clean command
    clean = disk_sub.add_parser('clean', help='Find cleanable items')
    clean.add_argument('--temp', action='store_true', help='Include temp files')
    clean.add_argument('--cache', action='store_true', help='Include cache files')
    clean.add_argument('--logs', action='store_true', help='Include old logs')
    clean.add_argument('--all', action='store_true', help='Include all cleanable items')
    clean.add_argument('--execute', action='store_true', help='Actually delete files')
    clean.add_argument('--no-quarantine', action='store_true', help='Delete without quarantine')
    
    # Quarantine commands
    quarantine = disk_sub.add_parser('quarantine', help='Manage quarantined files')
    quarantine_sub = quarantine.add_subparsers(dest='quarantine_command', help='Quarantine commands')
    
    quarantine_list = quarantine_sub.add_parser('list', help='List quarantined files')
    quarantine_list.add_argument('--limit', type=int, default=20, help='Maximum results')
    
    quarantine_restore = quarantine_sub.add_parser('restore', help='Restore quarantined file')
    quarantine_restore.add_argument('id', help='Quarantine ID to restore')
    
    quarantine_purge = quarantine_sub.add_parser('purge', help='Permanently delete expired items')
    quarantine_purge.add_argument('--all', action='store_true', help='Delete all quarantined items')


def handle_disk_command(args: argparse.Namespace, database: Database) -> int:
    """Handle disk commands."""
    
    formatter = Formatter()
    
    if not hasattr(args, 'disk_command') or not args.disk_command:
        return _handle_usage(args, formatter, database)
    
    cmd = args.disk_command
    
    if cmd == 'usage':
        return _handle_usage(args, formatter, database)
    elif cmd == 'analyze':
        return _handle_analyze(args, formatter, database)
    elif cmd == 'large':
        return _handle_large(args, formatter, database)
    elif cmd == 'old':
        return _handle_old(args, formatter, database)
    elif cmd == 'duplicates':
        return _handle_duplicates(args, formatter, database)
    elif cmd == 'clean':
        return _handle_clean(args, formatter, database)
    elif cmd == 'quarantine':
        return _handle_quarantine(args, formatter, database)
    else:
        print(f"{Colors.RED}Unknown disk command: {cmd}{Colors.RESET}")
        return 1


def _handle_usage(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show disk usage."""
    
    analyzer = DiskAnalyzer()
    
    # Get partition info
    print()
    print(formatter.box("Disk Partitions", width=70))
    print()
    
    try:
        partitions = analyzer.list_partitions()
        
        for part in partitions:
            percent = part['percent']
            color = Colors.GREEN if percent < 70 else Colors.YELLOW if percent < 90 else Colors.RED
            
            print(f"  {Colors.CYAN}{part['device']}{Colors.RESET} mounted on {part['mountpoint']}")
            print(f"    {formatter.progress_bar(percent / 100, width=40)} {color}{percent:.1f}%{Colors.RESET}")
            print(f"    Total: {formatter.file_size(part['total'])} | Used: {formatter.file_size(part['used'])} | Free: {formatter.file_size(part['free'])}")
            print()
    except Exception as e:
        print(f"  {Colors.YELLOW}Could not list partitions: {e}{Colors.RESET}")
    
    # Analyze path if specified
    path = getattr(args, 'path', '.')
    path = os.path.abspath(path)
    depth = getattr(args, 'depth', 1)
    
    if os.path.isdir(path):
        print()
        print(formatter.box(f"Directory: {path}", width=70))
        print()
        
        try:
            stats = analyzer.scan_directory(path)
            
            print(f"  Total Size: {formatter.file_size(stats.total_size)}")
            print(f"  Files: {stats.file_count:,} | Directories: {stats.dir_count:,}")
            print()
            
            if stats.largest_files:
                print(f"  {Colors.CYAN}Largest Files:{Colors.RESET}")
                for f in stats.largest_files[:5]:
                    print(f"    {formatter.file_size(f.size):>10}  {f.name}")
                print()
        except Exception as e:
            print(f"  {Colors.RED}Error analyzing directory: {e}{Colors.RESET}")
    
    return 0


def _handle_analyze(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Analyze directory."""
    
    path = os.path.abspath(getattr(args, 'path', '.'))
    limit = getattr(args, 'limit', 20)
    
    if not validate_path(path, must_exist=True, must_be_dir=True):
        print(f"{Colors.RED}Invalid directory: {path}{Colors.RESET}")
        return 1
    
    analyzer = DiskAnalyzer()
    
    print()
    print(formatter.box(f"Analyzing: {path}", width=70))
    print()
    
    print(f"  {Colors.YELLOW}Scanning...{Colors.RESET}", end='', flush=True)
    
    stats = analyzer.scan_directory(path)
    
    print(f"\r{Colors.GREEN}Scan complete!{Colors.RESET}                    ")
    print()
    
    print(f"  Total Size: {formatter.file_size(stats.total_size)}")
    print(f"  Files: {stats.file_count:,}")
    print(f"  Directories: {stats.dir_count:,}")
    print()
    
    # File type breakdown
    if stats.extensions:
        print(f"  {Colors.CYAN}Top File Types:{Colors.RESET}")
        sorted_exts = sorted(stats.extensions.items(), key=lambda x: x[1]['size'], reverse=True)
        for ext, info in sorted_exts[:10]:
            ext_name = ext if ext else '(no extension)'
            print(f"    {ext_name:>12}: {info['count']:>6} files, {formatter.file_size(info['size']):>10}")
        print()
    
    # Largest files
    if stats.top_files:
        print(f"  {Colors.CYAN}Largest Files:{Colors.RESET}")
        for f in stats.top_files[:limit]:
            rel_path = os.path.relpath(f.path, path)
            print(f"    {formatter.file_size(f.size):>10}  {rel_path}")
        print()
    
    return 0


def _handle_large(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Find large files."""
    
    path = os.path.abspath(getattr(args, 'path', '.'))
    min_size_str = getattr(args, 'min_size', '100MB')
    limit = getattr(args, 'limit', 20)
    
    min_size = parse_size(min_size_str)
    if min_size is None:
        print(f"{Colors.RED}Invalid size: {min_size_str}{Colors.RESET}")
        return 1
    
    analyzer = DiskAnalyzer()
    
    print()
    print(formatter.box(f"Large Files (>{min_size_str})", width=70))
    print()
    
    large_files = analyzer.find_large_files(path, min_size=min_size, limit=limit)
    
    if not large_files:
        print(f"  {Colors.GREEN}No files larger than {min_size_str} found.{Colors.RESET}")
    else:
        total_size = sum(f.size for f in large_files)
        print(f"  Found {len(large_files)} files totaling {formatter.file_size(total_size)}")
        print()
        
        headers = ['Size', 'Modified', 'Path']
        rows = []
        
        for f in large_files:
            rel_path = os.path.relpath(f.path, path)
            modified = f.modified.strftime('%Y-%m-%d')
            rows.append([formatter.file_size(f.size), modified, rel_path])
        
        print(formatter.table(headers, rows))
    
    print()
    return 0


def _handle_old(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Find old files."""
    
    path = os.path.abspath(getattr(args, 'path', '.'))
    days = getattr(args, 'days', 365)
    limit = getattr(args, 'limit', 20)
    
    analyzer = DiskAnalyzer()
    
    print()
    print(formatter.box(f"Old Files (>{days} days)", width=70))
    print()
    
    old_files = analyzer.find_old_files(path, days=days, limit=limit)
    
    if not old_files:
        print(f"  {Colors.GREEN}No files older than {days} days found.{Colors.RESET}")
    else:
        total_size = sum(f.size for f in old_files)
        print(f"  Found {len(old_files)} files totaling {formatter.file_size(total_size)}")
        print()
        
        headers = ['Size', 'Last Modified', 'Path']
        rows = []
        
        for f in old_files:
            rel_path = os.path.relpath(f.path, path)
            modified = f.modified.strftime('%Y-%m-%d')
            rows.append([formatter.file_size(f.size), modified, rel_path])
        
        print(formatter.table(headers, rows))
    
    print()
    return 0


def _handle_duplicates(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Find duplicate files."""
    
    path = os.path.abspath(getattr(args, 'path', '.'))
    min_size_str = getattr(args, 'min_size', '1KB')
    limit = getattr(args, 'limit', 10)
    
    min_size = parse_size(min_size_str)
    if min_size is None:
        print(f"{Colors.RED}Invalid size: {min_size_str}{Colors.RESET}")
        return 1
    
    finder = DuplicateFinder()
    
    print()
    print(formatter.box(f"Finding Duplicates in: {path}", width=70))
    print()
    
    print(f"  {Colors.YELLOW}Scanning and hashing files...{Colors.RESET}")
    
    groups = finder.find_duplicates(path, min_size=min_size)
    groups = groups[:limit]
    
    if not groups:
        print(f"\r  {Colors.GREEN}No duplicate files found.{Colors.RESET}                    ")
    else:
        total_waste = sum(g.wasted_space for g in groups)
        total_files = sum(len(g.files) for g in groups)
        
        print(f"\r  {Colors.GREEN}Found {len(groups)} duplicate groups ({total_files} files){Colors.RESET}                    ")
        print(f"  Wasted space: {formatter.file_size(total_waste)}")
        print()
        
        for i, group in enumerate(groups, 1):
            print(f"  {Colors.CYAN}Group {i}{Colors.RESET}: {len(group.files)} copies, {formatter.file_size(group.total_size)} total ({formatter.file_size(group.wasted_space)} wasted)")
            for f in group.files[:5]:
                rel_path = os.path.relpath(f.path, path)
                print(f"    {rel_path}")
            if len(group.files) > 5:
                print(f"    ... and {len(group.files) - 5} more")
            print()
    
    return 0


def _handle_clean(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Find and clean temporary files."""
    
    include_all = getattr(args, 'all', False)
    include_temp = getattr(args, 'temp', False) or include_all
    include_cache = getattr(args, 'cache', False) or include_all
    include_logs = getattr(args, 'logs', False) or include_all
    execute = getattr(args, 'execute', False)
    no_quarantine = getattr(args, 'no_quarantine', False)
    
    if not (include_temp or include_cache or include_logs):
        include_all = True
        include_temp = include_cache = include_logs = True
    
    cleaner = DiskCleaner(database)
    quarantine = QuarantineManager(database)
    
    print()
    print(formatter.box("Disk Cleanup", width=70))
    print()
    
    items = cleaner.find_cleanable_items(
        include_temp=include_temp,
        include_cache=include_cache,
        include_logs=include_logs
    )
    
    if not items:
        print(f"  {Colors.GREEN}No cleanable items found.{Colors.RESET}")
        print()
        return 0
    
    total_size = sum(item.size for item in items)
    
    print(f"  Found {len(items)} items totaling {formatter.file_size(total_size)}")
    print()
    
    # Group by category
    by_category: dict = {}
    for item in items:
        cat = item.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat, cat_items in by_category.items():
        cat_size = sum(i.size for i in cat_items)
        print(f"  {Colors.CYAN}{cat.title()}{Colors.RESET}: {len(cat_items)} items, {formatter.file_size(cat_size)}")
        for item in cat_items[:5]:
            print(f"    {formatter.file_size(item.size):>10}  {item.path}")
        if len(cat_items) > 5:
            print(f"    ... and {len(cat_items) - 5} more")
        print()
    
    if execute:
        print(f"  {Colors.YELLOW}Cleaning...{Colors.RESET}")
        
        use_quarantine = not no_quarantine
        result = cleaner.cleanup(items, quarantine_mgr=quarantine if use_quarantine else None)
        
        print()
        print(f"  {Colors.GREEN}Cleanup complete!{Colors.RESET}")
        print(f"    Deleted: {result.files_deleted} files, {result.dirs_deleted} directories")
        print(f"    Space freed: {formatter.file_size(result.space_freed)}")
        
        if result.errors:
            print(f"    {Colors.YELLOW}Errors: {len(result.errors)}{Colors.RESET}")
        
        if use_quarantine:
            print(f"    Files quarantined for 30 days before permanent deletion")
    else:
        print(f"  {Colors.YELLOW}To actually delete files, run with --execute{Colors.RESET}")
    
    print()
    return 0


def _handle_quarantine(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Handle quarantine commands."""
    
    qcmd = getattr(args, 'quarantine_command', None)
    
    if not qcmd:
        qcmd = 'list'
    
    quarantine = QuarantineManager(database)
    
    if qcmd == 'list':
        items = quarantine.list_items()
        
        print()
        print(formatter.box("Quarantined Files", width=70))
        print()
        
        if not items:
            print(f"  {Colors.GREEN}No quarantined files.{Colors.RESET}")
        else:
            headers = ['ID', 'Original Path', 'Size', 'Quarantined', 'Expires']
            rows = []
            
            for item in items:
                rows.append([
                    item.id[:8],
                    item.original_path[-40:],
                    formatter.file_size(item.size),
                    item.quarantine_time.strftime('%Y-%m-%d'),
                    item.expiry_time.strftime('%Y-%m-%d')
                ])
            
            print(formatter.table(headers, rows))
        print()
    
    elif qcmd == 'restore':
        item_id = args.id
        
        item = quarantine.restore_file(item_id)
        
        if item:
            print(f"{Colors.GREEN}Restored: {item.original_path}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Could not restore item with ID: {item_id}{Colors.RESET}")
            return 1
    
    elif qcmd == 'purge':
        delete_all = getattr(args, 'all', False)
        
        if delete_all:
            count = quarantine.purge_all()
            print(f"{Colors.GREEN}Permanently deleted {count} quarantined files.{Colors.RESET}")
        else:
            count = quarantine.cleanup_expired()
            print(f"{Colors.GREEN}Cleaned up {count} expired quarantine items.{Colors.RESET}")
    
    return 0
