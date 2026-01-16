"""
SYSMIND Memory Monitor Module

Memory metrics collection and analysis.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict
from pathlib import Path

from ...utils.platform_utils import is_windows, is_linux, is_macos


@dataclass
class MemoryMetrics:
    """Memory metrics data class."""
    total: int
    available: int
    used: int
    free: int
    usage_percent: float
    buffers: int
    cached: int
    shared: int
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


class MemoryMonitor:
    """
    Memory monitoring using /proc filesystem and OS-specific tools.
    
    Provides cross-platform memory metrics collection.
    """
    
    def _read_proc_meminfo(self) -> Optional[Dict[str, int]]:
        """Read memory info from /proc/meminfo on Linux."""
        if not is_linux():
            return None
        
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            info = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    # Values are in kB, convert to bytes
                    value_parts = parts[1].strip().split()
                    value = int(value_parts[0]) * 1024
                    info[key] = value
            
            return info
        except:
            return None
    
    def _get_windows_memory(self) -> Optional[Dict[str, int]]:
        """Get memory info on Windows."""
        try:
            result = subprocess.run(
                ['powershell', '-Command', '''
                    $os = Get-CimInstance Win32_OperatingSystem
                    $cs = Get-CimInstance Win32_ComputerSystem
                    Write-Output "TotalPhysicalMemory:$($cs.TotalPhysicalMemory)"
                    Write-Output "FreePhysicalMemory:$($os.FreePhysicalMemory * 1024)"
                    Write-Output "TotalVirtualMemory:$($os.TotalVirtualMemorySize * 1024)"
                    Write-Output "FreeVirtualMemory:$($os.FreeVirtualMemory * 1024)"
                '''],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                info = {}
                for line in result.stdout.strip().split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        info[key.strip()] = int(val.strip())
                return info
        except:
            pass
        
        return None
    
    def _get_macos_memory(self) -> Optional[Dict[str, int]]:
        """Get memory info on macOS."""
        try:
            # Get memory info using sysctl
            result = subprocess.run(
                ['sysctl', 'hw.memsize'],
                capture_output=True, text=True, timeout=5
            )
            
            info = {}
            if result.returncode == 0:
                # hw.memsize: 17179869184
                total = int(result.stdout.split(':')[1].strip())
                info['total'] = total
            
            # Get page size and memory stats
            result = subprocess.run(
                ['vm_stat'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                page_size = 4096  # Default
                for line in result.stdout.split('\n'):
                    if 'page size' in line.lower():
                        page_size = int(line.split()[-2])
                    elif 'Pages free' in line:
                        info['free'] = int(line.split(':')[1].strip().rstrip('.')) * page_size
                    elif 'Pages active' in line:
                        info['active'] = int(line.split(':')[1].strip().rstrip('.')) * page_size
                    elif 'Pages inactive' in line:
                        info['inactive'] = int(line.split(':')[1].strip().rstrip('.')) * page_size
                    elif 'Pages wired' in line:
                        info['wired'] = int(line.split(':')[1].strip().rstrip('.')) * page_size
            
            return info
        except:
            pass
        
        return None
    
    def get_total(self) -> int:
        """Get total physical memory in bytes."""
        if is_linux():
            info = self._read_proc_meminfo()
            if info and 'MemTotal' in info:
                return info['MemTotal']
        
        if is_windows():
            info = self._get_windows_memory()
            if info and 'TotalPhysicalMemory' in info:
                return info['TotalPhysicalMemory']
        
        if is_macos():
            info = self._get_macos_memory()
            if info and 'total' in info:
                return info['total']
        
        return 0
    
    def get_available(self) -> int:
        """Get available memory in bytes."""
        if is_linux():
            info = self._read_proc_meminfo()
            if info:
                # MemAvailable is the best metric (kernel 3.14+)
                if 'MemAvailable' in info:
                    return info['MemAvailable']
                # Fallback calculation
                return info.get('MemFree', 0) + info.get('Buffers', 0) + info.get('Cached', 0)
        
        if is_windows():
            info = self._get_windows_memory()
            if info and 'FreePhysicalMemory' in info:
                return info['FreePhysicalMemory']
        
        if is_macos():
            info = self._get_macos_memory()
            if info:
                return info.get('free', 0) + info.get('inactive', 0)
        
        return 0
    
    def get_usage_percent(self) -> float:
        """Get memory usage percentage."""
        total = self.get_total()
        available = self.get_available()
        
        if total == 0:
            return 0.0
        
        return ((total - available) / total) * 100
    
    def get_swap_info(self) -> Dict[str, int]:
        """Get swap memory information."""
        info = {'total': 0, 'used': 0, 'free': 0}
        
        if is_linux():
            meminfo = self._read_proc_meminfo()
            if meminfo:
                info['total'] = meminfo.get('SwapTotal', 0)
                info['free'] = meminfo.get('SwapFree', 0)
                info['used'] = info['total'] - info['free']
        
        elif is_windows():
            try:
                result = subprocess.run(
                    ['powershell', '-Command', '''
                        $os = Get-CimInstance Win32_OperatingSystem
                        Write-Output "Total:$($os.TotalSwapSpaceSize)"
                        Write-Output "Free:$($os.FreeSpaceInPagingFiles * 1024)"
                    '''],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            key, val = line.split(':', 1)
                            val = val.strip()
                            if val and val.isdigit():
                                info[key.lower()] = int(val)
                    
                    if 'total' in info and 'free' in info:
                        info['used'] = info['total'] - info['free']
            except:
                pass
        
        return info
    
    def get_metrics(self) -> MemoryMetrics:
        """Get comprehensive memory metrics."""
        if is_linux():
            info = self._read_proc_meminfo() or {}
            total = info.get('MemTotal', 0)
            available = info.get('MemAvailable', info.get('MemFree', 0))
            free = info.get('MemFree', 0)
            buffers = info.get('Buffers', 0)
            cached = info.get('Cached', 0) + info.get('SReclaimable', 0)
            shared = info.get('Shmem', 0)
            used = total - available
            
            swap_total = info.get('SwapTotal', 0)
            swap_free = info.get('SwapFree', 0)
            swap_used = swap_total - swap_free
            
        else:
            total = self.get_total()
            available = self.get_available()
            free = available
            used = total - available
            buffers = 0
            cached = 0
            shared = 0
            
            swap_info = self.get_swap_info()
            swap_total = swap_info['total']
            swap_used = swap_info['used']
            swap_free = swap_info['free']
        
        usage_percent = (used / total * 100) if total > 0 else 0.0
        swap_percent = (swap_used / swap_total * 100) if swap_total > 0 else 0.0
        
        return MemoryMetrics(
            total=total,
            available=available,
            used=used,
            free=free,
            usage_percent=usage_percent,
            buffers=buffers,
            cached=cached,
            shared=shared,
            swap_total=swap_total,
            swap_used=swap_used,
            swap_free=swap_free,
            swap_percent=swap_percent
        )
