"""
SYSMIND Baseline Monitor Module

System baseline creation and comparison for anomaly detection.
"""

import os
import json
import statistics
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

from .cpu import CPUMonitor
from .memory import MemoryMonitor
from .realtime import RealtimeMonitor, SystemSnapshot
from ...core.database import Database
from ...core.errors import ValidationError


@dataclass
class BaselineMetrics:
    """Baseline metrics with statistical measures."""
    cpu_mean: float
    cpu_std: float
    cpu_min: float
    cpu_max: float
    
    memory_mean: float
    memory_std: float
    memory_min: float
    memory_max: float
    
    sample_count: int
    duration_seconds: float
    created_at: str


@dataclass
class BaselineComparison:
    """Result of comparing current state to baseline."""
    cpu_current: float
    cpu_baseline_mean: float
    cpu_deviation: float  # Standard deviations from mean
    cpu_status: str  # 'normal', 'elevated', 'critical'
    
    memory_current: float
    memory_baseline_mean: float
    memory_deviation: float
    memory_status: str
    
    overall_status: str
    alerts: List[str]


class BaselineManager:
    """
    System baseline management for anomaly detection.
    
    Creates, stores, and compares system performance baselines
    to identify abnormal behavior.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize baseline manager.
        
        Args:
            database: Database for storing baselines
        """
        self.database = database
        self.realtime = RealtimeMonitor(interval=0.5)
        
        # Deviation thresholds
        self.warning_threshold = 2.0  # standard deviations
        self.critical_threshold = 3.0
    
    def create_baseline(
        self,
        name: str,
        duration_seconds: int = 60,
        sample_interval: float = 1.0,
        callback: Optional[callable] = None
    ) -> BaselineMetrics:
        """
        Create a new performance baseline.
        
        Args:
            name: Name for the baseline
            duration_seconds: How long to collect samples
            sample_interval: Time between samples
            callback: Optional progress callback(samples_collected, total_samples)
        
        Returns:
            BaselineMetrics with statistical measures
        """
        cpu_samples: List[float] = []
        memory_samples: List[float] = []
        
        total_samples = int(duration_seconds / sample_interval)
        start_time = datetime.now()
        
        import time
        
        for i in range(total_samples):
            snapshot = self.realtime.get_snapshot()
            cpu_samples.append(snapshot.cpu_metrics.usage_percent)
            memory_samples.append(snapshot.memory_metrics.usage_percent)
            
            if callback:
                callback(i + 1, total_samples)
            
            time.sleep(sample_interval)
        
        # Calculate statistics
        baseline = BaselineMetrics(
            cpu_mean=statistics.mean(cpu_samples),
            cpu_std=statistics.stdev(cpu_samples) if len(cpu_samples) > 1 else 0.0,
            cpu_min=min(cpu_samples),
            cpu_max=max(cpu_samples),
            
            memory_mean=statistics.mean(memory_samples),
            memory_std=statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0.0,
            memory_min=min(memory_samples),
            memory_max=max(memory_samples),
            
            sample_count=len(cpu_samples),
            duration_seconds=duration_seconds,
            created_at=start_time.isoformat()
        )
        
        # Save to database
        if self.database:
            self.database.save_baseline(
                name=name,
                metric_type='system',
                mean_value=baseline.cpu_mean,
                std_value=baseline.cpu_std,
                min_value=baseline.cpu_min,
                max_value=baseline.cpu_max,
                sample_count=baseline.sample_count,
                created_at=start_time
            )
            
            # Also save memory baseline
            self.database.save_baseline(
                name=f"{name}_memory",
                metric_type='memory',
                mean_value=baseline.memory_mean,
                std_value=baseline.memory_std,
                min_value=baseline.memory_min,
                max_value=baseline.memory_max,
                sample_count=baseline.sample_count,
                created_at=start_time
            )
        
        return baseline
    
    def get_baseline(self, name: str) -> Optional[BaselineMetrics]:
        """
        Retrieve a stored baseline.
        
        Args:
            name: Baseline name
        
        Returns:
            BaselineMetrics or None if not found
        """
        if not self.database:
            return None
        
        cpu_baseline = self.database.get_baseline(name)
        mem_baseline = self.database.get_baseline(f"{name}_memory")
        
        if not cpu_baseline:
            return None
        
        return BaselineMetrics(
            cpu_mean=cpu_baseline['mean_value'],
            cpu_std=cpu_baseline['std_value'],
            cpu_min=cpu_baseline['min_value'],
            cpu_max=cpu_baseline['max_value'],
            
            memory_mean=mem_baseline['mean_value'] if mem_baseline else 50.0,
            memory_std=mem_baseline['std_value'] if mem_baseline else 10.0,
            memory_min=mem_baseline['min_value'] if mem_baseline else 0.0,
            memory_max=mem_baseline['max_value'] if mem_baseline else 100.0,
            
            sample_count=cpu_baseline['sample_count'],
            duration_seconds=0.0,  # Not stored
            created_at=cpu_baseline['created_at']
        )
    
    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all stored baselines."""
        if not self.database:
            return []
        
        baselines_dict = self.database.get_all_baselines()
        # Convert to list and filter out memory-only entries to avoid duplicates
        return [{'name': k, **v} for k, v in baselines_dict.items() 
                if not k.endswith('_memory')]
    
    def delete_baseline(self, name: str) -> bool:
        """Delete a stored baseline."""
        if not self.database:
            return False
        
        success1 = self.database.delete_baseline(name)
        success2 = self.database.delete_baseline(f"{name}_memory")
        return success1 or success2
    
    def compare_to_baseline(
        self,
        baseline: BaselineMetrics,
        snapshot: Optional[SystemSnapshot] = None
    ) -> BaselineComparison:
        """
        Compare current system state to a baseline.
        
        Args:
            baseline: The baseline to compare against
            snapshot: Optional current snapshot (taken if not provided)
        
        Returns:
            BaselineComparison with deviation analysis
        """
        if snapshot is None:
            snapshot = self.realtime.get_snapshot()
        
        # Calculate deviations
        cpu_deviation = self._calculate_deviation(
            snapshot.cpu_metrics.usage_percent,
            baseline.cpu_mean,
            baseline.cpu_std
        )
        
        memory_deviation = self._calculate_deviation(
            snapshot.memory_metrics.usage_percent,
            baseline.memory_mean,
            baseline.memory_std
        )
        
        # Determine status
        cpu_status = self._get_status(cpu_deviation)
        memory_status = self._get_status(memory_deviation)
        
        # Overall status (worst of the two)
        status_priority = {'normal': 0, 'elevated': 1, 'critical': 2}
        overall_status = cpu_status if status_priority[cpu_status] >= status_priority[memory_status] else memory_status
        
        # Generate alerts
        alerts = []
        if cpu_status == 'critical':
            alerts.append(f"CPU usage critically elevated: {snapshot.cpu_metrics.usage_percent:.1f}% (baseline: {baseline.cpu_mean:.1f}%)")
        elif cpu_status == 'elevated':
            alerts.append(f"CPU usage elevated: {snapshot.cpu_metrics.usage_percent:.1f}% (baseline: {baseline.cpu_mean:.1f}%)")
        
        if memory_status == 'critical':
            alerts.append(f"Memory usage critically elevated: {snapshot.memory_metrics.usage_percent:.1f}% (baseline: {baseline.memory_mean:.1f}%)")
        elif memory_status == 'elevated':
            alerts.append(f"Memory usage elevated: {snapshot.memory_metrics.usage_percent:.1f}% (baseline: {baseline.memory_mean:.1f}%)")
        
        return BaselineComparison(
            cpu_current=snapshot.cpu_metrics.usage_percent,
            cpu_baseline_mean=baseline.cpu_mean,
            cpu_deviation=cpu_deviation,
            cpu_status=cpu_status,
            
            memory_current=snapshot.memory_metrics.usage_percent,
            memory_baseline_mean=baseline.memory_mean,
            memory_deviation=memory_deviation,
            memory_status=memory_status,
            
            overall_status=overall_status,
            alerts=alerts
        )
    
    def _calculate_deviation(self, current: float, mean: float, std: float) -> float:
        """Calculate number of standard deviations from mean."""
        if std == 0:
            return 0.0 if current == mean else float('inf')
        return (current - mean) / std
    
    def _get_status(self, deviation: float) -> str:
        """Get status based on deviation."""
        abs_dev = abs(deviation)
        if abs_dev >= self.critical_threshold:
            return 'critical'
        elif abs_dev >= self.warning_threshold:
            return 'elevated'
        return 'normal'
    
    def export_baseline(self, name: str, filepath: str) -> bool:
        """
        Export a baseline to JSON file.
        
        Args:
            name: Baseline name
            filepath: Output file path
        
        Returns:
            True if successful
        """
        baseline = self.get_baseline(name)
        if not baseline:
            return False
        
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(baseline), f, indent=2)
            return True
        except Exception:
            return False
    
    def import_baseline(self, filepath: str, name: Optional[str] = None) -> Optional[BaselineMetrics]:
        """
        Import a baseline from JSON file.
        
        Args:
            filepath: Input file path
            name: Optional new name for the baseline
        
        Returns:
            Imported BaselineMetrics or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            baseline = BaselineMetrics(**data)
            
            if name and self.database:
                # Save with new name
                self.database.save_baseline(
                    name=name,
                    metric_type='system',
                    mean_value=baseline.cpu_mean,
                    std_value=baseline.cpu_std,
                    min_value=baseline.cpu_min,
                    max_value=baseline.cpu_max,
                    sample_count=baseline.sample_count,
                    created_at=datetime.fromisoformat(baseline.created_at)
                )
                
                self.database.save_baseline(
                    name=f"{name}_memory",
                    metric_type='memory',
                    mean_value=baseline.memory_mean,
                    std_value=baseline.memory_std,
                    min_value=baseline.memory_min,
                    max_value=baseline.memory_max,
                    sample_count=baseline.sample_count,
                    created_at=datetime.fromisoformat(baseline.created_at)
                )
            
            return baseline
        except Exception:
            return None
