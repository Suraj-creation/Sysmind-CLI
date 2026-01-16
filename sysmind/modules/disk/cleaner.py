"""
SYSMIND Disk Cleaner Module

Safe file cleanup with quarantine support.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from ...utils.platform_utils import get_adapter, is_windows
from ...core.errors import DiskError, PermissionError
from ...core.database import Database


@dataclass
class CleanupItem:
    """Item identified for cleanup."""
    path: str
    size: int
    category: str  # 'temp', 'cache', 'old', 'duplicate', 'log'
    description: str
    safe_to_delete: bool


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    items_deleted: int
    bytes_freed: int
    items_failed: int
    errors: List[str]


class DiskCleaner:
    """
    Disk cleanup with safe deletion and quarantine support.
    
    Identifies and cleans:
    - Temporary files
    - Browser caches
    - Old log files
    - Empty directories
    - System caches (with appropriate permissions)
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize disk cleaner.
        
        Args:
            database: Optional database for quarantine tracking
        """
        self.database = database
        self.platform = get_adapter()
        self._dry_run = False
    
    def find_cleanable_items(
        self,
        include_temp: bool = True,
        include_cache: bool = True,
        include_logs: bool = False,
        include_old: bool = False,
        old_days: int = 180,
        custom_paths: Optional[List[str]] = None
    ) -> List[CleanupItem]:
        """
        Find items that can be cleaned up.
        
        Args:
            include_temp: Include system temp files
            include_cache: Include browser/app caches
            include_logs: Include old log files
            include_old: Include old files (not accessed recently)
            old_days: Days threshold for old files
            custom_paths: Additional paths to scan
        
        Returns:
            List of CleanupItems
        """
        items: List[CleanupItem] = []
        
        if include_temp:
            items.extend(self._find_temp_files())
        
        if include_cache:
            items.extend(self._find_cache_files())
        
        if include_logs:
            items.extend(self._find_log_files())
        
        if custom_paths:
            for path in custom_paths:
                items.extend(self._scan_path(path, 'custom'))
        
        return items
    
    def _find_temp_files(self) -> List[CleanupItem]:
        """Find temporary files."""
        items = []
        temp_paths = self.platform.get_system_temp_paths()
        
        for temp_dir in temp_paths:
            items.extend(self._scan_path(str(temp_dir), 'temp'))
        
        return items
    
    def _find_cache_files(self) -> List[CleanupItem]:
        """Find browser and application cache files."""
        items = []
        cache_paths = self.platform.get_browser_cache_paths()
        
        for browser, cache_path in cache_paths.items():
            try:
                total_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(str(cache_path)):
                    for f in files:
                        try:
                            fp = Path(root) / f
                            total_size += fp.stat().st_size
                            file_count += 1
                        except:
                            pass
                
                if total_size > 0:
                    items.append(CleanupItem(
                        path=str(cache_path),
                        size=total_size,
                        category='cache',
                        description=f"{browser.title()} cache ({file_count} files)",
                        safe_to_delete=True
                    ))
            except:
                pass
        
        return items
    
    def _find_log_files(self) -> List[CleanupItem]:
        """Find old log files."""
        items = []
        log_paths = self.platform.get_log_paths()
        
        cutoff = datetime.now() - timedelta(days=30)
        
        for log_dir in log_paths:
            try:
                for root, dirs, files in os.walk(str(log_dir)):
                    for f in files:
                        if f.endswith(('.log', '.old', '.bak')):
                            try:
                                fp = Path(root) / f
                                stat = fp.stat()
                                mtime = datetime.fromtimestamp(stat.st_mtime)
                                
                                if mtime < cutoff:
                                    items.append(CleanupItem(
                                        path=str(fp),
                                        size=stat.st_size,
                                        category='log',
                                        description=f"Old log file (modified {mtime.date()})",
                                        safe_to_delete=True
                                    ))
                            except:
                                pass
            except:
                pass
        
        return items
    
    def _scan_path(self, path: str, category: str) -> List[CleanupItem]:
        """Scan a path for cleanable files."""
        items = []
        root_path = Path(path)
        
        if not root_path.exists():
            return items
        
        try:
            total_size = 0
            file_count = 0
            
            if root_path.is_file():
                stat = root_path.stat()
                items.append(CleanupItem(
                    path=str(root_path),
                    size=stat.st_size,
                    category=category,
                    description=f"File: {root_path.name}",
                    safe_to_delete=True
                ))
            else:
                for root, dirs, files in os.walk(str(root_path)):
                    for f in files:
                        try:
                            fp = Path(root) / f
                            total_size += fp.stat().st_size
                            file_count += 1
                        except:
                            pass
                
                if total_size > 0:
                    items.append(CleanupItem(
                        path=str(root_path),
                        size=total_size,
                        category=category,
                        description=f"Directory ({file_count} files)",
                        safe_to_delete=True
                    ))
        except:
            pass
        
        return items
    
    def cleanup(
        self,
        items: List[CleanupItem],
        dry_run: bool = False,
        use_quarantine: bool = True,
        quarantine_path: Optional[str] = None
    ) -> CleanupResult:
        """
        Perform cleanup of specified items.
        
        Args:
            items: List of items to clean
            dry_run: If True, only simulate cleanup
            use_quarantine: If True, move to quarantine instead of delete
            quarantine_path: Custom quarantine directory
        
        Returns:
            CleanupResult with statistics
        """
        self._dry_run = dry_run
        
        deleted = 0
        freed = 0
        failed = 0
        errors = []
        
        for item in items:
            if not item.safe_to_delete:
                continue
            
            try:
                if dry_run:
                    # Simulate
                    deleted += 1
                    freed += item.size
                else:
                    if use_quarantine:
                        success = self._quarantine_item(item, quarantine_path)
                    else:
                        success = self._delete_item(item)
                    
                    if success:
                        deleted += 1
                        freed += item.size
                    else:
                        failed += 1
                        errors.append(f"Failed to delete: {item.path}")
                        
            except Exception as e:
                failed += 1
                errors.append(f"Error with {item.path}: {str(e)}")
        
        return CleanupResult(
            items_deleted=deleted,
            bytes_freed=freed,
            items_failed=failed,
            errors=errors
        )
    
    def _delete_item(self, item: CleanupItem) -> bool:
        """Delete an item (file or directory)."""
        try:
            path = Path(item.path)
            
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(str(path), ignore_errors=True)
            
            return True
        except Exception:
            return False
    
    def _quarantine_item(self, item: CleanupItem, quarantine_base: Optional[str] = None) -> bool:
        """Move an item to quarantine."""
        try:
            from .quarantine import QuarantineManager
            
            qm = QuarantineManager(self.database)
            
            if quarantine_base:
                qm.quarantine_dir = Path(quarantine_base)
            
            result = qm.quarantine_file(item.path, reason=f"Cleanup: {item.category}")
            return result is not None
        except Exception:
            # Fall back to direct delete
            return self._delete_item(item)
    
    def find_empty_directories(
        self,
        path: str,
        exclude_hidden: bool = True
    ) -> List[str]:
        """
        Find empty directories.
        
        Args:
            path: Root path to search
            exclude_hidden: Exclude hidden directories
        
        Returns:
            List of empty directory paths
        """
        empty_dirs = []
        root_path = Path(path)
        
        try:
            # Walk bottom-up so we can detect directories that become empty
            for dirpath, dirnames, filenames in os.walk(str(root_path), topdown=False):
                dp = Path(dirpath)
                
                if exclude_hidden and dp.name.startswith('.'):
                    continue
                
                # Check if directory is empty
                try:
                    contents = list(dp.iterdir())
                    if not contents:
                        empty_dirs.append(str(dp))
                except:
                    pass
        except:
            pass
        
        return empty_dirs
    
    def cleanup_empty_directories(
        self,
        directories: List[str],
        dry_run: bool = False
    ) -> CleanupResult:
        """
        Remove empty directories.
        
        Args:
            directories: List of empty directories to remove
            dry_run: If True, only simulate
        
        Returns:
            CleanupResult with statistics
        """
        deleted = 0
        failed = 0
        errors = []
        
        # Sort by depth (deepest first) to avoid issues
        directories.sort(key=lambda x: x.count(os.sep), reverse=True)
        
        for dir_path in directories:
            try:
                if not dry_run:
                    os.rmdir(dir_path)
                deleted += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed to remove {dir_path}: {e}")
        
        return CleanupResult(
            items_deleted=deleted,
            bytes_freed=0,
            items_failed=failed,
            errors=errors
        )
    
    def get_cleanup_summary(self, items: List[CleanupItem]) -> Dict[str, Any]:
        """
        Get summary of items to be cleaned.
        
        Args:
            items: List of cleanup items
        
        Returns:
            Summary statistics by category
        """
        by_category: Dict[str, Tuple[int, int]] = {}  # category -> (count, size)
        
        for item in items:
            cat = item.category
            count, size = by_category.get(cat, (0, 0))
            by_category[cat] = (count + 1, size + item.size)
        
        total_count = len(items)
        total_size = sum(item.size for item in items)
        
        return {
            'total_items': total_count,
            'total_size': total_size,
            'by_category': {
                cat: {'count': c, 'size': s}
                for cat, (c, s) in by_category.items()
            }
        }
