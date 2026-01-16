"""
SYSMIND Config CLI Commands

Command handlers for configuration management.
"""

import argparse
import json
from typing import Optional

from ..core.config import Config
from ..utils.formatters import Formatter, Colors
from ..utils.validators import validate_config_key
from ..core.database import Database


def register_config_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register config subcommands."""
    
    config = subparsers.add_parser(
        'config',
        help='Configuration management',
        description='View and modify SYSMIND configuration'
    )
    
    config_sub = config.add_subparsers(dest='config_command', help='Config commands')
    
    # Show command
    show = config_sub.add_parser('show', help='Show current configuration')
    show.add_argument('key', nargs='?', help='Specific key to show')
    show.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Get command
    get = config_sub.add_parser('get', help='Get a config value')
    get.add_argument('key', help='Configuration key')
    
    # Set command
    set_cmd = config_sub.add_parser('set', help='Set a config value')
    set_cmd.add_argument('key', help='Configuration key')
    set_cmd.add_argument('value', help='Value to set')
    
    # Reset command
    reset = config_sub.add_parser('reset', help='Reset configuration')
    reset.add_argument('--all', action='store_true', help='Reset all settings')
    reset.add_argument('key', nargs='?', help='Specific key to reset')
    
    # Path command
    path = config_sub.add_parser('path', help='Show config file path')
    
    # Export command
    export = config_sub.add_parser('export', help='Export configuration')
    export.add_argument('file', nargs='?', help='Output file (default: stdout)')
    
    # Import command
    import_cmd = config_sub.add_parser('import', help='Import configuration')
    import_cmd.add_argument('file', help='Input file')
    import_cmd.add_argument('--merge', action='store_true', help='Merge with existing')


def handle_config_command(args: argparse.Namespace, database: Database) -> int:
    """Handle config commands."""
    
    formatter = Formatter()
    config = Config()
    
    if not hasattr(args, 'config_command') or not args.config_command:
        return _handle_show(args, formatter, config)
    
    cmd = args.config_command
    
    if cmd == 'show':
        return _handle_show(args, formatter, config)
    elif cmd == 'get':
        return _handle_get(args, formatter, config)
    elif cmd == 'set':
        return _handle_set(args, formatter, config)
    elif cmd == 'reset':
        return _handle_reset(args, formatter, config)
    elif cmd == 'path':
        return _handle_path(args, formatter, config)
    elif cmd == 'export':
        return _handle_export(args, formatter, config)
    elif cmd == 'import':
        return _handle_import(args, formatter, config)
    else:
        print(f"{Colors.RED}Unknown config command: {cmd}{Colors.RESET}")
        return 1


def _handle_show(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Show configuration."""
    
    key = getattr(args, 'key', None)
    as_json = getattr(args, 'json', False)
    
    if key:
        value = config.get(key)
        if value is None:
            print(f"{Colors.YELLOW}Key not found: {key}{Colors.RESET}")
            return 1
        
        if as_json:
            print(json.dumps({key: value}, indent=2))
        else:
            print(f"{key} = {value}")
        return 0
    
    # Show all
    all_config = config.to_dict()
    
    if as_json:
        print(json.dumps(all_config, indent=2))
        return 0
    
    print()
    print(formatter.box("SYSMIND Configuration", width=60))
    print()
    
    def print_config(data: dict, prefix: str = ''):
        for k, v in sorted(data.items()):
            full_key = f"{prefix}.{k}" if prefix else k
            
            if isinstance(v, dict):
                print(f"  {Colors.CYAN}[{full_key}]{Colors.RESET}")
                print_config(v, full_key)
            else:
                value_str = str(v)
                if isinstance(v, bool):
                    value_str = f"{Colors.GREEN}true{Colors.RESET}" if v else f"{Colors.RED}false{Colors.RESET}"
                elif isinstance(v, (int, float)):
                    value_str = f"{Colors.YELLOW}{v}{Colors.RESET}"
                
                print(f"    {k}: {value_str}")
    
    print_config(all_config)
    print()
    
    return 0


def _handle_get(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Get a config value."""
    
    key = args.key
    
    if not validate_config_key(key):
        print(f"{Colors.RED}Invalid key format: {key}{Colors.RESET}")
        return 1
    
    value = config.get(key)
    
    if value is None:
        print(f"{Colors.YELLOW}Key not found: {key}{Colors.RESET}")
        return 1
    
    print(value)
    return 0


def _handle_set(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Set a config value."""
    
    key = args.key
    value_str = args.value
    
    if not validate_config_key(key):
        print(f"{Colors.RED}Invalid key format: {key}{Colors.RESET}")
        return 1
    
    # Try to parse the value
    value = value_str
    
    # Boolean
    if value_str.lower() in ('true', 'yes', 'on', '1'):
        value = True
    elif value_str.lower() in ('false', 'no', 'off', '0'):
        value = False
    # Integer
    elif value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
        value = int(value_str)
    # Float
    else:
        try:
            value = float(value_str)
        except ValueError:
            pass  # Keep as string
    
    try:
        config.set(key, value)
        config.save()
        print(f"{Colors.GREEN}Set {key} = {value}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error setting config: {e}{Colors.RESET}")
        return 1
    
    return 0


def _handle_reset(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Reset configuration."""
    
    reset_all = getattr(args, 'all', False)
    key = getattr(args, 'key', None)
    
    if reset_all:
        config.reset()
        config.save()
        print(f"{Colors.GREEN}All configuration reset to defaults.{Colors.RESET}")
        return 0
    
    if key:
        default = config.get_default(key)
        if default is None:
            print(f"{Colors.YELLOW}No default for key: {key}{Colors.RESET}")
            return 1
        
        config.set(key, default)
        config.save()
        print(f"{Colors.GREEN}Reset {key} to default: {default}{Colors.RESET}")
        return 0
    
    print(f"{Colors.YELLOW}Specify --all or a key to reset{Colors.RESET}")
    return 1


def _handle_path(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Show config file path."""
    
    print(config.config_path)
    return 0


def _handle_export(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Export configuration."""
    
    output_file = getattr(args, 'file', None)
    
    all_config = config.get_all()
    json_str = json.dumps(all_config, indent=2)
    
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(json_str)
            print(f"{Colors.GREEN}Configuration exported to: {output_file}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error writing file: {e}{Colors.RESET}")
            return 1
    else:
        print(json_str)
    
    return 0


def _handle_import(args: argparse.Namespace, formatter: Formatter, config: Config) -> int:
    """Import configuration."""
    
    input_file = args.file
    merge = getattr(args, 'merge', False)
    
    try:
        with open(input_file, 'r') as f:
            new_config = json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}File not found: {input_file}{Colors.RESET}")
        return 1
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}Invalid JSON: {e}{Colors.RESET}")
        return 1
    
    if not isinstance(new_config, dict):
        print(f"{Colors.RED}Configuration must be a JSON object{Colors.RESET}")
        return 1
    
    if merge:
        # Merge with existing
        def merge_dict(base: dict, update: dict):
            for k, v in update.items():
                if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                    merge_dict(base[k], v)
                else:
                    base[k] = v
        
        current = config.get_all()
        merge_dict(current, new_config)
        config._config = current
    else:
        config._config = new_config
    
    config.save()
    print(f"{Colors.GREEN}Configuration imported from: {input_file}{Colors.RESET}")
    
    return 0
