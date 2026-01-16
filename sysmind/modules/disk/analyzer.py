"""
SYSMIND Disk Analyzer Module

Disk space analysis and directory statistics.
"""

import os
import stat
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator, Any
from dataclasses import dataclass
from collections import defaultdict

from ...utils.platform_utils import is_windows
from ...core.errors import DiskError, PermissionError


@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    name: str
    size: int
    modified_time: datetime
    accessed_time: datetime
    extension: str
    is_hidden: bool


@dataclass
class DiskUsage:
    """Disk usage statistics."""
    total: int
    used: int
    free: int
    percent: float


@dataclass
class DirectoryStats:
    """Directory statistics."""
    path: str
    total_size: int
    file_count: int
    dir_count: int
    extensions: Dict[str, Tuple[int, int]]  # ext -> (count, size)
    largest_files: List[FileInfo]
    oldest_files: List[FileInfo]


class DiskAnalyzer:
    """
    Disk space analyzer for directory and file analysis.
    
    Provides detailed disk usage analysis, large file detection,
    and age-based file categorization.
    """
    
    def __init__(self, database=None):
        """
        Initialize disk analyzer.
        
        Args:
            database: Optional database for caching scan results
        """
        self.database = database
        self._scan_interrupted = False
    
    def get_disk_usage(self, path: str = "/") -> DiskUsage:
        """
        Get disk usage for a path.
        
        Args:
            path: Path to check (mount point or any path on the disk)
        
        Returns:
            DiskUsage with total, used, free space
        """
        try:
            if is_windows():
                path = str(Path(path).resolve().drive) + "\\"
            
            stat_vfs = os.statvfs(path) if hasattr(os, 'statvfs') else None
            
            if stat_vfs:
                total = stat_vfs.f_blocks * stat_vfs.f_frsize
                free = stat_vfs.f_bavail * stat_vfs.f_frsize
                used = total - free
            else:
                # Windows fallback
                import shutil
                total, used, free = shutil.disk_usage(path)
            
            percent = (used / total * 100) if total > 0 else 0.0
            
            return DiskUsage(
                total=total,
                used=used,
                free=free,
                percent=percent
            )
        except Exception as e:
            raise DiskError(f"Failed to get disk usage for {path}: {e}")
    
    def list_partitions(self) -> List[Dict[str, Any]]:
        """
        List all disk partitions/mount points.
        
        Returns:
            List of partition information dictionaries
        """
        partitions = []
        
        if is_windows():
            # Windows: check all drive letters
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        usage = self.get_disk_usage(drive)
                        partitions.append({
                            'device': drive,
                            'mountpoint': drive,
                            'fstype': 'ntfs',  # Assume NTFS
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent,
                        })
                    except:
                        pass
        else:
            # Unix: read /proc/mounts or use mount command
            try:
                with open('/proc/mounts', 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 4:
                            device, mountpoint, fstype = parts[0], parts[1], parts[2]
                            
                            # Skip pseudo filesystems
                            if fstype in ['proc', 'sysfs', 'devpts', 'tmpfs', 'securityfs',
                                         'cgroup', 'cgroup2', 'debugfs', 'tracefs', 'devtmpfs']:
                                continue
                            
                            if not device.startswith('/dev/'):
                                continue
                            
                            try:
                                usage = self.get_disk_usage(mountpoint)
                                partitions.append({
                                    'device': device,
                                    'mountpoint': mountpoint,
                                    'fstype': fstype,
                                    'total': usage.total,
                                    'used': usage.used,
                                    'free': usage.free,
                                    'percent': usage.percent,
                                })
                            except:
                                pass
            except:
                # Fallback to root
                try:
                    usage = self.get_disk_usage('/')
                    partitions.append({
                        'device': '/dev/root',
                        'mountpoint': '/',
                        'fstype': 'unknown',
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    })
                except:
                    pass
        
        return partitions
    
    def _iter_files(
        self,
        path: str,
        min_size: int = 0,
        extensions: Optional[List[str]] = None,
        max_depth: Optional[int] = None
    ) -> Generator[FileInfo, None, None]:
        """
        Iterate over files in a directory tree.
        
        Args:
            path: Root path to scan
            min_size: Minimum file size to include
            extensions: Optional list of extensions to filter
            max_depth: Maximum recursion depth (None for unlimited)
        
        Yields:
            FileInfo for each matching file
        """
        root_path = Path(path).resolve()
        root_depth = len(root_path.parts)
        
        def should_include(file_path: Path, size: int) -> bool:
            if size < min_size:
                return False
            if extensions:
                ext = file_path.suffix.lower().lstrip('.')
                if ext not in [e.lower().lstrip('.') for e in extensions]:
                    return False
            return True
        
        def is_hidden(file_path: Path) -> bool:
            name = file_path.name
            if name.startswith('.'):
                return True
            if is_windows():
                try:
                    attrs = file_path.stat().st_file_attributes
                    return bool(attrs & stat.FILE_ATTRIBUTE_HIDDEN)
                except:
                    pass
            return False
        
        try:
            for dirpath, dirnames, filenames in os.walk(str(root_path)):
                if self._scan_interrupted:
                    return
                
                # Check depth
                current_path = Path(dirpath)
                current_depth = len(current_path.parts) - root_depth
                
                if max_depth is not None and current_depth >= max_depth:
                    dirnames.clear()  # Don't recurse deeper
                    continue
                
                # Skip system directories
                dirnames[:] = [d for d in dirnames if not d.startswith('$') and d != 'System Volume Information']
                
                for filename in filenames:
                    try:
                        file_path = current_path / filename
                        stat_info = file_path.stat()
                        
                        if not stat.S_ISREG(stat_info.st_mode):
                            continue
                        
                        size = stat_info.st_size
                        
                        if not should_include(file_path, size):
                            continue
                        
                        yield FileInfo(
                            path=str(file_path),
                            name=filename,
                            size=size,
                            modified_time=datetime.fromtimestamp(stat_info.st_mtime),
                            accessed_time=datetime.fromtimestamp(stat_info.st_atime),
                            extension=file_path.suffix.lower().lstrip('.'),
                            is_hidden=is_hidden(file_path)
                        )
                    except (PermissionError, OSError):
                        continue
                        
        except PermissionError as e:
            raise PermissionError(f"Permission denied accessing {path}")
    
    def scan_directory(
        self,
        path: str,
        top_n: int = 20,
        min_size: int = 0,
        progress_callback: Optional[callable] = None
    ) -> DirectoryStats:
        """
        Scan a directory and gather comprehensive statistics.
        
        Args:
            path: Directory to scan
            top_n: Number of largest/oldest files to track
            min_size: Minimum file size to include
            progress_callback: Optional callback(files_scanned, current_file)
        
        Returns:
            DirectoryStats with analysis results
        """
        self._scan_interrupted = False
        root_path = Path(path).resolve()
        
        if not root_path.exists():
            raise DiskError(f"Path does not exist: {path}")
        
        if not root_path.is_dir():
            raise DiskError(f"Path is not a directory: {path}")
        
        total_size = 0
        file_count = 0
        dir_count = 0
        extensions: Dict[str, Tuple[int, int]] = defaultdict(lambda: (0, 0))
        
        largest_files: List[FileInfo] = []
        oldest_files: List[FileInfo] = []
        
        for file_info in self._iter_files(str(root_path), min_size=min_size):
            file_count += 1
            total_size += file_info.size
            
            # Track extension stats
            ext = file_info.extension or 'no_extension'
            count, size = extensions[ext]
            extensions[ext] = (count + 1, size + file_info.size)
            
            # Track largest files
            largest_files.append(file_info)
            largest_files.sort(key=lambda f: f.size, reverse=True)
            largest_files = largest_files[:top_n]
            
            # Track oldest files
            oldest_files.append(file_info)
            oldest_files.sort(key=lambda f: f.modified_time)
            oldest_files = oldest_files[:top_n]
            
            if progress_callback and file_count % 100 == 0:
                progress_callback(file_count, file_info.path)
        
        # Count directories
        try:
            for dirpath, dirnames, _ in os.walk(str(root_path)):
                dir_count += len(dirnames)
        except:
            pass
        
        return DirectoryStats(
            path=str(root_path),
            total_size=total_size,
            file_count=file_count,
            dir_count=dir_count,
            extensions=dict(extensions),
            largest_files=largest_files,
            oldest_files=oldest_files
        )
    
    def find_large_files(
        self,
        path: str,
        min_size: int = 100 * 1024 * 1024,  # 100 MB
        limit: int = 50
    ) -> List[FileInfo]:
        """
        Find large files in a directory tree.
        
        Args:
            path: Root path to search
            min_size: Minimum file size in bytes
            limit: Maximum number of results
        
        Returns:
            List of large files sorted by size (descending)
        """
        large_files = []
        
        for file_info in self._iter_files(path, min_size=min_size):
            large_files.append(file_info)
        
        large_files.sort(key=lambda f: f.size, reverse=True)
        return large_files[:limit]
    
    def find_old_files(
        self,
        path: str,
        days_old: int = 365,
        min_size: int = 0,
        limit: int = 100
    ) -> List[FileInfo]:
        """
        Find files that haven't been modified in a specified time.
        
        Args:
            path: Root path to search
            days_old: Minimum age in days
            min_size: Minimum file size
            limit: Maximum number of results
        
        Returns:
            List of old files sorted by age (oldest first)
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        old_files = []
        
        for file_info in self._iter_files(path, min_size=min_size):
            if file_info.modified_time < cutoff:
                old_files.append(file_info)
        
        old_files.sort(key=lambda f: f.modified_time)
        return old_files[:limit]
    
    def get_extension_breakdown(
        self,
        path: str,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get disk usage breakdown by file extension.
        
        Args:
            path: Directory to analyze
            top_n: Number of top extensions to return
        
        Returns:
            List of extension statistics
        """
        extensions: Dict[str, Tuple[int, int]] = defaultdict(lambda: (0, 0))
        
        for file_info in self._iter_files(path):
            ext = file_info.extension or 'no_extension'
            count, size = extensions[ext]
            extensions[ext] = (count + 1, size + file_info.size)
        
        # Sort by size
        sorted_exts = sorted(
            extensions.items(),
            key=lambda x: x[1][1],
            reverse=True
        )[:top_n]
        
        return [
            {
                'extension': ext,
                'count': count,
                'size': size,
            }
            for ext, (count, size) in sorted_exts
        ]
    
    def interrupt_scan(self):
        """Interrupt an ongoing scan."""
        self._scan_interrupted = True
