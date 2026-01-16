# 🧠 SYSMIND - System Intelligence & Automation CLI
## Comprehensive Development Plan

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement & Analysis](#problem-statement--analysis)
3. [Proposed Solution](#proposed-solution)
4. [System Architecture](#system-architecture)
5. [Feature Breakdown](#feature-breakdown)
6. [Technical Design](#technical-design)
7. [Data Structures & Algorithms](#data-structures--algorithms)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Testing Strategy](#testing-strategy)
11. [CLI Interface Design](#cli-interface-design)
12. [Advanced Features](#advanced-features)
13. [Code Organization](#code-organization)
14. [Extensibility & Future Scope](#extensibility--future-scope)

---

## 1. Executive Summary

### Tool Name: `sysmind`
**Tagline:** *"Your system's intelligent companion"*

**sysmind** is a unified command-line utility that provides intelligent system monitoring, process management, disk analytics, network diagnostics, and automated maintenance — all through a single, cohesive interface. Unlike traditional system tools that operate in isolation, sysmind treats the system as an interconnected ecosystem, correlating resource usage, process behavior, and disk activity to provide actionable insights.

### Why This Problem?

Every developer, student, and power user faces these daily challenges:

| Problem | Traditional Solution | Limitation |
|---------|---------------------|------------|
| System slowdown | Task Manager | No historical data, no root cause analysis |
| Disk full | Manually find large files | Time-consuming, misses duplicates |
| Memory leaks | Kill processes randomly | Doesn't identify patterns |
| Network issues | Multiple tools (ping, tracert, netstat) | Fragmented workflow |
| Startup bloat | Manual registry editing | Risky, no recommendations |

**sysmind** unifies these into one intelligent system with memory, learning, and automation.

---

## 2. Problem Statement & Analysis

### 2.1 Core Problems Identified

#### Problem 1: Fragmented System Visibility
Users lack a unified view of their system's health. CPU, memory, disk, and network are monitored separately, missing correlations like:
- High CPU → which process → is it normal for this time?
- Disk full → which files grew recently → are they temp files?
- Network slow → which process is consuming bandwidth?

#### Problem 2: Reactive vs. Proactive Management
Current tools only show *current state*. Users:
- Don't know their baseline "normal"
- Can't predict issues before they occur
- Have no historical trends for comparison

#### Problem 3: Dangerous Cleanup Operations
Disk cleanup tools either:
- Delete too aggressively (data loss risk)
- Are too conservative (ineffective)
- Don't consider file importance or recency

#### Problem 4: Process Management Blindness
Users kill processes without understanding:
- Why it's consuming resources
- If it's system-critical
- Historical behavior patterns

#### Problem 5: Lack of Automation
Repetitive maintenance tasks require manual intervention:
- Clearing temp files
- Managing startup programs
- Monitoring specific applications

### 2.2 Target Users

1. **Students/Developers** - Limited hardware, need optimization
2. **Power Users** - Want granular control without GUI overhead
3. **System Administrators** - Need quick diagnostics on remote machines
4. **Anyone with an aging computer** - Maximize performance

### 2.3 Design Constraints

| Constraint | Rationale |
|------------|-----------|
| Standard libraries only | Portability, no dependency hell |
| Cross-platform (Python) | Works on Windows, Linux, macOS |
| Minimal footprint | Should not be a resource hog itself |
| Non-destructive by default | Safety first |
| Offline operation | No internet dependency |

---

## 3. Proposed Solution

### 3.1 Unified System Intelligence

```
┌─────────────────────────────────────────────────────────────┐
│                        SYSMIND CLI                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Monitor │  │  Disk   │  │ Process │  │ Network │        │
│  │ Engine  │  │ Analyzer│  │ Manager │  │  Diag   │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴─────┬──────┴────────────┘              │
│                          │                                   │
│              ┌───────────▼───────────┐                      │
│              │   Intelligence Core   │                      │
│              │  ┌─────────────────┐  │                      │
│              │  │ Historical Data │  │                      │
│              │  │    Database     │  │                      │
│              │  └─────────────────┘  │                      │
│              │  ┌─────────────────┐  │                      │
│              │  │  Pattern        │  │                      │
│              │  │  Recognition    │  │                      │
│              │  └─────────────────┘  │                      │
│              │  ┌─────────────────┐  │                      │
│              │  │  Rule Engine    │  │                      │
│              │  │  (Automation)   │  │                      │
│              │  └─────────────────┘  │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Key Differentiators

| Feature | Traditional Tools | sysmind |
|---------|------------------|---------|
| Data persistence | None | SQLite database with history |
| Cross-correlation | Manual | Automatic (CPU spike → process → files) |
| Recommendations | None | Context-aware suggestions |
| Safety | Varies | Quarantine system, undo support |
| Learning | None | Baseline establishment, anomaly detection |

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
sysmind/
├── core/
│   ├── __init__.py
│   ├── cli.py                 # Main CLI entry point
│   ├── config.py              # Configuration management
│   └── database.py            # SQLite wrapper
│
├── modules/
│   ├── __init__.py
│   ├── monitor/
│   │   ├── __init__.py
│   │   ├── cpu.py             # CPU monitoring
│   │   ├── memory.py          # Memory monitoring
│   │   ├── realtime.py        # Real-time dashboard
│   │   └── baseline.py        # Baseline computation
│   │
│   ├── disk/
│   │   ├── __init__.py
│   │   ├── analyzer.py        # Disk space analysis
│   │   ├── duplicates.py      # Duplicate detection
│   │   ├── treemap.py         # Visual tree representation
│   │   └── cleaner.py         # Safe cleanup operations
│   │
│   ├── process/
│   │   ├── __init__.py
│   │   ├── manager.py         # Process listing & management
│   │   ├── profiler.py        # Process profiling
│   │   ├── watchdog.py        # Process monitoring rules
│   │   └── startup.py         # Startup program management
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── diagnostics.py     # Network testing
│   │   ├── connections.py     # Active connections
│   │   └── bandwidth.py       # Bandwidth monitoring
│   │
│   └── intelligence/
│       ├── __init__.py
│       ├── correlator.py      # Cross-module correlation
│       ├── anomaly.py         # Anomaly detection
│       ├── recommender.py     # Recommendation engine
│       └── scheduler.py       # Automated task scheduler
│
├── utils/
│   ├── __init__.py
│   ├── formatters.py          # Output formatting
│   ├── validators.py          # Input validation
│   ├── platform_utils.py      # OS-specific utilities
│   └── logger.py              # Logging infrastructure
│
├── data/
│   ├── sysmind.db             # SQLite database
│   ├── config.json            # User configuration
│   └── quarantine/            # Quarantined files
│
└── tests/
    ├── test_monitor.py
    ├── test_disk.py
    ├── test_process.py
    └── test_network.py
```

### 4.2 Component Interaction Diagram

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
   │  (Tables, JSON, Charts)             │
   └─────────────────────────────────────┘
```

### 4.3 Data Flow Architecture

```
                    ┌──────────────────┐
                    │   Raw System     │
                    │   Metrics        │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │   CPU    │  │  Memory  │  │   Disk   │
        │ Collector│  │ Collector│  │ Collector│
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             └──────┬──────┴──────┬──────┘
                    │             │
                    ▼             ▼
             ┌───────────┐ ┌───────────┐
             │ Normalizer│ │ Validator │
             └─────┬─────┘ └─────┬─────┘
                   │             │
                   └──────┬──────┘
                          │
                          ▼
                   ┌────────────┐
                   │  Database  │
                   │  Storage   │
                   └──────┬─────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │  Baseline  │ │  Anomaly   │ │ Correlator │
    │  Computer  │ │  Detector  │ │            │
    └────────────┘ └────────────┘ └────────────┘
```

---

## 5. Feature Breakdown

### 5.1 Module 1: System Monitor (`sysmind monitor`)

#### 5.1.1 Real-time Dashboard
```bash
sysmind monitor live
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║                    SYSMIND LIVE MONITOR                      ║
╠══════════════════════════════════════════════════════════════╣
║  CPU Usage     ████████████░░░░░░░░  58%  (Baseline: 35%)   ║
║  Memory        ██████████████░░░░░░  72%  (6.2/8.0 GB)      ║
║  Disk I/O      ███░░░░░░░░░░░░░░░░░  15%  Read: 45 MB/s     ║
║  Network       ██████░░░░░░░░░░░░░░  32%  ↓12 ↑3 Mbps       ║
╠══════════════════════════════════════════════════════════════╣
║  Top Processes:                                              ║
║  1. chrome.exe        CPU: 23%  MEM: 1.2GB  ⚠ Above normal  ║
║  2. code.exe          CPU: 12%  MEM: 890MB  ✓ Normal        ║
║  3. python.exe        CPU: 8%   MEM: 256MB  ✓ Normal        ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠ ALERT: CPU 23% above baseline. Likely cause: chrome.exe  ║
╚══════════════════════════════════════════════════════════════╝
         Press 'q' to quit | 'h' for help | 's' to snapshot
```

#### 5.1.2 Historical Analysis
```bash
sysmind monitor history --period 7d
```

**Features:**
- Hourly/daily/weekly aggregations
- Peak usage identification
- Trend analysis (improving/degrading)
- Baseline deviation tracking

#### 5.1.3 Baseline Establishment
```bash
sysmind monitor baseline --establish
sysmind monitor baseline --show
sysmind monitor baseline --compare
```

**Algorithm:**
```
For each metric (CPU, Memory, Disk I/O):
    1. Collect samples over 24-48 hours
    2. Remove outliers (>2 standard deviations)
    3. Compute mean and standard deviation
    4. Store as baseline profile
    5. Flag deviations > 1.5σ as warnings
    6. Flag deviations > 2σ as critical
```

### 5.2 Module 2: Disk Intelligence (`sysmind disk`)

#### 5.2.1 Space Analysis
```bash
sysmind disk analyze [path]
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║              DISK SPACE ANALYSIS: C:\Users\Govin             ║
╠══════════════════════════════════════════════════════════════╣
║  Total: 256 GB | Used: 198 GB (77%) | Free: 58 GB           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ████████████████████████████████████░░░░░░░░░░  77%        ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  TOP SPACE CONSUMERS                                         ║
╠══════════════════════════════════════════════════════════════╣
║  📁 AppData/Local          45.2 GB  ███████████░░  23%      ║
║  │  └── Google/Chrome      12.3 GB  (Cache: 8.1 GB)         ║
║  │  └── JetBrains          8.7 GB   (IDE caches)            ║
║  │  └── npm-cache          6.2 GB   ⚠ Cleanable             ║
║  │                                                           ║
║  📁 Downloads              23.8 GB  ██████░░░░░░░  12%      ║
║  │  └── 142 files older than 30 days (18.2 GB)              ║
║  │  └── 23 duplicate files (3.4 GB)                         ║
║  │                                                           ║
║  📁 Documents              18.5 GB  █████░░░░░░░░  9%       ║
║  │  └── Projects/          12.1 GB                          ║
║  │  └── node_modules/      8.9 GB   ⚠ In 12 projects        ║
╠══════════════════════════════════════════════════════════════╣
║  💡 RECOMMENDATIONS                                          ║
║  1. Clear browser cache: +8.1 GB                            ║
║  2. Remove old downloads: +18.2 GB                          ║
║  3. Deduplicate files: +3.4 GB                              ║
║  4. Clear npm cache: +6.2 GB                                ║
║                                                              ║
║  Total recoverable: ~35.9 GB                                ║
╚══════════════════════════════════════════════════════════════╝
```

#### 5.2.2 Duplicate Detection
```bash
sysmind disk duplicates [path] --min-size 1MB
```

**Algorithm (Multi-Phase):**
```
Phase 1: Size Grouping (Fast)
    - Group files by size
    - Skip unique sizes (no duplicates possible)
    
Phase 2: Quick Hash (Medium)
    - For same-size files, hash first 4KB
    - Skip if first-chunk differs
    
Phase 3: Full Hash (Thorough)
    - SHA-256 full file for remaining candidates
    - Group by hash
    
Phase 4: Analysis
    - Identify oldest/newest versions
    - Check file locations (same folder = likely intentional)
    - Score deletion safety
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║              DUPLICATE FILE ANALYSIS                         ║
╠══════════════════════════════════════════════════════════════╣
║  Scanned: 12,456 files | Duplicates Found: 89 sets          ║
║  Potential Space Recovery: 4.7 GB                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [1] presentation_final.pptx (3 copies, 45 MB each)         ║
║      ├── C:\Users\Downloads\presentation_final.pptx         ║
║      │   Created: 2025-12-15 | Last Access: 2026-01-10      ║
║      ├── C:\Users\Documents\presentation_final.pptx     ✓   ║
║      │   Created: 2025-12-16 | Last Access: 2026-01-15      ║
║      └── C:\Users\Desktop\presentation_final(1).pptx        ║
║          Created: 2025-12-16 | Last Access: 2025-12-16      ║
║      💡 Recommend: Keep Documents version, remove others    ║
║                                                              ║
║  [2] photo_2025.jpg (5 copies, 12 MB each)                  ║
║      ... (expand with --verbose)                            ║
╠══════════════════════════════════════════════════════════════╣
║  Actions:                                                    ║
║    sysmind disk duplicates --remove safe    (Auto-remove)   ║
║    sysmind disk duplicates --interactive    (Review each)   ║
║    sysmind disk duplicates --report         (Export CSV)    ║
╚══════════════════════════════════════════════════════════════╝
```

#### 5.2.3 Safe Cleanup
```bash
sysmind disk clean --safe
sysmind disk clean --aggressive --dry-run
```

**Safety Levels:**
| Level | What it cleans | Risk |
|-------|----------------|------|
| `--safe` | Temp files, browser cache, logs >30 days | None |
| `--moderate` | Above + old downloads, duplicate files | Low |
| `--aggressive` | Above + large files, unused apps data | Medium |

**All deletions go to quarantine first:**
```
~/.sysmind/quarantine/
└── 2026-01-16_143022/
    ├── manifest.json      # What was deleted
    ├── files/             # Actual files (compressed)
    └── restore.sh         # One-click restore
```

### 5.3 Module 3: Process Intelligence (`sysmind process`)

#### 5.3.1 Process Listing with Context
```bash
sysmind process list --sort cpu
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════════════════╗
║                        PROCESS INTELLIGENCE                              ║
╠═══════╤═══════════════════╤═══════╤════════╤══════════╤═════════════════╣
║  PID  │ Name              │ CPU % │ Memory │ Status   │ Intelligence    ║
╠═══════╪═══════════════════╪═══════╪════════╪══════════╪═════════════════╣
║ 4521  │ chrome.exe        │ 34.2  │ 1.8 GB │ ⚠ HIGH   │ 2x normal CPU   ║
║       │ └── 12 tabs open  │       │        │          │ Consider: Tab   ║
║       │                   │       │        │          │ suspender ext   ║
╟───────┼───────────────────┼───────┼────────┼──────────┼─────────────────╢
║ 2891  │ node.exe          │ 18.5  │ 512 MB │ ✓ NORMAL │ npm run dev     ║
║       │ └── Port 3000     │       │        │          │ Running 2h 15m  ║
╟───────┼───────────────────┼───────┼────────┼──────────┼─────────────────╢
║ 1205  │ Code.exe          │ 8.2   │ 890 MB │ ✓ NORMAL │ Baseline match  ║
╟───────┼───────────────────┼───────┼────────┼──────────┼─────────────────╢
║ 892   │ svchost.exe       │ 5.1   │ 45 MB  │ ✓ SYSTEM │ Windows Service ║
║       │                   │       │        │          │ 🔒 Protected    ║
╚═══════╧═══════════════════╧═══════╧════════╧══════════╧═════════════════╝
```

#### 5.3.2 Process Profiler
```bash
sysmind process profile chrome.exe --duration 60
```

**Features:**
- Track CPU/memory over time
- Identify resource spikes
- Correlate with user actions
- Generate behavior report

#### 5.3.3 Watchdog Rules
```bash
sysmind process watch add --name "chrome.exe" --cpu-max 50 --action alert
sysmind process watch add --name "*.exe" --memory-max 2GB --action log
sysmind process watch list
sysmind process watch run --daemon
```

**Rule Configuration:**
```json
{
  "rules": [
    {
      "id": "chrome-cpu-limit",
      "match": {"name": "chrome.exe"},
      "conditions": {"cpu_percent": {">": 50}},
      "duration": "5m",
      "actions": ["alert", "log"],
      "cooldown": "30m"
    },
    {
      "id": "memory-hog",
      "match": {"name": "*"},
      "conditions": {"memory_mb": {">": 2048}},
      "actions": ["alert"],
      "exclude": ["Code.exe", "chrome.exe"]
    }
  ]
}
```

#### 5.3.4 Startup Manager
```bash
sysmind process startup list
sysmind process startup disable "Spotify"
sysmind process startup analyze
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║                   STARTUP PROGRAM ANALYSIS                   ║
╠══════════════════════════════════════════════════════════════╣
║  Total Startup Items: 23                                     ║
║  Estimated Boot Impact: 45 seconds                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ✓ ESSENTIAL (Keep Enabled)                                 ║
║  ├── Windows Security (SecurityHealth)                      ║
║  ├── Audio Service (Realtek HD)                             ║
║  └── Display Driver (NVIDIA)                                ║
║                                                              ║
║  ⚡ HIGH IMPACT (Consider Disabling)                         ║
║  ├── Spotify (+8s boot time)          [Disable?]            ║
║  ├── Discord (+6s boot time)          [Disable?]            ║
║  └── Steam Client (+5s boot time)     [Disable?]            ║
║                                                              ║
║  ❓ UNKNOWN (Review Recommended)                             ║
║  ├── UpdateService.exe                                      ║
║  └── Helper.exe                        ⚠ Suspicious path    ║
╠══════════════════════════════════════════════════════════════╣
║  💡 Disabling high-impact items could save ~19 seconds      ║
╚══════════════════════════════════════════════════════════════╝
```

### 5.4 Module 4: Network Diagnostics (`sysmind network`)

#### 5.4.1 Quick Diagnostics
```bash
sysmind network diagnose
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║                   NETWORK DIAGNOSTICS                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🔗 CONNECTIVITY TEST                                        ║
║  ├── Local Network    ✓ Connected (192.168.1.105)           ║
║  ├── Gateway          ✓ Reachable (192.168.1.1) 2ms         ║
║  ├── DNS Resolution   ✓ Working (8.8.8.8)                   ║
║  └── Internet         ✓ Connected                           ║
║                                                              ║
║  📊 PERFORMANCE                                              ║
║  ├── Download Speed   45.2 Mbps (Testing...)                ║
║  ├── Upload Speed     12.8 Mbps                             ║
║  ├── Latency          23ms (to google.com)                  ║
║  └── Jitter           3ms                                   ║
║                                                              ║
║  🔍 ACTIVE CONNECTIONS                                       ║
║  ├── Total: 47 connections                                  ║
║  ├── chrome.exe       32 connections (normal)               ║
║  ├── Code.exe         8 connections (normal)                ║
║  └── unknown.exe      7 connections ⚠ Review                ║
║                                                              ║
║  ✓ Network health: GOOD                                     ║
╚══════════════════════════════════════════════════════════════╝
```

#### 5.4.2 Connection Monitor
```bash
sysmind network connections --live
sysmind network connections --by-process
```

#### 5.4.3 Bandwidth Monitor
```bash
sysmind network bandwidth --by-process
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║              BANDWIDTH USAGE BY PROCESS                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Process            Download      Upload        Total        ║
║  ─────────────────────────────────────────────────────────  ║
║  chrome.exe         12.4 MB/s     1.2 MB/s      13.6 MB/s   ║
║  │ └── youtube.com  11.8 MB/s     (streaming)               ║
║  │                                                           ║
║  Code.exe           245 KB/s      89 KB/s       334 KB/s    ║
║  │ └── extensions   sync                                    ║
║  │                                                           ║
║  OneDrive.exe       1.2 MB/s      3.4 MB/s      4.6 MB/s    ║
║  │ └── syncing      23 files                                ║
║                                                              ║
║  ─────────────────────────────────────────────────────────  ║
║  Total:             14.1 MB/s     4.7 MB/s      18.8 MB/s   ║
╚══════════════════════════════════════════════════════════════╝
```

### 5.5 Module 5: Intelligence Core (`sysmind intel`)

#### 5.5.1 System Health Score
```bash
sysmind status
```

**Output Example:**
```
╔══════════════════════════════════════════════════════════════╗
║               SYSTEM INTELLIGENCE REPORT                     ║
║                   Generated: 2026-01-16 14:30                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║               OVERALL HEALTH SCORE: 72/100                   ║
║               ████████████████░░░░░░░░  GOOD                ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  COMPONENT BREAKDOWN                                         ║
║  ─────────────────────────────────────────────────────────  ║
║  CPU Health         ████████████████████  95/100  Excellent ║
║  Memory Health      ██████████████░░░░░░  68/100  Fair      ║
║  Disk Health        ████████████░░░░░░░░  58/100  Warning   ║
║  Network Health     █████████████████░░░  82/100  Good      ║
║  Process Health     ██████████████████░░  78/100  Good      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  🔴 CRITICAL ISSUES (1)                                      ║
║  └── Disk space below 20% on C: drive                       ║
║                                                              ║
║  🟡 WARNINGS (3)                                             ║
║  ├── Memory usage above baseline for 2 hours                ║
║  ├── 23 startup programs detected (impacts boot by 45s)     ║
║  └── 4.7 GB duplicate files found                           ║
║                                                              ║
║  💡 RECOMMENDATIONS                                          ║
║  1. Run: sysmind disk clean --safe         (+8 GB space)    ║
║  2. Run: sysmind disk duplicates --remove  (+4.7 GB space)  ║
║  3. Run: sysmind process startup analyze                    ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  📈 TRENDS (Last 7 Days)                                     ║
║  ├── Disk usage: +2.3 GB/day (concerning)                   ║
║  ├── Average CPU: 35% → 42% (slight increase)               ║
║  └── Memory baseline: stable                                ║
╚══════════════════════════════════════════════════════════════╝
```

#### 5.5.2 Cross-Correlation Engine
```bash
sysmind intel correlate
```

**What it does:**
- Links high CPU with specific processes
- Correlates disk writes with running applications
- Associates network spikes with processes
- Identifies resource competition patterns

**Example insight:**
```
💡 CORRELATION DETECTED:
   - Every day at 14:00, CPU spikes to 80%
   - Cause: Windows Update + Antivirus scan overlap
   - Recommendation: Reschedule one task
```

#### 5.5.3 Anomaly Detection
```bash
sysmind intel anomalies --period 24h
```

**Algorithm:**
```python
def detect_anomaly(metric_values, baseline):
    mean = baseline['mean']
    std = baseline['std']
    
    for timestamp, value in metric_values:
        z_score = (value - mean) / std
        
        if abs(z_score) > 2.5:
            severity = 'critical'
        elif abs(z_score) > 2.0:
            severity = 'warning'
        elif abs(z_score) > 1.5:
            severity = 'info'
        else:
            continue
            
        yield Anomaly(timestamp, value, z_score, severity)
```

---

## 6. Technical Design

### 6.1 Database Schema

```sql
-- System snapshots (taken every 5 minutes by default)
CREATE TABLE system_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent REAL,
    memory_percent REAL,
    memory_used_bytes INTEGER,
    disk_read_bytes INTEGER,
    disk_write_bytes INTEGER,
    network_sent_bytes INTEGER,
    network_recv_bytes INTEGER
);

-- Process history
CREATE TABLE process_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER REFERENCES system_snapshots(id),
    pid INTEGER,
    name TEXT,
    cpu_percent REAL,
    memory_bytes INTEGER,
    status TEXT,
    create_time DATETIME
);

-- Baselines
CREATE TABLE baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT UNIQUE,
    mean_value REAL,
    std_deviation REAL,
    min_value REAL,
    max_value REAL,
    sample_count INTEGER,
    last_updated DATETIME
);

-- File index (for disk analysis)
CREATE TABLE file_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    size_bytes INTEGER,
    hash_sha256 TEXT,
    created_at DATETIME,
    modified_at DATETIME,
    last_scanned DATETIME,
    category TEXT
);

-- Duplicate groups
CREATE TABLE duplicate_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_sha256 TEXT,
    total_size_bytes INTEGER,
    file_count INTEGER,
    created_at DATETIME
);

CREATE TABLE duplicate_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER REFERENCES duplicate_groups(id),
    file_id INTEGER REFERENCES file_index(id),
    is_kept BOOLEAN DEFAULT FALSE
);

-- Watchdog rules
CREATE TABLE watchdog_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    process_pattern TEXT,
    condition_json TEXT,
    action TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered DATETIME
);

-- Alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    severity TEXT,
    category TEXT,
    message TEXT,
    details_json TEXT,
    acknowledged BOOLEAN DEFAULT FALSE
);

-- Quarantine manifest
CREATE TABLE quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT,
    quarantine_path TEXT,
    size_bytes INTEGER,
    reason TEXT,
    deleted_at DATETIME,
    expires_at DATETIME,
    restored BOOLEAN DEFAULT FALSE
);

-- Configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME
);

-- Create indexes for performance
CREATE INDEX idx_snapshots_timestamp ON system_snapshots(timestamp);
CREATE INDEX idx_process_history_name ON process_history(name);
CREATE INDEX idx_file_index_hash ON file_index(hash_sha256);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
```

### 6.2 Configuration System

```json
{
  "general": {
    "data_dir": "~/.sysmind",
    "log_level": "INFO",
    "color_output": true,
    "date_format": "%Y-%m-%d %H:%M:%S"
  },
  "monitor": {
    "snapshot_interval_seconds": 300,
    "history_retention_days": 30,
    "baseline_sample_hours": 48,
    "alert_thresholds": {
      "cpu_warning": 80,
      "cpu_critical": 95,
      "memory_warning": 85,
      "memory_critical": 95,
      "disk_warning": 80,
      "disk_critical": 90
    }
  },
  "disk": {
    "default_scan_paths": ["~"],
    "exclude_patterns": [
      "node_modules",
      ".git",
      "__pycache__",
      "*.pyc"
    ],
    "min_duplicate_size_mb": 1,
    "quarantine_retention_days": 30,
    "safe_clean_targets": [
      "temp_files",
      "browser_cache",
      "old_logs"
    ]
  },
  "process": {
    "refresh_interval_seconds": 5,
    "protected_processes": [
      "System",
      "smss.exe",
      "csrss.exe",
      "wininit.exe",
      "services.exe",
      "lsass.exe"
    ],
    "watchdog_check_interval_seconds": 30
  },
  "network": {
    "test_hosts": [
      "8.8.8.8",
      "1.1.1.1",
      "google.com"
    ],
    "bandwidth_sample_seconds": 1,
    "connection_refresh_seconds": 10
  }
}
```

### 6.3 Platform Abstraction Layer

```python
# platform_utils.py - Handles OS-specific operations

import platform
import os

class PlatformAdapter:
    """Abstract base for platform-specific operations"""
    
    @staticmethod
    def get_adapter():
        system = platform.system()
        if system == 'Windows':
            return WindowsAdapter()
        elif system == 'Linux':
            return LinuxAdapter()
        elif system == 'Darwin':
            return MacOSAdapter()
        raise NotImplementedError(f"Unsupported platform: {system}")
    
    def get_startup_items(self):
        raise NotImplementedError
    
    def disable_startup_item(self, name):
        raise NotImplementedError
    
    def get_system_temp_paths(self):
        raise NotImplementedError
    
    def get_browser_cache_paths(self):
        raise NotImplementedError


class WindowsAdapter(PlatformAdapter):
    """Windows-specific implementations"""
    
    def get_startup_items(self):
        # Read from Registry and Startup folders
        items = []
        
        # HKCU\Software\Microsoft\Windows\CurrentVersion\Run
        # HKLM\Software\Microsoft\Windows\CurrentVersion\Run
        # Shell:startup folder
        
        return items
    
    def get_system_temp_paths(self):
        return [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            os.path.join(os.environ.get('LOCALAPPDATA'), 'Temp'),
            os.path.join(os.environ.get('WINDIR'), 'Temp'),
        ]
    
    def get_browser_cache_paths(self):
        local_app_data = os.environ.get('LOCALAPPDATA')
        return {
            'chrome': os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
            'firefox': os.path.join(local_app_data, 'Mozilla', 'Firefox', 'Profiles'),
            'edge': os.path.join(local_app_data, 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
        }


class LinuxAdapter(PlatformAdapter):
    """Linux-specific implementations"""
    
    def get_startup_items(self):
        # Read from ~/.config/autostart, /etc/xdg/autostart, systemd user units
        pass
    
    def get_system_temp_paths(self):
        return ['/tmp', '/var/tmp', os.path.expanduser('~/.cache')]


class MacOSAdapter(PlatformAdapter):
    """macOS-specific implementations"""
    
    def get_startup_items(self):
        # Read from ~/Library/LaunchAgents, /Library/LaunchAgents
        pass
    
    def get_system_temp_paths(self):
        return ['/tmp', '/var/folders', os.path.expanduser('~/Library/Caches')]
```

---

## 7. Data Structures & Algorithms

### 7.1 Duplicate Detection Algorithm

```python
import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set, Generator
import concurrent.futures

@dataclass
class FileInfo:
    path: str
    size: int
    quick_hash: str = None
    full_hash: str = None

@dataclass
class DuplicateGroup:
    hash: str
    files: List[FileInfo]
    total_wasted_space: int
    
    @property
    def file_count(self):
        return len(self.files)
    
    def get_recommended_keep(self) -> FileInfo:
        """Return the file that should be kept (most recently accessed, in Documents, etc.)"""
        # Prioritize: Documents > Desktop > Downloads > Others
        # Then by most recent access time
        priority_paths = ['Documents', 'Desktop', 'Projects']
        
        for priority in priority_paths:
            for f in self.files:
                if priority in f.path:
                    return f
        
        # Default to most recently modified
        return max(self.files, key=lambda f: os.path.getmtime(f.path))


class DuplicateFinder:
    """
    Multi-phase duplicate file detection algorithm.
    
    Phase 1: Group by file size (O(n))
    Phase 2: Quick hash comparison - first 4KB (O(n) disk reads, minimal)
    Phase 3: Full hash for candidates (O(n) disk reads for candidates only)
    
    Time Complexity: O(n) average case, O(n²) worst case (all files same size)
    Space Complexity: O(n) for storing file info and hashes
    """
    
    QUICK_HASH_SIZE = 4096  # 4KB for quick comparison
    
    def __init__(self, min_size: int = 1024 * 1024):  # 1MB minimum
        self.min_size = min_size
        self.stats = {
            'files_scanned': 0,
            'quick_hashes_computed': 0,
            'full_hashes_computed': 0,
            'duplicates_found': 0,
        }
    
    def find_duplicates(self, paths: List[str]) -> List[DuplicateGroup]:
        """Main entry point for duplicate detection"""
        
        # Phase 1: Collect and group by size
        size_groups = self._group_by_size(paths)
        
        # Phase 2: Quick hash for same-size files
        quick_hash_groups = self._group_by_quick_hash(size_groups)
        
        # Phase 3: Full hash for candidates
        duplicate_groups = self._group_by_full_hash(quick_hash_groups)
        
        return duplicate_groups
    
    def _group_by_size(self, paths: List[str]) -> Dict[int, List[FileInfo]]:
        """Group files by size - files with unique sizes cannot be duplicates"""
        size_map = defaultdict(list)
        
        for path in paths:
            for root, _, files in os.walk(path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        if size >= self.min_size:
                            size_map[size].append(FileInfo(path=filepath, size=size))
                            self.stats['files_scanned'] += 1
                    except (OSError, PermissionError):
                        continue
        
        # Filter out unique sizes
        return {size: files for size, files in size_map.items() if len(files) > 1}
    
    def _compute_quick_hash(self, filepath: str) -> str:
        """Compute hash of first 4KB of file"""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                hasher.update(f.read(self.QUICK_HASH_SIZE))
            self.stats['quick_hashes_computed'] += 1
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None
    
    def _group_by_quick_hash(self, size_groups: Dict[int, List[FileInfo]]) -> Dict[str, List[FileInfo]]:
        """Further filter using quick hash of first 4KB"""
        quick_hash_map = defaultdict(list)
        
        for size, files in size_groups.items():
            for file_info in files:
                quick_hash = self._compute_quick_hash(file_info.path)
                if quick_hash:
                    file_info.quick_hash = quick_hash
                    # Use size + quick_hash as key for more precision
                    key = f"{size}_{quick_hash}"
                    quick_hash_map[key].append(file_info)
        
        # Filter out unique quick hashes
        return {k: v for k, v in quick_hash_map.items() if len(v) > 1}
    
    def _compute_full_hash(self, filepath: str) -> str:
        """Compute SHA-256 of entire file"""
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            self.stats['full_hashes_computed'] += 1
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None
    
    def _group_by_full_hash(self, quick_hash_groups: Dict[str, List[FileInfo]]) -> List[DuplicateGroup]:
        """Final confirmation using full file hash"""
        full_hash_map = defaultdict(list)
        
        for files in quick_hash_groups.values():
            for file_info in files:
                full_hash = self._compute_full_hash(file_info.path)
                if full_hash:
                    file_info.full_hash = full_hash
                    full_hash_map[full_hash].append(file_info)
        
        # Create duplicate groups
        groups = []
        for hash_val, files in full_hash_map.items():
            if len(files) > 1:
                wasted = sum(f.size for f in files) - files[0].size
                groups.append(DuplicateGroup(
                    hash=hash_val,
                    files=files,
                    total_wasted_space=wasted
                ))
                self.stats['duplicates_found'] += len(files) - 1
        
        return sorted(groups, key=lambda g: g.total_wasted_space, reverse=True)
```

### 7.2 Baseline & Anomaly Detection

```python
import math
import statistics
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum

class Severity(Enum):
    INFO = 1
    WARNING = 2
    CRITICAL = 3

@dataclass
class Baseline:
    metric_name: str
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    percentile_95: float
    sample_count: int
    last_updated: datetime
    
    def get_z_score(self, value: float) -> float:
        """Calculate how many standard deviations from mean"""
        if self.std_dev == 0:
            return 0
        return (value - self.mean) / self.std_dev
    
    def is_anomaly(self, value: float, threshold: float = 2.0) -> bool:
        """Check if value is anomalous (beyond threshold standard deviations)"""
        return abs(self.get_z_score(value)) > threshold

@dataclass
class Anomaly:
    timestamp: datetime
    metric_name: str
    value: float
    baseline_mean: float
    z_score: float
    severity: Severity
    
    def __str__(self):
        direction = "above" if self.value > self.baseline_mean else "below"
        return f"{self.metric_name}: {self.value:.1f} ({abs(self.z_score):.1f}σ {direction} normal)"


class BaselineComputer:
    """
    Computes statistical baselines from historical data.
    
    Uses robust statistics to handle outliers:
    - Median for central tendency
    - MAD (Median Absolute Deviation) for spread
    - Winsorization to limit outlier influence
    """
    
    def __init__(self, outlier_threshold: float = 3.0):
        self.outlier_threshold = outlier_threshold
    
    def compute_baseline(self, values: List[float], metric_name: str) -> Baseline:
        """Compute baseline statistics from a list of values"""
        if len(values) < 10:
            raise ValueError("Need at least 10 samples for reliable baseline")
        
        # Remove extreme outliers using IQR method
        cleaned_values = self._remove_outliers(values)
        
        mean = statistics.mean(cleaned_values)
        std_dev = statistics.stdev(cleaned_values) if len(cleaned_values) > 1 else 0
        
        sorted_vals = sorted(cleaned_values)
        percentile_95_idx = int(0.95 * len(sorted_vals))
        
        return Baseline(
            metric_name=metric_name,
            mean=mean,
            std_dev=std_dev,
            min_val=min(cleaned_values),
            max_val=max(cleaned_values),
            percentile_95=sorted_vals[percentile_95_idx],
            sample_count=len(values),
            last_updated=datetime.now()
        )
    
    def _remove_outliers(self, values: List[float]) -> List[float]:
        """Remove outliers using IQR method"""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return [v for v in values if lower_bound <= v <= upper_bound]


class AnomalyDetector:
    """
    Detects anomalies by comparing current values against established baselines.
    
    Severity levels:
    - INFO: 1.5σ - 2.0σ (notable but not concerning)
    - WARNING: 2.0σ - 2.5σ (requires attention)
    - CRITICAL: > 2.5σ (immediate action needed)
    """
    
    THRESHOLDS = {
        Severity.INFO: 1.5,
        Severity.WARNING: 2.0,
        Severity.CRITICAL: 2.5,
    }
    
    def __init__(self, baselines: dict):
        self.baselines = baselines  # metric_name -> Baseline
    
    def detect_anomalies(
        self, 
        metrics: List[Tuple[datetime, str, float]]
    ) -> List[Anomaly]:
        """
        Detect anomalies in a list of (timestamp, metric_name, value) tuples.
        
        Returns list of Anomaly objects sorted by severity (most severe first).
        """
        anomalies = []
        
        for timestamp, metric_name, value in metrics:
            baseline = self.baselines.get(metric_name)
            if not baseline:
                continue
            
            z_score = baseline.get_z_score(value)
            severity = self._get_severity(abs(z_score))
            
            if severity:
                anomalies.append(Anomaly(
                    timestamp=timestamp,
                    metric_name=metric_name,
                    value=value,
                    baseline_mean=baseline.mean,
                    z_score=z_score,
                    severity=severity
                ))
        
        return sorted(anomalies, key=lambda a: a.severity.value, reverse=True)
    
    def _get_severity(self, abs_z_score: float) -> Optional[Severity]:
        """Determine severity based on z-score magnitude"""
        if abs_z_score >= self.THRESHOLDS[Severity.CRITICAL]:
            return Severity.CRITICAL
        elif abs_z_score >= self.THRESHOLDS[Severity.WARNING]:
            return Severity.WARNING
        elif abs_z_score >= self.THRESHOLDS[Severity.INFO]:
            return Severity.INFO
        return None
```

### 7.3 Health Score Calculator

```python
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class HealthCategory(Enum):
    EXCELLENT = (90, 100, "🟢")
    GOOD = (70, 89, "🟡")
    FAIR = (50, 69, "🟠")
    POOR = (25, 49, "🔴")
    CRITICAL = (0, 24, "⚫")
    
    @classmethod
    def from_score(cls, score: int) -> 'HealthCategory':
        for category in cls:
            min_score, max_score, _ = category.value
            if min_score <= score <= max_score:
                return category
        return cls.CRITICAL

@dataclass
class ComponentHealth:
    name: str
    score: int
    issues: List[str]
    recommendations: List[str]
    
    @property
    def category(self) -> HealthCategory:
        return HealthCategory.from_score(self.score)

@dataclass
class SystemHealth:
    overall_score: int
    components: Dict[str, ComponentHealth]
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    @property
    def category(self) -> HealthCategory:
        return HealthCategory.from_score(self.overall_score)


class HealthScoreCalculator:
    """
    Calculates overall system health score from component metrics.
    
    Scoring methodology:
    - Each component starts at 100
    - Points deducted for issues based on severity
    - Components weighted by importance
    - Final score is weighted average
    
    Component Weights:
    - CPU: 25%
    - Memory: 25%
    - Disk: 25%
    - Network: 15%
    - Process: 10%
    """
    
    WEIGHTS = {
        'cpu': 0.25,
        'memory': 0.25,
        'disk': 0.25,
        'network': 0.15,
        'process': 0.10,
    }
    
    # Penalty points for various issues
    PENALTIES = {
        # CPU penalties
        'cpu_above_90': 30,
        'cpu_above_80': 15,
        'cpu_above_baseline': 10,
        
        # Memory penalties
        'memory_above_90': 30,
        'memory_above_80': 15,
        'memory_swap_used': 10,
        
        # Disk penalties
        'disk_above_90': 40,
        'disk_above_80': 20,
        'disk_above_70': 10,
        'duplicates_found': 5,
        'temp_files_large': 5,
        
        # Network penalties
        'network_unreachable': 50,
        'high_latency': 15,
        'packet_loss': 20,
        
        # Process penalties
        'too_many_startup': 10,
        'runaway_process': 20,
        'suspicious_process': 15,
    }
    
    def calculate(self, metrics: Dict) -> SystemHealth:
        """
        Calculate system health from metrics dictionary.
        
        Expected metrics format:
        {
            'cpu': {'usage': 45, 'baseline_deviation': 1.2, ...},
            'memory': {'usage': 72, 'swap_used': True, ...},
            'disk': {'usage': 85, 'duplicates_gb': 4.7, ...},
            'network': {'latency_ms': 23, 'packet_loss': 0, ...},
            'process': {'startup_count': 23, 'runaway_processes': [], ...}
        }
        """
        components = {}
        all_issues = []
        all_warnings = []
        all_recommendations = []
        
        # Calculate CPU health
        cpu_health = self._calculate_cpu_health(metrics.get('cpu', {}))
        components['cpu'] = cpu_health
        
        # Calculate Memory health
        memory_health = self._calculate_memory_health(metrics.get('memory', {}))
        components['memory'] = memory_health
        
        # Calculate Disk health
        disk_health = self._calculate_disk_health(metrics.get('disk', {}))
        components['disk'] = disk_health
        
        # Calculate Network health
        network_health = self._calculate_network_health(metrics.get('network', {}))
        components['network'] = network_health
        
        # Calculate Process health
        process_health = self._calculate_process_health(metrics.get('process', {}))
        components['process'] = process_health
        
        # Aggregate issues and recommendations
        for component in components.values():
            if component.score < 50:
                all_issues.extend(component.issues)
            elif component.score < 70:
                all_warnings.extend(component.issues)
            all_recommendations.extend(component.recommendations)
        
        # Calculate weighted overall score
        overall_score = sum(
            components[name].score * weight 
            for name, weight in self.WEIGHTS.items()
        )
        
        return SystemHealth(
            overall_score=int(overall_score),
            components=components,
            critical_issues=all_issues[:5],  # Top 5 critical
            warnings=all_warnings[:5],  # Top 5 warnings
            recommendations=all_recommendations[:5]  # Top 5 recommendations
        )
    
    def _calculate_cpu_health(self, metrics: Dict) -> ComponentHealth:
        score = 100
        issues = []
        recommendations = []
        
        usage = metrics.get('usage', 0)
        
        if usage > 90:
            score -= self.PENALTIES['cpu_above_90']
            issues.append(f"CPU usage critical: {usage}%")
            recommendations.append("Identify and close resource-heavy applications")
        elif usage > 80:
            score -= self.PENALTIES['cpu_above_80']
            issues.append(f"CPU usage high: {usage}%")
        
        baseline_deviation = metrics.get('baseline_deviation', 0)
        if baseline_deviation > 1.5:
            score -= self.PENALTIES['cpu_above_baseline']
            issues.append(f"CPU {baseline_deviation:.1f}x above baseline")
        
        return ComponentHealth(
            name='CPU',
            score=max(0, score),
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_memory_health(self, metrics: Dict) -> ComponentHealth:
        score = 100
        issues = []
        recommendations = []
        
        usage = metrics.get('usage', 0)
        
        if usage > 90:
            score -= self.PENALTIES['memory_above_90']
            issues.append(f"Memory usage critical: {usage}%")
            recommendations.append("Close unused applications or add more RAM")
        elif usage > 80:
            score -= self.PENALTIES['memory_above_80']
            issues.append(f"Memory usage high: {usage}%")
        
        if metrics.get('swap_used'):
            score -= self.PENALTIES['memory_swap_used']
            issues.append("System using swap memory (slow)")
            recommendations.append("Free up RAM to avoid swap usage")
        
        return ComponentHealth(
            name='Memory',
            score=max(0, score),
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_disk_health(self, metrics: Dict) -> ComponentHealth:
        score = 100
        issues = []
        recommendations = []
        
        usage = metrics.get('usage', 0)
        
        if usage > 90:
            score -= self.PENALTIES['disk_above_90']
            issues.append(f"Disk space critical: {usage}% used")
            recommendations.append("Run: sysmind disk clean --safe")
        elif usage > 80:
            score -= self.PENALTIES['disk_above_80']
            issues.append(f"Disk space low: {usage}% used")
        elif usage > 70:
            score -= self.PENALTIES['disk_above_70']
        
        duplicates_gb = metrics.get('duplicates_gb', 0)
        if duplicates_gb > 1:
            score -= self.PENALTIES['duplicates_found']
            issues.append(f"{duplicates_gb:.1f} GB of duplicate files found")
            recommendations.append("Run: sysmind disk duplicates --interactive")
        
        temp_gb = metrics.get('temp_files_gb', 0)
        if temp_gb > 2:
            score -= self.PENALTIES['temp_files_large']
            recommendations.append(f"Clear {temp_gb:.1f} GB of temp files")
        
        return ComponentHealth(
            name='Disk',
            score=max(0, score),
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_network_health(self, metrics: Dict) -> ComponentHealth:
        score = 100
        issues = []
        recommendations = []
        
        if not metrics.get('connected', True):
            score -= self.PENALTIES['network_unreachable']
            issues.append("No network connectivity")
            return ComponentHealth('Network', 0, issues, ["Check network connection"])
        
        latency = metrics.get('latency_ms', 0)
        if latency > 100:
            score -= self.PENALTIES['high_latency']
            issues.append(f"High network latency: {latency}ms")
        
        packet_loss = metrics.get('packet_loss', 0)
        if packet_loss > 5:
            score -= self.PENALTIES['packet_loss']
            issues.append(f"Packet loss detected: {packet_loss}%")
        
        return ComponentHealth(
            name='Network',
            score=max(0, score),
            issues=issues,
            recommendations=recommendations
        )
    
    def _calculate_process_health(self, metrics: Dict) -> ComponentHealth:
        score = 100
        issues = []
        recommendations = []
        
        startup_count = metrics.get('startup_count', 0)
        if startup_count > 15:
            score -= self.PENALTIES['too_many_startup']
            issues.append(f"{startup_count} startup programs detected")
            recommendations.append("Run: sysmind process startup analyze")
        
        runaway = metrics.get('runaway_processes', [])
        if runaway:
            score -= self.PENALTIES['runaway_process'] * len(runaway)
            for proc in runaway[:3]:
                issues.append(f"Runaway process: {proc}")
        
        return ComponentHealth(
            name='Process',
            score=max(0, score),
            issues=issues,
            recommendations=recommendations
        )
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 1.1 | Project setup, CLI framework | P0 | Low |
| 1.2 | Configuration system | P0 | Low |
| 1.3 | Database initialization | P0 | Medium |
| 1.4 | Logging infrastructure | P0 | Low |
| 1.5 | Platform detection & abstraction | P0 | Medium |

**Deliverables:**
- Working CLI skeleton with help system
- Configuration file handling
- SQLite database creation and migration
- Cross-platform utility functions

### Phase 2: Monitor Module (Week 3-4)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 2.1 | CPU/Memory/Disk metrics collection | P0 | Medium |
| 2.2 | Real-time display (curses/rich) | P1 | High |
| 2.3 | Historical data storage | P0 | Medium |
| 2.4 | Baseline computation | P1 | Medium |
| 2.5 | Anomaly detection | P2 | High |

**Deliverables:**
- `sysmind monitor live` command
- `sysmind monitor history` command
- `sysmind monitor baseline` command
- Automatic data collection daemon option

### Phase 3: Disk Module (Week 5-6)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 3.1 | Directory traversal & size calculation | P0 | Medium |
| 3.2 | Duplicate detection algorithm | P0 | High |
| 3.3 | File categorization | P1 | Medium |
| 3.4 | Safe cleanup with quarantine | P1 | High |
| 3.5 | Tree visualization | P2 | Medium |

**Deliverables:**
- `sysmind disk analyze` command
- `sysmind disk duplicates` command
- `sysmind disk clean` command
- Quarantine and restore system

### Phase 4: Process Module (Week 7-8)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 4.1 | Process listing with details | P0 | Medium |
| 4.2 | Process profiling | P1 | Medium |
| 4.3 | Watchdog rule engine | P1 | High |
| 4.4 | Startup program management | P1 | High |
| 4.5 | Process termination with safety | P2 | Medium |

**Deliverables:**
- `sysmind process list` command
- `sysmind process profile` command
- `sysmind process watch` commands
- `sysmind process startup` commands

### Phase 5: Network Module (Week 9)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 5.1 | Connectivity diagnostics | P0 | Medium |
| 5.2 | Active connections listing | P1 | Medium |
| 5.3 | Bandwidth monitoring | P2 | High |
| 5.4 | Speed testing | P2 | Medium |

**Deliverables:**
- `sysmind network diagnose` command
- `sysmind network connections` command
- `sysmind network bandwidth` command

### Phase 6: Intelligence Core (Week 10-11)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 6.1 | Health score calculator | P0 | Medium |
| 6.2 | Cross-component correlation | P1 | High |
| 6.3 | Recommendation engine | P1 | High |
| 6.4 | Automated scheduler | P2 | High |

**Deliverables:**
- `sysmind status` command
- `sysmind intel correlate` command
- `sysmind intel anomalies` command

### Phase 7: Polish & Testing (Week 12)

| Task | Description | Priority | Complexity |
|------|-------------|----------|------------|
| 7.1 | Unit tests for all modules | P0 | Medium |
| 7.2 | Integration tests | P1 | Medium |
| 7.3 | Documentation | P1 | Low |
| 7.4 | Performance optimization | P2 | Medium |
| 7.5 | Error message improvements | P1 | Low |

**Deliverables:**
- Test coverage > 80%
- README with examples
- Performance benchmarks
- Polished error handling

---

## 9. Error Handling Strategy

### 9.1 Error Hierarchy

```python
class SysmindError(Exception):
    """Base exception for all sysmind errors"""
    
    def __init__(self, message: str, code: str = None, suggestions: list = None):
        super().__init__(message)
        self.code = code
        self.suggestions = suggestions or []
    
    def to_user_message(self) -> str:
        msg = f"❌ Error: {str(self)}"
        if self.suggestions:
            msg += "\n\n💡 Suggestions:"
            for s in self.suggestions:
                msg += f"\n   • {s}"
        return msg


class ConfigurationError(SysmindError):
    """Configuration file errors"""
    pass


class PermissionError(SysmindError):
    """Insufficient permissions"""
    pass


class ResourceNotFoundError(SysmindError):
    """Requested resource (file, process, etc.) not found"""
    pass


class DatabaseError(SysmindError):
    """Database operation errors"""
    pass


class NetworkError(SysmindError):
    """Network connectivity errors"""
    pass


class ValidationError(SysmindError):
    """Input validation errors"""
    pass
```

### 9.2 Error Handling Patterns

```python
from functools import wraps
import logging

logger = logging.getLogger('sysmind')


def handle_errors(func):
    """Decorator for consistent error handling in CLI commands"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SysmindError as e:
            logger.error(f"{e.code}: {str(e)}")
            print(e.to_user_message())
            return 1
        except PermissionError as e:
            error = SysmindError(
                f"Permission denied: {e}",
                code="PERMISSION_DENIED",
                suggestions=[
                    "Try running with administrator/sudo privileges",
                    "Check file/folder permissions"
                ]
            )
            print(error.to_user_message())
            return 1
        except KeyboardInterrupt:
            print("\n⚠ Operation cancelled by user")
            return 130
        except Exception as e:
            logger.exception("Unexpected error")
            print(f"❌ Unexpected error: {e}")
            print("\n💡 This might be a bug. Please report at: github.com/user/sysmind/issues")
            return 1
    return wrapper


# Usage in commands
@handle_errors
def cmd_disk_analyze(path: str):
    if not os.path.exists(path):
        raise ResourceNotFoundError(
            f"Path not found: {path}",
            code="PATH_NOT_FOUND",
            suggestions=[
                "Check if the path is correct",
                "Use absolute path instead of relative",
                f"Try: sysmind disk analyze {os.path.expanduser('~')}"
            ]
        )
    # ... rest of implementation
```

### 9.3 Graceful Degradation

```python
class GracefulDegrader:
    """
    Handles partial failures gracefully.
    Instead of crashing, continues with available data and warns user.
    """
    
    def __init__(self):
        self.warnings = []
        self.errors = []
    
    def try_collect(self, collector_name: str, func, *args, **kwargs):
        """
        Try to collect data, continue gracefully on failure.
        
        Returns: (success: bool, data: Any)
        """
        try:
            data = func(*args, **kwargs)
            return True, data
        except PermissionError as e:
            self.warnings.append(f"{collector_name}: Permission denied (skipped)")
            return False, None
        except Exception as e:
            self.warnings.append(f"{collector_name}: {str(e)} (skipped)")
            logger.warning(f"Collector {collector_name} failed: {e}")
            return False, None
    
    def get_summary(self) -> str:
        if not self.warnings:
            return ""
        
        summary = "\n⚠ Some data collection failed:\n"
        for warning in self.warnings:
            summary += f"  • {warning}\n"
        return summary


# Usage example
def collect_system_metrics():
    degrader = GracefulDegrader()
    metrics = {}
    
    success, cpu_data = degrader.try_collect("CPU metrics", get_cpu_metrics)
    if success:
        metrics['cpu'] = cpu_data
    
    success, memory_data = degrader.try_collect("Memory metrics", get_memory_metrics)
    if success:
        metrics['memory'] = memory_data
    
    success, disk_data = degrader.try_collect("Disk metrics", get_disk_metrics)
    if success:
        metrics['disk'] = disk_data
    
    # Print partial results with warnings
    print(format_metrics(metrics))
    print(degrader.get_summary())
```

---

## 10. Testing Strategy

### 10.1 Test Categories

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_formatters.py
│   ├── test_validators.py
│   ├── test_duplicate_finder.py
│   ├── test_baseline_computer.py
│   ├── test_health_calculator.py
│   └── test_anomaly_detector.py
│
├── integration/             # Tests with real system calls
│   ├── test_monitor_integration.py
│   ├── test_disk_integration.py
│   ├── test_process_integration.py
│   └── test_network_integration.py
│
├── mocks/                   # Mock data and helpers
│   ├── mock_filesystem.py
│   ├── mock_processes.py
│   └── fixtures.py
│
└── performance/             # Performance benchmarks
    ├── bench_duplicate_finder.py
    └── bench_disk_scanner.py
```

### 10.2 Unit Test Examples

```python
# tests/unit/test_duplicate_finder.py
import pytest
import tempfile
import os
from sysmind.modules.disk.duplicates import DuplicateFinder, DuplicateGroup

class TestDuplicateFinder:
    
    @pytest.fixture
    def temp_dir_with_duplicates(self):
        """Create a temporary directory with known duplicate files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create duplicate files
            content = b"x" * 1024 * 1024  # 1MB of 'x'
            
            # Original
            with open(os.path.join(tmpdir, "original.bin"), "wb") as f:
                f.write(content)
            
            # Duplicate 1
            with open(os.path.join(tmpdir, "duplicate1.bin"), "wb") as f:
                f.write(content)
            
            # Duplicate 2 (in subfolder)
            os.makedirs(os.path.join(tmpdir, "subfolder"))
            with open(os.path.join(tmpdir, "subfolder", "duplicate2.bin"), "wb") as f:
                f.write(content)
            
            # Unique file
            with open(os.path.join(tmpdir, "unique.bin"), "wb") as f:
                f.write(b"y" * 1024 * 1024)
            
            yield tmpdir
    
    def test_finds_exact_duplicates(self, temp_dir_with_duplicates):
        finder = DuplicateFinder(min_size=1024)  # 1KB minimum
        groups = finder.find_duplicates([temp_dir_with_duplicates])
        
        assert len(groups) == 1  # One group of duplicates
        assert groups[0].file_count == 3  # Three identical files
    
    def test_calculates_wasted_space(self, temp_dir_with_duplicates):
        finder = DuplicateFinder(min_size=1024)
        groups = finder.find_duplicates([temp_dir_with_duplicates])
        
        # 3 files of 1MB each, wasted = 2MB (keeping one)
        assert groups[0].total_wasted_space == 2 * 1024 * 1024
    
    def test_respects_minimum_size(self):
        finder = DuplicateFinder(min_size=10 * 1024 * 1024)  # 10MB minimum
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create small duplicate files (should be ignored)
            for i in range(3):
                with open(os.path.join(tmpdir, f"small{i}.txt"), "w") as f:
                    f.write("small content")
            
            groups = finder.find_duplicates([tmpdir])
            assert len(groups) == 0  # No duplicates found (below size threshold)
    
    def test_different_content_not_duplicates(self):
        finder = DuplicateFinder(min_size=1024)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Files with same size but different content
            for i in range(3):
                with open(os.path.join(tmpdir, f"file{i}.bin"), "wb") as f:
                    f.write(bytes([i]) * 1024 * 1024)  # 1MB each, different content
            
            groups = finder.find_duplicates([tmpdir])
            assert len(groups) == 0  # No duplicates


# tests/unit/test_health_calculator.py
import pytest
from sysmind.modules.intelligence.health import HealthScoreCalculator, HealthCategory

class TestHealthScoreCalculator:
    
    @pytest.fixture
    def calculator(self):
        return HealthScoreCalculator()
    
    def test_healthy_system_high_score(self, calculator):
        metrics = {
            'cpu': {'usage': 30},
            'memory': {'usage': 50},
            'disk': {'usage': 40},
            'network': {'connected': True, 'latency_ms': 20},
            'process': {'startup_count': 10}
        }
        
        health = calculator.calculate(metrics)
        assert health.overall_score >= 80
        assert health.category == HealthCategory.EXCELLENT or health.category == HealthCategory.GOOD
    
    def test_critical_disk_lowers_score(self, calculator):
        metrics = {
            'cpu': {'usage': 30},
            'memory': {'usage': 50},
            'disk': {'usage': 95},  # Critical
            'network': {'connected': True},
            'process': {}
        }
        
        health = calculator.calculate(metrics)
        assert health.overall_score < 80
        assert len(health.critical_issues) > 0
        assert any('Disk' in issue or 'disk' in issue for issue in health.critical_issues)
    
    def test_multiple_issues_compound(self, calculator):
        metrics = {
            'cpu': {'usage': 85},
            'memory': {'usage': 90},
            'disk': {'usage': 85},
            'network': {'connected': False},
            'process': {'startup_count': 25, 'runaway_processes': ['chrome.exe']}
        }
        
        health = calculator.calculate(metrics)
        assert health.overall_score < 50  # Poor or Critical
        assert len(health.critical_issues) > 2
```

### 10.3 Integration Test Examples

```python
# tests/integration/test_monitor_integration.py
import pytest
import time
from sysmind.modules.monitor.cpu import get_cpu_usage
from sysmind.modules.monitor.memory import get_memory_usage
from sysmind.modules.monitor.realtime import SystemMonitor

class TestMonitorIntegration:
    
    def test_cpu_usage_in_valid_range(self):
        """CPU usage should be between 0 and 100"""
        usage = get_cpu_usage()
        assert 0 <= usage <= 100
    
    def test_memory_usage_returns_valid_data(self):
        """Memory usage should return dict with expected keys"""
        memory = get_memory_usage()
        
        assert 'percent' in memory
        assert 'total' in memory
        assert 'used' in memory
        assert 'available' in memory
        
        assert 0 <= memory['percent'] <= 100
        assert memory['total'] > 0
        assert memory['used'] >= 0
    
    def test_monitor_collects_samples_over_time(self):
        """Monitor should collect multiple samples"""
        monitor = SystemMonitor(interval_seconds=0.5)
        
        samples = []
        for _ in range(5):
            sample = monitor.collect_sample()
            samples.append(sample)
            time.sleep(0.5)
        
        assert len(samples) == 5
        assert all('timestamp' in s for s in samples)
        assert all('cpu' in s for s in samples)
        assert all('memory' in s for s in samples)
```

### 10.4 Mock Helpers

```python
# tests/mocks/mock_filesystem.py
import os
import tempfile
from contextlib import contextmanager

@contextmanager
def mock_filesystem(structure: dict):
    """
    Create a temporary filesystem with specified structure.
    
    Usage:
        structure = {
            'file1.txt': 'content1',
            'folder1': {
                'file2.txt': 'content2',
            },
            'large_file.bin': b'x' * 1024 * 1024,  # Binary content
        }
        
        with mock_filesystem(structure) as root:
            # root is the path to temp directory
            # All files are created automatically
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        _create_structure(tmpdir, structure)
        yield tmpdir


def _create_structure(base_path: str, structure: dict):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            _create_structure(path, content)
        elif isinstance(content, bytes):
            with open(path, 'wb') as f:
                f.write(content)
        else:
            with open(path, 'w') as f:
                f.write(str(content))
```

---

## 11. CLI Interface Design

### 11.1 Command Structure

```
sysmind <module> <command> [options] [arguments]

MODULES:
  monitor     System resource monitoring
  disk        Disk space analysis and cleanup
  process     Process management
  network     Network diagnostics
  intel       Intelligence and insights
  config      Configuration management

GLOBAL OPTIONS:
  --help, -h     Show help for any command
  --version, -v  Show version information
  --json         Output in JSON format
  --quiet, -q    Suppress non-essential output
  --verbose      Show detailed output
  --no-color     Disable colored output
```

### 11.2 Complete Command Reference

```bash
# ═══════════════════════════════════════════════════════════════
# MONITOR MODULE
# ═══════════════════════════════════════════════════════════════

# Real-time monitoring dashboard
sysmind monitor live
sysmind monitor live --refresh 2  # Custom refresh rate (seconds)

# View historical data
sysmind monitor history
sysmind monitor history --period 7d  # Last 7 days
sysmind monitor history --period 24h --metric cpu  # Specific metric

# Baseline management
sysmind monitor baseline --establish  # Create baseline (48h sampling)
sysmind monitor baseline --show       # Display current baselines
sysmind monitor baseline --compare    # Compare current vs baseline
sysmind monitor baseline --reset      # Reset and re-establish

# Single snapshot
sysmind monitor snapshot
sysmind monitor snapshot --save       # Save to database

# ═══════════════════════════════════════════════════════════════
# DISK MODULE
# ═══════════════════════════════════════════════════════════════

# Analyze disk usage
sysmind disk analyze
sysmind disk analyze ~/Downloads
sysmind disk analyze --depth 3  # Limit directory depth
sysmind disk analyze --min-size 100MB  # Only show items > 100MB

# Find duplicates
sysmind disk duplicates
sysmind disk duplicates ~/Documents
sysmind disk duplicates --min-size 1MB
sysmind disk duplicates --interactive  # Review each group
sysmind disk duplicates --remove safe  # Auto-remove (keeps best copy)
sysmind disk duplicates --report       # Export to CSV

# Cleanup
sysmind disk clean --safe       # Temp files, caches only
sysmind disk clean --moderate   # + old downloads, duplicates
sysmind disk clean --aggressive # + large unused files
sysmind disk clean --dry-run    # Preview without deleting

# Quarantine management
sysmind disk quarantine list
sysmind disk quarantine restore <id>
sysmind disk quarantine restore --all
sysmind disk quarantine purge   # Permanently delete

# File search
sysmind disk find --large       # Files > 100MB
sysmind disk find --old 90d     # Not accessed in 90 days
sysmind disk find --type video  # By file type

# ═══════════════════════════════════════════════════════════════
# PROCESS MODULE
# ═══════════════════════════════════════════════════════════════

# List processes
sysmind process list
sysmind process list --sort cpu    # Sort by CPU usage
sysmind process list --sort memory # Sort by memory
sysmind process list --filter "*chrome*"  # Filter by name

# Process details
sysmind process info <pid>
sysmind process info <name>

# Process profiling
sysmind process profile chrome.exe
sysmind process profile chrome.exe --duration 60  # 60 seconds
sysmind process profile --pid 1234

# Watchdog rules
sysmind process watch add --name "chrome.exe" --cpu-max 50 --action alert
sysmind process watch add --memory-max 2GB --action log
sysmind process watch list
sysmind process watch remove <id>
sysmind process watch run          # Start watchdog (foreground)
sysmind process watch run --daemon # Start watchdog (background)
sysmind process watch stop         # Stop watchdog daemon

# Startup management
sysmind process startup list
sysmind process startup analyze    # Get recommendations
sysmind process startup enable <name>
sysmind process startup disable <name>

# Process control (with confirmation)
sysmind process kill <pid>
sysmind process kill <name> --force

# ═══════════════════════════════════════════════════════════════
# NETWORK MODULE
# ═══════════════════════════════════════════════════════════════

# Quick diagnostics
sysmind network diagnose
sysmind network diagnose --full  # Include speed test

# Connectivity tests
sysmind network ping google.com
sysmind network ping 8.8.8.8 --count 10
sysmind network trace google.com  # Traceroute

# Connection monitoring
sysmind network connections
sysmind network connections --by-process
sysmind network connections --live  # Real-time updates

# Bandwidth monitoring
sysmind network bandwidth
sysmind network bandwidth --by-process
sysmind network bandwidth --live

# Speed test
sysmind network speed

# ═══════════════════════════════════════════════════════════════
# INTELLIGENCE MODULE
# ═══════════════════════════════════════════════════════════════

# Overall status (main command)
sysmind status
sysmind status --detailed

# Anomaly detection
sysmind intel anomalies
sysmind intel anomalies --period 24h
sysmind intel anomalies --severity critical

# Correlation analysis
sysmind intel correlate
sysmind intel correlate --period 7d

# Trends
sysmind intel trends
sysmind intel trends --metric cpu --period 30d

# Alerts
sysmind intel alerts
sysmind intel alerts --acknowledge <id>
sysmind intel alerts --acknowledge-all

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

sysmind config show
sysmind config set monitor.snapshot_interval_seconds 600
sysmind config reset
sysmind config path  # Show config file location

# ═══════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════

sysmind --version
sysmind --help
sysmind <module> --help
sysmind doctor  # System self-check
```

### 11.3 Output Formatting

```python
# utils/formatters.py
from enum import Enum
from typing import List, Dict, Any
import json

class OutputFormat(Enum):
    TABLE = "table"
    JSON = "json"
    PLAIN = "plain"

class Formatter:
    """Unified output formatting for all commands"""
    
    def __init__(self, format: OutputFormat = OutputFormat.TABLE, color: bool = True):
        self.format = format
        self.color = color
    
    def table(self, headers: List[str], rows: List[List[Any]], title: str = None) -> str:
        """Format data as an ASCII table"""
        if self.format == OutputFormat.JSON:
            return self._to_json(headers, rows)
        
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        
        # Build table
        lines = []
        
        # Top border
        border = "╔" + "╤".join("═" * (w + 2) for w in widths) + "╗"
        lines.append(border)
        
        # Title
        if title:
            title_line = "║" + title.center(sum(widths) + 3 * len(widths) - 1) + "║"
            lines.append(title_line)
            lines.append("╠" + "╪".join("═" * (w + 2) for w in widths) + "╣")
        
        # Headers
        header_line = "║" + "│".join(f" {h.center(widths[i])} " for i, h in enumerate(headers)) + "║"
        lines.append(header_line)
        lines.append("╠" + "╪".join("═" * (w + 2) for w in widths) + "╣")
        
        # Rows
        for row in rows:
            row_line = "║" + "│".join(f" {str(c).ljust(widths[i])} " for i, c in enumerate(row)) + "║"
            lines.append(row_line)
        
        # Bottom border
        lines.append("╚" + "╧".join("═" * (w + 2) for w in widths) + "╝")
        
        return "\n".join(lines)
    
    def progress_bar(self, value: float, max_value: float = 100, width: int = 20, 
                     label: str = "", show_percent: bool = True) -> str:
        """Render a progress bar"""
        percent = (value / max_value) * 100
        filled = int(width * value / max_value)
        empty = width - filled
        
        # Color based on value
        if self.color:
            if percent >= 90:
                color = "\033[91m"  # Red
            elif percent >= 70:
                color = "\033[93m"  # Yellow
            else:
                color = "\033[92m"  # Green
            reset = "\033[0m"
        else:
            color = reset = ""
        
        bar = f"{color}{'█' * filled}{'░' * empty}{reset}"
        
        if show_percent:
            return f"{label:20} {bar} {percent:5.1f}%"
        return f"{label:20} {bar}"
    
    def health_indicator(self, score: int) -> str:
        """Render health score with emoji indicator"""
        if score >= 90:
            return f"🟢 {score}/100 Excellent"
        elif score >= 70:
            return f"🟡 {score}/100 Good"
        elif score >= 50:
            return f"🟠 {score}/100 Fair"
        elif score >= 25:
            return f"🔴 {score}/100 Poor"
        else:
            return f"⚫ {score}/100 Critical"
    
    def _to_json(self, headers: List[str], rows: List[List[Any]]) -> str:
        """Convert table data to JSON"""
        data = [dict(zip(headers, row)) for row in rows]
        return json.dumps(data, indent=2, default=str)
```

---

## 12. Advanced Features

### 12.1 Scheduler & Automation

```python
# modules/intelligence/scheduler.py
import schedule
import time
import threading
from datetime import datetime
from typing import Callable, Dict, List

class Task:
    def __init__(self, name: str, func: Callable, schedule_expr: str):
        self.name = name
        self.func = func
        self.schedule_expr = schedule_expr
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.enabled = True

class AutomationScheduler:
    """
    Schedules automated maintenance tasks.
    
    Built-in tasks:
    - Hourly system snapshot
    - Daily disk scan
    - Weekly duplicate check
    - On-demand cleanup
    """
    
    DEFAULT_TASKS = {
        'system_snapshot': {
            'schedule': 'every 1 hour',
            'description': 'Collect system metrics'
        },
        'disk_scan': {
            'schedule': 'every day at 03:00',
            'description': 'Scan for large/old files'
        },
        'duplicate_check': {
            'schedule': 'every sunday at 04:00',
            'description': 'Scan for duplicate files'
        },
        'baseline_update': {
            'schedule': 'every week',
            'description': 'Update baseline statistics'
        }
    }
    
    def __init__(self, database):
        self.db = database
        self.tasks: Dict[str, Task] = {}
        self._running = False
        self._thread = None
    
    def register_task(self, name: str, func: Callable, schedule_expr: str):
        """Register a new scheduled task"""
        task = Task(name, func, schedule_expr)
        self.tasks[name] = task
        
        # Parse schedule expression and register with schedule library
        self._parse_and_register(task)
    
    def _parse_and_register(self, task: Task):
        """Parse schedule expression like 'every 1 hour' or 'every day at 03:00'"""
        expr = task.schedule_expr.lower()
        
        if 'every' in expr:
            if 'hour' in expr:
                schedule.every().hour.do(self._run_task, task)
            elif 'day' in expr:
                if 'at' in expr:
                    time_str = expr.split('at')[1].strip()
                    schedule.every().day.at(time_str).do(self._run_task, task)
                else:
                    schedule.every().day.do(self._run_task, task)
            elif 'week' in expr:
                schedule.every().week.do(self._run_task, task)
            elif 'sunday' in expr:
                time_str = expr.split('at')[1].strip() if 'at' in expr else "00:00"
                schedule.every().sunday.at(time_str).do(self._run_task, task)
    
    def _run_task(self, task: Task):
        """Execute a scheduled task"""
        if not task.enabled:
            return
        
        try:
            task.func()
            task.last_run = datetime.now()
            task.run_count += 1
            self.db.log_task_execution(task.name, 'success')
        except Exception as e:
            self.db.log_task_execution(task.name, 'error', str(e))
    
    def start_daemon(self):
        """Start the scheduler in background thread"""
        self._running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._thread.start()
    
    def _daemon_loop(self):
        """Main daemon loop"""
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_daemon(self):
        """Stop the scheduler daemon"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
```

### 12.2 Plugin System (Future)

```python
# Future extensibility through plugins
class PluginInterface:
    """Base interface for sysmind plugins"""
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def version(self) -> str:
        raise NotImplementedError
    
    def get_commands(self) -> List[dict]:
        """Return list of commands this plugin provides"""
        raise NotImplementedError
    
    def get_collectors(self) -> List[Callable]:
        """Return list of metric collectors"""
        return []
    
    def get_analyzers(self) -> List[Callable]:
        """Return list of analyzers"""
        return []


# Example plugin
class DockerPlugin(PluginInterface):
    name = "docker"
    version = "1.0.0"
    
    def get_commands(self):
        return [
            {'name': 'docker list', 'func': self.list_containers},
            {'name': 'docker stats', 'func': self.container_stats},
        ]
    
    def get_collectors(self):
        return [self.collect_docker_metrics]
```

### 12.3 Export & Reporting

```python
# modules/reporting/exporter.py
import csv
import json
from datetime import datetime
from typing import Dict, List, Any

class ReportExporter:
    """Export system reports in various formats"""
    
    def export_health_report(self, health_data: Dict, format: str = 'html') -> str:
        """Export health report"""
        if format == 'html':
            return self._to_html(health_data)
        elif format == 'json':
            return json.dumps(health_data, indent=2, default=str)
        elif format == 'csv':
            return self._to_csv(health_data)
        elif format == 'markdown':
            return self._to_markdown(health_data)
    
    def _to_html(self, data: Dict) -> str:
        """Generate HTML report"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>SYSMIND Health Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .score {{ font-size: 48px; text-align: center; }}
        .excellent {{ color: green; }}
        .good {{ color: #90EE90; }}
        .fair {{ color: orange; }}
        .poor {{ color: red; }}
        .component {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .progress {{ background: #eee; height: 20px; border-radius: 10px; }}
        .progress-bar {{ height: 100%; border-radius: 10px; }}
    </style>
</head>
<body>
    <h1>System Health Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="score {self._get_class(data['overall_score'])}">
        {data['overall_score']}/100
    </div>
    
    <h2>Components</h2>
    {''.join(self._component_html(c) for c in data['components'].values())}
    
    <h2>Issues</h2>
    <ul>
        {''.join(f'<li>{issue}</li>' for issue in data['critical_issues'])}
    </ul>
    
    <h2>Recommendations</h2>
    <ul>
        {''.join(f'<li>{rec}</li>' for rec in data['recommendations'])}
    </ul>
</body>
</html>
        """
    
    def _get_class(self, score: int) -> str:
        if score >= 90: return 'excellent'
        if score >= 70: return 'good'
        if score >= 50: return 'fair'
        return 'poor'
    
    def _component_html(self, component) -> str:
        return f"""
        <div class="component">
            <h3>{component.name}: {component.score}/100</h3>
            <div class="progress">
                <div class="progress-bar {self._get_class(component.score)}" 
                     style="width: {component.score}%"></div>
            </div>
        </div>
        """
    
    def _to_markdown(self, data: Dict) -> str:
        """Generate Markdown report"""
        md = f"""# System Health Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Score: {data['overall_score']}/100

## Components

| Component | Score | Status |
|-----------|-------|--------|
"""
        for name, comp in data['components'].items():
            md += f"| {name} | {comp.score}/100 | {comp.category.name} |\n"
        
        md += "\n## Critical Issues\n\n"
        for issue in data['critical_issues']:
            md += f"- ❌ {issue}\n"
        
        md += "\n## Recommendations\n\n"
        for rec in data['recommendations']:
            md += f"- 💡 {rec}\n"
        
        return md
```

---

## 13. Code Organization

### 13.1 Entry Point

```python
#!/usr/bin/env python3
# sysmind/cli.py
"""
SYSMIND - System Intelligence & Automation CLI

Main entry point for the command-line interface.
"""

import argparse
import sys
from typing import Optional

from sysmind import __version__
from sysmind.core.config import Config
from sysmind.core.database import Database
from sysmind.utils.logger import setup_logging
from sysmind.commands import (
    monitor_commands,
    disk_commands,
    process_commands,
    network_commands,
    intel_commands,
    config_commands,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands"""
    
    parser = argparse.ArgumentParser(
        prog='sysmind',
        description='System Intelligence & Automation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sysmind status                    Show system health overview
  sysmind monitor live              Real-time system monitoring
  sysmind disk analyze ~/Downloads  Analyze disk usage
  sysmind process list --sort cpu   List processes by CPU usage
  sysmind network diagnose          Network diagnostics

For more information on a specific command:
  sysmind <command> --help
        """
    )
    
    # Global options
    parser.add_argument('--version', '-v', action='version', version=f'sysmind {__version__}')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress non-essential output')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    parser.add_argument('--config', type=str, help='Path to config file')
    
    # Create subparsers for modules
    subparsers = parser.add_subparsers(dest='module', help='Available modules')
    
    # Add module subparsers
    monitor_commands.add_subparser(subparsers)
    disk_commands.add_subparser(subparsers)
    process_commands.add_subparser(subparsers)
    network_commands.add_subparser(subparsers)
    intel_commands.add_subparser(subparsers)
    config_commands.add_subparser(subparsers)
    
    # Add 'status' as a top-level command (shortcut for 'intel status')
    status_parser = subparsers.add_parser('status', help='Show system health overview')
    status_parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    status_parser.set_defaults(func=intel_commands.cmd_status)
    
    # Add 'doctor' command
    doctor_parser = subparsers.add_parser('doctor', help='Self-diagnostics for sysmind')
    doctor_parser.set_defaults(func=cmd_doctor)
    
    return parser


def cmd_doctor(args, config, db):
    """Run self-diagnostics"""
    from sysmind.utils.doctor import run_diagnostics
    return run_diagnostics()


def main(argv: Optional[list] = None) -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else ('WARNING' if args.quiet else 'INFO')
    setup_logging(level=log_level)
    
    # Load configuration
    config_path = args.config if hasattr(args, 'config') else None
    config = Config.load(config_path)
    
    # Initialize database
    db = Database(config.data_dir)
    
    # Handle no command
    if not args.module:
        parser.print_help()
        return 0
    
    # Execute command
    if hasattr(args, 'func'):
        return args.func(args, config, db)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
```

### 13.2 Module Command Example

```python
# sysmind/commands/disk_commands.py
"""Disk module commands"""

import argparse
import os
from sysmind.modules.disk.analyzer import DiskAnalyzer
from sysmind.modules.disk.duplicates import DuplicateFinder
from sysmind.modules.disk.cleaner import DiskCleaner
from sysmind.utils.formatters import Formatter
from sysmind.core.errors import handle_errors, ResourceNotFoundError


def add_subparser(subparsers):
    """Add disk subparser and its commands"""
    
    disk_parser = subparsers.add_parser('disk', help='Disk space analysis and cleanup')
    disk_subparsers = disk_parser.add_subparsers(dest='command')
    
    # analyze command
    analyze_parser = disk_subparsers.add_parser('analyze', help='Analyze disk usage')
    analyze_parser.add_argument('path', nargs='?', default=os.path.expanduser('~'),
                                help='Path to analyze (default: home directory)')
    analyze_parser.add_argument('--depth', type=int, default=4, help='Maximum depth')
    analyze_parser.add_argument('--min-size', type=str, default='1MB',
                                help='Minimum size to show (e.g., 1MB, 100KB)')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # duplicates command
    dup_parser = disk_subparsers.add_parser('duplicates', help='Find duplicate files')
    dup_parser.add_argument('path', nargs='?', default=os.path.expanduser('~'))
    dup_parser.add_argument('--min-size', type=str, default='1MB')
    dup_parser.add_argument('--interactive', '-i', action='store_true')
    dup_parser.add_argument('--remove', choices=['safe', 'all'])
    dup_parser.add_argument('--report', action='store_true', help='Export to CSV')
    dup_parser.set_defaults(func=cmd_duplicates)
    
    # clean command
    clean_parser = disk_subparsers.add_parser('clean', help='Clean up disk space')
    clean_parser.add_argument('--safe', action='store_true', default=True)
    clean_parser.add_argument('--moderate', action='store_true')
    clean_parser.add_argument('--aggressive', action='store_true')
    clean_parser.add_argument('--dry-run', action='store_true',
                              help='Preview without deleting')
    clean_parser.set_defaults(func=cmd_clean)
    
    # quarantine command
    quarantine_parser = disk_subparsers.add_parser('quarantine', help='Manage quarantine')
    quarantine_subparsers = quarantine_parser.add_subparsers(dest='quarantine_cmd')
    
    quarantine_subparsers.add_parser('list', help='List quarantined items')
    
    restore_parser = quarantine_subparsers.add_parser('restore', help='Restore items')
    restore_parser.add_argument('id', nargs='?', help='Item ID to restore')
    restore_parser.add_argument('--all', action='store_true')
    
    quarantine_subparsers.add_parser('purge', help='Permanently delete quarantined items')
    
    quarantine_parser.set_defaults(func=cmd_quarantine)


@handle_errors
def cmd_analyze(args, config, db):
    """Execute disk analyze command"""
    path = os.path.abspath(os.path.expanduser(args.path))
    
    if not os.path.exists(path):
        raise ResourceNotFoundError(
            f"Path not found: {path}",
            suggestions=["Check if the path is correct", "Use an absolute path"]
        )
    
    formatter = Formatter(color=not args.no_color)
    analyzer = DiskAnalyzer(config)
    
    print(f"Analyzing: {path}")
    print("This may take a while for large directories...\n")
    
    result = analyzer.analyze(path, max_depth=args.depth)
    
    # Display results
    print(formatter.disk_usage_report(result))
    
    # Store scan results
    db.store_disk_scan(result)
    
    return 0


@handle_errors
def cmd_duplicates(args, config, db):
    """Execute duplicate finder command"""
    path = os.path.abspath(os.path.expanduser(args.path))
    
    if not os.path.exists(path):
        raise ResourceNotFoundError(f"Path not found: {path}")
    
    formatter = Formatter(color=not args.no_color)
    finder = DuplicateFinder(min_size=parse_size(args.min_size))
    
    print(f"Scanning for duplicates in: {path}")
    print("Phase 1: Grouping by size...")
    
    groups = finder.find_duplicates([path])
    
    if not groups:
        print("✓ No duplicate files found!")
        return 0
    
    # Display results
    total_wasted = sum(g.total_wasted_space for g in groups)
    print(f"\nFound {len(groups)} duplicate groups")
    print(f"Potential space recovery: {format_bytes(total_wasted)}\n")
    
    if args.report:
        export_duplicates_csv(groups, 'duplicates_report.csv')
        print("Report exported to: duplicates_report.csv")
        return 0
    
    if args.interactive:
        return interactive_duplicate_review(groups, formatter, config)
    
    if args.remove == 'safe':
        cleaner = DiskCleaner(config)
        removed = cleaner.remove_duplicates_safe(groups)
        print(f"Removed {removed} duplicate files")
    
    # Display summary
    for i, group in enumerate(groups[:10], 1):  # Show top 10
        print(formatter.duplicate_group(i, group))
    
    if len(groups) > 10:
        print(f"\n... and {len(groups) - 10} more groups")
        print("Use --interactive to review all")
    
    return 0


@handle_errors
def cmd_clean(args, config, db):
    """Execute disk cleanup command"""
    cleaner = DiskCleaner(config)
    
    if args.aggressive:
        level = 'aggressive'
    elif args.moderate:
        level = 'moderate'
    else:
        level = 'safe'
    
    print(f"Running {level} cleanup...")
    
    if args.dry_run:
        print("(Dry run - no files will be deleted)\n")
    
    result = cleaner.clean(level=level, dry_run=args.dry_run)
    
    # Display results
    print(f"\nCleanup {'Preview' if args.dry_run else 'Results'}:")
    print(f"  Files {'to be removed' if args.dry_run else 'removed'}: {result.file_count}")
    print(f"  Space {'recoverable' if args.dry_run else 'recovered'}: {format_bytes(result.bytes_freed)}")
    
    if result.items:
        print("\nCategories:")
        for category, size in result.by_category.items():
            print(f"  {category}: {format_bytes(size)}")
    
    if not args.dry_run:
        print(f"\nFiles moved to quarantine. Use 'sysmind disk quarantine list' to review.")
    
    return 0


@handle_errors
def cmd_quarantine(args, config, db):
    """Manage quarantine"""
    from sysmind.modules.disk.quarantine import Quarantine
    
    quarantine = Quarantine(config.quarantine_dir)
    
    if args.quarantine_cmd == 'list':
        items = quarantine.list_items()
        if not items:
            print("Quarantine is empty")
            return 0
        
        formatter = Formatter(color=not args.no_color)
        print(formatter.quarantine_list(items))
    
    elif args.quarantine_cmd == 'restore':
        if args.all:
            restored = quarantine.restore_all()
            print(f"Restored {restored} items")
        elif args.id:
            quarantine.restore(args.id)
            print(f"Restored item {args.id}")
        else:
            print("Specify an item ID or use --all")
            return 1
    
    elif args.quarantine_cmd == 'purge':
        confirm = input("Permanently delete all quarantined items? [y/N] ")
        if confirm.lower() == 'y':
            deleted = quarantine.purge()
            print(f"Permanently deleted {deleted} items")
        else:
            print("Cancelled")
    
    return 0


def parse_size(size_str: str) -> int:
    """Parse size string like '1MB' to bytes"""
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    size_str = size_str.upper().strip()
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-len(unit)]) * multiplier)
    
    return int(size_str)


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"
```

---

## 14. Extensibility & Future Scope

### 14.1 Future Enhancements

| Feature | Description | Complexity |
|---------|-------------|------------|
| **GUI Dashboard** | Web-based dashboard using Flask/FastAPI | High |
| **Remote Monitoring** | Monitor multiple machines | High |
| **Machine Learning** | Predict failures, optimize automatically | Very High |
| **Docker/Container Support** | Monitor container metrics | Medium |
| **Cloud Sync** | Sync configurations and history | Medium |
| **Mobile Notifications** | Push alerts to phone | Medium |
| **Plugin Marketplace** | Community plugins | High |

### 14.2 Version Roadmap

```
v1.0 (MVP)
├── Core CLI framework
├── Monitor module (basic)
├── Disk analyzer & cleaner
├── Process listing
└── Network diagnostics

v1.5
├── Baseline system
├── Anomaly detection
├── Health scoring
├── Watchdog rules
└── Scheduler

v2.0
├── Web dashboard
├── Plugin system
├── Advanced analytics
└── Remote monitoring

v3.0
├── ML-based predictions
├── Auto-optimization
├── Multi-machine support
└── Enterprise features
```

### 14.3 Contribution Guidelines

```markdown
# Contributing to SYSMIND

## Code Style
- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions under 50 lines

## Testing
- Write unit tests for new features
- Maintain >80% coverage
- Run `pytest` before committing

## Pull Requests
1. Fork the repository
2. Create a feature branch
3. Write tests
4. Submit PR with description

## Commit Messages
- Use conventional commits
- Format: `type(scope): message`
- Types: feat, fix, docs, test, refactor
```

---

## 15. Summary

### Key Differentiators

1. **Unified System View** - One tool for monitoring, disk, process, and network
2. **Historical Intelligence** - Learning from past data, not just current state
3. **Safety-First Design** - Quarantine system, undo support, never destructive
4. **Actionable Insights** - Not just data, but recommendations
5. **Cross-Correlation** - Links events across different system components

### Technical Highlights

- Clean architecture with modular design
- Comprehensive error handling
- Extensive test coverage
- Cross-platform support
- Standard library focus (portable)

### Learning Outcomes

- CLI application design
- Database design and management
- Algorithm implementation (duplicate detection, anomaly detection)
- System programming (process, network, disk operations)
- Statistical analysis (baselines, health scores)
- Software engineering best practices

---

## Appendix A: Quick Start Commands

```bash
# First run - initialize
sysmind config init

# Daily workflow
sysmind status                      # Morning check
sysmind monitor live                # While working
sysmind disk clean --safe           # Weekly cleanup

# Troubleshooting
sysmind process list --sort cpu     # Find resource hogs
sysmind network diagnose            # Network issues
sysmind intel anomalies             # What's unusual?
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-16  
**Author:** [Your Name]  
**Project:** SYSMIND - System Intelligence CLI
