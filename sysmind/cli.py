"""
SYSMIND CLI - Main Entry Point

System Intelligence & Automation CLI
A unified command-line utility for system monitoring, process management,
disk analytics, network diagnostics, and intelligent recommendations.
"""

import argparse
import sys
import os
from typing import Optional

# Add package to path if running directly
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sysmind.core.config import Config
from sysmind.core.database import Database
from sysmind.core.errors import SysmindError, ConfigurationError, DatabaseError
from sysmind.utils.logger import setup_logging, get_logger
from sysmind.utils.formatters import Colors

from sysmind.commands.monitor_commands import register_monitor_commands, handle_monitor_command
from sysmind.commands.disk_commands import register_disk_commands, handle_disk_command
from sysmind.commands.process_commands import register_process_commands, handle_process_command
from sysmind.commands.network_commands import register_network_commands, handle_network_command
from sysmind.commands.intel_commands import register_intel_commands, handle_intel_command
from sysmind.commands.config_commands import register_config_commands, handle_config_command


__version__ = '1.0.0'


BANNER = f"""
{Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                                 ║
║   ███████╗██╗   ██╗███████╗███╗   ███╗██╗███╗   ██╗██████╗     ║
║   ██╔════╝╚██╗ ██╔╝██╔════╝████╗ ████║██║████╗  ██║██╔══██╗    ║
║   ███████╗ ╚████╔╝ ███████╗██╔████╔██║██║██╔██╗ ██║██║  ██║    ║
║   ╚════██║  ╚██╔╝  ╚════██║██║╚██╔╝██║██║██║╚██╗██║██║  ██║    ║
║   ███████║   ██║   ███████║██║ ╚═╝ ██║██║██║ ╚████║██████╔╝    ║
║   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝     ║
║                                                                 ║
║           System Intelligence & Automation CLI v{__version__}            ║
╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    
    parser = argparse.ArgumentParser(
        prog='sysmind',
        description='SYSMIND - System Intelligence & Automation CLI',
        epilog='Run "sysmind <command> --help" for more information on a command.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version', '-V',
        action='version',
        version=f'SYSMIND v{__version__}'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -vv for debug)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to config file'
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='Available commands',
        metavar='<command>'
    )
    
    # Register all command modules
    register_monitor_commands(subparsers)
    register_disk_commands(subparsers)
    register_process_commands(subparsers)
    register_network_commands(subparsers)
    register_intel_commands(subparsers)
    register_config_commands(subparsers)
    
    # Quick commands
    quick = subparsers.add_parser('quick', help='Quick system overview')
    
    return parser


def show_quick_overview(database: Database) -> int:
    """Show quick system overview."""
    
    from sysmind.modules.intelligence.health import HealthScorer
    from sysmind.modules.monitor.realtime import RealtimeMonitor
    from sysmind.utils.formatters import Formatter
    
    formatter = Formatter()
    
    print()
    print(f"  {Colors.CYAN}Quick System Overview{Colors.RESET}")
    print()
    
    # Get snapshot
    realtime = RealtimeMonitor()
    snapshot = realtime.get_snapshot()
    
    cpu = snapshot.cpu_metrics
    mem = snapshot.memory_metrics
    
    # CPU
    cpu_color = Colors.GREEN if cpu.usage_percent < 70 else Colors.YELLOW if cpu.usage_percent < 90 else Colors.RED
    print(f"  CPU:    {formatter.progress_bar(cpu.usage_percent / 100, width=30)} {cpu_color}{cpu.usage_percent:5.1f}%{Colors.RESET}")
    
    # Memory
    mem_color = Colors.GREEN if mem.usage_percent < 70 else Colors.YELLOW if mem.usage_percent < 90 else Colors.RED
    print(f"  Memory: {formatter.progress_bar(mem.usage_percent / 100, width=30)} {mem_color}{mem.usage_percent:5.1f}%{Colors.RESET}")
    
    # Health score
    scorer = HealthScorer(database)
    health = scorer.calculate_health()
    
    score = health.overall_score
    if score >= 70:
        health_color = Colors.GREEN
    elif score >= 50:
        health_color = Colors.YELLOW
    else:
        health_color = Colors.RED
    
    print()
    print(f"  Health Score: {health_color}{score}/100{Colors.RESET} ({health.overall_status})")
    
    # Quick issues
    issues = []
    for comp in health.components.values():
        issues.extend(comp.issues)
    
    if issues:
        print()
        print(f"  {Colors.YELLOW}Issues:{Colors.RESET}")
        for issue in issues[:3]:
            print(f"    • {issue}")
    
    print()
    print(f"  Run '{Colors.CYAN}sysmind intel health{Colors.RESET}' for detailed analysis")
    print()
    
    return 0


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle no color
    if args.no_color or os.environ.get('NO_COLOR'):
        Colors.disable()
    
    # Setup logging
    log_level = 'WARNING'
    if args.verbose == 1:
        log_level = 'INFO'
    elif args.verbose >= 2:
        log_level = 'DEBUG'
    elif args.quiet:
        log_level = 'ERROR'
    
    setup_logging(log_level)
    logger = get_logger('sysmind')
    
    # Load config
    try:
        config = Config()
        config.ensure_directories()
    except ConfigurationError as e:
        print(f"{Colors.RED}Configuration error: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    # Initialize database
    try:
        database = Database(config.data_dir)
    except DatabaseError as e:
        print(f"{Colors.RED}Database error: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    # No command - show help or banner
    if not args.command:
        print(BANNER)
        parser.print_help()
        return 0
    
    # Route to command handlers
    try:
        if args.command == 'monitor':
            return handle_monitor_command(args, database)
        elif args.command == 'disk':
            return handle_disk_command(args, database)
        elif args.command == 'process':
            return handle_process_command(args, database)
        elif args.command == 'network':
            return handle_network_command(args, database)
        elif args.command == 'intel':
            return handle_intel_command(args, database)
        elif args.command == 'config':
            return handle_config_command(args, database)
        elif args.command == 'quick':
            return show_quick_overview(database)
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted.{Colors.RESET}")
        return 130
    
    except SysmindError as e:
        logger.error(f"Error: {e}")
        print(f"{Colors.RED}Error: {e}{Colors.RESET}", file=sys.stderr)
        return 1
    
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}", file=sys.stderr)
        if args.verbose >= 2:
            import traceback
            traceback.print_exc()
        return 1


def cli():
    """Entry point for console script."""
    sys.exit(main())


if __name__ == '__main__':
    cli()
