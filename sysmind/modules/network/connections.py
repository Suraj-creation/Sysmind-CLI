"""
SYSMIND Network Connections Module

Track active network connections and listening ports.
"""

import os
import socket
import subprocess
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ...utils.platform_utils import is_windows, is_linux, is_macos
from ...core.errors import NetworkError


@dataclass
class NetworkConnection:
    """Active network connection information."""
    protocol: str  # tcp, tcp6, udp, udp6
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    state: str
    pid: Optional[int]
    process_name: Optional[str]


@dataclass
class ListeningPort:
    """Listening port information."""
    protocol: str
    address: str
    port: int
    pid: Optional[int]
    process_name: Optional[str]


class ConnectionTracker:
    """
    Track network connections and listening ports.
    
    Provides visibility into active network activity
    on the system.
    """
    
    def __init__(self):
        pass
    
    def _parse_linux_connections(self) -> List[NetworkConnection]:
        """Parse connections from /proc/net on Linux."""
        connections = []
        
        # Parse /proc/net/tcp and /proc/net/udp
        for proto, path in [('tcp', '/proc/net/tcp'), ('tcp6', '/proc/net/tcp6'),
                           ('udp', '/proc/net/udp'), ('udp6', '/proc/net/udp6')]:
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()[1:]  # Skip header
                
                for line in lines:
                    parts = line.split()
                    if len(parts) < 10:
                        continue
                    
                    # Parse local address
                    local_hex = parts[1]
                    local_addr, local_port = self._parse_hex_address(local_hex, proto)
                    
                    # Parse remote address
                    remote_hex = parts[2]
                    remote_addr, remote_port = self._parse_hex_address(remote_hex, proto)
                    
                    # Parse state (TCP only)
                    state_hex = parts[3]
                    state = self._tcp_state(int(state_hex, 16)) if 'tcp' in proto else 'N/A'
                    
                    # Get PID if available (requires root for some)
                    pid = None
                    inode = parts[9] if len(parts) > 9 else None
                    if inode:
                        pid = self._get_pid_from_inode(inode)
                    
                    connections.append(NetworkConnection(
                        protocol=proto,
                        local_address=local_addr,
                        local_port=local_port,
                        remote_address=remote_addr,
                        remote_port=remote_port,
                        state=state,
                        pid=pid,
                        process_name=None
                    ))
            except:
                pass
        
        return connections
    
    def _parse_hex_address(self, hex_str: str, proto: str) -> tuple:
        """Parse hex address:port string."""
        addr_hex, port_hex = hex_str.split(':')
        port = int(port_hex, 16)
        
        if '6' in proto:
            # IPv6
            # Simplified - just return hex for now
            return (addr_hex, port)
        else:
            # IPv4 - reverse byte order
            bytes_addr = bytes.fromhex(addr_hex)
            addr = '.'.join(str(b) for b in reversed(bytes_addr))
            return (addr, port)
    
    def _tcp_state(self, state: int) -> str:
        """Convert TCP state number to name."""
        states = {
            1: 'ESTABLISHED',
            2: 'SYN_SENT',
            3: 'SYN_RECV',
            4: 'FIN_WAIT1',
            5: 'FIN_WAIT2',
            6: 'TIME_WAIT',
            7: 'CLOSE',
            8: 'CLOSE_WAIT',
            9: 'LAST_ACK',
            10: 'LISTEN',
            11: 'CLOSING',
        }
        return states.get(state, 'UNKNOWN')
    
    def _get_pid_from_inode(self, inode: str) -> Optional[int]:
        """Get PID from socket inode."""
        try:
            for pid in os.listdir('/proc'):
                if not pid.isdigit():
                    continue
                
                fd_dir = f'/proc/{pid}/fd'
                try:
                    for fd in os.listdir(fd_dir):
                        try:
                            link = os.readlink(f'{fd_dir}/{fd}')
                            if f'socket:[{inode}]' in link:
                                return int(pid)
                        except:
                            pass
                except:
                    pass
        except:
            pass
        
        return None
    
    def _parse_netstat_connections(self) -> List[NetworkConnection]:
        """Parse connections using netstat command."""
        connections = []
        
        try:
            if is_windows():
                cmd = ['netstat', '-ano']
            else:
                cmd = ['netstat', '-tunaep']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                # Skip headers
                if 'Proto' in line or 'Active' in line:
                    continue
                
                try:
                    if is_windows():
                        # Windows: Proto LocalAddress ForeignAddress State PID
                        if parts[0].upper() in ['TCP', 'UDP']:
                            proto = parts[0].lower()
                            local = parts[1]
                            remote = parts[2]
                            state = parts[3] if len(parts) > 3 else 'N/A'
                            pid = int(parts[-1]) if parts[-1].isdigit() else None
                            
                            local_addr, local_port = self._parse_address(local)
                            remote_addr, remote_port = self._parse_address(remote)
                            
                            connections.append(NetworkConnection(
                                protocol=proto,
                                local_address=local_addr,
                                local_port=local_port,
                                remote_address=remote_addr,
                                remote_port=remote_port,
                                state=state,
                                pid=pid,
                                process_name=None
                            ))
                    else:
                        # Unix: Proto Recv-Q Send-Q LocalAddress ForeignAddress State PID/Program
                        if parts[0] in ['tcp', 'tcp6', 'udp', 'udp6']:
                            proto = parts[0]
                            local = parts[3]
                            remote = parts[4]
                            state = parts[5] if len(parts) > 5 and 'tcp' in proto else 'N/A'
                            
                            pid = None
                            process_name = None
                            if len(parts) > 6 and '/' in parts[6]:
                                pid_prog = parts[6].split('/')
                                pid = int(pid_prog[0]) if pid_prog[0].isdigit() else None
                                process_name = pid_prog[1] if len(pid_prog) > 1 else None
                            
                            local_addr, local_port = self._parse_address(local)
                            remote_addr, remote_port = self._parse_address(remote)
                            
                            connections.append(NetworkConnection(
                                protocol=proto,
                                local_address=local_addr,
                                local_port=local_port,
                                remote_address=remote_addr,
                                remote_port=remote_port,
                                state=state,
                                pid=pid,
                                process_name=process_name
                            ))
                except:
                    continue
        except:
            pass
        
        return connections
    
    def _parse_address(self, addr_str: str) -> tuple:
        """Parse address:port string."""
        if addr_str.startswith('['):
            # IPv6
            match = re.match(r'\[([^\]]+)\]:(\d+)', addr_str)
            if match:
                return (match.group(1), int(match.group(2)))
            return (addr_str, 0)
        else:
            # IPv4 or simple format
            if ':' in addr_str:
                parts = addr_str.rsplit(':', 1)
                try:
                    return (parts[0], int(parts[1]))
                except:
                    return (addr_str, 0)
            return (addr_str, 0)
    
    def get_connections(
        self,
        protocol: Optional[str] = None,
        state: Optional[str] = None,
        process_name: Optional[str] = None
    ) -> List[NetworkConnection]:
        """
        Get active network connections.
        
        Args:
            protocol: Filter by protocol (tcp, udp)
            state: Filter by state (ESTABLISHED, LISTEN, etc.)
            process_name: Filter by process name
        
        Returns:
            List of NetworkConnection
        """
        # Try /proc first on Linux, fall back to netstat
        if is_linux():
            connections = self._parse_linux_connections()
        else:
            connections = self._parse_netstat_connections()
        
        # Apply filters
        if protocol:
            connections = [c for c in connections if protocol.lower() in c.protocol.lower()]
        
        if state:
            connections = [c for c in connections if state.upper() in c.state.upper()]
        
        if process_name:
            connections = [c for c in connections 
                         if c.process_name and process_name.lower() in c.process_name.lower()]
        
        return connections
    
    def get_listening_ports(self) -> List[ListeningPort]:
        """
        Get all listening ports.
        
        Returns:
            List of ListeningPort
        """
        connections = self.get_connections(state='LISTEN')
        
        ports = []
        seen = set()
        
        for conn in connections:
            key = (conn.protocol, conn.local_address, conn.local_port)
            if key in seen:
                continue
            seen.add(key)
            
            ports.append(ListeningPort(
                protocol=conn.protocol,
                address=conn.local_address,
                port=conn.local_port,
                pid=conn.pid,
                process_name=conn.process_name
            ))
        
        # Sort by port
        ports.sort(key=lambda p: p.port)
        
        return ports
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection counts by state
        """
        connections = self.get_connections()
        
        by_state: Dict[str, int] = {}
        by_protocol: Dict[str, int] = {}
        
        for conn in connections:
            by_state[conn.state] = by_state.get(conn.state, 0) + 1
            
            proto = conn.protocol.rstrip('6')  # Normalize tcp6 -> tcp
            by_protocol[proto] = by_protocol.get(proto, 0) + 1
        
        return {
            'total': len(connections),
            'by_state': by_state,
            'by_protocol': by_protocol,
            'established': by_state.get('ESTABLISHED', 0),
            'listening': by_state.get('LISTEN', 0),
        }
    
    def find_process_connections(self, pid: int) -> List[NetworkConnection]:
        """
        Find all connections for a specific process.
        
        Args:
            pid: Process ID
        
        Returns:
            List of connections for the process
        """
        connections = self.get_connections()
        return [c for c in connections if c.pid == pid]
    
    def check_port_usage(self, port: int) -> Optional[NetworkConnection]:
        """
        Check if a port is in use.
        
        Args:
            port: Port number to check
        
        Returns:
            NetworkConnection if port is in use, None otherwise
        """
        connections = self.get_connections()
        
        for conn in connections:
            if conn.local_port == port:
                return conn
        
        return None
