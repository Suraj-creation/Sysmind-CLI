"""
SYSMIND Network CLI Commands

Command handlers for network diagnostics.
"""

import argparse
from typing import Optional

from ..modules.network.diagnostics import NetworkDiagnostics
from ..modules.network.connections import ConnectionTracker
from ..modules.network.bandwidth import BandwidthMonitor
from ..utils.formatters import Formatter, Colors
from ..core.database import Database


def register_network_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register network subcommands."""
    
    network = subparsers.add_parser(
        'network',
        help='Network diagnostics and monitoring',
        description='Network connectivity testing and bandwidth monitoring'
    )
    
    network_sub = network.add_subparsers(dest='network_command', help='Network commands')
    
    # Status command
    status = network_sub.add_parser('status', help='Show network status')
    
    # Ping command
    ping = network_sub.add_parser('ping', help='Ping a host')
    ping.add_argument('host', help='Host to ping')
    ping.add_argument('--count', '-c', type=int, default=4, help='Number of pings')
    ping.add_argument('--timeout', type=float, default=5.0, help='Timeout in seconds')
    
    # DNS command
    dns = network_sub.add_parser('dns', help='DNS lookup')
    dns.add_argument('host', help='Host to look up')
    dns.add_argument('--type', choices=['A', 'AAAA', 'MX', 'TXT'], default='A',
                    help='Record type')
    
    # Traceroute command
    trace = network_sub.add_parser('trace', help='Trace route to host')
    trace.add_argument('host', help='Target host')
    trace.add_argument('--max-hops', type=int, default=30, help='Maximum hops')
    
    # Check port command
    check = network_sub.add_parser('check', help='Check port connectivity')
    check.add_argument('host', help='Target host')
    check.add_argument('port', type=int, help='Port number')
    check.add_argument('--timeout', type=float, default=5.0, help='Timeout')
    
    # Connections command
    connections = network_sub.add_parser('connections', help='Show active connections')
    connections.add_argument('--state', choices=['established', 'listen', 'all'], default='all',
                            help='Filter by state')
    connections.add_argument('--limit', type=int, default=50, help='Maximum connections')
    
    # Listening command
    listening = network_sub.add_parser('listening', help='Show listening ports')
    listening.add_argument('--protocol', choices=['tcp', 'udp', 'all'], default='all',
                          help='Filter by protocol')
    
    # Bandwidth command
    bandwidth = network_sub.add_parser('bandwidth', help='Monitor bandwidth')
    bandwidth.add_argument('--interface', '-i', help='Interface name')
    bandwidth.add_argument('--watch', action='store_true', help='Continuous monitoring')
    bandwidth.add_argument('--interval', type=float, default=1.0, help='Update interval')
    bandwidth.add_argument('--duration', type=int, help='Duration in seconds')
    
    # Interfaces command
    interfaces = network_sub.add_parser('interfaces', help='List network interfaces')


def handle_network_command(args: argparse.Namespace, database: Database) -> int:
    """Handle network commands."""
    
    formatter = Formatter()
    
    if not hasattr(args, 'network_command') or not args.network_command:
        return _handle_status(args, formatter, database)
    
    cmd = args.network_command
    
    if cmd == 'status':
        return _handle_status(args, formatter, database)
    elif cmd == 'ping':
        return _handle_ping(args, formatter, database)
    elif cmd == 'dns':
        return _handle_dns(args, formatter, database)
    elif cmd == 'trace':
        return _handle_trace(args, formatter, database)
    elif cmd == 'check':
        return _handle_check(args, formatter, database)
    elif cmd == 'connections':
        return _handle_connections(args, formatter, database)
    elif cmd == 'listening':
        return _handle_listening(args, formatter, database)
    elif cmd == 'bandwidth':
        return _handle_bandwidth(args, formatter, database)
    elif cmd == 'interfaces':
        return _handle_interfaces(args, formatter, database)
    else:
        print(f"{Colors.RED}Unknown network command: {cmd}{Colors.RESET}")
        return 1


def _handle_status(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show network status."""
    
    diag = NetworkDiagnostics()
    bandwidth = BandwidthMonitor()
    tracker = ConnectionTracker()
    
    print()
    print(formatter.box("Network Status", width=70))
    print()
    
    # Internet connectivity
    print(f"  {Colors.CYAN}Connectivity Check{Colors.RESET}")
    status = diag.check_internet_connectivity()
    
    if status['connected']:
        print(f"    Internet: {Colors.GREEN}✓ Connected{Colors.RESET}")
    else:
        print(f"    Internet: {Colors.RED}✗ Not Connected{Colors.RESET}")
    
    if status['dns_working']:
        print(f"    DNS: {Colors.GREEN}✓ Working{Colors.RESET}")
    else:
        print(f"    DNS: {Colors.RED}✗ Not Working{Colors.RESET}")
    
    if status['latency']:
        print(f"    Latency: {status['latency']:.1f} ms")
    print()
    
    # Interfaces
    print(f"  {Colors.CYAN}Network Interfaces{Colors.RESET}")
    stats = bandwidth.get_interface_stats()
    
    for name, iface in stats.items():
        if name.startswith('lo'):
            continue
        
        print(f"    {Colors.GREEN}{name}{Colors.RESET}")
        print(f"      RX: {formatter.file_size(iface.bytes_recv)} | TX: {formatter.file_size(iface.bytes_sent)}")
        
        if iface.errors_in + iface.errors_out > 0:
            print(f"      {Colors.YELLOW}Errors: {iface.errors_in + iface.errors_out}{Colors.RESET}")
    print()
    
    # Active connections summary
    connections = tracker.get_connections()
    established = [c for c in connections if c.state == 'ESTABLISHED']
    
    print(f"  {Colors.CYAN}Connections{Colors.RESET}")
    print(f"    Active: {len(established)} established")
    print(f"    Total: {len(connections)}")
    print()
    
    return 0


def _handle_ping(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Ping a host."""
    
    diag = NetworkDiagnostics()
    
    host = args.host
    count = getattr(args, 'count', 4)
    timeout = getattr(args, 'timeout', 5.0)
    
    print()
    print(f"  Pinging {host}...")
    print()
    
    results = []
    for i in range(count):
        result = diag.ping(host, timeout=timeout)
        results.append(result)
        
        if result.success:
            print(f"  {Colors.GREEN}✓{Colors.RESET} Reply from {result.ip_address}: time={result.time_ms:.1f}ms")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} Request timed out ({result.error})")
    
    # Summary
    successful = [r for r in results if r.success]
    
    print()
    print(f"  --- {host} ping statistics ---")
    print(f"  {count} packets transmitted, {len(successful)} received, {(count - len(successful)) * 100 // count}% packet loss")
    
    if successful:
        times = [r.time_ms for r in successful]
        print(f"  rtt min/avg/max = {min(times):.1f}/{sum(times)/len(times):.1f}/{max(times):.1f} ms")
    print()
    
    return 0 if successful else 1


def _handle_dns(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """DNS lookup."""
    
    diag = NetworkDiagnostics()
    
    host = args.host
    record_type = getattr(args, 'type', 'A')
    
    print()
    print(f"  DNS Lookup: {host}")
    print()
    
    result = diag.dns_lookup(host)
    
    if result.success:
        print(f"  {Colors.GREEN}✓ Resolved successfully{Colors.RESET}")
        print(f"    Query time: {result.query_time_ms:.1f} ms")
        print()
        
        for ip in result.addresses[:10]:
            print(f"    {ip}")
        
        if len(result.addresses) > 10:
            print(f"    ... and {len(result.addresses) - 10} more")
    else:
        print(f"  {Colors.RED}✗ Lookup failed: {result.error}{Colors.RESET}")
    
    print()
    return 0 if result.success else 1


def _handle_trace(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Trace route to host."""
    
    diag = NetworkDiagnostics()
    
    host = args.host
    max_hops = getattr(args, 'max_hops', 30)
    
    print()
    print(f"  Traceroute to {host} (max {max_hops} hops)")
    print()
    
    result = diag.traceroute(host, max_hops=max_hops)
    
    for hop in result.hops:
        if hop['ip'] == '*':
            print(f"  {hop['hop']:>2}  *")
        else:
            print(f"  {hop['hop']:>2}  {hop['ip']:<15}  {hop['rtt']:.1f} ms")
    
    print()
    
    if result.reached:
        print(f"  {Colors.GREEN}✓ Target reached{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}Target not reached within {max_hops} hops{Colors.RESET}")
    
    print()
    return 0


def _handle_check(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Check port connectivity."""
    
    diag = NetworkDiagnostics()
    
    host = args.host
    port = args.port
    timeout = getattr(args, 'timeout', 5.0)
    
    print()
    print(f"  Checking {host}:{port}...")
    
    is_open = diag.check_port(host, port, timeout=timeout)
    
    if is_open:
        print(f"  {Colors.GREEN}✓ Port {port} is OPEN{Colors.RESET}")
    else:
        print(f"  {Colors.RED}✗ Port {port} is CLOSED or filtered{Colors.RESET}")
    
    print()
    return 0 if is_open else 1


def _handle_connections(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show active connections."""
    
    tracker = ConnectionTracker()
    
    state_filter = getattr(args, 'state', 'all')
    limit = getattr(args, 'limit', 50)
    
    connections = tracker.get_connections()
    
    if state_filter == 'established':
        connections = [c for c in connections if c.state == 'ESTABLISHED']
    elif state_filter == 'listen':
        connections = [c for c in connections if c.state == 'LISTEN']
    
    connections = connections[:limit]
    
    print()
    print(formatter.box(f"Network Connections ({len(connections)} shown)", width=80))
    print()
    
    if not connections:
        print(f"  {Colors.YELLOW}No connections found.{Colors.RESET}")
    else:
        headers = ['Protocol', 'Local Address', 'Remote Address', 'State', 'PID']
        rows = []
        
        for conn in connections:
            local = f"{conn.local_address}:{conn.local_port}"
            remote = f"{conn.remote_address}:{conn.remote_port}" if conn.remote_address else "*:*"
            
            state_color = ''
            if conn.state == 'ESTABLISHED':
                state_color = Colors.GREEN
            elif conn.state == 'LISTEN':
                state_color = Colors.CYAN
            elif conn.state in ('TIME_WAIT', 'CLOSE_WAIT'):
                state_color = Colors.YELLOW
            
            rows.append([
                conn.protocol.upper(),
                local[:22],
                remote[:22],
                f"{state_color}{conn.state}{Colors.RESET}",
                str(conn.pid) if conn.pid else '-'
            ])
        
        print(formatter.table(headers, rows))
    
    print()
    return 0


def _handle_listening(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show listening ports."""
    
    tracker = ConnectionTracker()
    
    protocol_filter = getattr(args, 'protocol', 'all')
    
    ports = tracker.get_listening_ports()
    
    if protocol_filter == 'tcp':
        ports = [p for p in ports if p.protocol == 'tcp']
    elif protocol_filter == 'udp':
        ports = [p for p in ports if p.protocol == 'udp']
    
    print()
    print(formatter.box(f"Listening Ports ({len(ports)} found)", width=70))
    print()
    
    if not ports:
        print(f"  {Colors.YELLOW}No listening ports found.{Colors.RESET}")
    else:
        headers = ['Protocol', 'Address', 'Port', 'PID', 'Process']
        rows = []
        
        for port in ports:
            rows.append([
                port.protocol.upper(),
                port.address or '*',
                str(port.port),
                str(port.pid) if port.pid else '-',
                (port.process_name or '-')[:20]
            ])
        
        print(formatter.table(headers, rows))
    
    print()
    return 0


def _handle_bandwidth(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Monitor bandwidth."""
    
    import time
    
    monitor = BandwidthMonitor()
    
    interface = getattr(args, 'interface', None)
    watch = getattr(args, 'watch', False)
    interval = getattr(args, 'interval', 1.0)
    duration = getattr(args, 'duration', None)
    
    def show_bandwidth():
        rates = monitor.get_bandwidth_rates()
        
        if interface:
            rates = {k: v for k, v in rates.items() if k == interface}
        else:
            # Skip loopback
            rates = {k: v for k, v in rates.items() if not k.startswith('lo')}
        
        if watch:
            print('\033[2J\033[H', end='')  # Clear screen
        
        print()
        print(formatter.box("Bandwidth Monitor", width=60))
        print()
        
        for iface_name, rate in rates.items():
            print(f"  {Colors.CYAN}{iface_name}{Colors.RESET}")
            
            rx_rate = rate['rx_rate'] / 1024  # KB/s
            tx_rate = rate['tx_rate'] / 1024  # KB/s
            
            rx_unit = 'KB/s'
            tx_unit = 'KB/s'
            
            if rx_rate > 1024:
                rx_rate /= 1024
                rx_unit = 'MB/s'
            if tx_rate > 1024:
                tx_rate /= 1024
                tx_unit = 'MB/s'
            
            print(f"    {Colors.GREEN}↓{Colors.RESET} RX: {rx_rate:>8.2f} {rx_unit}")
            print(f"    {Colors.RED}↑{Colors.RESET} TX: {tx_rate:>8.2f} {tx_unit}")
            print()
        
        if watch:
            print("  Press Ctrl+C to stop")
    
    if watch:
        start_time = time.time()
        try:
            while True:
                show_bandwidth()
                time.sleep(interval)
                
                if duration and (time.time() - start_time) >= duration:
                    break
        except KeyboardInterrupt:
            print()
    else:
        # Take a sample first
        time.sleep(1)
        show_bandwidth()
    
    return 0


def _handle_interfaces(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """List network interfaces."""
    
    monitor = BandwidthMonitor()
    
    stats = monitor.get_interface_stats()
    
    print()
    print(formatter.box("Network Interfaces", width=70))
    print()
    
    for name, iface in stats.items():
        print(f"  {Colors.CYAN}{name}{Colors.RESET}")
        print(f"    Received:  {formatter.file_size(iface.bytes_recv):>12} ({iface.packets_recv:,} packets)")
        print(f"    Sent:      {formatter.file_size(iface.bytes_sent):>12} ({iface.packets_sent:,} packets)")
        
        if iface.errors_in + iface.errors_out > 0:
            print(f"    {Colors.YELLOW}Errors:    {iface.errors_in + iface.errors_out}{Colors.RESET}")
        
        if iface.drop_in + iface.drop_out > 0:
            print(f"    {Colors.YELLOW}Dropped:   {iface.drop_in + iface.drop_out}{Colors.RESET}")
        
        print()
    
    return 0
