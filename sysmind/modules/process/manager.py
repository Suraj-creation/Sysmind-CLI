"""
SYSMIND Process Manager Module

Process listing, filtering, and management.
"""

import os
import signal
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Generator
from dataclasses import dataclass

from ...utils.platform_utils import is_windows, is_linux, is_macos, is_admin
from ...core.errors import ProcessError, PermissionError


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    username: str
    create_time: datetime
    command: str
    parent_pid: int
    threads: int


class ProcessManager:
    """
    Process management using /proc filesystem and OS-specific tools.
    
    Provides cross-platform process listing, filtering, and control.
    """
    
    def __init__(self):
        self._process_cache: Dict[int, ProcessInfo] = {}
        self._last_refresh = None
    
    def _parse_proc_stat(self, pid: int) -> Optional[Dict[str, Any]]:
        """Parse /proc/[pid]/stat on Linux."""
        try:
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read()
            
            # Parse stat line - name is in parentheses
            # Format: pid (name) state ppid pgrp session tty_nr tpgid flags ...
            # Find name between parentheses
            start = stat.find('(')
            end = stat.rfind(')')
            
            if start == -1 or end == -1:
                return None
            
            name = stat[start+1:end]
            rest = stat[end+2:].split()
            
            return {
                'pid': pid,
                'name': name,
                'state': rest[0],
                'ppid': int(rest[1]),
                'utime': int(rest[11]),
                'stime': int(rest[12]),
                'threads': int(rest[17]),
                'starttime': int(rest[19]),
            }
        except:
            return None
    
    def _parse_proc_status(self, pid: int) -> Optional[Dict[str, Any]]:
        """Parse /proc/[pid]/status on Linux."""
        try:
            with open(f'/proc/{pid}/status', 'r') as f:
                lines = f.readlines()
            
            status = {}
            for line in lines:
                if ':' in line:
                    key, val = line.split(':', 1)
                    status[key.strip()] = val.strip()
            
            return {
                'name': status.get('Name', ''),
                'state': status.get('State', '').split()[0] if status.get('State') else '',
                'uid': int(status.get('Uid', '0').split()[0]),
                'vmrss': int(status.get('VmRSS', '0 kB').split()[0]) * 1024 if 'VmRSS' in status else 0,
                'threads': int(status.get('Threads', '1')),
            }
        except:
            return None
    
    def _parse_proc_cmdline(self, pid: int) -> str:
        """Get command line for a process on Linux."""
        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmdline = f.read()
            return cmdline.replace('\x00', ' ').strip()
        except:
            return ''
    
    def _get_username(self, uid: int) -> str:
        """Get username from UID."""
        try:
            import pwd
            return pwd.getpwuid(uid).pw_name
        except:
            return str(uid)
    
    def _get_linux_processes(self) -> Generator[ProcessInfo, None, None]:
        """Get processes from /proc on Linux."""
        for entry in os.listdir('/proc'):
            if not entry.isdigit():
                continue
            
            pid = int(entry)
            
            stat = self._parse_proc_stat(pid)
            if not stat:
                continue
            
            status = self._parse_proc_status(pid)
            if not status:
                continue
            
            cmdline = self._parse_proc_cmdline(pid)
            
            # Calculate CPU percent would require sampling over time
            # For simplicity, return 0 here - realtime module handles this
            
            state_map = {
                'R': 'running',
                'S': 'sleeping',
                'D': 'disk-sleep',
                'Z': 'zombie',
                'T': 'stopped',
                'I': 'idle',
            }
            
            try:
                # Get process start time
                boot_time = 0
                try:
                    with open('/proc/stat', 'r') as f:
                        for line in f:
                            if line.startswith('btime'):
                                boot_time = int(line.split()[1])
                                break
                except:
                    pass
                
                # Clock ticks per second
                clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                start_time = datetime.fromtimestamp(boot_time + stat['starttime'] / clk_tck)
                
                yield ProcessInfo(
                    pid=pid,
                    name=status.get('name', stat.get('name', '')),
                    status=state_map.get(status.get('state', 'S')[0], 'unknown'),
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_rss=status.get('vmrss', 0),
                    username=self._get_username(status.get('uid', 0)),
                    create_time=start_time,
                    command=cmdline or status.get('name', ''),
                    parent_pid=stat.get('ppid', 0),
                    threads=status.get('threads', 1)
                )
            except:
                continue
    
    def _get_windows_processes(self) -> Generator[ProcessInfo, None, None]:
        """Get processes on Windows using wmic/powershell."""
        try:
            result = subprocess.run(
                ['powershell', '-Command', '''
                    Get-Process | ForEach-Object {
                        $cpu = $_.CPU
                        $ws = $_.WorkingSet64
                        $id = $_.Id
                        $name = $_.ProcessName
                        $threads = $_.Threads.Count
                        $start = $_.StartTime
                        Write-Output "$id|$name|$ws|$cpu|$threads|$start"
                    }
                '''],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line or '|' not in line:
                        continue
                    
                    try:
                        parts = line.split('|')
                        if len(parts) >= 5:
                            pid = int(parts[0])
                            name = parts[1]
                            memory = int(parts[2]) if parts[2] else 0
                            cpu = float(parts[3]) if parts[3] else 0.0
                            threads = int(parts[4]) if parts[4] else 1
                            
                            yield ProcessInfo(
                                pid=pid,
                                name=name,
                                status='running',
                                cpu_percent=cpu,
                                memory_percent=0.0,
                                memory_rss=memory,
                                username='',
                                create_time=datetime.now(),
                                command=name,
                                parent_pid=0,
                                threads=threads
                            )
                    except:
                        continue
        except:
            pass
    
    def _get_macos_processes(self) -> Generator[ProcessInfo, None, None]:
        """Get processes on macOS using ps."""
        try:
            result = subprocess.run(
                ['ps', '-axo', 'pid,ppid,stat,rss,comm,user'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    parts = line.split(None, 5)
                    if len(parts) >= 5:
                        try:
                            pid = int(parts[0])
                            ppid = int(parts[1])
                            status = parts[2]
                            rss = int(parts[3]) * 1024  # KB to bytes
                            command = parts[4]
                            user = parts[5] if len(parts) > 5 else ''
                            
                            yield ProcessInfo(
                                pid=pid,
                                name=Path(command).name,
                                status='running' if 'R' in status else 'sleeping',
                                cpu_percent=0.0,
                                memory_percent=0.0,
                                memory_rss=rss,
                                username=user,
                                create_time=datetime.now(),
                                command=command,
                                parent_pid=ppid,
                                threads=1
                            )
                        except:
                            continue
        except:
            pass
    
    def list_processes(
        self,
        sort_by: str = 'memory',
        reverse: bool = True,
        limit: Optional[int] = None
    ) -> List[ProcessInfo]:
        """
        List all running processes.
        
        Args:
            sort_by: Field to sort by ('cpu', 'memory', 'name', 'pid')
            reverse: Sort in descending order
            limit: Maximum number of processes to return
        
        Returns:
            List of ProcessInfo
        """
        if is_linux():
            processes = list(self._get_linux_processes())
        elif is_windows():
            processes = list(self._get_windows_processes())
        elif is_macos():
            processes = list(self._get_macos_processes())
        else:
            processes = []
        
        # Sort
        sort_keys = {
            'cpu': lambda p: p.cpu_percent,
            'memory': lambda p: p.memory_rss,
            'name': lambda p: p.name.lower(),
            'pid': lambda p: p.pid,
        }
        
        if sort_by in sort_keys:
            processes.sort(key=sort_keys[sort_by], reverse=reverse)
        
        if limit:
            processes = processes[:limit]
        
        return processes
    
    def get_process(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a specific process."""
        for proc in self.list_processes():
            if proc.pid == pid:
                return proc
        return None
    
    def find_processes(
        self,
        name: Optional[str] = None,
        user: Optional[str] = None,
        min_memory: Optional[int] = None,
        min_cpu: Optional[float] = None
    ) -> List[ProcessInfo]:
        """
        Find processes matching criteria.
        
        Args:
            name: Process name pattern (case-insensitive)
            user: Username
            min_memory: Minimum memory usage in bytes
            min_cpu: Minimum CPU percentage
        
        Returns:
            List of matching processes
        """
        processes = self.list_processes()
        results = []
        
        for proc in processes:
            if name and name.lower() not in proc.name.lower():
                continue
            
            if user and user.lower() != proc.username.lower():
                continue
            
            if min_memory and proc.memory_rss < min_memory:
                continue
            
            if min_cpu and proc.cpu_percent < min_cpu:
                continue
            
            results.append(proc)
        
        return results
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """
        Terminate a process.
        
        Args:
            pid: Process ID
            force: If True, use SIGKILL; otherwise use SIGTERM
        
        Returns:
            True if successful
        """
        try:
            if is_windows():
                if force:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
                else:
                    subprocess.run(['taskkill', '/PID', str(pid)], check=True)
            else:
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(pid, sig)
            
            return True
        except PermissionError:
            raise PermissionError(f"Permission denied to kill process {pid}")
        except ProcessLookupError:
            raise ProcessError(f"Process {pid} not found")
        except Exception as e:
            raise ProcessError(f"Failed to kill process {pid}: {e}")
    
    def get_process_tree(self, pid: int) -> Dict[str, Any]:
        """
        Get process tree starting from a PID.
        
        Args:
            pid: Root process ID
        
        Returns:
            Dictionary with process info and children
        """
        processes = self.list_processes()
        pid_map = {p.pid: p for p in processes}
        
        def build_tree(root_pid: int) -> Dict[str, Any]:
            proc = pid_map.get(root_pid)
            if not proc:
                return {}
            
            children = [p for p in processes if p.parent_pid == root_pid]
            
            return {
                'pid': proc.pid,
                'name': proc.name,
                'memory_rss': proc.memory_rss,
                'children': [build_tree(c.pid) for c in children]
            }
        
        return build_tree(pid)
    
    def get_top_processes(
        self,
        by: str = 'memory',
        n: int = 10
    ) -> List[ProcessInfo]:
        """
        Get top N processes by resource usage.
        
        Args:
            by: Resource to sort by ('memory', 'cpu')
            n: Number of processes to return
        
        Returns:
            List of top processes
        """
        return self.list_processes(sort_by=by, reverse=True, limit=n)
