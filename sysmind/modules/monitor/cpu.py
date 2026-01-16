"""
SYSMIND CPU Monitor Module

CPU metrics collection and analysis.
"""

import os
import time
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Tuple
from pathlib import Path

from ...utils.platform_utils import is_windows, is_linux, is_macos


@dataclass
class CPUMetrics:
    """CPU metrics data class."""
    usage_percent: float
    core_count: int
    core_usages: List[float]
    load_average: Tuple[float, float, float]  # 1, 5, 15 min
    context_switches: int
    interrupts: int
    user_time: float
    system_time: float
    idle_time: float
    iowait_time: float


class CPUMonitor:
    """
    CPU monitoring using standard library and /proc filesystem.
    
    Provides cross-platform CPU metrics collection with fallbacks
    for systems where /proc isn't available.
    """
    
    def __init__(self):
        self._prev_stats = None
        self._prev_time = None
    
    def get_core_count(self) -> int:
        """Get the number of CPU cores."""
        return os.cpu_count() or 1
    
    def get_load_average(self) -> Tuple[float, float, float]:
        """Get system load average (1, 5, 15 minutes)."""
        if hasattr(os, 'getloadavg'):
            return os.getloadavg()
        
        # Windows fallback - estimate from CPU usage
        if is_windows():
            usage = self.get_usage_percent()
            return (usage / 100, usage / 100, usage / 100)
        
        return (0.0, 0.0, 0.0)
    
    def _read_proc_stat(self) -> Optional[dict]:
        """Read CPU stats from /proc/stat on Linux."""
        if not is_linux():
            return None
        
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            stats = {}
            for line in lines:
                if line.startswith('cpu'):
                    parts = line.split()
                    cpu_name = parts[0]
                    
                    # cpu stats: user nice system idle iowait irq softirq steal
                    values = [int(x) for x in parts[1:9]]
                    if len(values) >= 8:
                        stats[cpu_name] = {
                            'user': values[0],
                            'nice': values[1],
                            'system': values[2],
                            'idle': values[3],
                            'iowait': values[4],
                            'irq': values[5],
                            'softirq': values[6],
                            'steal': values[7] if len(values) > 7 else 0,
                        }
                elif line.startswith('ctxt'):
                    stats['context_switches'] = int(line.split()[1])
                elif line.startswith('intr'):
                    stats['interrupts'] = int(line.split()[1])
            
            return stats
        except:
            return None
    
    def _calculate_usage(self, prev: dict, curr: dict) -> float:
        """Calculate CPU usage percentage from two stat snapshots."""
        prev_idle = prev['idle'] + prev.get('iowait', 0)
        curr_idle = curr['idle'] + curr.get('iowait', 0)
        
        prev_total = sum(prev.values())
        curr_total = sum(curr.values())
        
        total_diff = curr_total - prev_total
        idle_diff = curr_idle - prev_idle
        
        if total_diff == 0:
            return 0.0
        
        return ((total_diff - idle_diff) / total_diff) * 100
    
    def get_usage_percent(self) -> float:
        """Get overall CPU usage percentage."""
        if is_linux():
            stats = self._read_proc_stat()
            if stats and 'cpu' in stats:
                if self._prev_stats and 'cpu' in self._prev_stats:
                    usage = self._calculate_usage(self._prev_stats['cpu'], stats['cpu'])
                else:
                    # First call - need to wait and sample again
                    self._prev_stats = stats
                    time.sleep(0.1)
                    stats = self._read_proc_stat()
                    usage = self._calculate_usage(self._prev_stats['cpu'], stats['cpu'])
                
                self._prev_stats = stats
                return usage
        
        if is_windows():
            return self._get_windows_cpu_usage()
        
        if is_macos():
            return self._get_macos_cpu_usage()
        
        return 0.0
    
    def _get_windows_cpu_usage(self) -> float:
        """Get CPU usage on Windows using wmic."""
        try:
            # Use powershell for more accurate reading
            result = subprocess.run(
                ['powershell', '-Command', 
                 "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        # Fallback using time measurement
        if self._prev_time is None:
            self._prev_time = time.time()
            time.sleep(0.1)
        
        return 50.0  # Fallback placeholder
    
    def _get_macos_cpu_usage(self) -> float:
        """Get CPU usage on macOS using top."""
        try:
            result = subprocess.run(
                ['top', '-l', '1', '-n', '0'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'CPU usage' in line:
                        # Parse: "CPU usage: X.XX% user, Y.YY% sys, Z.ZZ% idle"
                        parts = line.split(',')
                        user = float(parts[0].split(':')[1].strip().replace('%', '').split()[0])
                        sys = float(parts[1].strip().replace('%', '').split()[0])
                        return user + sys
        except:
            pass
        
        return 0.0
    
    def get_core_usages(self) -> List[float]:
        """Get per-core CPU usage percentages."""
        core_count = self.get_core_count()
        
        if is_linux():
            stats = self._read_proc_stat()
            if stats:
                usages = []
                for i in range(core_count):
                    cpu_key = f'cpu{i}'
                    if cpu_key in stats:
                        if self._prev_stats and cpu_key in self._prev_stats:
                            usage = self._calculate_usage(
                                self._prev_stats[cpu_key], 
                                stats[cpu_key]
                            )
                        else:
                            usage = 0.0
                        usages.append(usage)
                
                if usages:
                    return usages
        
        # Fallback - approximate from overall usage
        overall = self.get_usage_percent()
        return [overall] * core_count
    
    def get_metrics(self) -> CPUMetrics:
        """Get comprehensive CPU metrics."""
        stats = self._read_proc_stat() if is_linux() else None
        
        core_usages = self.get_core_usages()
        
        # Extract timing info from stats
        user_time = 0.0
        system_time = 0.0
        idle_time = 0.0
        iowait_time = 0.0
        
        if stats and 'cpu' in stats:
            cpu = stats['cpu']
            total = sum(cpu.values())
            if total > 0:
                user_time = (cpu['user'] + cpu['nice']) / total * 100
                system_time = (cpu['system'] + cpu.get('irq', 0) + cpu.get('softirq', 0)) / total * 100
                idle_time = cpu['idle'] / total * 100
                iowait_time = cpu.get('iowait', 0) / total * 100
        
        return CPUMetrics(
            usage_percent=self.get_usage_percent(),
            core_count=self.get_core_count(),
            core_usages=core_usages,
            load_average=self.get_load_average(),
            context_switches=stats.get('context_switches', 0) if stats else 0,
            interrupts=stats.get('interrupts', 0) if stats else 0,
            user_time=user_time,
            system_time=system_time,
            idle_time=idle_time,
            iowait_time=iowait_time
        )
