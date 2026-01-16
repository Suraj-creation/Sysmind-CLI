"""
SYSMIND Process Profiler Module

Detailed process analysis and resource profiling.
"""

import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from .manager import ProcessManager, ProcessInfo
from ...utils.platform_utils import is_linux, is_windows
from ...core.errors import ProcessError


@dataclass
class ProcessProfile:
    """Detailed process profile."""
    pid: int
    name: str
    
    # Memory details
    memory_rss: int
    memory_vms: int
    memory_percent: float
    
    # CPU details
    cpu_percent: float
    cpu_times_user: float
    cpu_times_system: float
    
    # I/O details
    io_read_bytes: int
    io_write_bytes: int
    io_read_count: int
    io_write_count: int
    
    # File descriptors
    open_files: List[str]
    connections: List[Dict[str, Any]]
    
    # Environment
    cwd: str
    environ: Dict[str, str]
    
    # Threads
    threads: int
    
    # Timing
    create_time: datetime
    running_time: timedelta


class ProcessProfiler:
    """
    Deep process analysis and profiling.
    
    Provides detailed information about process resource usage,
    I/O patterns, and system interactions.
    """
    
    def __init__(self):
        self.manager = ProcessManager()
        self._cpu_times_cache: Dict[int, Tuple[float, float, float]] = {}  # pid -> (user, system, timestamp)
    
    def _read_proc_io(self, pid: int) -> Dict[str, int]:
        """Read I/O stats from /proc/[pid]/io on Linux."""
        io_stats = {
            'read_bytes': 0,
            'write_bytes': 0,
            'read_count': 0,
            'write_count': 0,
        }
        
        try:
            with open(f'/proc/{pid}/io', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        key = key.strip()
                        val = int(val.strip())
                        
                        if key == 'read_bytes':
                            io_stats['read_bytes'] = val
                        elif key == 'write_bytes':
                            io_stats['write_bytes'] = val
                        elif key == 'syscr':
                            io_stats['read_count'] = val
                        elif key == 'syscw':
                            io_stats['write_count'] = val
        except:
            pass
        
        return io_stats
    
    def _read_proc_statm(self, pid: int) -> Dict[str, int]:
        """Read memory stats from /proc/[pid]/statm on Linux."""
        try:
            with open(f'/proc/{pid}/statm', 'r') as f:
                parts = f.read().split()
            
            page_size = os.sysconf('SC_PAGE_SIZE')
            
            return {
                'vms': int(parts[0]) * page_size,
                'rss': int(parts[1]) * page_size,
                'shared': int(parts[2]) * page_size,
            }
        except:
            return {'vms': 0, 'rss': 0, 'shared': 0}
    
    def _read_proc_fd(self, pid: int) -> List[str]:
        """Read open file descriptors from /proc/[pid]/fd on Linux."""
        files = []
        
        try:
            fd_dir = f'/proc/{pid}/fd'
            for fd in os.listdir(fd_dir):
                try:
                    link = os.readlink(f'{fd_dir}/{fd}')
                    if not link.startswith('pipe:') and not link.startswith('socket:'):
                        files.append(link)
                except:
                    pass
        except:
            pass
        
        return files[:100]  # Limit to 100
    
    def _read_proc_cwd(self, pid: int) -> str:
        """Read current working directory from /proc/[pid]/cwd on Linux."""
        try:
            return os.readlink(f'/proc/{pid}/cwd')
        except:
            return ''
    
    def _read_proc_environ(self, pid: int) -> Dict[str, str]:
        """Read environment from /proc/[pid]/environ on Linux."""
        environ = {}
        
        try:
            with open(f'/proc/{pid}/environ', 'r') as f:
                content = f.read()
            
            for item in content.split('\x00'):
                if '=' in item:
                    key, val = item.split('=', 1)
                    environ[key] = val
        except:
            pass
        
        return environ
    
    def _get_cpu_percent(self, pid: int) -> float:
        """Calculate CPU percent for a process."""
        if not is_linux():
            return 0.0
        
        try:
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read()
            
            # Parse stat
            end = stat.rfind(')')
            parts = stat[end+2:].split()
            
            utime = int(parts[11])
            stime = int(parts[12])
            
            clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            current_time = time.time()
            
            # Check cache
            if pid in self._cpu_times_cache:
                prev_utime, prev_stime, prev_time = self._cpu_times_cache[pid]
                
                delta_time = current_time - prev_time
                if delta_time > 0:
                    delta_utime = (utime - prev_utime) / clk_tck
                    delta_stime = (stime - prev_stime) / clk_tck
                    cpu_percent = ((delta_utime + delta_stime) / delta_time) * 100
                else:
                    cpu_percent = 0.0
            else:
                cpu_percent = 0.0
            
            # Update cache
            self._cpu_times_cache[pid] = (utime, stime, current_time)
            
            return cpu_percent
        except:
            return 0.0
    
    def _get_net_connections(self, pid: int) -> List[Dict[str, Any]]:
        """Get network connections for a process on Linux."""
        connections = []
        
        try:
            # Parse /proc/[pid]/net/tcp and tcp6
            for proto in ['tcp', 'tcp6', 'udp', 'udp6']:
                try:
                    with open(f'/proc/{pid}/net/{proto}', 'r') as f:
                        lines = f.readlines()[1:]  # Skip header
                    
                    for line in lines[:20]:  # Limit
                        parts = line.split()
                        if len(parts) >= 10:
                            local_addr = parts[1]
                            remote_addr = parts[2]
                            state = parts[3]
                            
                            connections.append({
                                'protocol': proto.rstrip('6'),
                                'local': local_addr,
                                'remote': remote_addr,
                                'state': state,
                            })
                except:
                    pass
        except:
            pass
        
        return connections
    
    def profile_process(self, pid: int) -> ProcessProfile:
        """
        Create a detailed profile of a process.
        
        Args:
            pid: Process ID to profile
        
        Returns:
            ProcessProfile with detailed metrics
        
        Raises:
            ProcessError: If process not found or access denied
        """
        # Get basic info first
        proc_info = self.manager.get_process(pid)
        if not proc_info:
            raise ProcessError(f"Process {pid} not found")
        
        if is_linux():
            # Get detailed Linux metrics
            mem_stats = self._read_proc_statm(pid)
            io_stats = self._read_proc_io(pid)
            open_files = self._read_proc_fd(pid)
            cwd = self._read_proc_cwd(pid)
            environ = self._read_proc_environ(pid)
            cpu_percent = self._get_cpu_percent(pid)
            connections = self._get_net_connections(pid)
            
            # Get CPU times
            try:
                with open(f'/proc/{pid}/stat', 'r') as f:
                    stat = f.read()
                end = stat.rfind(')')
                parts = stat[end+2:].split()
                clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                cpu_user = int(parts[11]) / clk_tck
                cpu_system = int(parts[12]) / clk_tck
            except:
                cpu_user = 0.0
                cpu_system = 0.0
            
            # Calculate memory percent
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            total_mem = int(line.split()[1]) * 1024
                            break
                memory_percent = (mem_stats['rss'] / total_mem) * 100 if total_mem > 0 else 0
            except:
                memory_percent = 0.0
        else:
            # Minimal info for non-Linux
            mem_stats = {'rss': proc_info.memory_rss, 'vms': 0}
            io_stats = {'read_bytes': 0, 'write_bytes': 0, 'read_count': 0, 'write_count': 0}
            open_files = []
            cwd = ''
            environ = {}
            cpu_percent = proc_info.cpu_percent
            cpu_user = 0.0
            cpu_system = 0.0
            memory_percent = proc_info.memory_percent
            connections = []
        
        running_time = datetime.now() - proc_info.create_time
        
        return ProcessProfile(
            pid=pid,
            name=proc_info.name,
            memory_rss=mem_stats.get('rss', proc_info.memory_rss),
            memory_vms=mem_stats.get('vms', 0),
            memory_percent=memory_percent,
            cpu_percent=cpu_percent,
            cpu_times_user=cpu_user,
            cpu_times_system=cpu_system,
            io_read_bytes=io_stats['read_bytes'],
            io_write_bytes=io_stats['write_bytes'],
            io_read_count=io_stats['read_count'],
            io_write_count=io_stats['write_count'],
            open_files=open_files,
            connections=connections,
            cwd=cwd,
            environ=environ,
            threads=proc_info.threads,
            create_time=proc_info.create_time,
            running_time=running_time
        )
    
    def monitor_process(
        self,
        pid: int,
        duration: float = 10.0,
        interval: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Monitor a process over time.
        
        Args:
            pid: Process ID to monitor
            duration: How long to monitor in seconds
            interval: Sampling interval in seconds
        
        Returns:
            List of samples with CPU and memory usage
        """
        samples = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            try:
                profile = self.profile_process(pid)
                
                samples.append({
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': profile.cpu_percent,
                    'memory_rss': profile.memory_rss,
                    'memory_percent': profile.memory_percent,
                    'io_read': profile.io_read_bytes,
                    'io_write': profile.io_write_bytes,
                    'threads': profile.threads,
                })
                
                time.sleep(interval)
            except ProcessError:
                # Process may have ended
                break
        
        return samples
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary of resource usage across all processes.
        
        Returns:
            Dictionary with aggregate statistics
        """
        processes = self.manager.list_processes()
        
        total_memory = sum(p.memory_rss for p in processes)
        total_threads = sum(p.threads for p in processes)
        
        # Top consumers
        top_memory = sorted(processes, key=lambda p: p.memory_rss, reverse=True)[:5]
        top_cpu = sorted(processes, key=lambda p: p.cpu_percent, reverse=True)[:5]
        
        # By status
        by_status: Dict[str, int] = {}
        for p in processes:
            by_status[p.status] = by_status.get(p.status, 0) + 1
        
        return {
            'total_processes': len(processes),
            'total_memory': total_memory,
            'total_threads': total_threads,
            'by_status': by_status,
            'top_memory': [
                {'pid': p.pid, 'name': p.name, 'memory': p.memory_rss}
                for p in top_memory
            ],
            'top_cpu': [
                {'pid': p.pid, 'name': p.name, 'cpu': p.cpu_percent}
                for p in top_cpu
            ],
        }
