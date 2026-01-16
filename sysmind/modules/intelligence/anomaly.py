"""
SYSMIND Anomaly Detection Module

Statistical anomaly detection for system metrics.
"""

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import deque

from ..monitor.realtime import RealtimeMonitor
from ...core.database import Database


@dataclass
class Anomaly:
    """Detected anomaly."""
    timestamp: datetime
    metric: str
    value: float
    expected_range: tuple  # (min, max)
    severity: str  # info, warning, critical
    deviation: float  # Standard deviations from mean
    description: str


@dataclass
class AnomalyStats:
    """Statistics for anomaly detection."""
    metric: str
    sample_count: int
    mean: float
    std: float
    min: float
    max: float
    threshold_low: float
    threshold_high: float


class AnomalyDetector:
    """
    Statistical anomaly detection for system metrics.
    
    Uses rolling statistics to detect unusual patterns
    in CPU, memory, and other system metrics.
    """
    
    def __init__(
        self,
        database: Optional[Database] = None,
        window_size: int = 100,
        sensitivity: float = 2.0
    ):
        """
        Initialize anomaly detector.
        
        Args:
            database: Optional database for persistence
            window_size: Number of samples for rolling statistics
            sensitivity: Number of standard deviations for anomaly threshold
        """
        self.database = database
        self.window_size = window_size
        self.sensitivity = sensitivity
        
        self.realtime = RealtimeMonitor()
        
        # Rolling windows for each metric
        self._windows: Dict[str, deque] = {
            'cpu': deque(maxlen=window_size),
            'memory': deque(maxlen=window_size),
            'load_1': deque(maxlen=window_size),
        }
        
        self._anomalies: List[Anomaly] = []
        self._stats_cache: Dict[str, AnomalyStats] = {}
    
    def _calculate_stats(self, metric: str) -> Optional[AnomalyStats]:
        """Calculate statistics for a metric."""
        window = self._windows.get(metric)
        if not window or len(window) < 10:
            return None
        
        values = list(window)
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        
        # Prevent division by zero
        if std == 0:
            std = 0.1
        
        threshold_low = mean - (self.sensitivity * std)
        threshold_high = mean + (self.sensitivity * std)
        
        stats = AnomalyStats(
            metric=metric,
            sample_count=len(values),
            mean=mean,
            std=std,
            min=min(values),
            max=max(values),
            threshold_low=max(0, threshold_low),  # Can't go below 0
            threshold_high=min(100, threshold_high)  # Can't exceed 100%
        )
        
        self._stats_cache[metric] = stats
        return stats
    
    def add_sample(self, metric: str, value: float) -> Optional[Anomaly]:
        """
        Add a sample and check for anomaly.
        
        Args:
            metric: Metric name
            value: Metric value
        
        Returns:
            Anomaly if detected, None otherwise
        """
        if metric not in self._windows:
            self._windows[metric] = deque(maxlen=self.window_size)
        
        window = self._windows[metric]
        
        # Check for anomaly before adding new sample
        anomaly = None
        if len(window) >= 10:
            stats = self._calculate_stats(metric)
            if stats:
                if value < stats.threshold_low or value > stats.threshold_high:
                    deviation = abs(value - stats.mean) / stats.std
                    
                    # Determine severity
                    if deviation > 3:
                        severity = 'critical'
                    elif deviation > 2:
                        severity = 'warning'
                    else:
                        severity = 'info'
                    
                    # Create description
                    direction = 'high' if value > stats.mean else 'low'
                    description = f"{metric} anomaly: {value:.1f}% is unusually {direction} (expected {stats.threshold_low:.1f}% - {stats.threshold_high:.1f}%)"
                    
                    anomaly = Anomaly(
                        timestamp=datetime.now(),
                        metric=metric,
                        value=value,
                        expected_range=(stats.threshold_low, stats.threshold_high),
                        severity=severity,
                        deviation=deviation,
                        description=description
                    )
                    
                    self._anomalies.append(anomaly)
        
        # Add to window
        window.append(value)
        
        return anomaly
    
    def analyze_snapshot(self) -> List[Anomaly]:
        """
        Analyze current system snapshot for anomalies.
        
        Returns:
            List of detected anomalies
        """
        snapshot = self.realtime.get_snapshot()
        anomalies = []
        
        # Check CPU
        cpu_anomaly = self.add_sample('cpu', snapshot.cpu_metrics.usage_percent)
        if cpu_anomaly:
            anomalies.append(cpu_anomaly)
        
        # Check memory
        memory_anomaly = self.add_sample('memory', snapshot.memory_metrics.usage_percent)
        if memory_anomaly:
            anomalies.append(memory_anomaly)
        
        # Check load average (1 min)
        load_anomaly = self.add_sample('load_1', snapshot.cpu_metrics.load_average[0])
        if load_anomaly:
            anomalies.append(load_anomaly)
        
        return anomalies
    
    def continuous_monitoring(
        self,
        duration: float = 60.0,
        interval: float = 1.0,
        callback: Optional[callable] = None
    ) -> List[Anomaly]:
        """
        Monitor for anomalies over a period.
        
        Args:
            duration: How long to monitor in seconds
            interval: Sample interval in seconds
            callback: Function to call on anomaly detection
        
        Returns:
            List of all anomalies detected
        """
        import time
        
        all_anomalies = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            anomalies = self.analyze_snapshot()
            
            if anomalies:
                all_anomalies.extend(anomalies)
                
                if callback:
                    for anomaly in anomalies:
                        callback(anomaly)
            
            time.sleep(interval)
        
        return all_anomalies
    
    def get_stats(self) -> Dict[str, AnomalyStats]:
        """
        Get current statistics for all metrics.
        
        Returns:
            Dictionary mapping metric name to stats
        """
        for metric in self._windows:
            self._calculate_stats(metric)
        
        return self._stats_cache.copy()
    
    def get_recent_anomalies(
        self,
        minutes: int = 60,
        severity: Optional[str] = None
    ) -> List[Anomaly]:
        """
        Get recent anomalies.
        
        Args:
            minutes: Time window in minutes
            severity: Filter by severity
        
        Returns:
            List of anomalies (newest first)
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        anomalies = [a for a in self._anomalies if a.timestamp >= cutoff]
        
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        
        anomalies.sort(key=lambda a: a.timestamp, reverse=True)
        
        return anomalies
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """
        Get summary of anomaly detection status.
        
        Returns:
            Dictionary with summary information
        """
        recent = self.get_recent_anomalies(minutes=60)
        
        by_severity = {'info': 0, 'warning': 0, 'critical': 0}
        by_metric: Dict[str, int] = {}
        
        for anomaly in recent:
            by_severity[anomaly.severity] = by_severity.get(anomaly.severity, 0) + 1
            by_metric[anomaly.metric] = by_metric.get(anomaly.metric, 0) + 1
        
        return {
            'total_anomalies_1h': len(recent),
            'by_severity': by_severity,
            'by_metric': by_metric,
            'metrics_monitored': len(self._windows),
            'samples_collected': sum(len(w) for w in self._windows.values()),
        }
    
    def reset(self):
        """Reset all statistics and history."""
        for window in self._windows.values():
            window.clear()
        
        self._anomalies.clear()
        self._stats_cache.clear()
    
    def set_sensitivity(self, sensitivity: float):
        """
        Set anomaly detection sensitivity.
        
        Args:
            sensitivity: Number of standard deviations for threshold
        """
        self.sensitivity = max(0.5, min(5.0, sensitivity))  # Clamp to reasonable range
