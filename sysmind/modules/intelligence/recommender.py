"""
SYSMIND Recommender Module

AI-driven system optimization recommendations.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..monitor.realtime import RealtimeMonitor
from ..process.manager import ProcessManager
from ..disk.analyzer import DiskAnalyzer
from ..network.bandwidth import BandwidthMonitor
from ...core.database import Database


@dataclass 
class Recommendation:
    """System optimization recommendation."""
    id: str
    category: str  # performance, disk, memory, startup, network
    priority: str  # low, medium, high, critical
    title: str
    description: str
    impact: str
    action: str
    automated: bool  # Can be automated
    risk: str  # low, medium, high


class SystemRecommender:
    """
    Generate intelligent system optimization recommendations.
    
    Analyzes system state and provides actionable suggestions
    for improving performance, freeing resources, and optimizing
    system configuration.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """
        Initialize recommender.
        
        Args:
            database: Optional database for historical analysis
        """
        self.database = database
        self.realtime = RealtimeMonitor()
        self.process_manager = ProcessManager()
        self.disk_analyzer = DiskAnalyzer()
        self.bandwidth_monitor = BandwidthMonitor()
    
    def get_all_recommendations(self) -> List[Recommendation]:
        """
        Generate all recommendations based on current system state.
        
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        
        recommendations.extend(self._analyze_performance())
        recommendations.extend(self._analyze_memory())
        recommendations.extend(self._analyze_disk())
        recommendations.extend(self._analyze_processes())
        recommendations.extend(self._analyze_startup())
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 4))
        
        return recommendations
    
    def _analyze_performance(self) -> List[Recommendation]:
        """Analyze CPU/performance issues."""
        recommendations = []
        
        snapshot = self.realtime.get_snapshot()
        cpu = snapshot.cpu_metrics
        
        # High CPU usage
        if cpu.usage_percent > 80:
            top_cpu = self.process_manager.get_top_processes(by='cpu', n=3)
            process_names = [p.name for p in top_cpu]
            
            recommendations.append(Recommendation(
                id='perf_high_cpu',
                category='performance',
                priority='high' if cpu.usage_percent > 90 else 'medium',
                title='High CPU Usage Detected',
                description=f'CPU usage is at {cpu.usage_percent:.1f}%. Top consumers: {", ".join(process_names)}',
                impact='System responsiveness may be degraded',
                action='Consider closing resource-intensive applications or investigate processes',
                automated=False,
                risk='low'
            ))
        
        # High load average
        load_1, load_5, load_15 = cpu.load_average
        cores = cpu.core_count
        
        if load_1 > cores * 2:
            recommendations.append(Recommendation(
                id='perf_high_load',
                category='performance',
                priority='high',
                title='System Under Heavy Load',
                description=f'Load average ({load_1:.2f}) exceeds recommended threshold for {cores} cores',
                impact='System may become unresponsive',
                action='Investigate running processes and consider scheduling tasks',
                automated=False,
                risk='medium'
            ))
        
        return recommendations
    
    def _analyze_memory(self) -> List[Recommendation]:
        """Analyze memory issues."""
        recommendations = []
        
        snapshot = self.realtime.get_snapshot()
        memory = snapshot.memory_metrics
        
        # High memory usage
        if memory.usage_percent > 85:
            top_memory = self.process_manager.get_top_processes(by='memory', n=3)
            
            mem_details = []
            for p in top_memory:
                mem_mb = p.memory_rss / (1024 * 1024)
                mem_details.append(f'{p.name} ({mem_mb:.0f} MB)')
            
            recommendations.append(Recommendation(
                id='mem_high_usage',
                category='memory',
                priority='critical' if memory.usage_percent > 95 else 'high',
                title='High Memory Usage',
                description=f'Memory usage at {memory.usage_percent:.1f}%. Top consumers: {", ".join(mem_details)}',
                impact='System may swap to disk, causing slowdowns',
                action='Close memory-intensive applications or add more RAM',
                automated=False,
                risk='low'
            ))
        
        # High swap usage
        if memory.swap_total > 0 and memory.swap_percent > 50:
            recommendations.append(Recommendation(
                id='mem_high_swap',
                category='memory',
                priority='medium',
                title='Significant Swap Usage',
                description=f'Swap usage at {memory.swap_percent:.1f}% indicates memory pressure',
                impact='Disk I/O increases, performance degrades',
                action='Free up RAM or consider adding more memory',
                automated=False,
                risk='low'
            ))
        
        return recommendations
    
    def _analyze_disk(self) -> List[Recommendation]:
        """Analyze disk space issues."""
        recommendations = []
        
        try:
            partitions = self.disk_analyzer.list_partitions()
            
            for part in partitions:
                if part['percent'] > 85:
                    recommendations.append(Recommendation(
                        id=f"disk_space_{part['mountpoint'].replace('/', '_')}",
                        category='disk',
                        priority='critical' if part['percent'] > 95 else 'high',
                        title=f"Low Disk Space on {part['mountpoint']}",
                        description=f"Disk is {part['percent']:.1f}% full ({part['free'] / (1024**3):.1f} GB free)",
                        impact='May cause application failures or system instability',
                        action='Run disk cleanup, remove old files, or add storage',
                        automated=True,
                        risk='medium'
                    ))
        except:
            pass
        
        return recommendations
    
    def _analyze_processes(self) -> List[Recommendation]:
        """Analyze process-related issues."""
        recommendations = []
        
        processes = self.process_manager.list_processes()
        
        # Check for zombies
        zombies = [p for p in processes if 'zombie' in p.status.lower()]
        if zombies:
            recommendations.append(Recommendation(
                id='proc_zombies',
                category='performance',
                priority='low',
                title='Zombie Processes Detected',
                description=f'Found {len(zombies)} zombie processes',
                impact='Minor resource waste',
                action='Parent processes should be fixed to reap children',
                automated=False,
                risk='low'
            ))
        
        # Check for too many processes
        if len(processes) > 500:
            recommendations.append(Recommendation(
                id='proc_many',
                category='performance',
                priority='low',
                title='High Process Count',
                description=f'{len(processes)} processes running',
                impact='May indicate runaway process creation',
                action='Review running applications and services',
                automated=False,
                risk='low'
            ))
        
        # Check for duplicate instances
        process_names: Dict[str, int] = {}
        for p in processes:
            process_names[p.name] = process_names.get(p.name, 0) + 1
        
        duplicates = [(name, count) for name, count in process_names.items() 
                     if count > 10 and name not in ['python', 'chrome', 'firefox', 'java']]
        
        for name, count in duplicates[:3]:
            recommendations.append(Recommendation(
                id=f'proc_dup_{name}',
                category='performance',
                priority='medium',
                title=f'Multiple {name} Instances',
                description=f'{count} instances of {name} running',
                impact='May indicate runaway process or memory leak',
                action=f'Review if all {name} instances are needed',
                automated=False,
                risk='medium'
            ))
        
        return recommendations
    
    def _analyze_startup(self) -> List[Recommendation]:
        """Analyze startup optimization opportunities."""
        recommendations = []
        
        from ..process.startup import StartupManager
        
        try:
            startup = StartupManager()
            items = startup.list_startup_items()
            
            if len(items) > 15:
                recommendations.append(Recommendation(
                    id='startup_many',
                    category='startup',
                    priority='medium',
                    title='Many Startup Programs',
                    description=f'{len(items)} programs configured to run at startup',
                    impact='Slower boot time and initial system responsiveness',
                    action='Review and disable unnecessary startup programs',
                    automated=True,
                    risk='low'
                ))
            
            # Get startup analysis
            analysis = startup.analyze_startup_impact()
            if analysis['potentially_heavy']:
                recommendations.append(Recommendation(
                    id='startup_heavy',
                    category='startup',
                    priority='medium',
                    title='Heavy Startup Programs',
                    description=f'Resource-intensive programs at startup: {", ".join(analysis["potentially_heavy"][:5])}',
                    impact='Slower boot and delayed availability',
                    action='Consider disabling or delaying heavy startup items',
                    automated=False,
                    risk='low'
                ))
        except:
            pass
        
        return recommendations
    
    def get_quick_wins(self) -> List[Recommendation]:
        """
        Get easy-to-implement recommendations with high impact.
        
        Returns:
            List of quick-win recommendations
        """
        all_recs = self.get_all_recommendations()
        
        # Quick wins: automated + low risk + high/medium priority
        quick_wins = [
            r for r in all_recs
            if r.automated and r.risk == 'low' and r.priority in ['high', 'medium']
        ]
        
        return quick_wins
    
    def get_recommendations_by_category(self, category: str) -> List[Recommendation]:
        """
        Get recommendations for a specific category.
        
        Args:
            category: Category to filter by
        
        Returns:
            Filtered list of recommendations
        """
        all_recs = self.get_all_recommendations()
        return [r for r in all_recs if r.category == category]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all recommendations.
        
        Returns:
            Summary statistics
        """
        all_recs = self.get_all_recommendations()
        
        by_priority = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        by_category: Dict[str, int] = {}
        
        for rec in all_recs:
            by_priority[rec.priority] = by_priority.get(rec.priority, 0) + 1
            by_category[rec.category] = by_category.get(rec.category, 0) + 1
        
        return {
            'total': len(all_recs),
            'by_priority': by_priority,
            'by_category': by_category,
            'automatable': sum(1 for r in all_recs if r.automated),
            'critical_count': by_priority['critical'],
        }
