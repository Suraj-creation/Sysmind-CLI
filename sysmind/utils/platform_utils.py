"""
SYSMIND Platform Utilities

OS-specific utilities and platform abstraction layer.
Provides unified interface for platform-dependent operations.
"""

import os
import platform
import subprocess
import ctypes
from pathlib import Path
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod


def get_platform() -> str:
    """Get the current platform name."""
    return platform.system().lower()


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_admin() -> bool:
    """Check if the current process has admin/root privileges."""
    if is_windows():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0


class PlatformAdapter(ABC):
    """Abstract base class for platform-specific operations."""
    
    @staticmethod
    def get_adapter() -> 'PlatformAdapter':
        """Get the appropriate adapter for the current platform."""
        system = platform.system()
        if system == "Windows":
            return WindowsAdapter()
        elif system == "Linux":
            return LinuxAdapter()
        elif system == "Darwin":
            return MacOSAdapter()
        else:
            raise NotImplementedError(f"Unsupported platform: {system}")
    
    @abstractmethod
    def get_startup_items(self) -> List[Dict[str, Any]]:
        """Get list of startup programs."""
        pass
    
    @abstractmethod
    def disable_startup_item(self, name: str) -> bool:
        """Disable a startup program."""
        pass
    
    @abstractmethod
    def enable_startup_item(self, name: str) -> bool:
        """Enable a startup program."""
        pass
    
    @abstractmethod
    def get_system_temp_paths(self) -> List[Path]:
        """Get system temporary file paths."""
        pass
    
    @abstractmethod
    def get_browser_cache_paths(self) -> Dict[str, Path]:
        """Get browser cache directory paths."""
        pass
    
    @abstractmethod
    def get_log_paths(self) -> List[Path]:
        """Get system log file paths."""
        pass
    
    @abstractmethod
    def open_file_explorer(self, path: str) -> bool:
        """Open file explorer at the given path."""
        pass


class WindowsAdapter(PlatformAdapter):
    """Windows-specific implementations."""
    
    def get_startup_items(self) -> List[Dict[str, Any]]:
        """Get Windows startup items from Registry and Startup folders."""
        items = []
        
        # Try to read from Registry
        try:
            import winreg
            
            # HKCU Run
            locations = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
            ]
            
            for hive, path, hive_name in locations:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            items.append({
                                'name': name,
                                'command': value,
                                'location': f"{hive_name}\\{path}",
                                'type': 'registry',
                                'enabled': True
                            })
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except WindowsError:
                    pass
        except ImportError:
            pass
        
        # Check Startup folder
        startup_folder = Path(os.environ.get('APPDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if startup_folder.exists():
            for item in startup_folder.iterdir():
                if item.suffix in ['.lnk', '.exe', '.bat', '.cmd']:
                    items.append({
                        'name': item.stem,
                        'command': str(item),
                        'location': str(startup_folder),
                        'type': 'startup_folder',
                        'enabled': True
                    })
        
        return items
    
    def disable_startup_item(self, name: str) -> bool:
        """Disable a Windows startup item."""
        try:
            import winreg
            
            locations = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            
            for hive, path in locations:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
                    try:
                        winreg.DeleteValue(key, name)
                        winreg.CloseKey(key)
                        return True
                    except WindowsError:
                        winreg.CloseKey(key)
                except WindowsError:
                    pass
        except ImportError:
            pass
        return False
    
    def enable_startup_item(self, name: str) -> bool:
        """Enable a Windows startup item (requires stored command)."""
        # This would need the original command to be stored somewhere
        return False
    
    def get_system_temp_paths(self) -> List[Path]:
        """Get Windows temp directories."""
        paths = []
        
        temp_vars = ['TEMP', 'TMP']
        for var in temp_vars:
            val = os.environ.get(var)
            if val:
                paths.append(Path(val))
        
        # Windows temp
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        paths.append(Path(windir) / "Temp")
        
        # Local app data temp
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata:
            paths.append(Path(localappdata) / "Temp")
        
        return [p for p in paths if p.exists()]
    
    def get_browser_cache_paths(self) -> Dict[str, Path]:
        """Get Windows browser cache paths."""
        local_app_data = Path(os.environ.get('LOCALAPPDATA', ''))
        
        paths = {}
        
        chrome_cache = local_app_data / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
        if chrome_cache.exists():
            paths['chrome'] = chrome_cache
        
        edge_cache = local_app_data / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache"
        if edge_cache.exists():
            paths['edge'] = edge_cache
        
        firefox_profiles = local_app_data / "Mozilla" / "Firefox" / "Profiles"
        if firefox_profiles.exists():
            paths['firefox'] = firefox_profiles
        
        return paths
    
    def get_log_paths(self) -> List[Path]:
        """Get Windows log paths."""
        paths = []
        
        # Windows logs
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        paths.append(Path(windir) / "Logs")
        
        # User logs
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata:
            paths.append(Path(localappdata) / "Logs")
        
        return [p for p in paths if p.exists()]
    
    def open_file_explorer(self, path: str) -> bool:
        """Open Windows Explorer at path."""
        try:
            subprocess.run(['explorer', path], check=True)
            return True
        except:
            return False


class LinuxAdapter(PlatformAdapter):
    """Linux-specific implementations."""
    
    def get_startup_items(self) -> List[Dict[str, Any]]:
        """Get Linux startup items from autostart directories."""
        items = []
        
        autostart_dirs = [
            Path.home() / ".config" / "autostart",
            Path("/etc/xdg/autostart"),
        ]
        
        for autostart_dir in autostart_dirs:
            if autostart_dir.exists():
                for item in autostart_dir.glob("*.desktop"):
                    try:
                        content = item.read_text()
                        name = item.stem
                        command = ""
                        
                        for line in content.split('\n'):
                            if line.startswith('Name='):
                                name = line[5:]
                            elif line.startswith('Exec='):
                                command = line[5:]
                        
                        items.append({
                            'name': name,
                            'command': command,
                            'location': str(autostart_dir),
                            'type': 'desktop_file',
                            'enabled': True
                        })
                    except:
                        pass
        
        return items
    
    def disable_startup_item(self, name: str) -> bool:
        """Disable a Linux startup item."""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / f"{name}.desktop"
        
        if desktop_file.exists():
            try:
                desktop_file.unlink()
                return True
            except:
                pass
        return False
    
    def enable_startup_item(self, name: str) -> bool:
        return False
    
    def get_system_temp_paths(self) -> List[Path]:
        """Get Linux temp directories."""
        paths = [
            Path("/tmp"),
            Path("/var/tmp"),
            Path.home() / ".cache",
        ]
        return [p for p in paths if p.exists()]
    
    def get_browser_cache_paths(self) -> Dict[str, Path]:
        """Get Linux browser cache paths."""
        home = Path.home()
        paths = {}
        
        chrome_cache = home / ".cache" / "google-chrome"
        if chrome_cache.exists():
            paths['chrome'] = chrome_cache
        
        firefox_cache = home / ".cache" / "mozilla" / "firefox"
        if firefox_cache.exists():
            paths['firefox'] = firefox_cache
        
        return paths
    
    def get_log_paths(self) -> List[Path]:
        """Get Linux log paths."""
        paths = [
            Path("/var/log"),
            Path.home() / ".local" / "share",
        ]
        return [p for p in paths if p.exists()]
    
    def open_file_explorer(self, path: str) -> bool:
        """Open file manager at path."""
        try:
            subprocess.run(['xdg-open', path], check=True)
            return True
        except:
            return False


class MacOSAdapter(PlatformAdapter):
    """macOS-specific implementations."""
    
    def get_startup_items(self) -> List[Dict[str, Any]]:
        """Get macOS startup items from LaunchAgents."""
        items = []
        
        launch_dirs = [
            Path.home() / "Library" / "LaunchAgents",
            Path("/Library/LaunchAgents"),
        ]
        
        for launch_dir in launch_dirs:
            if launch_dir.exists():
                for item in launch_dir.glob("*.plist"):
                    items.append({
                        'name': item.stem,
                        'command': str(item),
                        'location': str(launch_dir),
                        'type': 'launchagent',
                        'enabled': True
                    })
        
        return items
    
    def disable_startup_item(self, name: str) -> bool:
        """Disable a macOS startup item."""
        try:
            subprocess.run(['launchctl', 'unload', f"~/Library/LaunchAgents/{name}.plist"], check=True)
            return True
        except:
            return False
    
    def enable_startup_item(self, name: str) -> bool:
        try:
            subprocess.run(['launchctl', 'load', f"~/Library/LaunchAgents/{name}.plist"], check=True)
            return True
        except:
            return False
    
    def get_system_temp_paths(self) -> List[Path]:
        """Get macOS temp directories."""
        paths = [
            Path("/tmp"),
            Path("/var/folders"),
            Path.home() / "Library" / "Caches",
        ]
        return [p for p in paths if p.exists()]
    
    def get_browser_cache_paths(self) -> Dict[str, Path]:
        """Get macOS browser cache paths."""
        home = Path.home()
        paths = {}
        
        chrome_cache = home / "Library" / "Caches" / "Google" / "Chrome"
        if chrome_cache.exists():
            paths['chrome'] = chrome_cache
        
        safari_cache = home / "Library" / "Caches" / "com.apple.Safari"
        if safari_cache.exists():
            paths['safari'] = safari_cache
        
        return paths
    
    def get_log_paths(self) -> List[Path]:
        """Get macOS log paths."""
        paths = [
            Path("/var/log"),
            Path.home() / "Library" / "Logs",
        ]
        return [p for p in paths if p.exists()]
    
    def open_file_explorer(self, path: str) -> bool:
        """Open Finder at path."""
        try:
            subprocess.run(['open', path], check=True)
            return True
        except:
            return False


def get_adapter() -> PlatformAdapter:
    """Get the platform adapter for the current OS."""
    return PlatformAdapter.get_adapter()
