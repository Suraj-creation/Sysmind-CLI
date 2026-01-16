"""
SYSMIND Realtime Monitor Module

Real-time system monitoring with live updates.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass

from .cpu import CPUMonitor, CPUMetrics
from .memory import MemoryMonitor, MemoryMetrics
from ...core.database import Database
from ...utils.formatters import Formatter, Colors


@dataclass
class SystemSnapshot:
    """Complete system state snapshot."""
    timestamp: datetime
    cpu_metrics: CPUMetrics
    memory_metrics: MemoryMetrics
    disk_usage: Optional[Dict[str, Any]] = None
    network_stats: Optional[Dict[str, Any]] = None


class RealtimeMonitor:
    """
    Real-time system monitoring with live dashboard display.
    
    Provides continuous monitoring with configurable update intervals
    and optional data persistence.
    """
    
    def __init__(
        self,
        interval: float = 1.0,
        database: Optional[Database] = None,
        persist_snapshots: bool = False
    ):
        """
        Initialize realtime monitor.
        
        Args:
            interval: Update interval in seconds
            database: Optional database for persisting snapshots
            persist_snapshots: Whether to save snapshots to database
        """
        self.interval = interval
        self.database = database
        self.persist_snapshots = persist_snapshots
        
        self.cpu_monitor = CPUMonitor()
        self.memory_monitor = MemoryMonitor()
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[SystemSnapshot], None]] = None
        self._history: List[SystemSnapshot] = []
        self._max_history = 60  # Keep 1 minute of history at 1s interval
    
    def get_snapshot(self) -> SystemSnapshot:
        """Get a current system snapshot."""
        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu_metrics=self.cpu_monitor.get_metrics(),
            memory_metrics=self.memory_monitor.get_metrics()
        )
    
    def _monitor_loop(self):
        """Internal monitoring loop."""
        while self._running:
            try:
                snapshot = self.get_snapshot()
                
                # Store in history
                self._history.append(snapshot)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
                
                # Persist if enabled
                if self.persist_snapshots and self.database:
                    self._save_snapshot(snapshot)
                
                # Callback if set
                if self._callback:
                    self._callback(snapshot)
                
            except Exception as e:
                pass  # Ignore errors in monitoring loop
            
            time.sleep(self.interval)
    
    def _save_snapshot(self, snapshot: SystemSnapshot):
        """Save snapshot to database."""
        if self.database:
            self.database.save_system_snapshot(
                timestamp=snapshot.timestamp,
                cpu_percent=snapshot.cpu_metrics.usage_percent,
                memory_percent=snapshot.memory_metrics.usage_percent,
                disk_percent=0.0,  # Will be added with disk module
                network_bytes_sent=0,
                network_bytes_recv=0
            )
    
    def start(self, callback: Optional[Callable[[SystemSnapshot], None]] = None):
        """
        Start background monitoring.
        
        Args:
            callback: Function to call with each snapshot
        """
        if self._running:
            return
        
        self._running = True
        self._callback = callback
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop background monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def get_history(self) -> List[SystemSnapshot]:
        """Get recent snapshot history."""
        return list(self._history)
    
    def run_dashboard(self, duration: Optional[float] = None, formatter: Optional[Formatter] = None):
        """
        Run interactive dashboard display.
        
        Args:
            duration: How long to run (None for indefinitely)
            formatter: Output formatter to use
        """
        if formatter is None:
            formatter = Formatter()
        
        start_time = time.time()
        
        # Clear screen function
        def clear_screen():
            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')
        
        try:
            while True:
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
                
                snapshot = self.get_snapshot()
                
                # Clear and redraw
                clear_screen()
                print(self._render_dashboard(snapshot, formatter))
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            pass
    
    def _render_dashboard(self, snapshot: SystemSnapshot, fmt: Formatter) -> str:
        """Render the dashboard display."""
        lines = []
        
        # Header
        lines.append(fmt.header("SYSMIND System Monitor", 60))
        lines.append(f"  Time: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # CPU Section
        lines.append(fmt.bold("  CPU"))
        lines.append(fmt.progress_bar(
            snapshot.cpu_metrics.usage_percent, 100, 30,
            label="  Usage"
        ))
        lines.append(f"  Cores: {snapshot.cpu_metrics.core_count}  |  Load: {snapshot.cpu_metrics.load_average[0]:.2f}, {snapshot.cpu_metrics.load_average[1]:.2f}, {snapshot.cpu_metrics.load_average[2]:.2f}")
        
        # Per-core usage (compact)
        if snapshot.cpu_metrics.core_usages:
            core_strs = [f"C{i}:{u:.0f}%" for i, u in enumerate(snapshot.cpu_metrics.core_usages[:8])]
            lines.append(f"  {' | '.join(core_strs)}")
        
        lines.append("")
        
        # Memory Section
        lines.append(fmt.bold("  Memory"))
        lines.append(fmt.progress_bar(
            snapshot.memory_metrics.usage_percent, 100, 30,
            label="  RAM"
        ))
        
        used_gb = snapshot.memory_metrics.used / (1024**3)
        total_gb = snapshot.memory_metrics.total / (1024**3)
        lines.append(f"  Used: {used_gb:.1f} GB / {total_gb:.1f} GB")
        
        if snapshot.memory_metrics.swap_total > 0:
            lines.append(fmt.progress_bar(
                snapshot.memory_metrics.swap_percent, 100, 30,
                label="  Swap"
            ))
        
        lines.append("")
        
        # Timing breakdown
        lines.append(fmt.bold("  CPU Time Distribution"))
        if snapshot.cpu_metrics.user_time > 0:
            lines.append(f"  User: {snapshot.cpu_metrics.user_time:.1f}%  |  System: {snapshot.cpu_metrics.system_time:.1f}%  |  Idle: {snapshot.cpu_metrics.idle_time:.1f}%")
        
        lines.append("")
        lines.append(fmt.dim("  Press Ctrl+C to exit"))
        
        return "\n".join(lines)
    
    def get_averages(self, seconds: int = 60) -> Dict[str, float]:
        """
        Get average metrics over a time period.
        
        Args:
            seconds: Number of seconds to average over
        
        Returns:
            Dictionary with average CPU and memory usage
        """
        if not self._history:
            snapshot = self.get_snapshot()
            return {
                'cpu_avg': snapshot.cpu_metrics.usage_percent,
                'memory_avg': snapshot.memory_metrics.usage_percent,
            }
        
        # Filter history to time window
        cutoff = datetime.now().timestamp() - seconds
        recent = [s for s in self._history if s.timestamp.timestamp() >= cutoff]
        
        if not recent:
            recent = self._history[-1:]
        
        cpu_avg = sum(s.cpu_metrics.usage_percent for s in recent) / len(recent)
        mem_avg = sum(s.memory_metrics.usage_percent for s in recent) / len(recent)
        
        return {
            'cpu_avg': cpu_avg,
            'memory_avg': mem_avg,
            'sample_count': len(recent),
        }
