"""
SYSMIND Configuration Management

Handles loading, saving, and managing application configuration.
Uses JSON format for human-readable configuration files.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path

from .errors import ConfigurationError


@dataclass
class MonitorConfig:
    """Monitor module configuration."""
    snapshot_interval_seconds: int = 300
    history_retention_days: int = 30
    baseline_sample_hours: int = 48
    alert_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "cpu_warning": 80,
        "cpu_critical": 95,
        "memory_warning": 85,
        "memory_critical": 95,
        "disk_warning": 80,
        "disk_critical": 90
    })


@dataclass
class DiskConfig:
    """Disk module configuration."""
    default_scan_paths: List[str] = field(default_factory=lambda: ["~"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules",
        ".git",
        "__pycache__",
        "*.pyc",
        ".venv",
        "venv"
    ])
    min_duplicate_size_mb: int = 1
    quarantine_retention_days: int = 30
    safe_clean_targets: List[str] = field(default_factory=lambda: [
        "temp_files",
        "browser_cache",
        "old_logs"
    ])


@dataclass
class ProcessConfig:
    """Process module configuration."""
    refresh_interval_seconds: int = 5
    protected_processes: List[str] = field(default_factory=lambda: [
        "System",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "winlogon.exe"
    ])
    watchdog_check_interval_seconds: int = 30


@dataclass
class NetworkConfig:
    """Network module configuration."""
    test_hosts: List[str] = field(default_factory=lambda: [
        "8.8.8.8",
        "1.1.1.1",
        "google.com"
    ])
    bandwidth_sample_seconds: int = 1
    connection_refresh_seconds: int = 10
    timeout_seconds: int = 5


@dataclass
class GeneralConfig:
    """General application configuration."""
    data_dir: str = "~/.sysmind"
    log_level: str = "INFO"
    color_output: bool = True
    date_format: str = "%Y-%m-%d %H:%M:%S"


class Config:
    """
    Main configuration class for SYSMIND.
    
    Manages all configuration settings with defaults and persistence.
    """
    
    DEFAULT_CONFIG_FILENAME = "config.json"
    
    def __init__(self):
        self.general = GeneralConfig()
        self.monitor = MonitorConfig()
        self.disk = DiskConfig()
        self.process = ProcessConfig()
        self.network = NetworkConfig()
        self._config_path: Optional[Path] = None
    
    @property
    def data_dir(self) -> Path:
        """Get the expanded data directory path."""
        return Path(os.path.expanduser(self.general.data_dir))
    
    @property
    def database_path(self) -> Path:
        """Get the database file path."""
        return self.data_dir / "sysmind.db"
    
    @property
    def quarantine_dir(self) -> Path:
        """Get the quarantine directory path."""
        return self.data_dir / "quarantine"
    
    @property
    def log_dir(self) -> Path:
        """Get the log directory path."""
        return self.data_dir / "logs"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.quarantine_dir,
            self.log_dir
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "general": asdict(self.general),
            "monitor": asdict(self.monitor),
            "disk": asdict(self.disk),
            "process": asdict(self.process),
            "network": asdict(self.network)
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        if "general" in data:
            for key, value in data["general"].items():
                if hasattr(self.general, key):
                    setattr(self.general, key, value)
        
        if "monitor" in data:
            for key, value in data["monitor"].items():
                if hasattr(self.monitor, key):
                    setattr(self.monitor, key, value)
        
        if "disk" in data:
            for key, value in data["disk"].items():
                if hasattr(self.disk, key):
                    setattr(self.disk, key, value)
        
        if "process" in data:
            for key, value in data["process"].items():
                if hasattr(self.process, key):
                    setattr(self.process, key, value)
        
        if "network" in data:
            for key, value in data["network"].items():
                if hasattr(self.network, key):
                    setattr(self.network, key, value)
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        save_path = path or self._config_path or (self.data_dir / self.DEFAULT_CONFIG_FILENAME)
        
        try:
            self.ensure_directories()
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
            self._config_path = save_path
        except (IOError, OSError) as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> 'Config':
        """
        Load configuration from file.
        
        If path is not provided, looks in default locations.
        Returns default configuration if no config file found.
        """
        config = cls()
        
        # Determine config path
        if path:
            config_path = Path(path)
        else:
            config_path = config.data_dir / cls.DEFAULT_CONFIG_FILENAME
        
        # Try to load existing config
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config.from_dict(data)
                config._config_path = config_path
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file: {e}")
            except (IOError, OSError) as e:
                raise ConfigurationError(f"Failed to read config file: {e}")
        else:
            # Create default config
            config.ensure_directories()
            config.save(config_path)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Example: config.get("monitor.snapshot_interval_seconds")
        """
        parts = key.split(".")
        obj = self
        
        try:
            for part in parts:
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Example: config.set("monitor.snapshot_interval_seconds", 600)
        """
        parts = key.split(".")
        if len(parts) < 2:
            raise ConfigurationError(f"Invalid key format: {key}")
        
        obj = self
        for part in parts[:-1]:
            if not hasattr(obj, part):
                raise ConfigurationError(f"Unknown configuration section: {part}")
            obj = getattr(obj, part)
        
        attr_name = parts[-1]
        if not hasattr(obj, attr_name):
            raise ConfigurationError(f"Unknown configuration key: {attr_name}")
        
        setattr(obj, attr_name, value)
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.general = GeneralConfig()
        self.monitor = MonitorConfig()
        self.disk = DiskConfig()
        self.process = ProcessConfig()
        self.network = NetworkConfig()
        
        if self._config_path:
            self.save(self._config_path)
