# 🧠 SYSMIND - System Intelligence & Automation CLI

<div align="center">

**Your system's intelligent companion**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/)
[![Dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](https://github.com/)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem Statement](#-problem-statement)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Command Reference](#-command-reference)
- [Architecture & Design](#-architecture--design)
- [Technical Design Decisions](#-technical-design-decisions)
- [Project Structure](#-project-structure)
- [Example Outputs](#-example-outputs)
- [Data Storage](#-data-storage)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## Overview

**SYSMIND** is a unified command-line utility that provides intelligent system monitoring, process management, disk analytics, network diagnostics, and automated maintenance — all through a single, cohesive interface.

Unlike traditional system tools that operate in isolation, SYSMIND treats the system as an interconnected ecosystem, correlating resource usage, process behavior, and disk activity to provide **actionable insights** rather than just raw data.

### Why SYSMIND?

| Traditional Tools | SYSMIND |
|-------------------|---------|
| Fragmented - multiple tools needed | Unified interface for all operations |
| No historical context | SQLite database with full history |
| Manual correlation required | Automatic cross-component analysis |
| Reactive (show current state) | Proactive (baselines, anomaly detection) |
| Risky cleanup operations | Safe quarantine system with undo support |

---

## 🎯 Problem Statement

### The Daily Challenges Users Face

Every developer, student, and power user encounters these recurring problems:

#### 1. System Slowdown Without Clear Cause
- Task Manager shows high CPU, but which process is abnormal?
- Is this usage spike normal for this time of day?
- How does current usage compare to the baseline?

#### 2. Disk Space Mysteriously Disappearing
- Where did all the space go?
- Which directories are growing fastest?
- Are there duplicate files wasting space?

#### 3. Network Issues Without Diagnostic Tools
- Is it the DNS, the gateway, or the internet?
- Which application is consuming all the bandwidth?
- What connections are active right now?

#### 4. Process Management Blindness
- Which processes are safe to kill?
- What's consuming resources and why?
- How do I manage startup programs safely?

#### 5. Risky Cleanup Operations
- Traditional cleaners delete without recovery options
- No way to undo accidental deletions
- Aggressive cleanup can break applications

### SYSMIND's Solution

SYSMIND addresses these challenges through:

- **Unified System View**: One tool for monitoring, disk, process, and network analysis
- **Historical Intelligence**: Learning from past data to provide context
- **Safety-First Design**: Quarantine system with full undo support
- **Actionable Insights**: Not just data, but recommendations
- **Cross-Correlation**: Linking events across different system components

---

## ✨ Features

### 🖥️ System Monitor (`sysmind monitor`)
- Real-time CPU, memory, and disk I/O monitoring
- Historical data tracking with trend analysis
- Baseline establishment and anomaly detection
- Live dashboard with visual progress bars

### 💾 Disk Intelligence (`sysmind disk`)
- Space analysis with visual breakdowns
- **Multi-phase duplicate detection** (size → quick hash → full hash)
- Safe cleanup with quarantine system
- Large file and old file finder

### ⚙️ Process Manager (`sysmind process`)
- Process listing with detailed context
- Process tree visualization
- Startup program management
- Watchdog rules for automated monitoring

### 🌐 Network Diagnostics (`sysmind network`)
- Connectivity testing (DNS, gateway, internet)
- Active connection monitoring
- Bandwidth usage by process
- Listening ports analysis

### 🧠 Intelligence Core (`sysmind intel`)
- Overall system health scoring (0-100)
- Cross-component correlation
- Anomaly detection
- AI-driven recommendations

### ⚙️ Configuration (`sysmind config`)
- Persistent settings management
- Customizable thresholds and intervals
- JSON-based configuration

---

## 📦 Installation

### Prerequisites

- **Python 3.8 or higher** (standard library only - no external dependencies!)
- Windows, Linux, or macOS

### Step 1: Clone or Download

```bash
git clone https://github.com/yourusername/sysmind.git
cd sysmind
```

Or download and extract the ZIP file.

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install SYSMIND

```bash
pip install -e .
```

This installs SYSMIND in development mode, making the `sysmind` command available globally in your virtual environment.

### Step 4: Verify Installation

```bash
sysmind --version
# Output: SYSMIND v1.0.0

sysmind --help
```

---

## 🚀 Quick Start

### 1. Get a Quick System Overview

```bash
sysmind quick
```

This shows:
- Current CPU and memory usage with visual bars
- Overall health score
- Any immediate issues detected
- Recommendations for improvement

### 2. Monitor System Resources

```bash
# Real-time status
sysmind monitor status

# Detailed CPU metrics
sysmind monitor cpu

# Memory breakdown
sysmind monitor memory

# Live dashboard (auto-refreshing)
sysmind monitor dashboard
```

### 3. Analyze Disk Usage

```bash
# Show disk partitions and usage
sysmind disk usage

# Analyze a specific directory
sysmind disk analyze ~/Downloads

# Find large files (>100MB)
sysmind disk large .

# Find duplicate files
sysmind disk duplicates ~/Documents
```

### 4. Manage Processes

```bash
# List all processes (sorted by CPU)
sysmind process list --sort cpu

# Top resource consumers
sysmind process top

# View process tree
sysmind process tree

# Manage startup programs
sysmind process startup list
```

### 5. Network Diagnostics

```bash
# Quick connectivity check
sysmind network status

# View active connections
sysmind network connections

# Ping a host
sysmind network ping google.com
```

### 6. System Intelligence

```bash
# Get detailed health report
sysmind intel health

# Get optimization recommendations
sysmind intel recommend

# Detect anomalies
sysmind intel anomaly
```

---

## 📚 Command Reference

### Global Options

```
sysmind [OPTIONS] <command> [args...]

Options:
  --version, -V     Show version number
  --verbose, -v     Increase verbosity
  --quiet, -q       Suppress non-essential output
  --no-color        Disable colored output
  --config FILE     Use custom config file
```

### Monitor Commands

| Command | Description |
|---------|-------------|
| `sysmind monitor status` | Show current system status |
| `sysmind monitor cpu` | Detailed CPU metrics |
| `sysmind monitor memory` | Memory usage breakdown |
| `sysmind monitor dashboard` | Live monitoring dashboard |
| `sysmind monitor baseline create` | Create performance baseline |
| `sysmind monitor baseline compare` | Compare current state to baseline |
| `sysmind monitor baseline list` | List saved baselines |

### Disk Commands

| Command | Description |
|---------|-------------|
| `sysmind disk usage [path]` | Show disk usage |
| `sysmind disk analyze <path>` | Analyze directory |
| `sysmind disk large <path>` | Find large files (>100MB) |
| `sysmind disk old <path>` | Find old unused files |
| `sysmind disk duplicates <path>` | Find duplicate files |
| `sysmind disk clean` | Find cleanable items (preview) |
| `sysmind disk clean --execute` | Actually clean files |
| `sysmind disk quarantine list` | View quarantined files |
| `sysmind disk quarantine restore <id>` | Restore a file |

### Process Commands

| Command | Description |
|---------|-------------|
| `sysmind process list` | List running processes |
| `sysmind process list --sort cpu` | Sort by CPU usage |
| `sysmind process list --sort memory` | Sort by memory |
| `sysmind process top` | Top resource consumers |
| `sysmind process tree` | Show process tree |
| `sysmind process profile <name>` | Profile a process |
| `sysmind process startup list` | List startup programs |
| `sysmind process kill <pid>` | Kill a process |

### Network Commands

| Command | Description |
|---------|-------------|
| `sysmind network status` | Network connectivity status |
| `sysmind network ping <host>` | Ping a host |
| `sysmind network trace <host>` | Traceroute to host |
| `sysmind network connections` | Active connections |
| `sysmind network connections --established` | Established only |
| `sysmind network listening` | Listening ports |
| `sysmind network bandwidth` | Bandwidth monitor |
| `sysmind network interfaces` | Network interfaces |

### Intelligence Commands

| Command | Description |
|---------|-------------|
| `sysmind intel health` | System health score |
| `sysmind intel analyze` | Deep system analysis |
| `sysmind intel recommend` | Optimization suggestions |
| `sysmind intel anomaly` | Detect anomalies |
| `sysmind intel correlate` | Cross-metric correlation |
| `sysmind intel summary` | Quick summary |

### Configuration Commands

| Command | Description |
|---------|-------------|
| `sysmind config show` | Show all settings |
| `sysmind config get <key>` | Get specific setting |
| `sysmind config set <key> <value>` | Set a value |
| `sysmind config reset` | Reset to defaults |

---

## 🏗️ Architecture & Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SYSMIND CLI                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Monitor │  │  Disk   │  │ Process │  │ Network │        │
│  │ Module  │  │ Module  │  │ Module  │  │ Module  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴─────┬──────┴────────────┘              │
│                          │                                   │
│              ┌───────────▼───────────┐                      │
│              │   Intelligence Core   │                      │
│              │  • Correlator         │                      │
│              │  • Anomaly Detector   │                      │
│              │  • Recommender        │                      │
│              │  • Health Calculator  │                      │
│              └───────────┬───────────┘                      │
│                          │                                   │
│              ┌───────────▼───────────┐                      │
│              │    SQLite Database    │                      │
│              │  • System Snapshots   │                      │
│              │  • Baselines          │                      │
│              │  • Alerts & History   │                      │
│              │  • Quarantine Manifest│                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Command
     │
     ▼
┌─────────────┐
│   CLI.py    │ ◄── Argument parsing, routing
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│            Command Router                    │
│  ┌─────────┬─────────┬─────────┬─────────┐  │
│  │ monitor │  disk   │ process │ network │  │
│  └────┬────┴────┬────┴────┬────┴────┬────┘  │
└───────┼─────────┼─────────┼─────────┼───────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
   ┌─────────────────────────────────────┐
   │         Module Executors            │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │         Database Layer              │
   │  (Historical Data, Baselines)       │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │         Output Formatter            │
   │  (Tables, JSON, Progress Bars)      │
   └─────────────────────────────────────┘
```

---

## 🔧 Technical Design Decisions

### 1. Standard Library Only

**Decision**: Use only Python standard library - no external dependencies.

**Rationale**:
- Maximum portability across systems
- No dependency conflicts or version issues
- Easy installation (just Python)
- Reduced attack surface
- Works offline without pip

**Trade-offs Accepted**:
- More code for things like system metrics (reimplemented using /proc, ctypes, WMI)
- Less sophisticated visualizations (no Rich library)
- Manual cross-platform handling

### 2. SQLite for Persistence

**Decision**: Use SQLite for all data storage.

**Rationale**:
- Part of Python standard library
- Zero configuration required
- Single file database (easy backup/portability)
- ACID compliant for data integrity
- Supports complex queries for analytics

**Schema Design**:
```sql
-- Core tables
system_snapshots    -- Point-in-time system state
process_history     -- Process metrics over time
baselines           -- Computed normal ranges
alerts              -- System alerts/warnings
quarantine          -- Deleted file manifests

-- Indexed for performance
CREATE INDEX idx_snapshots_timestamp ON system_snapshots(timestamp);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
```

### 3. Quarantine System for Safety

**Decision**: Never permanently delete files directly - always quarantine first.

**Rationale**:
- Users can recover accidentally deleted files
- Builds trust in the cleanup system
- 30-day retention before permanent deletion
- Full manifest of what was deleted and why

**Implementation**:
```
~/.sysmind/quarantine/
├── <uuid>/
│   ├── manifest.json    # Original path, reason, timestamp
│   └── file.dat         # Compressed original file
```

### 4. Multi-Phase Duplicate Detection

**Decision**: Use 3-phase algorithm (size → quick hash → full hash).

**Rationale**:
- Size grouping is O(n) and eliminates most files immediately
- Quick hash (first 4KB) catches differences cheaply
- Full SHA-256 only for true candidate duplicates
- Balances accuracy with performance

**Algorithm Complexity**:
- Phase 1 (Size): O(n) scan
- Phase 2 (Quick Hash): O(k) where k << n (same-size files)
- Phase 3 (Full Hash): O(m) where m << k (same quick-hash files)

### 5. Health Score Algorithm

**Decision**: Weighted scoring across 5 components.

**Formula**:
```python
overall_score = (
    cpu_score * 0.25 +
    memory_score * 0.25 +
    disk_score * 0.20 +
    process_score * 0.15 +
    network_score * 0.15
)
```

**Score Calculation**:
- **CPU**: Based on usage vs baseline, with penalty for sustained high usage
- **Memory**: Usage percentage with available memory consideration
- **Disk**: Space usage + I/O health
- **Processes**: Resource distribution, zombie detection
- **Network**: Connectivity success, error rates

### 6. Platform Abstraction Layer

**Decision**: Abstract all OS-specific operations.

**Implementation**:
```python
class PlatformAdapter:
    @staticmethod
    def get_adapter():
        if is_windows():
            return WindowsAdapter()
        elif is_linux():
            return LinuxAdapter()
        else:
            return MacOSAdapter()
```

**Coverage**:
- Process enumeration (WMI vs /proc)
- Startup program locations (Registry vs .desktop files)
- System metrics collection
- Network interface enumeration

### 7. Command Structure Design

**Decision**: Use `sysmind <module> <command> [options]` pattern.

**Rationale**:
- Intuitive grouping by functionality
- Discoverable through `--help` at each level
- Consistent with modern CLI tools (git, docker, kubectl)
- Easy to extend with new modules

---

## 📁 Project Structure

```
sysmind/
├── cli.py                 # Main entry point, argument parsing
├── __init__.py            # Package version and metadata
│
├── core/                  # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── database.py        # SQLite wrapper with all DB operations
│   └── errors.py          # Custom exception hierarchy
│
├── modules/               # Feature modules
│   ├── monitor/           # System monitoring
│   │   ├── cpu.py         # CPU metrics collection
│   │   ├── memory.py      # Memory monitoring
│   │   ├── realtime.py    # Live dashboard
│   │   └── baseline.py    # Baseline computation
│   │
│   ├── disk/              # Disk analysis
│   │   ├── analyzer.py    # Directory scanning
│   │   ├── duplicates.py  # Duplicate detection (3-phase)
│   │   ├── cleaner.py     # Safe cleanup operations
│   │   └── quarantine.py  # Quarantine management
│   │
│   ├── process/           # Process management
│   │   ├── manager.py     # Process listing
│   │   ├── profiler.py    # Process profiling
│   │   ├── startup.py     # Startup programs
│   │   └── watchdog.py    # Monitoring rules
│   │
│   ├── network/           # Network diagnostics
│   │   ├── diagnostics.py # Ping, DNS, traceroute
│   │   ├── connections.py # Active connections
│   │   └── bandwidth.py   # Bandwidth monitoring
│   │
│   └── intelligence/      # AI/ML components
│       ├── correlator.py  # Cross-metric correlation
│       ├── anomaly.py     # Anomaly detection
│       ├── recommender.py # Recommendation engine
│       └── health.py      # Health score calculator
│
├── commands/              # CLI command handlers
│   ├── monitor_commands.py
│   ├── disk_commands.py
│   ├── process_commands.py
│   ├── network_commands.py
│   ├── intel_commands.py
│   └── config_commands.py
│
└── utils/                 # Shared utilities
    ├── formatters.py      # Output formatting (tables, boxes)
    ├── validators.py      # Input validation
    ├── platform_utils.py  # OS-specific utilities
    └── logger.py          # Logging infrastructure
```

---

## 📊 Example Outputs

### Quick System Overview

```
$ sysmind quick

  Quick System Overview

  CPU:    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0.3%  31.0%
  Memory: █████████████████░░░░░░░░░░░░░   0.9%  85.2%

  Health Score: 59/100 (fair)

  Issues:
    • High memory usage: 86.2%

  Run 'sysmind intel health' for detailed analysis
```

### Disk Usage Analysis

```
$ sysmind disk usage

╔════════════════════════════════════════════════════════════════════╗
║ Disk Partitions                                                    ║
╚════════════════════════════════════════════════════════════════════╝

  C:\ mounted on C:\
    ████████████████████░░░░░░░░░░░░░░░░░░░░  55.7%
    Total: 237.2 GB | Used: 132.0 GB | Free: 105.1 GB
```

### Network Status

```
$ sysmind network status

╔════════════════════════════════════════════════════════════════════╗
║ Network Status                                                     ║
╚════════════════════════════════════════════════════════════════════╝

  Connectivity Check
    Internet: ✓ Connected
    DNS: ✓ Working
    Latency: 19.0 ms

  Network Interfaces
    Wi-Fi
      RX: 282.7 MB | TX: 138.8 MB

  Connections
    Active: 30 established
    Total: 111
```

### System Health Report

```
$ sysmind intel health

╔══════════════════════════════════════════════════════════╗
║ System Health                                            ║
╚══════════════════════════════════════════════════════════╝

  Overall Score: 62/100 (FAIR)
  ●●●○○

  Components:
    CPU                   ░░░░░░░░░░░░░░░░░░░░   0.8%  78
    Memory                ████████████████░░░░   0.2%  16
    Disk                  ██████████░░░░░░░░░░   0.4%  44
    Processes             ████████████████████   1.0% 100
    Network               ████████████████████   1.0% 100

  Recommendations:
    • Multiple Code Instances detected
    • Multiple chrome Instances running
    • Heavy Startup Programs
```

### Disk Cleanup Preview

```
$ sysmind disk clean

╔════════════════════════════════════════════════════════════════════╗
║ Disk Cleanup                                                       ║
╚════════════════════════════════════════════════════════════════════╝

  Found 67 items totaling 2.3 GB

  Temp: 3 items, 1.5 GB
      518.6 MB  C:\Users\...\AppData\Local\Temp
      
  Cache: 2 items, 752.2 MB
      391.6 MB  Chrome Cache
      360.6 MB  Edge Cache
      
  Log: 62 items, 2.7 MB
      (old log files)

  To actually delete files, run with --execute
```

---

## 💾 Data Storage

SYSMIND stores all data in `~/.sysmind/`:

```
~/.sysmind/
├── sysmind.db         # SQLite database
├── config.json        # User configuration
├── logs/              # Application logs
└── quarantine/        # Quarantined files (30-day retention)
```

### Configuration File

```json
{
  "general": {
    "data_dir": "~/.sysmind",
    "log_level": "INFO",
    "color_output": true
  },
  "monitor": {
    "snapshot_interval_seconds": 300,
    "alert_thresholds": {
      "cpu_warning": 80,
      "cpu_critical": 95,
      "memory_warning": 85,
      "memory_critical": 95
    }
  },
  "disk": {
    "exclude_patterns": ["node_modules", ".git", "__pycache__"],
    "min_duplicate_size_mb": 1
  },
  "process": {
    "protected_processes": ["System", "smss.exe", "csrss.exe"]
  }
}
```

---

## ❓ Troubleshooting

### Common Issues

**1. Permission Errors**

Some operations require elevated privileges:
```bash
# Windows (Run as Administrator)
sysmind process startup list

# Linux
sudo sysmind process list
```

**2. Slow Duplicate Detection**

For large directories, use size filtering:
```bash
sysmind disk duplicates ~/Documents --min-size 10MB
```

**3. Database Locked**

If you see SQLite lock errors:
```bash
# Wait for any running sysmind instance to finish
# Or delete the lock file
rm ~/.sysmind/sysmind.db-journal
```

### Getting Help

```bash
# General help
sysmind --help

# Module-specific help
sysmind monitor --help
sysmind disk --help

# Command-specific help
sysmind disk duplicates --help
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions under 50 lines
- Add tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by tools like `htop`, `ncdu`, `fdupes`, and `glances`
- Built with ❤️ using only Python's standard library
- Designed for the community of developers who want to understand their systems better

---

<div align="center">

**SYSMIND** - *Your system's intelligent companion*

[Report Bug](https://github.com/yourusername/sysmind/issues) · [Request Feature](https://github.com/yourusername/sysmind/issues) · [Documentation](https://github.com/yourusername/sysmind/wiki)

</div>
