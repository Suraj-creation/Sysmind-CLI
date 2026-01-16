"""
SYSMIND Validators Module

Input validation utilities for CLI arguments and configuration.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple, Any, List

from ..core.errors import ValidationError


def validate_path(path: str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
    """
    Validate a file system path.
    
    Args:
        path: Path string to validate
        must_exist: If True, path must exist
        must_be_dir: If True, path must be a directory
    
    Returns:
        Validated Path object
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        expanded = os.path.expanduser(path)
        resolved = Path(expanded).resolve()
        
        if must_exist and not resolved.exists():
            raise ValidationError(f"Path does not exist: {path}", field="path")
        
        if must_be_dir and resolved.exists() and not resolved.is_dir():
            raise ValidationError(f"Path is not a directory: {path}", field="path")
        
        return resolved
    except (OSError, ValueError) as e:
        raise ValidationError(f"Invalid path: {path} - {e}", field="path")


def validate_positive_int(value: Any, field_name: str = "value") -> int:
    """
    Validate that value is a positive integer.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated integer
    """
    try:
        int_val = int(value)
        if int_val <= 0:
            raise ValidationError(f"{field_name} must be positive", field=field_name)
        return int_val
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be an integer", field=field_name)


def validate_percentage(value: Any, field_name: str = "percentage") -> float:
    """
    Validate that value is a percentage (0-100).
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated float percentage
    """
    try:
        float_val = float(value)
        if float_val < 0 or float_val > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100", field=field_name)
        return float_val
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a number", field=field_name)


def parse_size(size_str: str) -> int:
    """
    Parse a size string to bytes.
    
    Supports: B, KB, MB, GB, TB (case-insensitive)
    Examples: "1MB", "500KB", "2GB"
    
    Args:
        size_str: Size string to parse
    
    Returns:
        Size in bytes
    """
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    size_str = size_str.strip().upper()
    
    # Match number and optional unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([A-Z]{1,2})?$', size_str)
    
    if not match:
        raise ValidationError(f"Invalid size format: {size_str}", field="size")
    
    number = float(match.group(1))
    unit = match.group(2) or 'B'
    
    if unit not in units:
        raise ValidationError(f"Unknown size unit: {unit}", field="size")
    
    return int(number * units[unit])


def format_size(bytes_val: int) -> str:
    """
    Format bytes to human-readable size string.
    
    Args:
        bytes_val: Size in bytes
    
    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string to seconds.
    
    Supports: s (seconds), m (minutes), h (hours), d (days)
    Examples: "30s", "5m", "2h", "7d"
    
    Args:
        duration_str: Duration string to parse
    
    Returns:
        Duration in seconds
    """
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    duration_str = duration_str.strip().lower()
    
    # Match number and unit
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([smhd])$', duration_str)
    
    if not match:
        raise ValidationError(f"Invalid duration format: {duration_str}", field="duration")
    
    number = float(match.group(1))
    unit = match.group(2)
    
    return int(number * units[unit])


def format_duration(seconds: float) -> str:
    """
    Format seconds to human-readable duration.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    else:
        return f"{seconds / 86400:.1f}d"


def validate_process_pattern(pattern: str) -> str:
    """
    Validate a process name pattern.
    
    Supports wildcards: * (any characters), ? (single character)
    
    Args:
        pattern: Process name pattern
    
    Returns:
        Validated pattern
    """
    if not pattern:
        raise ValidationError("Process pattern cannot be empty", field="pattern")
    
    # Convert wildcards to regex for validation
    # Just check it doesn't have invalid characters
    invalid_chars = ['/', '\\', ':', '<', '>', '|', '"']
    for char in invalid_chars:
        if char in pattern:
            raise ValidationError(f"Invalid character in pattern: {char}", field="pattern")
    
    return pattern


def pattern_to_regex(pattern: str) -> re.Pattern:
    """
    Convert a wildcard pattern to regex.
    
    Args:
        pattern: Pattern with wildcards (* and ?)
    
    Returns:
        Compiled regex pattern
    """
    # Escape special regex characters except * and ?
    escaped = re.escape(pattern)
    # Convert wildcards
    escaped = escaped.replace(r'\*', '.*')
    escaped = escaped.replace(r'\?', '.')
    return re.compile(f'^{escaped}$', re.IGNORECASE)


def validate_config_key(key: str) -> Tuple[str, str]:
    """
    Validate and parse a configuration key in dot notation.
    
    Args:
        key: Configuration key (e.g., "monitor.snapshot_interval_seconds")
    
    Returns:
        Tuple of (section, setting)
    """
    parts = key.split('.')
    
    if len(parts) != 2:
        raise ValidationError(
            f"Invalid config key format: {key}. Use 'section.setting' format.",
            field="key"
        )
    
    valid_sections = ['general', 'monitor', 'disk', 'process', 'network']
    section = parts[0]
    
    if section not in valid_sections:
        raise ValidationError(
            f"Unknown config section: {section}. Valid: {', '.join(valid_sections)}",
            field="key"
        )
    
    return section, parts[1]


def validate_severity(severity: str) -> str:
    """
    Validate a severity level.
    
    Args:
        severity: Severity string
    
    Returns:
        Normalized severity string (uppercase)
    """
    valid = ['INFO', 'WARNING', 'CRITICAL']
    severity = severity.upper()
    
    if severity not in valid:
        raise ValidationError(
            f"Invalid severity: {severity}. Valid: {', '.join(valid)}",
            field="severity"
        )
    
    return severity


def validate_action(action: str) -> str:
    """
    Validate a watchdog action.
    
    Args:
        action: Action string
    
    Returns:
        Validated action string
    """
    valid = ['alert', 'log', 'kill', 'notify']
    action = action.lower()
    
    if action not in valid:
        raise ValidationError(
            f"Invalid action: {action}. Valid: {', '.join(valid)}",
            field="action"
        )
    
    return action


def validate_sort_field(field: str, valid_fields: List[str]) -> str:
    """
    Validate a sort field.
    
    Args:
        field: Field name to sort by
        valid_fields: List of valid field names
    
    Returns:
        Validated field name
    """
    field = field.lower()
    
    if field not in valid_fields:
        raise ValidationError(
            f"Invalid sort field: {field}. Valid: {', '.join(valid_fields)}",
            field="sort"
        )
    
    return field
