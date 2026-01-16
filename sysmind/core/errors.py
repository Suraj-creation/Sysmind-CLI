"""
SYSMIND Error Classes

Comprehensive error handling hierarchy for the SYSMIND CLI.
All custom exceptions inherit from SysmindError base class.
"""

from typing import List, Optional


class SysmindError(Exception):
    """Base exception for all sysmind errors."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None, 
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "SYSMIND_ERROR"
        self.suggestions = suggestions or []
    
    def to_user_message(self) -> str:
        """Format error message for user display."""
        msg = f"❌ Error [{self.code}]: {self.message}"
        if self.suggestions:
            msg += "\n\n💡 Suggestions:"
            for suggestion in self.suggestions:
                msg += f"\n   • {suggestion}"
        return msg
    
    def __str__(self) -> str:
        return self.message


class ConfigurationError(SysmindError):
    """Configuration file or settings errors."""
    
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        default_suggestions = [
            "Check your configuration file at ~/.sysmind/config.json",
            "Run 'sysmind config reset' to restore defaults"
        ]
        super().__init__(
            message, 
            code="CONFIG_ERROR",
            suggestions=suggestions or default_suggestions
        )


class PermissionError(SysmindError):
    """Insufficient permissions to perform operation."""
    
    def __init__(self, message: str, path: Optional[str] = None):
        suggestions = [
            "Try running with administrator/sudo privileges",
            "Check file/folder permissions"
        ]
        if path:
            suggestions.append(f"Verify you have access to: {path}")
        super().__init__(message, code="PERMISSION_DENIED", suggestions=suggestions)


class ResourceNotFoundError(SysmindError):
    """Requested resource (file, process, etc.) not found."""
    
    def __init__(self, message: str, resource_type: str = "resource"):
        suggestions = [
            f"Check if the {resource_type} exists",
            "Verify the path or identifier is correct",
            "Use absolute paths instead of relative paths"
        ]
        super().__init__(message, code="NOT_FOUND", suggestions=suggestions)


class DatabaseError(SysmindError):
    """Database operation errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        suggestions = [
            "Check if the database file is accessible",
            "Run 'sysmind doctor' to check database integrity",
            "Try removing ~/.sysmind/sysmind.db and restarting"
        ]
        if operation:
            message = f"Database {operation} failed: {message}"
        super().__init__(message, code="DATABASE_ERROR", suggestions=suggestions)


class NetworkError(SysmindError):
    """Network connectivity or operation errors."""
    
    def __init__(self, message: str, host: Optional[str] = None):
        suggestions = [
            "Check your internet connection",
            "Verify firewall settings"
        ]
        if host:
            suggestions.append(f"Ensure {host} is reachable")
        super().__init__(message, code="NETWORK_ERROR", suggestions=suggestions)


class ValidationError(SysmindError):
    """Input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        suggestions = ["Check the input format and try again"]
        if field:
            suggestions.insert(0, f"Invalid value for '{field}'")
        super().__init__(message, code="VALIDATION_ERROR", suggestions=suggestions)


class ProcessError(SysmindError):
    """Process operation errors."""
    
    def __init__(self, message: str, pid: Optional[int] = None):
        suggestions = [
            "The process may have already terminated",
            "Check if you have permission to manage this process"
        ]
        if pid:
            suggestions.append(f"Verify process {pid} exists with 'sysmind process list'")
        super().__init__(message, code="PROCESS_ERROR", suggestions=suggestions)


class DiskError(SysmindError):
    """Disk operation errors."""
    
    def __init__(self, message: str, path: Optional[str] = None):
        suggestions = [
            "Check if you have sufficient disk space",
            "Verify the path is accessible"
        ]
        if path:
            suggestions.append(f"Check path: {path}")
        super().__init__(message, code="DISK_ERROR", suggestions=suggestions)


class QuarantineError(SysmindError):
    """Quarantine operation errors."""
    
    def __init__(self, message: str):
        suggestions = [
            "Run 'sysmind disk quarantine list' to see quarantined items",
            "Check the quarantine directory permissions"
        ]
        super().__init__(message, code="QUARANTINE_ERROR", suggestions=suggestions)
