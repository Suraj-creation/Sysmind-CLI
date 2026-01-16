"""
SYSMIND Health Score Module

Composite system health scoring.
"""

from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from ..monitor.realtime import RealtimeMonitor
from ..process.manager import ProcessManager
from ..disk.analyzer import DiskAnalyzer
from ..network.bandwidth import BandwidthMonitor
from .anomaly import AnomalyDetector
from .recommender import SystemRecommender
from ...core.database import Database


@dataclass
class HealthComponent:
    """Health score for a single component."""
    name: str
    score: int  # 0-100
    status: str  # excellent, good, fair, poor, critical
    issues: List[str]
    details: Dict[str, Any]


@dataclass
class SystemHealth:
    """Overall system health assessment."""
    timestamp: datetime
    overall_score: int  # 0-100
    overall_status: str
    components: Dict[str, HealthComponent]
    recommendations: List[str]


class HealthScorer:
    """
    Calculate composite system health score.
    
    Combines metrics from CPU, memory, disk, network,
    and process analysis into a single health score.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize health scorer.
        
        Args:
            database: Optional database for historical tracking
        """
        self.database = database
        self.realtime = RealtimeMonitor()
        self.process_manager = ProcessManager()
        self.disk_analyzer = DiskAnalyzer()
        self.bandwidth_monitor = BandwidthMonitor()
        self.anomaly_detector = AnomalyDetector()
        self.recommender = SystemRecommender(database)
        
        # Weights for each component
        self.weights = {
            'cpu': 0.25,
            'memory': 0.25,
            'disk': 0.20,
            'processes': 0.15,
            'network': 0.15,
        }
    
    def _score_to_status(self, score: int) -> str:
        """Convert score to status string."""
        if score >= 90:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 25:
            return 'poor'
        else:
            return 'critical'
    
    def _calculate_cpu_health(self) -> HealthComponent:
        """Calculate CPU health score."""
        snapshot = self.realtime.get_snapshot()
        cpu = snapshot.cpu_metrics
        
        issues = []
        
        # Base score from usage (inverted - lower usage = higher score)
        usage_score = max(0, 100 - cpu.usage_percent)
        
        # Load average factor
        load_factor = 1.0
        if cpu.load_average[0] > cpu.core_count:
            load_factor = max(0.5, 1 - (cpu.load_average[0] - cpu.core_count) / cpu.core_count * 0.5)
            issues.append(f"High load average: {cpu.load_average[0]:.2f}")
        
        # Usage penalty
        if cpu.usage_percent > 90:
            issues.append(f"Critical CPU usage: {cpu.usage_percent:.1f}%")
        elif cpu.usage_percent > 70:
            issues.append(f"High CPU usage: {cpu.usage_percent:.1f}%")
        
        score = int(usage_score * load_factor)
        
        return HealthComponent(
            name='CPU',
            score=score,
            status=self._score_to_status(score),
            issues=issues,
            details={
                'usage_percent': cpu.usage_percent,
                'load_average': cpu.load_average,
                'core_count': cpu.core_count,
            }
        )
    
    def _calculate_memory_health(self) -> HealthComponent:
        """Calculate memory health score."""
        snapshot = self.realtime.get_snapshot()
        memory = snapshot.memory_metrics
        
        issues = []
        
        # Base score from available memory percentage
        available_percent = 100 - memory.usage_percent
        score = int(available_percent)
        
        # Swap penalty
        if memory.swap_total > 0 and memory.swap_percent > 50:
            score = int(score * 0.9)
            issues.append(f"High swap usage: {memory.swap_percent:.1f}%")
        
        if memory.usage_percent > 90:
            issues.append(f"Critical memory usage: {memory.usage_percent:.1f}%")
        elif memory.usage_percent > 80:
            issues.append(f"High memory usage: {memory.usage_percent:.1f}%")
        
        return HealthComponent(
            name='Memory',
            score=max(0, min(100, score)),
            status=self._score_to_status(score),
            issues=issues,
            details={
                'usage_percent': memory.usage_percent,
                'available_gb': memory.available / (1024**3),
                'swap_percent': memory.swap_percent,
            }
        )
    
    def _calculate_disk_health(self) -> HealthComponent:
        """Calculate disk health score."""
        issues = []
        scores = []
        
        try:
            partitions = self.disk_analyzer.list_partitions()
            
            for part in partitions:
                # Score based on free space
                free_percent = 100 - part['percent']
                scores.append(free_percent)
                
                if part['percent'] > 95:
                    issues.append(f"Critical: {part['mountpoint']} is {part['percent']:.1f}% full")
                elif part['percent'] > 85:
                    issues.append(f"Warning: {part['mountpoint']} is {part['percent']:.1f}% full")
            
            # Use minimum score (worst partition determines health)
            score = int(min(scores)) if scores else 100
        except:
            score = 100  # If we can't check, assume ok
        
        return HealthComponent(
            name='Disk',
            score=score,
            status=self._score_to_status(score),
            issues=issues,
            details={
                'partitions_checked': len(scores) if scores else 0,
            }
        )
    
    def _calculate_process_health(self) -> HealthComponent:
        """Calculate process health score."""
        issues = []
        score = 100
        
        processes = self.process_manager.list_processes()
        
        # Check for zombies
        zombies = [p for p in processes if 'zombie' in p.status.lower()]
        if zombies:
            score -= len(zombies) * 2
            issues.append(f"{len(zombies)} zombie processes")
        
        # Check for excessive process count
        if len(processes) > 500:
            score -= 10
            issues.append(f"High process count: {len(processes)}")
        
        # Check for resource hogs
        memory_hogs = [p for p in processes if p.memory_rss > 1024 * 1024 * 1024]  # > 1 GB
        if len(memory_hogs) > 5:
            score -= len(memory_hogs) * 2
            issues.append(f"{len(memory_hogs)} processes using > 1GB memory")
        
        return HealthComponent(
            name='Processes',
            score=max(0, min(100, score)),
            status=self._score_to_status(score),
            issues=issues,
            details={
                'total_processes': len(processes),
                'zombie_count': len(zombies),
                'memory_hogs': len(memory_hogs),
            }
        )
    
    def _calculate_network_health(self) -> HealthComponent:
        """Calculate network health score."""
        issues = []
        score = 100
        
        try:
            # Check interface stats
            stats = self.bandwidth_monitor.get_interface_stats()
            
            for name, iface in stats.items():
                if name.startswith('lo'):
                    continue
                
                # Check for errors
                total_errors = iface.errors_in + iface.errors_out
                if total_errors > 1000:
                    score -= 10
                    issues.append(f"High error count on {name}: {total_errors}")
                
                # Check for drops
                total_drops = iface.drop_in + iface.drop_out
                if total_drops > 1000:
                    score -= 10
                    issues.append(f"High packet drops on {name}: {total_drops}")
        except:
            pass  # Network info unavailable
        
        return HealthComponent(
            name='Network',
            score=max(0, min(100, score)),
            status=self._score_to_status(score),
            issues=issues,
            details={}
        )
    
    def calculate_health(self) -> SystemHealth:
        """
        Calculate overall system health.
        
        Returns:
            SystemHealth with component scores and overall assessment
        """
        components = {}
        
        # Calculate each component
        components['cpu'] = self._calculate_cpu_health()
        components['memory'] = self._calculate_memory_health()
        components['disk'] = self._calculate_disk_health()
        components['processes'] = self._calculate_process_health()
        components['network'] = self._calculate_network_health()
        
        # Calculate weighted overall score
        overall_score = 0
        for name, component in components.items():
            weight = self.weights.get(name, 0.1)
            overall_score += component.score * weight
        
        overall_score = int(overall_score)
        
        # Collect all issues
        all_issues = []
        for component in components.values():
            all_issues.extend(component.issues)
        
        # Get recommendations
        recs = self.recommender.get_all_recommendations()
        recommendations = [r.title for r in recs[:5]]
        
        return SystemHealth(
            timestamp=datetime.now(),
            overall_score=overall_score,
            overall_status=self._score_to_status(overall_score),
            components=components,
            recommendations=recommendations
        )
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health score history.
        
        Args:
            hours: Hours of history to retrieve
        
        Returns:
            List of historical health scores
        """
        if not self.database:
            return []
        
        # Would query database for historical health scores
        # For now, return current only
        health = self.calculate_health()
        return [{
            'timestamp': health.timestamp.isoformat(),
            'score': health.overall_score,
            'status': health.overall_status,
        }]
    
    def get_component_summary(self) -> Dict[str, int]:
        """
        Get summary of component health scores.
        
        Returns:
            Dictionary mapping component name to score
        """
        health = self.calculate_health()
        return {name: comp.score for name, comp in health.components.items()}
    
    def export_health_report(self) -> str:
        """
        Generate a text health report.
        
        Returns:
            Formatted health report string
        """
        health = self.calculate_health()
        
        lines = [
            "=" * 50,
            "SYSMIND SYSTEM HEALTH REPORT",
            f"Generated: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            "",
            f"Overall Health Score: {health.overall_score}/100 ({health.overall_status.upper()})",
            "",
            "Component Scores:",
            "-" * 30,
        ]
        
        for name, component in health.components.items():
            lines.append(f"  {component.name}: {component.score}/100 ({component.status})")
            for issue in component.issues:
                lines.append(f"    - {issue}")
        
        if health.recommendations:
            lines.append("")
            lines.append("Top Recommendations:")
            lines.append("-" * 30)
            for i, rec in enumerate(health.recommendations, 1):
                lines.append(f"  {i}. {rec}")
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines)
