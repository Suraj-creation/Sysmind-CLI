"""
SYSMIND Correlator Module

Cross-module data correlation and pattern detection.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from ..monitor.realtime import RealtimeMonitor, SystemSnapshot
from ..process.manager import ProcessManager
from ...core.database import Database


@dataclass
class CorrelationEvent:
    """Event from correlation analysis."""
    timestamp: datetime
    event_type: str
    severity: str  # info, warning, critical
    description: str
    related_metrics: Dict[str, Any]
    recommendations: List[str]


@dataclass
class ResourceCorrelation:
    """Correlation between resource usage and processes."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    top_cpu_processes: List[Dict[str, Any]]
    top_memory_processes: List[Dict[str, Any]]
    correlation_strength: float  # 0-1


class MetricCorrelator:
    """
    Correlate metrics across system modules.
    
    Identifies patterns and relationships between
    CPU, memory, disk, network, and process data.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize correlator.
        
        Args:
            database: Optional database for historical analysis
        """
        self.database = database
        self.realtime = RealtimeMonitor()
        self.process_manager = ProcessManager()
        
        self._events: List[CorrelationEvent] = []
        self._correlations: List[ResourceCorrelation] = []
    
    def analyze_current_state(self) -> CorrelationEvent:
        """
        Analyze current system state for correlations.
        
        Returns:
            CorrelationEvent with analysis results
        """
        snapshot = self.realtime.get_snapshot()
        processes = self.process_manager.list_processes(sort_by='memory', limit=10)
        
        cpu = snapshot.cpu_metrics.usage_percent
        memory = snapshot.memory_metrics.usage_percent
        
        # Get top consumers
        top_cpu = self.process_manager.get_top_processes(by='cpu', n=5)
        top_memory = self.process_manager.get_top_processes(by='memory', n=5)
        
        # Determine severity
        if cpu > 90 or memory > 90:
            severity = 'critical'
        elif cpu > 70 or memory > 70:
            severity = 'warning'
        else:
            severity = 'info'
        
        # Build description
        descriptions = []
        recommendations = []
        
        if cpu > 80:
            top_cpu_names = [p.name for p in top_cpu[:3]]
            descriptions.append(f"High CPU usage ({cpu:.1f}%)")
            descriptions.append(f"Top CPU consumers: {', '.join(top_cpu_names)}")
            recommendations.append("Consider closing CPU-intensive applications")
        
        if memory > 80:
            top_mem_names = [p.name for p in top_memory[:3]]
            descriptions.append(f"High memory usage ({memory:.1f}%)")
            descriptions.append(f"Top memory consumers: {', '.join(top_mem_names)}")
            recommendations.append("Consider closing memory-intensive applications")
        
        if not descriptions:
            descriptions.append(f"System running normally (CPU: {cpu:.1f}%, Memory: {memory:.1f}%)")
        
        # Store correlation
        correlation = ResourceCorrelation(
            timestamp=datetime.now(),
            cpu_percent=cpu,
            memory_percent=memory,
            top_cpu_processes=[{'name': p.name, 'pid': p.pid, 'cpu': p.cpu_percent} for p in top_cpu],
            top_memory_processes=[{'name': p.name, 'pid': p.pid, 'memory': p.memory_rss} for p in top_memory],
            correlation_strength=self._calculate_correlation_strength(cpu, memory)
        )
        self._correlations.append(correlation)
        
        event = CorrelationEvent(
            timestamp=datetime.now(),
            event_type='system_analysis',
            severity=severity,
            description=' | '.join(descriptions),
            related_metrics={
                'cpu_percent': cpu,
                'memory_percent': memory,
                'process_count': len(processes),
            },
            recommendations=recommendations
        )
        
        self._events.append(event)
        return event
    
    def _calculate_correlation_strength(self, cpu: float, memory: float) -> float:
        """
        Calculate correlation strength between CPU and memory.
        
        When both are high or both are low, correlation is strong.
        """
        # Normalize to 0-1
        cpu_norm = cpu / 100
        memory_norm = memory / 100
        
        # Calculate correlation as similarity
        diff = abs(cpu_norm - memory_norm)
        return 1 - diff
    
    def detect_resource_spikes(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        samples: int = 10
    ) -> List[CorrelationEvent]:
        """
        Detect sudden spikes in resource usage.
        
        Args:
            cpu_threshold: CPU percentage to consider a spike
            memory_threshold: Memory percentage to consider a spike
            samples: Number of samples to collect
        
        Returns:
            List of spike events detected
        """
        import time
        
        events = []
        history = []
        
        for _ in range(samples):
            snapshot = self.realtime.get_snapshot()
            history.append({
                'time': datetime.now(),
                'cpu': snapshot.cpu_metrics.usage_percent,
                'memory': snapshot.memory_metrics.usage_percent,
            })
            time.sleep(1)
        
        # Detect spikes
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            
            cpu_jump = curr['cpu'] - prev['cpu']
            mem_jump = curr['memory'] - prev['memory']
            
            if curr['cpu'] > cpu_threshold and cpu_jump > 20:
                events.append(CorrelationEvent(
                    timestamp=curr['time'],
                    event_type='cpu_spike',
                    severity='warning',
                    description=f"CPU spike detected: {prev['cpu']:.1f}% -> {curr['cpu']:.1f}%",
                    related_metrics={'cpu_before': prev['cpu'], 'cpu_after': curr['cpu']},
                    recommendations=['Check recently started processes']
                ))
            
            if curr['memory'] > memory_threshold and mem_jump > 10:
                events.append(CorrelationEvent(
                    timestamp=curr['time'],
                    event_type='memory_spike',
                    severity='warning',
                    description=f"Memory spike detected: {prev['memory']:.1f}% -> {curr['memory']:.1f}%",
                    related_metrics={'memory_before': prev['memory'], 'memory_after': curr['memory']},
                    recommendations=['Check for memory leaks or large allocations']
                ))
        
        return events
    
    def find_resource_hogs(self) -> List[Dict[str, Any]]:
        """
        Find processes that are resource hogs.
        
        Returns:
            List of process info with resource usage
        """
        processes = self.process_manager.list_processes()
        
        hogs = []
        
        for proc in processes:
            # Check if process is a resource hog
            is_cpu_hog = proc.cpu_percent > 50
            is_memory_hog = proc.memory_rss > 500 * 1024 * 1024  # 500 MB
            
            if is_cpu_hog or is_memory_hog:
                hogs.append({
                    'pid': proc.pid,
                    'name': proc.name,
                    'cpu_percent': proc.cpu_percent,
                    'memory_mb': proc.memory_rss / (1024 * 1024),
                    'is_cpu_hog': is_cpu_hog,
                    'is_memory_hog': is_memory_hog,
                })
        
        # Sort by combined resource usage
        hogs.sort(key=lambda x: x['cpu_percent'] + x['memory_mb'] / 100, reverse=True)
        
        return hogs
    
    def get_resource_trends(self, minutes: int = 10) -> Dict[str, Any]:
        """
        Analyze resource usage trends.
        
        Args:
            minutes: Time window to analyze
        
        Returns:
            Dictionary with trend analysis
        """
        if len(self._correlations) < 2:
            return {
                'insufficient_data': True,
                'message': 'Need more samples to determine trends'
            }
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [c for c in self._correlations if c.timestamp >= cutoff]
        
        if len(recent) < 2:
            return {
                'insufficient_data': True,
                'message': 'Need more recent samples'
            }
        
        # Calculate trends
        cpu_values = [c.cpu_percent for c in recent]
        memory_values = [c.memory_percent for c in recent]
        
        cpu_trend = cpu_values[-1] - cpu_values[0]
        memory_trend = memory_values[-1] - memory_values[0]
        
        cpu_avg = sum(cpu_values) / len(cpu_values)
        memory_avg = sum(memory_values) / len(memory_values)
        
        trend_direction = 'stable'
        if cpu_trend > 10 or memory_trend > 10:
            trend_direction = 'increasing'
        elif cpu_trend < -10 or memory_trend < -10:
            trend_direction = 'decreasing'
        
        return {
            'insufficient_data': False,
            'sample_count': len(recent),
            'time_window_minutes': minutes,
            'cpu': {
                'current': cpu_values[-1],
                'average': cpu_avg,
                'min': min(cpu_values),
                'max': max(cpu_values),
                'trend': cpu_trend,
            },
            'memory': {
                'current': memory_values[-1],
                'average': memory_avg,
                'min': min(memory_values),
                'max': max(memory_values),
                'trend': memory_trend,
            },
            'overall_trend': trend_direction,
        }
    
    def get_events(
        self,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[CorrelationEvent]:
        """
        Get recent correlation events.
        
        Args:
            severity: Filter by severity
            event_type: Filter by event type
            limit: Maximum events to return
        
        Returns:
            List of events (newest first)
        """
        events = self._events.copy()
        events.reverse()
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[:limit]
