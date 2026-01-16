"""
SYSMIND Duplicate Files Finder Module

Multi-phase duplicate file detection using size and hash comparison.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Generator, Any
from dataclasses import dataclass
from collections import defaultdict

from ...core.errors import DiskError
from ...core.database import Database


@dataclass
class DuplicateFile:
    """Information about a duplicate file."""
    path: str
    size: int
    hash: str
    modified_time: datetime


@dataclass
class DuplicateGroup:
    """A group of duplicate files."""
    hash: str
    size: int
    files: List[DuplicateFile]
    wasted_space: int  # Total size - one copy
    
    @property
    def count(self) -> int:
        return len(self.files)


class DuplicateFinder:
    """
    Multi-phase duplicate file detection.
    
    Phase 1: Group files by size (fast filtering)
    Phase 2: Partial hash comparison (first 4KB)
    Phase 3: Full hash for remaining candidates
    
    This approach minimizes disk I/O by only fully hashing
    files that have matching sizes and partial hashes.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize duplicate finder.
        
        Args:
            database: Optional database for caching file hashes
        """
        self.database = database
        self._interrupted = False
        self._hash_cache: Dict[str, str] = {}  # path -> hash
    
    def _partial_hash(self, path: str, chunk_size: int = 4096) -> str:
        """
        Calculate partial hash of a file (first chunk only).
        
        Args:
            path: File path
            chunk_size: Number of bytes to hash
        
        Returns:
            Hex digest of partial hash
        """
        hasher = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                data = f.read(chunk_size)
                hasher.update(data)
            return hasher.hexdigest()
        except (PermissionError, OSError):
            return ""
    
    def _full_hash(self, path: str, chunk_size: int = 65536) -> str:
        """
        Calculate full hash of a file.
        
        Args:
            path: File path
            chunk_size: Chunk size for reading
        
        Returns:
            Hex digest of full file hash
        """
        # Check cache first
        if path in self._hash_cache:
            return self._hash_cache[path]
        
        hasher = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    hasher.update(data)
            
            hash_val = hasher.hexdigest()
            self._hash_cache[path] = hash_val
            return hash_val
        except (PermissionError, OSError):
            return ""
    
    def _iter_files(
        self,
        paths: List[str],
        min_size: int = 1,
        extensions: Optional[Set[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Generator[Tuple[str, int, datetime], None, None]:
        """
        Iterate over files in multiple paths.
        
        Yields:
            Tuple of (path, size, modified_time)
        """
        seen_inodes: Set[int] = set()  # Avoid hardlink duplicates
        
        for root_path in paths:
            root = Path(root_path).resolve()
            
            if not root.exists():
                continue
            
            try:
                for dirpath, dirnames, filenames in os.walk(str(root)):
                    if self._interrupted:
                        return
                    
                    # Filter directories
                    dirnames[:] = [
                        d for d in dirnames
                        if not d.startswith('.')
                        and d not in ['$RECYCLE.BIN', 'System Volume Information', '__pycache__', 'node_modules']
                    ]
                    
                    for filename in filenames:
                        try:
                            file_path = Path(dirpath) / filename
                            stat_info = file_path.stat()
                            
                            # Skip if too small
                            if stat_info.st_size < min_size:
                                continue
                            
                            # Skip hardlinks we've already seen
                            inode = stat_info.st_ino
                            if inode in seen_inodes:
                                continue
                            seen_inodes.add(inode)
                            
                            # Filter by extension
                            if extensions:
                                ext = file_path.suffix.lower().lstrip('.')
                                if ext not in extensions:
                                    continue
                            
                            # Check exclude patterns
                            if exclude_patterns:
                                skip = False
                                path_str = str(file_path)
                                for pattern in exclude_patterns:
                                    if pattern in path_str:
                                        skip = True
                                        break
                                if skip:
                                    continue
                            
                            yield (
                                str(file_path),
                                stat_info.st_size,
                                datetime.fromtimestamp(stat_info.st_mtime)
                            )
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError):
                continue
    
    def find_duplicates(
        self,
        paths: List[str],
        min_size: int = 1024,  # 1 KB minimum
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> List[DuplicateGroup]:
        """
        Find duplicate files using multi-phase detection.
        
        Args:
            paths: List of directory paths to scan
            min_size: Minimum file size to consider
            extensions: Optional list of extensions to include
            exclude_patterns: Optional list of path patterns to exclude
            progress_callback: Optional callback(phase, current, total, message)
        
        Returns:
            List of DuplicateGroups
        """
        self._interrupted = False
        self._hash_cache.clear()
        
        ext_set = {e.lower().lstrip('.') for e in extensions} if extensions else None
        
        # Phase 1: Group by size
        if progress_callback:
            progress_callback('size', 0, 0, "Phase 1: Grouping files by size...")
        
        size_groups: Dict[int, List[Tuple[str, datetime]]] = defaultdict(list)
        file_count = 0
        
        for path, size, mtime in self._iter_files(paths, min_size, ext_set, exclude_patterns):
            size_groups[size].append((path, mtime))
            file_count += 1
            
            if progress_callback and file_count % 500 == 0:
                progress_callback('size', file_count, 0, f"Indexed {file_count} files")
        
        # Keep only sizes with multiple files
        candidates = {
            size: files for size, files in size_groups.items()
            if len(files) > 1
        }
        
        total_candidates = sum(len(files) for files in candidates.values())
        
        if progress_callback:
            progress_callback('size', file_count, file_count, 
                            f"Phase 1 complete: {total_candidates} potential duplicates")
        
        if self._interrupted:
            return []
        
        # Phase 2: Partial hash comparison
        if progress_callback:
            progress_callback('partial', 0, total_candidates, "Phase 2: Computing partial hashes...")
        
        partial_groups: Dict[str, List[Tuple[str, int, datetime]]] = defaultdict(list)
        processed = 0
        
        for size, files in candidates.items():
            for path, mtime in files:
                if self._interrupted:
                    return []
                
                partial = self._partial_hash(path)
                if partial:
                    key = f"{size}:{partial}"
                    partial_groups[key].append((path, size, mtime))
                
                processed += 1
                if progress_callback and processed % 100 == 0:
                    progress_callback('partial', processed, total_candidates, f"Processed {processed}/{total_candidates}")
        
        # Keep only partial hashes with multiple files
        partial_candidates = {
            key: files for key, files in partial_groups.items()
            if len(files) > 1
        }
        
        final_candidates = sum(len(files) for files in partial_candidates.values())
        
        if progress_callback:
            progress_callback('partial', total_candidates, total_candidates,
                            f"Phase 2 complete: {final_candidates} candidates remaining")
        
        if self._interrupted:
            return []
        
        # Phase 3: Full hash comparison
        if progress_callback:
            progress_callback('full', 0, final_candidates, "Phase 3: Computing full hashes...")
        
        full_groups: Dict[str, List[DuplicateFile]] = defaultdict(list)
        processed = 0
        
        for key, files in partial_candidates.items():
            for path, size, mtime in files:
                if self._interrupted:
                    return []
                
                full_hash = self._full_hash(path)
                if full_hash:
                    full_groups[full_hash].append(DuplicateFile(
                        path=path,
                        size=size,
                        hash=full_hash,
                        modified_time=mtime
                    ))
                
                processed += 1
                if progress_callback and processed % 50 == 0:
                    progress_callback('full', processed, final_candidates, f"Hashed {processed}/{final_candidates}")
        
        # Build duplicate groups
        duplicates: List[DuplicateGroup] = []
        
        for hash_val, files in full_groups.items():
            if len(files) > 1:
                # Sort by modified time (oldest first) - this helps decide which to keep
                files.sort(key=lambda f: f.modified_time)
                
                size = files[0].size
                wasted = size * (len(files) - 1)
                
                duplicates.append(DuplicateGroup(
                    hash=hash_val,
                    size=size,
                    files=files,
                    wasted_space=wasted
                ))
        
        # Sort by wasted space (descending)
        duplicates.sort(key=lambda g: g.wasted_space, reverse=True)
        
        if progress_callback:
            total_wasted = sum(g.wasted_space for g in duplicates)
            progress_callback('complete', final_candidates, final_candidates,
                            f"Found {len(duplicates)} duplicate groups ({total_wasted / (1024**2):.1f} MB wasted)")
        
        # Save to database if available
        if self.database and duplicates:
            self._save_results(duplicates)
        
        return duplicates
    
    def _save_results(self, duplicates: List[DuplicateGroup]):
        """Save duplicate results to database."""
        if not self.database:
            return
        
        scan_id = self.database.create_disk_scan(
            path="multiple",
            scan_type="duplicates"
        )
        
        for group in duplicates:
            group_id = self.database.save_duplicate_group(
                scan_id=scan_id,
                hash_value=group.hash,
                size=group.size,
                count=group.count
            )
            
            for file in group.files:
                self.database.save_duplicate_file(
                    group_id=group_id,
                    path=file.path,
                    modified_time=file.modified_time
                )
    
    def get_summary(self, duplicates: List[DuplicateGroup]) -> Dict[str, Any]:
        """
        Get summary statistics for duplicate results.
        
        Args:
            duplicates: List of duplicate groups
        
        Returns:
            Dictionary with summary statistics
        """
        total_groups = len(duplicates)
        total_files = sum(g.count for g in duplicates)
        total_wasted = sum(g.wasted_space for g in duplicates)
        
        # Size distribution
        size_brackets = {
            'tiny': 0,      # < 1 KB
            'small': 0,     # 1 KB - 1 MB
            'medium': 0,    # 1 MB - 100 MB
            'large': 0,     # 100 MB - 1 GB
            'huge': 0,      # > 1 GB
        }
        
        for group in duplicates:
            size = group.size
            if size < 1024:
                size_brackets['tiny'] += group.wasted_space
            elif size < 1024 * 1024:
                size_brackets['small'] += group.wasted_space
            elif size < 100 * 1024 * 1024:
                size_brackets['medium'] += group.wasted_space
            elif size < 1024 * 1024 * 1024:
                size_brackets['large'] += group.wasted_space
            else:
                size_brackets['huge'] += group.wasted_space
        
        return {
            'total_groups': total_groups,
            'total_files': total_files,
            'total_wasted_bytes': total_wasted,
            'size_distribution': size_brackets,
        }
    
    def interrupt(self):
        """Interrupt an ongoing duplicate search."""
        self._interrupted = True
