"""
SYSMIND Bandwidth Monitor Module

Network bandwidth monitoring and statistics.
"""

import os
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from ...utils.platform_utils import is_linux, is_windows, is_macos
from ...core.errors import NetworkError


@dataclass
class InterfaceStats:
    """Network interface statistics."""
    name: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    drop_in: int
    drop_out: int


@dataclass
class BandwidthSample:
    """Bandwidth measurement sample."""
    timestamp: datetime
    interface: str
    bytes_sent_rate: float  # bytes per second
    bytes_recv_rate: float
    packets_sent_rate: float
    packets_recv_rate: float


class BandwidthMonitor:
    """
    Monitor network bandwidth usage.
    
    Tracks bytes sent/received across network interfaces
    and calculates bandwidth utilization.
    """
    
    def __init__(self):
        self._prev_stats: Dict[str, Tuple[InterfaceStats, float]] = {}
        self._history: List[BandwidthSample] = []
        self._max_history = 3600  # 1 hour at 1 sample/second
    
    def _read_linux_net_dev(self) -> Dict[str, InterfaceStats]:
        """Read network stats from /proc/net/dev on Linux."""
        stats = {}
        
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()[2:]  # Skip headers
            
            for line in lines:
                if ':' not in line:
                    continue
                
                parts = line.split(':')
                name = parts[0].strip()
                values = parts[1].split()
                
                if len(values) >= 16:
                    stats[name] = InterfaceStats(
                        name=name,
                        bytes_recv=int(values[0]),
                        packets_recv=int(values[1]),
                        errors_in=int(values[2]),
                        drop_in=int(values[3]),
                        bytes_sent=int(values[8]),
                        packets_sent=int(values[9]),
                        errors_out=int(values[10]),
                        drop_out=int(values[11])
                    )
        except:
            pass
        
        return stats
    
    def _get_windows_stats(self) -> Dict[str, InterfaceStats]:
        """Get network stats on Windows."""
        stats = {}
        
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-Command', '''
                    Get-NetAdapterStatistics | ForEach-Object {
                        $name = $_.Name
                        $recv = $_.ReceivedBytes
                        $sent = $_.SentBytes
                        $rpkt = $_.ReceivedUnicastPackets
                        $spkt = $_.SentUnicastPackets
                        Write-Output "$name|$recv|$sent|$rpkt|$spkt"
                    }
                '''],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '|' not in line:
                        continue
                    
                    parts = line.split('|')
                    if len(parts) >= 5:
                        name = parts[0]
                        stats[name] = InterfaceStats(
                            name=name,
                            bytes_recv=int(parts[1]) if parts[1] else 0,
                            bytes_sent=int(parts[2]) if parts[2] else 0,
                            packets_recv=int(parts[3]) if parts[3] else 0,
                            packets_sent=int(parts[4]) if parts[4] else 0,
                            errors_in=0,
                            errors_out=0,
                            drop_in=0,
                            drop_out=0
                        )
        except:
            pass
        
        return stats
    
    def _get_macos_stats(self) -> Dict[str, InterfaceStats]:
        """Get network stats on macOS."""
        stats = {}
        
        try:
            import subprocess
            result = subprocess.run(
                ['netstat', '-ibn'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 10:
                        name = parts[0]
                        
                        # Skip loopback
                        if name.startswith('lo'):
                            continue
                        
                        try:
                            stats[name] = InterfaceStats(
                                name=name,
                                bytes_recv=int(parts[6]),
                                packets_recv=int(parts[4]),
                                bytes_sent=int(parts[9]),
                                packets_sent=int(parts[7]),
                                errors_in=int(parts[5]),
                                errors_out=int(parts[8]),
                                drop_in=0,
                                drop_out=0
                            )
                        except:
                            pass
        except:
            pass
        
        return stats
    
    def get_interface_stats(self) -> Dict[str, InterfaceStats]:
        """
        Get current interface statistics.
        
        Returns:
            Dictionary mapping interface name to stats
        """
        if is_linux():
            return self._read_linux_net_dev()
        elif is_windows():
            return self._get_windows_stats()
        elif is_macos():
            return self._get_macos_stats()
        
        return {}
    
    def get_bandwidth_rates(self, interface: Optional[str] = None) -> Dict[str, BandwidthSample]:
        """
        Get current bandwidth rates for interfaces.
        
        Args:
            interface: Specific interface to check (None for all)
        
        Returns:
            Dictionary mapping interface name to bandwidth sample
        """
        current_stats = self.get_interface_stats()
        current_time = time.time()
        rates = {}
        
        for name, stats in current_stats.items():
            if interface and name != interface:
                continue
            
            # Skip loopback
            if name.startswith('lo'):
                continue
            
            # Calculate rate if we have previous stats
            if name in self._prev_stats:
                prev_stats, prev_time = self._prev_stats[name]
                delta_time = current_time - prev_time
                
                if delta_time > 0:
                    sample = BandwidthSample(
                        timestamp=datetime.now(),
                        interface=name,
                        bytes_sent_rate=(stats.bytes_sent - prev_stats.bytes_sent) / delta_time,
                        bytes_recv_rate=(stats.bytes_recv - prev_stats.bytes_recv) / delta_time,
                        packets_sent_rate=(stats.packets_sent - prev_stats.packets_sent) / delta_time,
                        packets_recv_rate=(stats.packets_recv - prev_stats.packets_recv) / delta_time
                    )
                    rates[name] = sample
                    
                    # Add to history
                    self._history.append(sample)
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
            
            # Update previous stats
            self._prev_stats[name] = (stats, current_time)
        
        return rates
    
    def get_total_bandwidth(self) -> Tuple[float, float]:
        """
        Get total bandwidth across all interfaces.
        
        Returns:
            Tuple of (total_sent_rate, total_recv_rate) in bytes/second
        """
        rates = self.get_bandwidth_rates()
        
        total_sent = sum(r.bytes_sent_rate for r in rates.values())
        total_recv = sum(r.bytes_recv_rate for r in rates.values())
        
        return (total_sent, total_recv)
    
    def get_interface_list(self) -> List[str]:
        """Get list of network interfaces."""
        stats = self.get_interface_stats()
        return [name for name in stats.keys() if not name.startswith('lo')]
    
    def get_total_transferred(self) -> Dict[str, int]:
        """
        Get total bytes transferred since boot.
        
        Returns:
            Dictionary with total sent and received bytes
        """
        stats = self.get_interface_stats()
        
        total_sent = 0
        total_recv = 0
        
        for name, iface_stats in stats.items():
            if name.startswith('lo'):
                continue
            total_sent += iface_stats.bytes_sent
            total_recv += iface_stats.bytes_recv
        
        return {
            'sent': total_sent,
            'recv': total_recv,
            'total': total_sent + total_recv
        }
    
    def get_history(
        self,
        interface: Optional[str] = None,
        seconds: int = 60
    ) -> List[BandwidthSample]:
        """
        Get bandwidth history.
        
        Args:
            interface: Filter by interface name
            seconds: How many seconds of history to return
        
        Returns:
            List of BandwidthSample
        """
        cutoff = datetime.now().timestamp() - seconds
        
        history = [
            s for s in self._history
            if s.timestamp.timestamp() >= cutoff
            and (interface is None or s.interface == interface)
        ]
        
        return history
    
    def get_average_bandwidth(self, seconds: int = 60) -> Dict[str, Tuple[float, float]]:
        """
        Get average bandwidth over a time period.
        
        Args:
            seconds: Time period to average over
        
        Returns:
            Dictionary mapping interface to (avg_sent, avg_recv)
        """
        history = self.get_history(seconds=seconds)
        
        by_interface: Dict[str, List[BandwidthSample]] = {}
        for sample in history:
            if sample.interface not in by_interface:
                by_interface[sample.interface] = []
            by_interface[sample.interface].append(sample)
        
        averages = {}
        for interface, samples in by_interface.items():
            if samples:
                avg_sent = sum(s.bytes_sent_rate for s in samples) / len(samples)
                avg_recv = sum(s.bytes_recv_rate for s in samples) / len(samples)
                averages[interface] = (avg_sent, avg_recv)
        
        return averages
    
    def monitor(
        self,
        interval: float = 1.0,
        duration: Optional[float] = None,
        callback: Optional[callable] = None
    ):
        """
        Monitor bandwidth in real-time.
        
        Args:
            interval: Sampling interval in seconds
            duration: How long to monitor (None for indefinitely)
            callback: Function to call with each sample
        """
        start_time = time.time()
        
        # Initial sample
        self.get_bandwidth_rates()
        time.sleep(interval)
        
        try:
            while True:
                if duration and (time.time() - start_time) >= duration:
                    break
                
                rates = self.get_bandwidth_rates()
                
                if callback:
                    callback(rates)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
