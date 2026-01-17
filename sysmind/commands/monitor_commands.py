"""
SYSMIND Monitor CLI Commands

Command handlers for system monitoring.
"""

import argparse
import time
from typing import Optional

from ..modules.monitor.cpu import CPUMonitor
from ..modules.monitor.memory import MemoryMonitor
from ..modules.monitor.realtime import RealtimeMonitor
from ..modules.monitor.baseline import BaselineManager
from ..utils.formatters import Formatter, Colors
from ..core.database import Database


def register_monitor_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register monitor subcommands."""
    
    monitor = subparsers.add_parser(
        'monitor',
        help='System resource monitoring',
        description='Monitor CPU, memory, and system resources'
    )
    
    monitor_sub = monitor.add_subparsers(dest='monitor_command', help='Monitor commands')
    
    # Status command
    status = monitor_sub.add_parser('status', help='Show current system status')
    status.add_argument('--json', action='store_true', help='Output as JSON')
    
    # CPU command
    cpu = monitor_sub.add_parser('cpu', help='Show CPU metrics')
    cpu.add_argument('--cores', action='store_true', help='Show per-core usage')
    cpu.add_argument('--watch', action='store_true', help='Continuously update')
    cpu.add_argument('--interval', type=float, default=1.0, help='Update interval in seconds')
    
    # Memory command
    memory = monitor_sub.add_parser('memory', help='Show memory metrics')
    memory.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    memory.add_argument('--watch', action='store_true', help='Continuously update')
    
    # Dashboard command
    dashboard = monitor_sub.add_parser('dashboard', help='Real-time monitoring dashboard')
    dashboard.add_argument('--interval', type=float, default=1.0, help='Update interval')
    dashboard.add_argument('--duration', type=int, help='Duration in seconds (default: indefinite)')
    
    # Baseline commands
    baseline = monitor_sub.add_parser('baseline', help='Baseline management')
    baseline_sub = baseline.add_subparsers(dest='baseline_command', help='Baseline commands')
    
    baseline_create = baseline_sub.add_parser('create', help='Create a new baseline')
    baseline_create.add_argument('name', help='Baseline name')
    baseline_create.add_argument('--samples', type=int, default=60, help='Number of samples')
    baseline_create.add_argument('--interval', type=float, default=1.0, help='Sample interval')
    
    baseline_compare = baseline_sub.add_parser('compare', help='Compare current state to baseline')
    baseline_compare.add_argument('name', help='Baseline name to compare against')
    
    baseline_list = baseline_sub.add_parser('list', help='List all baselines')
    
    baseline_delete = baseline_sub.add_parser('delete', help='Delete a baseline')
    baseline_delete.add_argument('name', help='Baseline name to delete')


def handle_monitor_command(args: argparse.Namespace, database: Database) -> int:
    """Handle monitor commands."""
    
    formatter = Formatter()
    
    if not hasattr(args, 'monitor_command') or not args.monitor_command:
        # Default to status
        return _handle_status(args, formatter, database)
    
    cmd = args.monitor_command
    
    if cmd == 'status':
        return _handle_status(args, formatter, database)
    elif cmd == 'cpu':
        return _handle_cpu(args, formatter, database)
    elif cmd == 'memory':
        return _handle_memory(args, formatter, database)
    elif cmd == 'dashboard':
        return _handle_dashboard(args, formatter, database)
    elif cmd == 'baseline':
        return _handle_baseline(args, formatter, database)
    else:
        print(f"{Colors.RED}Unknown monitor command: {cmd}{Colors.RESET}")
        return 1
    
    return 0


def _handle_status(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show current system status."""
    
    realtime = RealtimeMonitor()
    snapshot = realtime.get_snapshot()
    
    cpu = snapshot.cpu_metrics
    mem = snapshot.memory_metrics
    
    print()
    print(formatter.box("System Status", width=60))
    print()
    
    # CPU section
    cpu_color = Colors.GREEN if cpu.usage_percent < 70 else Colors.YELLOW if cpu.usage_percent < 90 else Colors.RED
    print(f"  {Colors.CYAN}CPU{Colors.RESET}")
    print(f"    Usage: {cpu_color}{cpu.usage_percent:.1f}%{Colors.RESET}")
    print(f"    {formatter.progress_bar(cpu.usage_percent / 100, width=40)}")
    print(f"    Cores: {cpu.core_count} | Load: {cpu.load_average[0]:.2f}, {cpu.load_average[1]:.2f}, {cpu.load_average[2]:.2f}")
    print()
    
    # Memory section
    mem_color = Colors.GREEN if mem.usage_percent < 70 else Colors.YELLOW if mem.usage_percent < 90 else Colors.RED
    print(f"  {Colors.CYAN}Memory{Colors.RESET}")
    print(f"    Usage: {mem_color}{mem.usage_percent:.1f}%{Colors.RESET}")
    print(f"    {formatter.progress_bar(mem.usage_percent / 100, width=40)}")
    print(f"    Used: {formatter.file_size(mem.used)} / Total: {formatter.file_size(mem.total)}")
    print(f"    Available: {formatter.file_size(mem.available)}")
    
    if mem.swap_total > 0:
        swap_color = Colors.GREEN if mem.swap_percent < 50 else Colors.YELLOW
        print(f"    Swap: {swap_color}{mem.swap_percent:.1f}%{Colors.RESET} ({formatter.file_size(mem.swap_used)} / {formatter.file_size(mem.swap_total)})")
    
    print()
    
    # Health indicator - calculate simple health score
    health_score = int(100 - (cpu.usage_percent * 0.4 + mem.usage_percent * 0.6))
    health_score = max(0, min(100, health_score))
    health = formatter.health_indicator(health_score)
    print(f"  {Colors.CYAN}Overall Health:{Colors.RESET} {health}")
    print()
    
    return 0


def _handle_cpu(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show CPU metrics."""
    
    cpu_monitor = CPUMonitor()
    
    def show_cpu():
        usage = cpu_monitor.get_usage_percent()
        load = cpu_monitor.get_load_average()
        cores = cpu_monitor.get_core_count()
        
        print(f"\r{Colors.CYAN}CPU:{Colors.RESET} {usage:5.1f}% | ", end='')
        print(f"Load: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f} | ", end='')
        print(f"Cores: {cores}", end='')
        
        if hasattr(args, 'cores') and args.cores:
            core_usages = cpu_monitor.get_core_usages()
            print()
            for i, core_usage in enumerate(core_usages):
                bar = formatter.progress_bar(core_usage / 100, width=20)
                print(f"  Core {i}: {bar} {core_usage:5.1f}%")
        else:
            print()
    
    if hasattr(args, 'watch') and args.watch:
        interval = getattr(args, 'interval', 1.0)
        try:
            while True:
                show_cpu()
                time.sleep(interval)
        except KeyboardInterrupt:
            print()
    else:
        show_cpu()
    
    return 0


def _handle_memory(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show memory metrics."""
    
    mem_monitor = MemoryMonitor()
    
    def show_memory():
        metrics = mem_monitor.get_metrics()
        
        print()
        print(formatter.box("Memory Usage", width=50))
        print()
        print(f"  Total:     {formatter.file_size(metrics.total):>12}")
        print(f"  Used:      {formatter.file_size(metrics.used):>12} ({metrics.usage_percent:.1f}%)")
        print(f"  Available: {formatter.file_size(metrics.available):>12}")
        print(f"  Free:      {formatter.file_size(metrics.free):>12}")
        
        if hasattr(args, 'detailed') and args.detailed:
            print()
            print(f"  Buffers:   {formatter.file_size(metrics.buffers):>12}")
            print(f"  Cached:    {formatter.file_size(metrics.cached):>12}")
        
        if metrics.swap_total > 0:
            print()
            print(f"  {Colors.CYAN}Swap{Colors.RESET}")
            print(f"  Total:     {formatter.file_size(metrics.swap_total):>12}")
            print(f"  Used:      {formatter.file_size(metrics.swap_used):>12} ({metrics.swap_percent:.1f}%)")
            print(f"  Free:      {formatter.file_size(metrics.swap_free):>12}")
        
        print()
    
    if hasattr(args, 'watch') and args.watch:
        try:
            while True:
                # Clear screen
                print('\033[2J\033[H', end='')
                show_memory()
                time.sleep(1)
        except KeyboardInterrupt:
            print()
    else:
        show_memory()
    
    return 0


def _handle_dashboard(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Run real-time dashboard."""
    
    interval = getattr(args, 'interval', 1.0)
    duration = getattr(args, 'duration', None)
    realtime = RealtimeMonitor(interval=interval)
    
    try:
        realtime.run_dashboard(duration=duration, formatter=formatter)
    except KeyboardInterrupt:
        pass
    
    return 0


def _handle_baseline(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Handle baseline commands."""
    
    baseline_cmd = getattr(args, 'baseline_command', None)
    
    if not baseline_cmd:
        print(f"{Colors.YELLOW}Usage: sysmind monitor baseline [create|compare|list|delete]{Colors.RESET}")
        return 1
    
    baseline_mgr = BaselineManager(database)
    
    if baseline_cmd == 'create':
        name = args.name
        samples = getattr(args, 'samples', 60)
        interval = getattr(args, 'interval', 1.0)
        
        print(f"{Colors.CYAN}Creating baseline '{name}' with {samples} samples...{Colors.RESET}")
        print(f"This will take approximately {samples * interval:.0f} seconds.")
        print()
        
        try:
            baseline = baseline_mgr.create_baseline(name, samples=samples, interval=interval)
            
            print()
            print(f"{Colors.GREEN}Baseline '{name}' created successfully!{Colors.RESET}")
            print()
            print(f"  CPU Average: {baseline.cpu_avg:.1f}% (±{baseline.cpu_std:.1f}%)")
            print(f"  Memory Average: {baseline.memory_avg:.1f}% (±{baseline.memory_std:.1f}%)")
            print(f"  Load Average: {baseline.load_avg:.2f} (±{baseline.load_std:.2f})")
            print()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Baseline creation cancelled.{Colors.RESET}")
            return 1
    
    elif baseline_cmd == 'compare':
        name = args.name
        
        baseline = baseline_mgr.load_baseline(name)
        if not baseline:
            print(f"{Colors.RED}Baseline '{name}' not found.{Colors.RESET}")
            return 1
        
        comparison = baseline_mgr.compare_to_baseline(baseline)
        
        print()
        print(formatter.box(f"Comparison to '{name}'", width=60))
        print()
        
        # CPU comparison
        cpu_color = Colors.GREEN if abs(comparison.cpu_deviation) < 1 else Colors.YELLOW if abs(comparison.cpu_deviation) < 2 else Colors.RED
        cpu_dir = "▲" if comparison.cpu_deviation > 0 else "▼" if comparison.cpu_deviation < 0 else "="
        print(f"  {Colors.CYAN}CPU{Colors.RESET}")
        print(f"    Baseline: {baseline.cpu_avg:.1f}% | Current: {comparison.cpu_deviation * baseline.cpu_std + baseline.cpu_avg:.1f}%")
        print(f"    Deviation: {cpu_color}{cpu_dir} {abs(comparison.cpu_deviation):.1f}σ{Colors.RESET}")
        print()
        
        # Memory comparison
        mem_color = Colors.GREEN if abs(comparison.memory_deviation) < 1 else Colors.YELLOW if abs(comparison.memory_deviation) < 2 else Colors.RED
        mem_dir = "▲" if comparison.memory_deviation > 0 else "▼" if comparison.memory_deviation < 0 else "="
        print(f"  {Colors.CYAN}Memory{Colors.RESET}")
        print(f"    Baseline: {baseline.memory_avg:.1f}% | Current: {comparison.memory_deviation * baseline.memory_std + baseline.memory_avg:.1f}%")
        print(f"    Deviation: {mem_color}{mem_dir} {abs(comparison.memory_deviation):.1f}σ{Colors.RESET}")
        print()
        
        # Status
        if comparison.is_anomaly:
            print(f"  {Colors.RED}⚠ Anomaly detected - system behavior differs significantly from baseline{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ System behavior is within normal range{Colors.RESET}")
        print()
    
    elif baseline_cmd == 'list':
        baselines = baseline_mgr.list_baselines()
        
        if not baselines:
            print(f"{Colors.YELLOW}No baselines found.{Colors.RESET}")
            return 0
        
        print()
        print(formatter.box("Saved Baselines", width=60))
        print()
        
        headers = ['Name', 'Created', 'Samples', 'CPU Avg', 'Mem Avg']
        rows = []
        
        for b in baselines:
            rows.append([
                b.name,
                b.created.strftime('%Y-%m-%d %H:%M'),
                str(b.sample_count),
                f"{b.cpu_avg:.1f}%",
                f"{b.memory_avg:.1f}%"
            ])
        
        print(formatter.table(headers, rows))
        print()
    
    elif baseline_cmd == 'delete':
        name = args.name
        
        if baseline_mgr.delete_baseline(name):
            print(f"{Colors.GREEN}Baseline '{name}' deleted.{Colors.RESET}")
        else:
            print(f"{Colors.RED}Baseline '{name}' not found.{Colors.RESET}")
            return 1
    
    return 0
