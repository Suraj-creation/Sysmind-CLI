"""
SYSMIND Intelligence CLI Commands

Command handlers for system intelligence features.
"""

import argparse
from typing import Optional

from ..modules.intelligence.correlator import MetricCorrelator
from ..modules.intelligence.anomaly import AnomalyDetector
from ..modules.intelligence.recommender import SystemRecommender
from ..modules.intelligence.health import HealthScorer
from ..utils.formatters import Formatter, Colors
from ..core.database import Database


def register_intel_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register intelligence subcommands."""
    
    intel = subparsers.add_parser(
        'intel',
        help='System intelligence and analysis',
        description='AI-driven system analysis and recommendations'
    )
    
    intel_sub = intel.add_subparsers(dest='intel_command', help='Intel commands')
    
    # Health command
    health = intel_sub.add_parser('health', help='Show system health score')
    health.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    health.add_argument('--report', action='store_true', help='Generate full report')
    
    # Analyze command
    analyze = intel_sub.add_parser('analyze', help='Analyze current system state')
    analyze.add_argument('--duration', type=int, default=30, help='Analysis duration in seconds')
    
    # Recommendations command
    recommend = intel_sub.add_parser('recommend', help='Get optimization recommendations')
    recommend.add_argument('--category', choices=['performance', 'memory', 'disk', 'startup', 'all'],
                          default='all', help='Category to focus on')
    recommend.add_argument('--quick-wins', action='store_true', help='Show only quick wins')
    
    # Anomaly detection command
    anomaly = intel_sub.add_parser('anomaly', help='Detect anomalies')
    anomaly.add_argument('--duration', type=int, default=60, help='Monitoring duration in seconds')
    anomaly.add_argument('--sensitivity', type=float, default=2.0, 
                        help='Detection sensitivity (1-5, lower = more sensitive)')
    
    # Correlate command
    correlate = intel_sub.add_parser('correlate', help='Correlate system metrics')
    correlate.add_argument('--spikes', action='store_true', help='Detect resource spikes')
    correlate.add_argument('--hogs', action='store_true', help='Find resource hogs')
    
    # Summary command
    summary = intel_sub.add_parser('summary', help='Quick system summary')


def handle_intel_command(args: argparse.Namespace, database: Database) -> int:
    """Handle intelligence commands."""
    
    formatter = Formatter()
    
    if not hasattr(args, 'intel_command') or not args.intel_command:
        return _handle_summary(args, formatter, database)
    
    cmd = args.intel_command
    
    if cmd == 'health':
        return _handle_health(args, formatter, database)
    elif cmd == 'analyze':
        return _handle_analyze(args, formatter, database)
    elif cmd == 'recommend':
        return _handle_recommend(args, formatter, database)
    elif cmd == 'anomaly':
        return _handle_anomaly(args, formatter, database)
    elif cmd == 'correlate':
        return _handle_correlate(args, formatter, database)
    elif cmd == 'summary':
        return _handle_summary(args, formatter, database)
    else:
        print(f"{Colors.RED}Unknown intel command: {cmd}{Colors.RESET}")
        return 1


def _handle_health(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Show system health."""
    
    scorer = HealthScorer(database)
    
    detailed = getattr(args, 'detailed', False)
    report = getattr(args, 'report', False)
    
    if report:
        report_text = scorer.export_health_report()
        print(report_text)
        return 0
    
    health = scorer.calculate_health()
    
    print()
    
    # Overall score with visual indicator
    score = health.overall_score
    status = health.overall_status
    
    if score >= 90:
        score_color = Colors.GREEN
        indicator = "●●●●●"
    elif score >= 70:
        score_color = Colors.GREEN
        indicator = "●●●●○"
    elif score >= 50:
        score_color = Colors.YELLOW
        indicator = "●●●○○"
    elif score >= 25:
        score_color = Colors.YELLOW
        indicator = "●●○○○"
    else:
        score_color = Colors.RED
        indicator = "●○○○○"
    
    print(formatter.box("System Health", width=60))
    print()
    print(f"  {Colors.CYAN}Overall Score:{Colors.RESET} {score_color}{score}/100{Colors.RESET} ({status.upper()})")
    print(f"  {score_color}{indicator}{Colors.RESET}")
    print()
    
    # Component scores
    print(f"  {Colors.CYAN}Components:{Colors.RESET}")
    
    for name, component in health.components.items():
        comp_color = Colors.GREEN if component.score >= 70 else Colors.YELLOW if component.score >= 50 else Colors.RED
        bar = formatter.progress_bar(component.score / 100, width=20)
        print(f"    {component.name:12} {bar} {comp_color}{component.score:3d}{Colors.RESET}")
    
    print()
    
    if detailed:
        # Show issues
        all_issues = []
        for component in health.components.values():
            all_issues.extend(component.issues)
        
        if all_issues:
            print(f"  {Colors.CYAN}Issues:{Colors.RESET}")
            for issue in all_issues:
                print(f"    {Colors.YELLOW}•{Colors.RESET} {issue}")
            print()
    
    if health.recommendations:
        print(f"  {Colors.CYAN}Recommendations:{Colors.RESET}")
        for rec in health.recommendations[:5]:
            print(f"    • {rec}")
        print()
    
    return 0


def _handle_analyze(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Analyze system state."""
    
    duration = getattr(args, 'duration', 30)
    
    correlator = MetricCorrelator(database)
    anomaly = AnomalyDetector(database)
    
    print()
    print(formatter.box("System Analysis", width=60))
    print()
    
    print(f"  {Colors.YELLOW}Analyzing system for {duration} seconds...{Colors.RESET}")
    print()
    
    # Current state analysis
    event = correlator.analyze_current_state()
    
    print(f"  {Colors.CYAN}Current State:{Colors.RESET}")
    print(f"    {event.description}")
    
    if event.recommendations:
        print()
        print(f"    {Colors.CYAN}Suggestions:{Colors.RESET}")
        for rec in event.recommendations:
            print(f"      • {rec}")
    
    print()
    
    # Monitor for anomalies
    print(f"  {Colors.YELLOW}Monitoring for anomalies...{Colors.RESET}")
    
    anomalies = anomaly.continuous_monitoring(duration=min(duration, 30))
    
    if anomalies:
        print()
        print(f"  {Colors.RED}Anomalies Detected:{Colors.RESET}")
        for a in anomalies[:10]:
            severity_color = Colors.RED if a.severity == 'critical' else Colors.YELLOW
            print(f"    {severity_color}●{Colors.RESET} {a.description}")
    else:
        print(f"\n  {Colors.GREEN}✓ No anomalies detected during monitoring{Colors.RESET}")
    
    print()
    
    # Resource trends
    trends = correlator.get_resource_trends()
    
    if not trends.get('insufficient_data'):
        print(f"  {Colors.CYAN}Resource Trends:{Colors.RESET}")
        print(f"    Overall: {trends['overall_trend']}")
        print(f"    CPU: {trends['cpu']['current']:.1f}% (trend: {trends['cpu']['trend']:+.1f}%)")
        print(f"    Memory: {trends['memory']['current']:.1f}% (trend: {trends['memory']['trend']:+.1f}%)")
    
    print()
    return 0


def _handle_recommend(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Get recommendations."""
    
    category = getattr(args, 'category', 'all')
    quick_wins = getattr(args, 'quick_wins', False)
    
    recommender = SystemRecommender(database)
    
    print()
    print(formatter.box("System Recommendations", width=70))
    print()
    
    if quick_wins:
        recommendations = recommender.get_quick_wins()
        print(f"  {Colors.CYAN}Quick Wins (low risk, automatable):{Colors.RESET}")
    elif category != 'all':
        recommendations = recommender.get_recommendations_by_category(category)
        print(f"  {Colors.CYAN}Recommendations for {category.title()}:{Colors.RESET}")
    else:
        recommendations = recommender.get_all_recommendations()
        print(f"  {Colors.CYAN}All Recommendations:{Colors.RESET}")
    
    print()
    
    if not recommendations:
        print(f"  {Colors.GREEN}✓ No recommendations - system is running well!{Colors.RESET}")
    else:
        for rec in recommendations:
            priority_color = Colors.RED if rec.priority == 'critical' else \
                            Colors.YELLOW if rec.priority == 'high' else \
                            Colors.CYAN if rec.priority == 'medium' else Colors.WHITE
            
            automated_badge = f" {Colors.GREEN}[AUTO]{Colors.RESET}" if rec.automated else ""
            
            print(f"  {priority_color}[{rec.priority.upper()}]{Colors.RESET} {rec.title}{automated_badge}")
            print(f"    {rec.description}")
            print(f"    {Colors.DIM}Impact:{Colors.RESET} {rec.impact}")
            print(f"    {Colors.DIM}Action:{Colors.RESET} {rec.action}")
            print()
    
    # Summary
    summary = recommender.get_summary()
    print(f"  {Colors.CYAN}Summary:{Colors.RESET}")
    print(f"    Total: {summary['total']} recommendations")
    print(f"    Critical: {summary['critical_count']} | Automatable: {summary['automatable']}")
    print()
    
    return 0


def _handle_anomaly(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Detect anomalies."""
    
    duration = getattr(args, 'duration', 60)
    sensitivity = getattr(args, 'sensitivity', 2.0)
    
    detector = AnomalyDetector(database, sensitivity=sensitivity)
    
    print()
    print(formatter.box("Anomaly Detection", width=60))
    print()
    print(f"  Sensitivity: {sensitivity} (lower = more sensitive)")
    print(f"  Duration: {duration} seconds")
    print()
    print(f"  {Colors.YELLOW}Monitoring...{Colors.RESET}")
    print()
    
    def on_anomaly(a):
        severity_color = Colors.RED if a.severity == 'critical' else Colors.YELLOW
        print(f"  {severity_color}ANOMALY{Colors.RESET} [{a.timestamp.strftime('%H:%M:%S')}] {a.description}")
    
    try:
        anomalies = detector.continuous_monitoring(
            duration=duration,
            interval=1.0,
            callback=on_anomaly
        )
        
        print()
        
        # Summary
        summary = detector.get_anomaly_summary()
        
        print(f"  {Colors.CYAN}Detection Summary:{Colors.RESET}")
        print(f"    Anomalies detected: {summary['total_anomalies_1h']}")
        print(f"    By severity: Critical={summary['by_severity']['critical']}, "
              f"Warning={summary['by_severity']['warning']}, "
              f"Info={summary['by_severity']['info']}")
        print(f"    Samples collected: {summary['samples_collected']}")
        print()
        
        # Statistics
        stats = detector.get_stats()
        if stats:
            print(f"  {Colors.CYAN}Current Statistics:{Colors.RESET}")
            for metric, stat in stats.items():
                print(f"    {metric}: mean={stat.mean:.1f}, std={stat.std:.1f}, "
                      f"range=[{stat.threshold_low:.1f}, {stat.threshold_high:.1f}]")
            print()
    
    except KeyboardInterrupt:
        print(f"\n  {Colors.YELLOW}Monitoring stopped.{Colors.RESET}")
    
    return 0


def _handle_correlate(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Correlate metrics."""
    
    detect_spikes = getattr(args, 'spikes', False)
    find_hogs = getattr(args, 'hogs', False)
    
    correlator = MetricCorrelator(database)
    
    print()
    print(formatter.box("Metric Correlation", width=60))
    print()
    
    if detect_spikes:
        print(f"  {Colors.YELLOW}Detecting resource spikes (10 samples)...{Colors.RESET}")
        print()
        
        events = correlator.detect_resource_spikes(samples=10)
        
        if events:
            print(f"  {Colors.RED}Spikes Detected:{Colors.RESET}")
            for event in events:
                print(f"    • {event.description}")
        else:
            print(f"  {Colors.GREEN}✓ No resource spikes detected{Colors.RESET}")
        print()
    
    if find_hogs:
        print(f"  {Colors.CYAN}Resource Hogs:{Colors.RESET}")
        hogs = correlator.find_resource_hogs()
        
        if hogs:
            for hog in hogs[:10]:
                badges = []
                if hog['is_cpu_hog']:
                    badges.append(f"{Colors.RED}CPU{Colors.RESET}")
                if hog['is_memory_hog']:
                    badges.append(f"{Colors.YELLOW}MEM{Colors.RESET}")
                
                badge_str = " ".join(badges)
                print(f"    {hog['name']} (PID: {hog['pid']}) [{badge_str}]")
                print(f"      CPU: {hog['cpu_percent']:.1f}% | Memory: {hog['memory_mb']:.0f} MB")
        else:
            print(f"    {Colors.GREEN}✓ No resource hogs found{Colors.RESET}")
        print()
    
    if not detect_spikes and not find_hogs:
        # Default: current analysis
        event = correlator.analyze_current_state()
        
        severity_color = Colors.RED if event.severity == 'critical' else \
                        Colors.YELLOW if event.severity == 'warning' else Colors.GREEN
        
        print(f"  {Colors.CYAN}Current State:{Colors.RESET}")
        print(f"    Severity: {severity_color}{event.severity.upper()}{Colors.RESET}")
        print(f"    {event.description}")
        
        if event.recommendations:
            print()
            print(f"    {Colors.CYAN}Recommendations:{Colors.RESET}")
            for rec in event.recommendations:
                print(f"      • {rec}")
        print()
    
    return 0


def _handle_summary(args: argparse.Namespace, formatter: Formatter, database: Database) -> int:
    """Quick system summary."""
    
    scorer = HealthScorer(database)
    recommender = SystemRecommender(database)
    
    health = scorer.calculate_health()
    
    print()
    
    # Quick health indicator
    score = health.overall_score
    if score >= 70:
        indicator = f"{Colors.GREEN}●{Colors.RESET}"
        status_text = "Healthy"
    elif score >= 50:
        indicator = f"{Colors.YELLOW}●{Colors.RESET}"
        status_text = "Needs Attention"
    else:
        indicator = f"{Colors.RED}●{Colors.RESET}"
        status_text = "Issues Detected"
    
    print(f"  {indicator} System Health: {score}/100 ({status_text})")
    print()
    
    # Component summary
    print(f"  {Colors.CYAN}Components:{Colors.RESET}")
    for name, comp in health.components.items():
        color = Colors.GREEN if comp.score >= 70 else Colors.YELLOW if comp.score >= 50 else Colors.RED
        print(f"    {comp.name}: {color}{comp.score}{Colors.RESET}", end="")
        if comp.issues:
            print(f" - {comp.issues[0][:40]}...", end="")
        print()
    print()
    
    # Quick recommendations
    recs = recommender.get_all_recommendations()
    critical = [r for r in recs if r.priority == 'critical']
    
    if critical:
        print(f"  {Colors.RED}Critical Issues ({len(critical)}):{Colors.RESET}")
        for rec in critical[:3]:
            print(f"    • {rec.title}")
    elif recs:
        print(f"  {Colors.YELLOW}Recommendations ({len(recs)}):{Colors.RESET}")
        for rec in recs[:3]:
            print(f"    • {rec.title}")
    else:
        print(f"  {Colors.GREEN}✓ No issues found{Colors.RESET}")
    
    print()
    print(f"  Run '{Colors.CYAN}sysmind intel health --detailed{Colors.RESET}' for full analysis")
    print()
    
    return 0
