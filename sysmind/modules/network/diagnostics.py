"""
SYSMIND Network Diagnostics Module

Network connectivity testing and diagnostics.
"""

import os
import socket
import subprocess
import time
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.request import urlopen
from urllib.error import URLError

from ...utils.platform_utils import is_windows
from ...core.errors import NetworkError


@dataclass
class PingResult:
    """Result of a ping operation."""
    host: str
    success: bool
    packets_sent: int
    packets_received: int
    packet_loss: float
    min_rtt: float
    avg_rtt: float
    max_rtt: float
    error: Optional[str] = None


@dataclass
class DNSResult:
    """Result of DNS lookup."""
    hostname: str
    addresses: List[str]
    canonical_name: str
    lookup_time: float


@dataclass
class TraceResult:
    """Result of a traceroute hop."""
    hop: int
    address: Optional[str]
    hostname: Optional[str]
    rtt: List[float]
    timed_out: bool


class NetworkDiagnostics:
    """
    Network diagnostic tools.
    
    Provides ping, DNS lookup, traceroute, and other
    network connectivity tests.
    """
    
    def __init__(self):
        self.timeout = 5.0
    
    def ping(
        self,
        host: str,
        count: int = 4,
        timeout: float = 5.0
    ) -> PingResult:
        """
        Ping a host.
        
        Args:
            host: Hostname or IP address
            count: Number of ping requests
            timeout: Timeout in seconds
        
        Returns:
            PingResult with statistics
        """
        try:
            if is_windows():
                cmd = ['ping', '-n', str(count), '-w', str(int(timeout * 1000)), host]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(int(timeout)), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout * count + 10
            )
            
            return self._parse_ping_output(host, result.stdout, result.returncode == 0)
        except subprocess.TimeoutExpired:
            return PingResult(
                host=host,
                success=False,
                packets_sent=count,
                packets_received=0,
                packet_loss=100.0,
                min_rtt=0,
                avg_rtt=0,
                max_rtt=0,
                error="Timeout"
            )
        except Exception as e:
            return PingResult(
                host=host,
                success=False,
                packets_sent=count,
                packets_received=0,
                packet_loss=100.0,
                min_rtt=0,
                avg_rtt=0,
                max_rtt=0,
                error=str(e)
            )
    
    def _parse_ping_output(self, host: str, output: str, success: bool) -> PingResult:
        """Parse ping command output."""
        packets_sent = 0
        packets_received = 0
        min_rtt = 0.0
        avg_rtt = 0.0
        max_rtt = 0.0
        
        if is_windows():
            # Windows ping output parsing
            # "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
            match = re.search(r'Sent = (\d+), Received = (\d+)', output)
            if match:
                packets_sent = int(match.group(1))
                packets_received = int(match.group(2))
            
            # "Minimum = 1ms, Maximum = 5ms, Average = 2ms"
            match = re.search(r'Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms', output)
            if match:
                min_rtt = float(match.group(1))
                max_rtt = float(match.group(2))
                avg_rtt = float(match.group(3))
        else:
            # Unix ping output parsing
            # "4 packets transmitted, 4 received, 0% packet loss"
            match = re.search(r'(\d+) packets transmitted, (\d+) received', output)
            if match:
                packets_sent = int(match.group(1))
                packets_received = int(match.group(2))
            
            # "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.123 ms"
            match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)', output)
            if match:
                min_rtt = float(match.group(1))
                avg_rtt = float(match.group(2))
                max_rtt = float(match.group(3))
        
        packet_loss = ((packets_sent - packets_received) / packets_sent * 100) if packets_sent > 0 else 100
        
        return PingResult(
            host=host,
            success=success and packets_received > 0,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss=packet_loss,
            min_rtt=min_rtt,
            avg_rtt=avg_rtt,
            max_rtt=max_rtt
        )
    
    def dns_lookup(self, hostname: str) -> DNSResult:
        """
        Perform DNS lookup.
        
        Args:
            hostname: Hostname to resolve
        
        Returns:
            DNSResult with addresses
        """
        start = time.time()
        
        try:
            # Get all addresses
            results = socket.getaddrinfo(hostname, None)
            addresses = list(set(r[4][0] for r in results))
            
            # Try to get canonical name
            try:
                canonical = socket.getfqdn(hostname)
            except:
                canonical = hostname
            
            lookup_time = time.time() - start
            
            return DNSResult(
                hostname=hostname,
                addresses=addresses,
                canonical_name=canonical,
                lookup_time=lookup_time
            )
        except socket.gaierror as e:
            raise NetworkError(f"DNS lookup failed for {hostname}: {e}")
    
    def reverse_dns(self, ip_address: str) -> str:
        """
        Perform reverse DNS lookup.
        
        Args:
            ip_address: IP address to look up
        
        Returns:
            Hostname or original IP if not found
        """
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except:
            return ip_address
    
    def traceroute(
        self,
        host: str,
        max_hops: int = 30,
        timeout: float = 3.0
    ) -> List[TraceResult]:
        """
        Perform traceroute to a host.
        
        Args:
            host: Target hostname or IP
            max_hops: Maximum number of hops
            timeout: Timeout per hop
        
        Returns:
            List of TraceResult for each hop
        """
        results = []
        
        try:
            if is_windows():
                cmd = ['tracert', '-h', str(max_hops), '-w', str(int(timeout * 1000)), host]
            else:
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), host]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max_hops * timeout + 30
            )
            
            return self._parse_traceroute_output(result.stdout)
        except subprocess.TimeoutExpired:
            return results
        except Exception as e:
            raise NetworkError(f"Traceroute failed: {e}")
    
    def _parse_traceroute_output(self, output: str) -> List[TraceResult]:
        """Parse traceroute output."""
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            # Skip header lines
            if not line.strip() or 'traceroute' in line.lower() or 'tracing' in line.lower():
                continue
            
            # Try to parse hop line
            # Format varies: "1  192.168.1.1 (192.168.1.1)  1.234 ms  1.345 ms  1.456 ms"
            # Or: "1  * * *" for timeout
            
            parts = line.split()
            if not parts:
                continue
            
            try:
                hop = int(parts[0])
            except ValueError:
                continue
            
            if '*' in line:
                # Timeout
                results.append(TraceResult(
                    hop=hop,
                    address=None,
                    hostname=None,
                    rtt=[],
                    timed_out=True
                ))
            else:
                # Find IP address and RTT values
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                address = ip_match.group(1) if ip_match else None
                
                # Find RTT values (numbers followed by 'ms')
                rtt_matches = re.findall(r'([\d.]+)\s*ms', line)
                rtt = [float(r) for r in rtt_matches]
                
                # Find hostname
                hostname = None
                for part in parts[1:]:
                    if '(' not in part and ')' not in part and 'ms' not in part and not re.match(r'[\d.]+$', part):
                        hostname = part
                        break
                
                results.append(TraceResult(
                    hop=hop,
                    address=address,
                    hostname=hostname,
                    rtt=rtt,
                    timed_out=False
                ))
        
        return results
    
    def check_port(
        self,
        host: str,
        port: int,
        timeout: float = 5.0
    ) -> Tuple[bool, float]:
        """
        Check if a port is open.
        
        Args:
            host: Hostname or IP
            port: Port number
            timeout: Connection timeout
        
        Returns:
            Tuple of (is_open, response_time)
        """
        start = time.time()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            response_time = time.time() - start
            
            return (result == 0, response_time)
        except Exception:
            return (False, 0.0)
    
    def check_http(
        self,
        url: str,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check HTTP(S) connectivity.
        
        Args:
            url: URL to check
            timeout: Request timeout
        
        Returns:
            Dictionary with status and response time
        """
        start = time.time()
        
        try:
            response = urlopen(url, timeout=timeout)
            response_time = time.time() - start
            
            return {
                'success': True,
                'status_code': response.getcode(),
                'response_time': response_time,
                'url': url,
                'error': None
            }
        except URLError as e:
            return {
                'success': False,
                'status_code': None,
                'response_time': time.time() - start,
                'url': url,
                'error': str(e.reason)
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'response_time': time.time() - start,
                'url': url,
                'error': str(e)
            }
    
    def check_internet_connectivity(self) -> Dict[str, Any]:
        """
        Comprehensive internet connectivity check.
        
        Returns:
            Dictionary with connectivity status
        """
        results = {
            'connected': False,
            'dns_working': False,
            'http_working': False,
            'latency': None,
            'details': []
        }
        
        # Test DNS
        try:
            dns_result = self.dns_lookup('google.com')
            results['dns_working'] = len(dns_result.addresses) > 0
            results['details'].append(f"DNS: Resolved google.com to {dns_result.addresses}")
        except:
            results['details'].append("DNS: Failed to resolve google.com")
        
        # Test HTTP
        http_result = self.check_http('http://www.google.com')
        results['http_working'] = http_result['success']
        if http_result['success']:
            results['details'].append(f"HTTP: Connected in {http_result['response_time']:.2f}s")
        else:
            results['details'].append(f"HTTP: Failed - {http_result['error']}")
        
        # Test ping
        ping_result = self.ping('8.8.8.8', count=3)
        if ping_result.success:
            results['latency'] = ping_result.avg_rtt
            results['details'].append(f"Ping: {ping_result.avg_rtt:.1f}ms to 8.8.8.8")
        else:
            results['details'].append("Ping: Failed to reach 8.8.8.8")
        
        results['connected'] = results['dns_working'] and results['http_working']
        
        return results
    
    def get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Create a socket to an external host to find local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except:
            return '127.0.0.1'
    
    def get_public_ip(self) -> Optional[str]:
        """Get public IP address."""
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://checkip.amazonaws.com',
        ]
        
        for service in services:
            try:
                response = urlopen(service, timeout=5)
                return response.read().decode().strip()
            except:
                continue
        
        return None
