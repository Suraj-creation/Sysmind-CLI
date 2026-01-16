"""
SYSMIND Quarantine Module

Safe file quarantine with metadata tracking and restoration.
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from ...core.errors import QuarantineError, DiskError
from ...core.database import Database
from ...core.config import Config


@dataclass
class QuarantinedItem:
    """Metadata for a quarantined file."""
    id: str
    original_path: str
    quarantine_path: str
    file_hash: str
    size: int
    reason: str
    quarantined_at: str
    original_permissions: int
    expires_at: Optional[str] = None


class QuarantineManager:
    """
    Safe file quarantine system.
    
    Moves files to a secure quarantine location while preserving
    metadata for restoration. Supports automatic expiration and
    permanent deletion.
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        quarantine_dir: Optional[Path] = None,
        retention_days: int = 30
    ):
        """
        Initialize quarantine manager.
        
        Args:
            database: Database for tracking quarantined items
            quarantine_dir: Quarantine directory (default: ~/.sysmind/quarantine)
            retention_days: Days to keep quarantined items before expiration
        """
        self.database = database
        self.retention_days = retention_days
        
        if quarantine_dir:
            self.quarantine_dir = Path(quarantine_dir)
        else:
            self.quarantine_dir = Path.home() / ".sysmind" / "quarantine"
        
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.quarantine_dir / "metadata.json"
        
        # Load existing metadata
        self._metadata: Dict[str, QuarantinedItem] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for item_id, item_data in data.items():
                        self._metadata[item_id] = QuarantinedItem(**item_data)
            except:
                self._metadata = {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            data = {
                item_id: asdict(item)
                for item_id, item in self._metadata.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise QuarantineError(f"Failed to save quarantine metadata: {e}")
    
    def _generate_id(self, path: str) -> str:
        """Generate a unique ID for a quarantined item."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path_hash = hashlib.md5(path.encode()).hexdigest()[:8]
        return f"{timestamp}_{path_hash}"
    
    def _calculate_hash(self, path: str) -> str:
        """Calculate MD5 hash of a file."""
        hasher = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
    
    def quarantine_file(
        self,
        path: str,
        reason: str = "Manual quarantine"
    ) -> Optional[QuarantinedItem]:
        """
        Move a file to quarantine.
        
        Args:
            path: Path to file to quarantine
            reason: Reason for quarantine
        
        Returns:
            QuarantinedItem if successful, None otherwise
        """
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise QuarantineError(f"File does not exist: {path}")
        
        if not file_path.is_file():
            raise QuarantineError(f"Path is not a file: {path}")
        
        # Generate quarantine info
        item_id = self._generate_id(str(file_path))
        stat_info = file_path.stat()
        
        # Create quarantine subdirectory by date
        date_dir = self.quarantine_dir / datetime.now().strftime('%Y-%m-%d')
        date_dir.mkdir(exist_ok=True)
        
        # Quarantine path preserves original filename with ID prefix
        quarantine_name = f"{item_id}_{file_path.name}"
        quarantine_path = date_dir / quarantine_name
        
        # Calculate expiration
        expires_at = (datetime.now() + timedelta(days=self.retention_days)).isoformat()
        
        # Create metadata
        item = QuarantinedItem(
            id=item_id,
            original_path=str(file_path),
            quarantine_path=str(quarantine_path),
            file_hash=self._calculate_hash(str(file_path)),
            size=stat_info.st_size,
            reason=reason,
            quarantined_at=datetime.now().isoformat(),
            original_permissions=stat_info.st_mode,
            expires_at=expires_at
        )
        
        try:
            # Move file to quarantine
            shutil.move(str(file_path), str(quarantine_path))
            
            # Store metadata
            self._metadata[item_id] = item
            self._save_metadata()
            
            # Also save to database if available
            if self.database:
                self.database.add_quarantine_item(
                    item_id=item_id,
                    original_path=str(file_path),
                    quarantine_path=str(quarantine_path),
                    reason=reason,
                    size=stat_info.st_size,
                    file_hash=item.file_hash,
                    quarantined_at=datetime.now(),
                    expires_at=datetime.fromisoformat(expires_at)
                )
            
            return item
            
        except Exception as e:
            raise QuarantineError(f"Failed to quarantine {path}: {e}")
    
    def restore_file(self, item_id: str, restore_path: Optional[str] = None) -> bool:
        """
        Restore a quarantined file.
        
        Args:
            item_id: ID of the quarantined item
            restore_path: Optional custom restore path (default: original location)
        
        Returns:
            True if successful
        """
        if item_id not in self._metadata:
            raise QuarantineError(f"Quarantine item not found: {item_id}")
        
        item = self._metadata[item_id]
        quarantine_path = Path(item.quarantine_path)
        
        if not quarantine_path.exists():
            raise QuarantineError(f"Quarantined file missing: {quarantine_path}")
        
        # Determine restore location
        if restore_path:
            target_path = Path(restore_path)
        else:
            target_path = Path(item.original_path)
        
        # Create parent directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle existing file at target
        if target_path.exists():
            # Rename existing file
            backup_path = target_path.with_suffix(target_path.suffix + '.bak')
            shutil.move(str(target_path), str(backup_path))
        
        try:
            # Move file back
            shutil.move(str(quarantine_path), str(target_path))
            
            # Restore permissions if possible
            try:
                os.chmod(str(target_path), item.original_permissions)
            except:
                pass
            
            # Remove from metadata
            del self._metadata[item_id]
            self._save_metadata()
            
            # Update database
            if self.database:
                self.database.restore_quarantine_item(item_id)
            
            return True
            
        except Exception as e:
            raise QuarantineError(f"Failed to restore {item_id}: {e}")
    
    def delete_permanently(self, item_id: str) -> bool:
        """
        Permanently delete a quarantined item.
        
        Args:
            item_id: ID of the item to delete
        
        Returns:
            True if successful
        """
        if item_id not in self._metadata:
            raise QuarantineError(f"Quarantine item not found: {item_id}")
        
        item = self._metadata[item_id]
        quarantine_path = Path(item.quarantine_path)
        
        try:
            if quarantine_path.exists():
                quarantine_path.unlink()
            
            # Remove from metadata
            del self._metadata[item_id]
            self._save_metadata()
            
            # Update database
            if self.database:
                self.database.delete_quarantine_item(item_id)
            
            return True
            
        except Exception as e:
            raise QuarantineError(f"Failed to delete {item_id}: {e}")
    
    def list_items(self) -> List[QuarantinedItem]:
        """List all quarantined items."""
        return list(self._metadata.values())
    
    def get_item(self, item_id: str) -> Optional[QuarantinedItem]:
        """Get a specific quarantined item."""
        return self._metadata.get(item_id)
    
    def cleanup_expired(self) -> int:
        """
        Delete expired quarantine items.
        
        Returns:
            Number of items deleted
        """
        now = datetime.now()
        expired = []
        
        for item_id, item in self._metadata.items():
            if item.expires_at:
                expires = datetime.fromisoformat(item.expires_at)
                if now > expires:
                    expired.append(item_id)
        
        deleted = 0
        for item_id in expired:
            try:
                self.delete_permanently(item_id)
                deleted += 1
            except:
                pass
        
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get quarantine statistics."""
        total_items = len(self._metadata)
        total_size = sum(item.size for item in self._metadata.values())
        
        # Count by reason
        by_reason: Dict[str, int] = {}
        for item in self._metadata.values():
            reason = item.reason.split(':')[0].strip()
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        # Count expired
        now = datetime.now()
        expired = 0
        for item in self._metadata.values():
            if item.expires_at:
                if now > datetime.fromisoformat(item.expires_at):
                    expired += 1
        
        return {
            'total_items': total_items,
            'total_size': total_size,
            'expired_items': expired,
            'by_reason': by_reason,
        }
    
    def search(
        self,
        original_path: Optional[str] = None,
        reason: Optional[str] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[QuarantinedItem]:
        """
        Search quarantined items.
        
        Args:
            original_path: Filter by original path (partial match)
            reason: Filter by reason (partial match)
            min_size: Minimum file size
            max_size: Maximum file size
        
        Returns:
            List of matching items
        """
        results = []
        
        for item in self._metadata.values():
            # Apply filters
            if original_path and original_path.lower() not in item.original_path.lower():
                continue
            
            if reason and reason.lower() not in item.reason.lower():
                continue
            
            if min_size and item.size < min_size:
                continue
            
            if max_size and item.size > max_size:
                continue
            
            results.append(item)
        
        return results
