"""
SYSMIND Process CLI Commands

Command handlers for process management.
"""

import argparse
import signal
from typing import Optional

from ..modules.process.manager import ProcessManager
from ..modules.process.profiler import ProcessProfiler
from ..modules.process.watchdog import ProcessWatchdog
from ..modules.process.startup import StartupManager
from ..utils.formatters import Formatter, Colors
from ..core.database import Database


def register_process_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register process subcommands."""
    
    process = subparsers.add_parser(
        'process',
        help='Process management and monitoring',
        description='List, manage, and monitor system processes'
    )
    
    process_sub = process.add_subparsers(dest='process_command', help='Process commands')
    
    # List command
    list_cmd = process_sub.add_parser('list', help='List running processes')
    list_cmd.add_argument('--sort', choices=['cpu', 'memory', 'pid', 'name'], default='memory',
                         help='Sort by field')
    list_cmd.add_argument('--limit', type=int, default=20, help='Maximum processes to show')
    list_cmd.add_argument('--filter', type=str, help='Filter by process name')
    list_cmd.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Top command
    top = process_sub.add_parser('top', help='Show top processes')
    top.add_argument('--by', choices=['cpu', 'memory'], default='cpu', help='Sort by metric')
    top.add_argument('-n', type=int, default=10, help='Number of processes')
    top.add_argument('--watch', action='store_true', help='Continuously update')
    top.add_argument('--interval', type=float, default=2.0, help='Update interval')
    
    # Profile command
    profile = process_sub.add_parser('profile', help='Profile a process')
    profile.add_argument('pid', type=int, help='Process ID to profile')
    profile.add_argument('--duration', type=int, default=10, help='Profile duration in seconds')
    profile.add_argument('--detailed', action='store_true', help='Include detailed metrics')
    
    # Kill command
    kill = process_sub.add_parser('kill', help='Kill a process')
    kill.add_argument('pid', type=int, help='Process ID to kill')
    kill.add_argument('--force', '-f', action='store_true', help='Force kill (SIGKILL)')
    kill.add_argument('--tree', action='store_true', help='Kill process tree')
    
    # Tree command
    tree = process_sub.add_parser('tree', help='Show process tree')
    tree.add_argument('--pid', type=int, help='Root PID (default: show all)')
    
    # Watchdog commands
    watchdog = process_sub.add_parser('watchdog', help='Process monitoring watchdog')
    watchdog_sub = watchdog.add_subparsers(dest='watchdog_command', help='Watchdog commands')
    
    watchdog_add = watchdog_sub.add_parser('add', help='Add monitoring rule')
    watchdog_add.add_argument('--name', required=True, help='Process name to watch')
    watchdog_add.add_argument('--cpu-limit', type=float, help='CPU usage limit')
    watchdog_add.add_argument('--memory-limit', type=str, help='Memory limit (e.g., 500MB)')
    watchdog_add.add_argument('--action', choices=['log', 'notify', 'kill'], default='log',
                             help='Action when limit exceeded')
    
    watchdog_list = watchdog_sub.add_parser('list', help='List watchdog rules')
    
    watchdog_remove = watchdog_sub.add_parser('remove', help='Remove watchdog rule')
    watchdog_remove.add_argument('rule_id', help='Rule ID to remove')
    
    watchdog_start = watchdog_sub.add_parser('start', help='Start watchdog monitoring')
    watchdog_start.add_argument('--interval', type=float, default=5.0, help='Check interval')
    
    watchdog_alerts = watchdog_sub.add_parser('alerts', help='Show recent alerts')
    watchdog_alerts.add_argument('--limit', type=int, default=20, help='Maximum alerts')
    
    # Startup commands
    startup = process_sub.add_parser('startup', help='Manage startup programs')
    startup_sub = startup.add_subparsers(dest='startup_command', help='Startup commands')
    
    startup_list = startup_sub.add_parser('list', help='List startup programs')
    
    startup_disable = startup_sub.add_parser('disable', help='Disable startup program')
    startup_disable.add_argument('name', help='Program name')
    
    startup_enable = startup_sub.add_parser('enable', help='Enable startup program')
    startup_enable.add_argument('name', help='Program name')
    
    startup_analyze = startup_sub.add_parser('analyze', help='Analyze startup impact')


def handle_process_command(args: argparse.Namespace, database: Database) -> int:
    """Handle process commands."""
    
    formatter = Formatter()
    
    if not hasattr(args, 'process_command') or not args.process_command:
        return _handle_list(args, formatter, database)
    
    cmd = args.process_command
    
    if cmd == 'list':
        return _handle_list(args, formatter, database)
    elif cmd == 'top':
        return _handle_top(args, formatter, database)
    elif cmd == 'profile':
        return _handle_profile(args, formatter, database)
    elif cmd == 'kill':
        return _handle_kill(args, formatter, database)
    elif cmd == 'tree':
        return _handle_tree(args, formatter, database)
    elif cmd == 'watchdog':
        return _handle_watchdog(args, formatter, database)
    elif cmd == 'startup':
        return _handle_startup(args, formatter, database)
    else:
        print(f"{Colors.RED}Unknown process command: {cmd}{Colors.RESET}")
        return 1


def _handle_list(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """List running processes."""
    
    manager = ProcessManager()
    
    sort_by = getattr(args, 'sort', 'memory')
    limit = getattr(args, 'limit', 20)
    filter_name = getattr(args, 'filter', None)
    
    processes = manager.list_processes(sort_by=sort_by, limit=limit)
    
    if filter_name:
        filter_lower = filter_name.lower()
        processes = [p for p in processes if filter_lower in p.name.lower()]
    
    print()
    print(formatter.box(f"Running Processes ({len(processes)} shown)", width=80))
    print()
    
    headers = ['PID', 'Name', 'CPU %', 'Memory', 'Status', 'User']
    rows = []
    
    for proc in processes:
        mem_str = formatter.file_size(proc.memory_rss)
        cpu_str = f"{proc.cpu_percent:.1f}"
        rows.append([
            str(proc.pid),
            proc.name[:20],
            cpu_str,
            mem_str,
            proc.status[:10],
            (proc.username or 'unknown')[:15]
        ])
    
    print(formatter.table(headers, rows))
    print()
    
    return 0


def _handle_top(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show top processes."""
    
    import time
    
    manager = ProcessManager()
    
    by = getattr(args, 'by', 'cpu')
    n = getattr(args, 'n', 10)
    watch = getattr(args, 'watch', False)
    interval = getattr(args, 'interval', 2.0)
    
    def show_top():
        processes = manager.get_top_processes(by=by, n=n)
        
        # Clear screen
        print('\033[2J\033[H', end='')
        
        print()
        metric_name = 'CPU' if by == 'cpu' else 'Memory'
        print(formatter.box(f"Top Processes by {metric_name}", width=70))
        print()
        
        headers = ['PID', 'Name', 'CPU %', 'Memory', 'Status']
        rows = []
        
        for proc in processes:
            cpu_color = ''
            if proc.cpu_percent > 80:
                cpu_color = Colors.RED
            elif proc.cpu_percent > 50:
                cpu_color = Colors.YELLOW
            
            rows.append([
                str(proc.pid),
                proc.name[:25],
                f"{cpu_color}{proc.cpu_percent:.1f}{Colors.RESET}",
                formatter.file_size(proc.memory_rss),
                proc.status
            ])
        
        print(formatter.table(headers, rows))
        print()
        print(f"Press Ctrl+C to exit")
    
    if watch:
        try:
            while True:
                show_top()
                time.sleep(interval)
        except KeyboardInterrupt:
            print()
    else:
        show_top()
    
    return 0


def _handle_profile(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Profile a process."""
    
    pid = args.pid
    duration = getattr(args, 'duration', 10)
    detailed = getattr(args, 'detailed', False)
    
    profiler = ProcessProfiler()
    
    print()
    print(formatter.box(f"Profiling Process {pid}", width=70))
    print()
    
    print(f"  {Colors.YELLOW}Profiling for {duration} seconds...{Colors.RESET}")
    
    try:
        profile = profiler.profile_process(pid, duration=duration)
        
        if not profile:
            print(f"\n  {Colors.RED}Could not profile process {pid} - may not exist{Colors.RESET}")
            return 1
        
        print(f"\r{Colors.GREEN}Profile complete!{Colors.RESET}                    ")
        print()
        
        print(f"  {Colors.CYAN}Process Info{Colors.RESET}")
        print(f"    Name: {profile.name}")
        print(f"    PID: {profile.pid}")
        print(f"    Status: {profile.status}")
        print(f"    User: {profile.username or 'unknown'}")
        print()
        
        print(f"  {Colors.CYAN}Resource Usage{Colors.RESET}")
        print(f"    CPU Average: {profile.cpu_average:.1f}%")
        print(f"    CPU Max: {profile.cpu_max:.1f}%")
        print(f"    Memory RSS: {formatter.file_size(profile.memory_rss)}")
        print(f"    Memory VMS: {formatter.file_size(profile.memory_vms)}")
        print()
        
        if detailed:
            print(f"  {Colors.CYAN}I/O Statistics{Colors.RESET}")
            print(f"    Read: {formatter.file_size(profile.io_read_bytes)}")
            print(f"    Write: {formatter.file_size(profile.io_write_bytes)}")
            print(f"    Read Ops: {profile.io_read_count}")
            print(f"    Write Ops: {profile.io_write_count}")
            print()
            
            print(f"  {Colors.CYAN}Thread Info{Colors.RESET}")
            print(f"    Thread Count: {profile.thread_count}")
            print()
            
            if profile.open_files:
                print(f"  {Colors.CYAN}Open Files ({len(profile.open_files)}){Colors.RESET}")
                for f in profile.open_files[:10]:
                    print(f"    {f}")
                if len(profile.open_files) > 10:
                    print(f"    ... and {len(profile.open_files) - 10} more")
                print()
            
            if profile.connections:
                print(f"  {Colors.CYAN}Network Connections ({len(profile.connections)}){Colors.RESET}")
                for conn in profile.connections[:5]:
                    print(f"    {conn}")
                if len(profile.connections) > 5:
                    print(f"    ... and {len(profile.connections) - 5} more")
                print()
    
    except KeyboardInterrupt:
        print(f"\n  {Colors.YELLOW}Profiling cancelled.{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"\n  {Colors.RED}Error profiling: {e}{Colors.RESET}")
        return 1
    
    return 0


def _handle_kill(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Kill a process."""
    
    pid = args.pid
    force = getattr(args, 'force', False)
    tree = getattr(args, 'tree', False)
    
    manager = ProcessManager()
    
    # Get process info first
    processes = manager.list_processes()
    proc = next((p for p in processes if p.pid == pid), None)
    
    if not proc:
        print(f"{Colors.RED}Process {pid} not found{Colors.RESET}")
        return 1
    
    print(f"Killing process: {proc.name} (PID: {pid})")
    
    if tree:
        # Get child processes
        children = manager.get_process_tree(pid)
        if children:
            print(f"  Will also kill {len(children)} child processes")
    
    sig = signal.SIGKILL if force else signal.SIGTERM
    sig_name = 'SIGKILL' if force else 'SIGTERM'
    
    try:
        success = manager.kill_process(pid, sig)
        
        if success:
            print(f"{Colors.GREEN}Sent {sig_name} to process {pid}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Failed to kill process {pid}{Colors.RESET}")
            return 1
        
        if tree:
            children = manager.get_process_tree(pid)
            for child in children:
                manager.kill_process(child.pid, sig)
                print(f"  Killed child: {child.name} ({child.pid})")
    
    except PermissionError:
        print(f"{Colors.RED}Permission denied - try running as administrator{Colors.RESET}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return 1
    
    return 0


def _handle_tree(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show process tree."""
    
    manager = ProcessManager()
    root_pid = getattr(args, 'pid', None)
    
    print()
    print(formatter.box("Process Tree", width=70))
    print()
    
    def print_tree(pid: int, indent: int = 0):
        processes = manager.list_processes()
        proc = next((p for p in processes if p.pid == pid), None)
        
        if not proc:
            return
        
        prefix = "  " * indent + ("├── " if indent > 0 else "")
        print(f"{prefix}{proc.name} ({proc.pid})")
        
        # Find children
        children = [p for p in processes if p.parent_pid == pid]
        for child in children:
            print_tree(child.pid, indent + 1)
    
    if root_pid:
        print_tree(root_pid)
    else:
        # Show tree starting from init/system processes
        processes = manager.list_processes()
        
        # Find root processes (parent_pid = 0 or 1)
        roots = [p for p in processes if p.parent_pid in (0, 1) or p.pid == 1]
        
        for root in roots[:10]:  # Limit to avoid huge output
            print_tree(root.pid)
            print()
    
    return 0


def _handle_watchdog(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Handle watchdog commands."""
    
    wcmd = getattr(args, 'watchdog_command', None)
    
    if not wcmd:
        print(f"{Colors.YELLOW}Usage: sysmind process watchdog [add|list|remove|start|alerts]{Colors.RESET}")
        return 1
    
    watchdog = ProcessWatchdog(database)
    
    if wcmd == 'add':
        from ..utils.validators import parse_size
        
        name = args.name
        cpu_limit = getattr(args, 'cpu_limit', None)
        memory_limit_str = getattr(args, 'memory_limit', None)
        action = getattr(args, 'action', 'log')
        
        memory_limit = None
        if memory_limit_str:
            memory_limit = parse_size(memory_limit_str)
        
        rule = watchdog.add_rule(
            process_name=name,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            action=action
        )
        
        print(f"{Colors.GREEN}Added watchdog rule:{Colors.RESET}")
        print(f"  ID: {rule.id}")
        print(f"  Process: {rule.process_name}")
        if cpu_limit:
            print(f"  CPU Limit: {cpu_limit}%")
        if memory_limit:
            print(f"  Memory Limit: {formatter.file_size(memory_limit)}")
        print(f"  Action: {action}")
    
    elif wcmd == 'list':
        rules = watchdog.list_rules()
        
        if not rules:
            print(f"{Colors.YELLOW}No watchdog rules configured.{Colors.RESET}")
            return 0
        
        print()
        print(formatter.box("Watchdog Rules", width=70))
        print()
        
        for rule in rules:
            status = f"{Colors.GREEN}active{Colors.RESET}" if rule.enabled else f"{Colors.YELLOW}disabled{Colors.RESET}"
            print(f"  {Colors.CYAN}{rule.id[:8]}{Colors.RESET} | {rule.process_name} | {status}")
            if rule.cpu_limit:
                print(f"    CPU Limit: {rule.cpu_limit}%")
            if rule.memory_limit:
                print(f"    Memory Limit: {formatter.file_size(rule.memory_limit)}")
            print(f"    Action: {rule.action}")
            print()
    
    elif wcmd == 'remove':
        rule_id = args.rule_id
        
        if watchdog.remove_rule(rule_id):
            print(f"{Colors.GREEN}Rule removed.{Colors.RESET}")
        else:
            print(f"{Colors.RED}Rule not found: {rule_id}{Colors.RESET}")
            return 1
    
    elif wcmd == 'start':
        interval = getattr(args, 'interval', 5.0)
        
        print(f"{Colors.CYAN}Starting watchdog monitoring (interval: {interval}s){Colors.RESET}")
        print("Press Ctrl+C to stop")
        print()
        
        def on_alert(alert):
            print(f"  {Colors.YELLOW}ALERT{Colors.RESET} [{alert.timestamp.strftime('%H:%M:%S')}]: {alert.message}")
        
        try:
            watchdog.start(interval=interval, callback=on_alert)
            
            # Keep running until interrupted
            import time
            while watchdog.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            watchdog.stop()
            print(f"\n{Colors.GREEN}Watchdog stopped.{Colors.RESET}")
    
    elif wcmd == 'alerts':
        limit = getattr(args, 'limit', 20)
        alerts = watchdog.get_alerts(limit=limit)
        
        if not alerts:
            print(f"{Colors.GREEN}No recent alerts.{Colors.RESET}")
            return 0
        
        print()
        print(formatter.box("Recent Alerts", width=70))
        print()
        
        for alert in alerts:
            severity_color = Colors.RED if alert.severity == 'critical' else Colors.YELLOW
            print(f"  {severity_color}●{Colors.RESET} [{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"    {alert.message}")
            print()
    
    return 0


def _handle_startup(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Handle startup commands."""
    
    scmd = getattr(args, 'startup_command', None)
    
    if not scmd:
        scmd = 'list'
    
    startup = StartupManager()
    
    if scmd == 'list':
        items = startup.list_startup_items()
        
        print()
        print(formatter.box("Startup Programs", width=70))
        print()
        
        if not items:
            print(f"  {Colors.YELLOW}No startup programs found.{Colors.RESET}")
        else:
            print(f"  Found {len(items)} startup programs")
            print()
            
            for item in items:
                status = f"{Colors.GREEN}enabled{Colors.RESET}" if item.enabled else f"{Colors.YELLOW}disabled{Colors.RESET}"
                print(f"  {Colors.CYAN}{item.name}{Colors.RESET} [{status}]")
                print(f"    Location: {item.location}")
                print(f"    Command: {item.command[:50]}...")
                print()
    
    elif scmd == 'disable':
        name = args.name
        
        if startup.disable_startup_item(name):
            print(f"{Colors.GREEN}Disabled startup item: {name}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Could not disable: {name}{Colors.RESET}")
            return 1
    
    elif scmd == 'enable':
        name = args.name
        
        if startup.enable_startup_item(name):
            print(f"{Colors.GREEN}Enabled startup item: {name}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Could not enable: {name}{Colors.RESET}")
            return 1
    
    elif scmd == 'analyze':
        analysis = startup.analyze_startup_impact()
        
        print()
        print(formatter.box("Startup Impact Analysis", width=70))
        print()
        
        print(f"  Total startup programs: {analysis['total_count']}")
        print(f"  Enabled: {analysis['enabled_count']}")
        print()
        
        if analysis['potentially_heavy']:
            print(f"  {Colors.YELLOW}Potentially Heavy Programs:{Colors.RESET}")
            for prog in analysis['potentially_heavy']:
                print(f"    - {prog}")
            print()
        
        if analysis['recommendations']:
            print(f"  {Colors.CYAN}Recommendations:{Colors.RESET}")
            for rec in analysis['recommendations']:
                print(f"    • {rec}")
            print()
    
    return 0
