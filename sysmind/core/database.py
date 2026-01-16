"""
SYSMIND Database Module

SQLite database wrapper for storing historical data, baselines,
file indexes, and application state.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

from .errors import DatabaseError


class Database:
    """
    SQLite database wrapper for SYSMIND.
    
    Provides methods for storing and retrieving system metrics,
    baselines, file indexes, and other persistent data.
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, data_dir: Path):
        """
        Initialize database connection.
        
        Args:
            data_dir: Directory where database file will be stored
        """
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "sysmind.db"
        self._connection: Optional[sqlite3.Connection] = None
        
        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(str(e), operation="transaction")
        finally:
            conn.close()
    
    def _initialize(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # System snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_bytes INTEGER,
                    memory_total_bytes INTEGER,
                    disk_read_bytes INTEGER,
                    disk_write_bytes INTEGER,
                    network_sent_bytes INTEGER,
                    network_recv_bytes INTEGER
                )
            """)
            
            # Process history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER REFERENCES system_snapshots(id),
                    pid INTEGER,
                    name TEXT,
                    cpu_percent REAL,
                    memory_bytes INTEGER,
                    status TEXT,
                    create_time DATETIME
                )
            """)
            
            # Baselines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT UNIQUE,
                    mean_value REAL,
                    std_deviation REAL,
                    min_value REAL,
                    max_value REAL,
                    percentile_95 REAL,
                    sample_count INTEGER,
                    last_updated DATETIME
                )
            """)
            
            # File index table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE,
                    size_bytes INTEGER,
                    hash_sha256 TEXT,
                    created_at DATETIME,
                    modified_at DATETIME,
                    last_scanned DATETIME,
                    category TEXT
                )
            """)
            
            # Duplicate groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash_sha256 TEXT,
                    total_size_bytes INTEGER,
                    file_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Duplicate files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER REFERENCES duplicate_groups(id),
                    file_path TEXT,
                    is_kept BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Watchdog rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchdog_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    process_pattern TEXT,
                    condition_json TEXT,
                    action TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    last_triggered DATETIME
                )
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT,
                    category TEXT,
                    message TEXT,
                    details_json TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Quarantine manifest table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarantine (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT,
                    quarantine_path TEXT,
                    size_bytes INTEGER,
                    reason TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    restored BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Disk scans history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disk_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT,
                    total_size_bytes INTEGER,
                    file_count INTEGER,
                    folder_count INTEGER,
                    scan_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details_json TEXT
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_process_history_name ON process_history(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_index_hash ON file_index(hash_sha256)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_baselines_metric ON baselines(metric_name)")
    
    # ==================== System Snapshots ====================
    
    def store_snapshot(
        self,
        cpu_percent: float,
        memory_percent: float,
        memory_used_bytes: int,
        memory_total_bytes: int,
        disk_read_bytes: int = 0,
        disk_write_bytes: int = 0,
        network_sent_bytes: int = 0,
        network_recv_bytes: int = 0
    ) -> int:
        """Store a system snapshot and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_snapshots 
                (cpu_percent, memory_percent, memory_used_bytes, memory_total_bytes,
                 disk_read_bytes, disk_write_bytes, network_sent_bytes, network_recv_bytes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cpu_percent, memory_percent, memory_used_bytes, memory_total_bytes,
                  disk_read_bytes, disk_write_bytes, network_sent_bytes, network_recv_bytes))
            return cursor.lastrowid
    
    def get_snapshots(
        self,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get system snapshots from the last N hours."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM system_snapshots 
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (f"-{hours} hours",))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_snapshot_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated statistics from snapshots."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    MIN(cpu_percent) as min_cpu,
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as max_memory,
                    MIN(memory_percent) as min_memory,
                    COUNT(*) as sample_count
                FROM system_snapshots
                WHERE timestamp >= datetime('now', ?)
            """, (f"-{hours} hours",))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    # ==================== Baselines ====================
    
    def store_baseline(
        self,
        metric_name: str,
        mean_value: float,
        std_deviation: float,
        min_value: float,
        max_value: float,
        percentile_95: float,
        sample_count: int
    ) -> None:
        """Store or update a baseline metric."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO baselines 
                (metric_name, mean_value, std_deviation, min_value, max_value, 
                 percentile_95, sample_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (metric_name, mean_value, std_deviation, min_value, max_value,
                  percentile_95, sample_count))
    
    def get_baseline(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get baseline for a specific metric."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM baselines WHERE metric_name = ?",
                (metric_name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_baselines(self) -> Dict[str, Dict[str, Any]]:
        """Get all baselines as a dictionary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM baselines")
            return {row['metric_name']: dict(row) for row in cursor.fetchall()}
    
    # ==================== Alerts ====================
    
    def store_alert(
        self,
        severity: str,
        category: str,
        message: str,
        details: Optional[Dict] = None
    ) -> int:
        """Store an alert and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (severity, category, message, details_json)
                VALUES (?, ?, ?, ?)
            """, (severity, category, message, json.dumps(details or {})))
            return cursor.lastrowid
    
    def get_alerts(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM alerts WHERE timestamp >= datetime('now', ?)"
            params = [f"-{hours} hours"]
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if acknowledged is not None:
                query += " AND acknowledged = ?"
                params.append(acknowledged)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get('details_json'):
                    item['details'] = json.loads(item['details_json'])
                results.append(item)
            return results
    
    def acknowledge_alert(self, alert_id: int) -> None:
        """Mark an alert as acknowledged."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE alerts SET acknowledged = TRUE WHERE id = ?",
                (alert_id,)
            )
    
    def acknowledge_all_alerts(self) -> int:
        """Mark all alerts as acknowledged. Returns count."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET acknowledged = TRUE WHERE acknowledged = FALSE")
            return cursor.rowcount
    
    # ==================== Quarantine ====================
    
    def store_quarantine_item(
        self,
        original_path: str,
        quarantine_path: str,
        size_bytes: int,
        reason: str,
        retention_days: int = 30
    ) -> int:
        """Store a quarantined item record."""
        expires_at = datetime.now() + timedelta(days=retention_days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quarantine 
                (original_path, quarantine_path, size_bytes, reason, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (original_path, quarantine_path, size_bytes, reason, expires_at))
            return cursor.lastrowid
    
    def get_quarantine_items(self, include_restored: bool = False) -> List[Dict[str, Any]]:
        """Get all quarantined items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM quarantine"
            if not include_restored:
                query += " WHERE restored = FALSE"
            query += " ORDER BY deleted_at DESC"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_restored(self, quarantine_id: int) -> None:
        """Mark a quarantine item as restored."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE quarantine SET restored = TRUE WHERE id = ?",
                (quarantine_id,)
            )
    
    def get_expired_quarantine(self) -> List[Dict[str, Any]]:
        """Get quarantine items that have expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quarantine 
                WHERE restored = FALSE AND expires_at < datetime('now')
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Disk Scans ====================
    
    def store_disk_scan(
        self,
        path: str,
        total_size_bytes: int,
        file_count: int,
        folder_count: int,
        details: Optional[Dict] = None
    ) -> int:
        """Store a disk scan result."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disk_scans 
                (path, total_size_bytes, file_count, folder_count, details_json)
                VALUES (?, ?, ?, ?, ?)
            """, (path, total_size_bytes, file_count, folder_count, json.dumps(details or {})))
            return cursor.lastrowid
    
    def get_disk_scan_history(self, path: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get disk scan history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if path:
                cursor.execute("""
                    SELECT * FROM disk_scans WHERE path = ?
                    ORDER BY scan_time DESC LIMIT ?
                """, (path, limit))
            else:
                cursor.execute("""
                    SELECT * FROM disk_scans 
                    ORDER BY scan_time DESC LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get('details_json'):
                    item['details'] = json.loads(item['details_json'])
                results.append(item)
            return results
    
    # ==================== Watchdog Rules ====================
    
    def store_watchdog_rule(
        self,
        name: str,
        process_pattern: str,
        conditions: Dict,
        action: str
    ) -> int:
        """Store a watchdog rule."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO watchdog_rules 
                (name, process_pattern, condition_json, action)
                VALUES (?, ?, ?, ?)
            """, (name, process_pattern, json.dumps(conditions), action))
            return cursor.lastrowid
    
    def get_watchdog_rules(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get watchdog rules."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM watchdog_rules"
            if enabled_only:
                query += " WHERE enabled = TRUE"
            
            cursor.execute(query)
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get('condition_json'):
                    item['conditions'] = json.loads(item['condition_json'])
                results.append(item)
            return results
    
    def delete_watchdog_rule(self, rule_id: int) -> bool:
        """Delete a watchdog rule."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchdog_rules WHERE id = ?", (rule_id,))
            return cursor.rowcount > 0
    
    # ==================== Process History ====================
    
    def store_process_snapshot(
        self,
        snapshot_id: int,
        processes: List[Dict[str, Any]]
    ) -> None:
        """Store process data for a snapshot."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for proc in processes:
                cursor.execute("""
                    INSERT INTO process_history 
                    (snapshot_id, pid, name, cpu_percent, memory_bytes, status, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot_id,
                    proc.get('pid'),
                    proc.get('name'),
                    proc.get('cpu_percent'),
                    proc.get('memory_bytes'),
                    proc.get('status'),
                    proc.get('create_time')
                ))
    
    def get_process_history(
        self,
        process_name: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get history for a specific process."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ph.*, ss.timestamp 
                FROM process_history ph
                JOIN system_snapshots ss ON ph.snapshot_id = ss.id
                WHERE ph.name LIKE ? AND ss.timestamp >= datetime('now', ?)
                ORDER BY ss.timestamp DESC
            """, (f"%{process_name}%", f"-{hours} hours"))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Cleanup ====================
    
    def cleanup_old_data(self, retention_days: int = 30) -> Dict[str, int]:
        """Remove old data beyond retention period."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = f"-{retention_days} days"
            
            counts = {}
            
            # Cleanup snapshots
            cursor.execute(
                "DELETE FROM system_snapshots WHERE timestamp < datetime('now', ?)",
                (cutoff,)
            )
            counts['snapshots'] = cursor.rowcount
            
            # Cleanup alerts
            cursor.execute(
                "DELETE FROM alerts WHERE timestamp < datetime('now', ?) AND acknowledged = TRUE",
                (cutoff,)
            )
            counts['alerts'] = cursor.rowcount
            
            # Cleanup disk scans
            cursor.execute(
                "DELETE FROM disk_scans WHERE scan_time < datetime('now', ?)",
                (cutoff,)
            )
            counts['disk_scans'] = cursor.rowcount
            
            return counts
    
    def vacuum(self) -> None:
        """Optimize database by running VACUUM."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            tables = [
                'system_snapshots', 'process_history', 'baselines',
                'file_index', 'duplicate_groups', 'watchdog_rules',
                'alerts', 'quarantine', 'disk_scans'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
        
        # Get file size
        if self.db_path.exists():
            stats['file_size_bytes'] = self.db_path.stat().st_size
        
        return stats
