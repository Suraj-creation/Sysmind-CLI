"""
SYSMIND Formatters Module

Output formatting utilities for tables, progress bars, and colored output.
Supports multiple output formats: table, JSON, plain text.
"""

import json
import os
import sys
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class OutputFormat(Enum):
    """Supported output formats."""
    TABLE = "table"
    JSON = "json"
    PLAIN = "plain"


class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get('NO_COLOR'):
        return False
    if not hasattr(sys.stdout, 'isatty'):
        return False
    if not sys.stdout.isatty():
        return False
    if os.name == 'nt':
        # Windows 10+ supports ANSI colors
        return True
    return True


class Formatter:
    """
    Unified output formatting for SYSMIND CLI.
    
    Provides consistent formatting for tables, progress bars,
    health indicators, and other visual elements.
    """
    
    def __init__(self, output_format: OutputFormat = OutputFormat.TABLE, use_color: bool = True):
        self.format = output_format
        self.use_color = use_color and supports_color()
    
    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text
    
    def bold(self, text: str) -> str:
        """Make text bold."""
        return self.colorize(text, Colors.BOLD)
    
    def success(self, text: str) -> str:
        """Format success text (green)."""
        return self.colorize(text, Colors.GREEN)
    
    def error(self, text: str) -> str:
        """Format error text (red)."""
        return self.colorize(text, Colors.BRIGHT_RED)
    
    def warning(self, text: str) -> str:
        """Format warning text (yellow)."""
        return self.colorize(text, Colors.YELLOW)
    
    def info(self, text: str) -> str:
        """Format info text (cyan)."""
        return self.colorize(text, Colors.CYAN)
    
    def dim(self, text: str) -> str:
        """Format dimmed text."""
        return self.colorize(text, Colors.DIM)
    
    def table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        title: Optional[str] = None,
        alignments: Optional[List[str]] = None
    ) -> str:
        """
        Format data as an ASCII table.
        
        Args:
            headers: Column headers
            rows: List of rows (each row is a list of values)
            title: Optional table title
            alignments: List of alignments ('left', 'right', 'center') per column
        """
        if self.format == OutputFormat.JSON:
            return self._to_json(headers, rows)
        
        if not rows:
            return "No data to display."
        
        # Calculate column widths
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Default alignments
        if not alignments:
            alignments = ['left'] * len(headers)
        
        lines = []
        total_width = sum(widths) + 3 * len(widths) + 1
        
        # Top border
        lines.append("╔" + "╤".join("═" * (w + 2) for w in widths) + "╗")
        
        # Title
        if title:
            title_line = "║" + self.bold(title.center(total_width - 2)) + "║"
            lines.append(title_line)
            lines.append("╠" + "╪".join("═" * (w + 2) for w in widths) + "╣")
        
        # Headers
        header_cells = []
        for i, (h, w) in enumerate(zip(headers, widths)):
            header_cells.append(" " + self.bold(str(h).center(w)) + " ")
        lines.append("║" + "│".join(header_cells) + "║")
        lines.append("╠" + "╪".join("═" * (w + 2) for w in widths) + "╣")
        
        # Data rows
        for row in rows:
            row_cells = []
            for i, (cell, w) in enumerate(zip(row, widths)):
                cell_str = str(cell)
                if alignments[i] == 'right':
                    row_cells.append(" " + cell_str.rjust(w) + " ")
                elif alignments[i] == 'center':
                    row_cells.append(" " + cell_str.center(w) + " ")
                else:
                    row_cells.append(" " + cell_str.ljust(w) + " ")
            lines.append("║" + "│".join(row_cells) + "║")
        
        # Bottom border
        lines.append("╚" + "╧".join("═" * (w + 2) for w in widths) + "╝")
        
        return "\n".join(lines)
    
    def simple_table(
        self,
        headers: List[str],
        rows: List[List[Any]]
    ) -> str:
        """Format a simple table without fancy borders."""
        if self.format == OutputFormat.JSON:
            return self._to_json(headers, rows)
        
        if not rows:
            return "No data to display."
        
        # Calculate widths
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        lines = []
        
        # Header
        header_line = "  ".join(self.bold(str(h).ljust(w)) for h, w in zip(headers, widths))
        lines.append(header_line)
        lines.append("─" * len(header_line))
        
        # Rows
        for row in rows:
            line = "  ".join(str(c).ljust(w) for c, w in zip(row, widths))
            lines.append(line)
        
        return "\n".join(lines)
    
    def _to_json(self, headers: List[str], rows: List[List[Any]]) -> str:
        """Convert table data to JSON."""
        data = [dict(zip(headers, row)) for row in rows]
        return json.dumps(data, indent=2, default=str)
    
    def progress_bar(
        self,
        value: float,
        max_value: float = 100,
        width: int = 20,
        label: str = "",
        show_percent: bool = True
    ) -> str:
        """
        Render a progress bar.
        
        Args:
            value: Current value
            max_value: Maximum value
            width: Bar width in characters
            label: Label to show before the bar
            show_percent: Whether to show percentage after the bar
        """
        percent = min((value / max_value) * 100, 100) if max_value > 0 else 0
        filled = int(width * value / max_value) if max_value > 0 else 0
        empty = width - filled
        
        # Color based on percentage
        if percent >= 90:
            color = Colors.BRIGHT_RED
        elif percent >= 70:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        
        bar = self.colorize("█" * filled, color) + self.dim("░" * empty)
        
        result = f"{label:20} {bar}"
        if show_percent:
            result += f" {percent:5.1f}%"
        
        return result
    
    def health_indicator(self, score: int) -> str:
        """Render health score with emoji indicator."""
        if score >= 90:
            return f"🟢 {score}/100 {self.success('Excellent')}"
        elif score >= 70:
            return f"🟡 {score}/100 {self.colorize('Good', Colors.BRIGHT_GREEN)}"
        elif score >= 50:
            return f"🟠 {score}/100 {self.warning('Fair')}"
        elif score >= 25:
            return f"🔴 {score}/100 {self.error('Poor')}"
        else:
            return f"⚫ {score}/100 {self.error('Critical')}"
    
    def severity_badge(self, severity: str) -> str:
        """Format a severity badge."""
        severity = severity.upper()
        if severity == "CRITICAL":
            return self.colorize(f"[{severity}]", Colors.BRIGHT_RED)
        elif severity == "WARNING":
            return self.colorize(f"[{severity}]", Colors.YELLOW)
        elif severity == "INFO":
            return self.colorize(f"[{severity}]", Colors.CYAN)
        else:
            return f"[{severity}]"
    
    def status_icon(self, status: str) -> str:
        """Get status icon."""
        status = status.lower()
        icons = {
            'success': self.success("✓"),
            'ok': self.success("✓"),
            'running': self.info("●"),
            'warning': self.warning("⚠"),
            'error': self.error("✗"),
            'critical': self.error("✗"),
            'pending': self.dim("○"),
            'unknown': self.dim("?"),
        }
        return icons.get(status, "•")
    
    def file_size(self, bytes_val: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(bytes_val) < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"
    
    def duration(self, seconds: float) -> str:
        """Format seconds to human-readable duration."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"
    
    def timestamp(self, dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime."""
        if dt is None:
            dt = datetime.now()
        return dt.strftime(format_str)
    
    def header(self, text: str, width: int = 60) -> str:
        """Format a section header."""
        padding = (width - len(text) - 2) // 2
        line = "═" * width
        return f"\n{line}\n{'═' * padding} {self.bold(text)} {'═' * padding}\n{line}"
    
    def box(self, content: str, title: Optional[str] = None, width: int = 60) -> str:
        """Draw a box around content."""
        lines = content.split('\n')
        max_line = max(len(line) for line in lines) if lines else 0
        box_width = max(width, max_line + 4)
        
        result = []
        
        # Top border
        if title:
            title_str = f" {title} "
            left_pad = (box_width - len(title_str) - 2) // 2
            right_pad = box_width - len(title_str) - left_pad - 2
            result.append("╔" + "═" * left_pad + title_str + "═" * right_pad + "╗")
        else:
            result.append("╔" + "═" * (box_width - 2) + "╗")
        
        # Content
        for line in lines:
            padding = box_width - len(line) - 4
            result.append("║ " + line + " " * padding + " ║")
        
        # Bottom border
        result.append("╚" + "═" * (box_width - 2) + "╝")
        
        return "\n".join(result)
    
    def key_value(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Format key-value pairs."""
        lines = []
        prefix = "  " * indent
        max_key_len = max(len(str(k)) for k in data.keys()) if data else 0
        
        for key, value in data.items():
            key_str = self.bold(str(key).ljust(max_key_len))
            lines.append(f"{prefix}{key_str} : {value}")
        
        return "\n".join(lines)
    
    def list_items(self, items: List[str], bullet: str = "•", indent: int = 0) -> str:
        """Format a bulleted list."""
        prefix = "  " * indent
        return "\n".join(f"{prefix}{bullet} {item}" for item in items)
    
    def tree(self, data: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
        """Format data as a tree structure."""
        lines = []
        
        items = list(data.items()) if isinstance(data, dict) else []
        
        for i, (key, value) in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # Current item prefix
            if prefix:
                connector = "└── " if is_last_item else "├── "
            else:
                connector = ""
            
            if isinstance(value, dict):
                lines.append(f"{prefix}{connector}{self.bold(key)}/")
                # Recurse with updated prefix
                new_prefix = prefix + ("    " if is_last_item else "│   ")
                lines.append(self.tree(value, new_prefix, is_last_item))
            else:
                lines.append(f"{prefix}{connector}{key}: {value}")
        
        return "\n".join(lines)


# Global formatter instance
_default_formatter: Optional[Formatter] = None


def get_formatter() -> Formatter:
    """Get the default formatter instance."""
    global _default_formatter
    if _default_formatter is None:
        _default_formatter = Formatter()
    return _default_formatter


def set_formatter(formatter: Formatter) -> None:
    """Set the default formatter instance."""
    global _default_formatter
    _default_formatter = formatter
