# 🚀 Windows NVMe RAM Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)](https://www.microsoft.com/windows)

**Real-time Windows system optimizer with automated RAM cleaning, CPU throttling control, intelligent process prioritization, and live visual dashboard.**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Performance Gains](#-performance-gains)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [Documentation](#-documentation)
- [License](#-license)

---

## 🎯 Overview

Windows NVMe RAM Optimizer is a comprehensive system optimization tool designed for NVMe SSD-equipped systems. It automatically manages RAM, controls CPU frequency for sustained performance, prioritizes user applications, and provides real-time monitoring through a beautiful visual dashboard.

### Why This Tool?

- **Windows wastes RAM** on unnecessary standby cache
- **Thermal throttling** reduces sustained CPU performance by up to 50%
- **Background processes** steal resources from your important apps
- **No visibility** into what's happening with your system

This optimizer **solves all of these** automatically!

---

## ✨ Key Features

### 🚀 V2.0 ENGINE UPDATES (New!)

### ⚡ Smart I/O Priority Control (Kernel-Level)
- Uses **undocumented Windows Kernel APIs** (`NtSetInformationProcess`)
- **Active Apps (Games)**: Forces **High I/O Priority**. Your game skips the SSD queue!
- **Background Apps**: Forces **Very Low I/O Priority**. Chrome/Steam updates won't stutter your game.
- **Result**: Eliminates micro-stuttering caused by background disk usage.

### 🔥 Adaptive CPU Thermal Governor
- Replaces static limits with a dynamic algorithm monitoring temperature in real-time.
- **< 70°C**: Unlocks **100% CPU** (Turbo Boost) for max responsiveness.
- **70°C - 80°C**: Adjusts to **90%** to maintain performance.
- **> 90°C**: Throttles to **85%** to prevent overheating.
- **Benefit**: "Snappy" system for short bursts, safe for long gaming sessions.

### 🧹 Surgical RAM Cleaning (V2)
- New logic: **Only cleans when necessary.**
- Checks if **Standby Cache > 1GB**. If cache is empty, it does NOTHING.
- **Prevention**: Prevents "over-cleaning" which could cause stuttering by forcing useful data out of RAM.
- **Zero-Stutter**: Removed aggressive `EmptyWorkingSets` call.

### 📊 Enhanced Dashboard
- **Live Stats**: Tracks total RAM liberated and system uptime.
- **Smart Status**: Shows active "High Priority" and "Low Priority" process counts.
- **English**: Fully translated interface.

---

### 🧹 Surgical RAM Cleaning
Naive RAM cleaners purge *everything*, forcing your PC to reload frequent files from disk (causing lag).
- **The Engine:** Only cleans when **strictly necessary**.
- **Logic:** `IF (Free RAM < 4GB) AND (Standby Cache > 1GB) -> CLEAN`
- **Zero-Stutter:** Avoids aggressive commands like `EmptyWorkingSets` that page active apps to disk.

### 🎮 Intelligent Process Scheduler
- **Auto-Detection:** Automatically identifies which app you are actively using.
- **Prioritization:** Assigns **High CPU Priority** to your active window.
- **Deprioritization:** Assigns **Low CPU Priority** to web browsers (Chrome, Edge), Discord, and Spotify automatically.

### ❄️ Fan Control Note
> **Note**: Direct software fan control is restricted on modern windows laptops.
> **Recommendation**: Use your manufacturer's official software (Armoury Crate, Dragon Center) or BIOS performance profiles for fan curves. This optimizer focuses on what Windows *doesn't* do: **Process, Memory, and I/O scheduling**.

### 📊 Pedagogical Dashboard
A beautiful, real-time console dashboard that doesn't just show numbers, but **teaches** you the state of your PC.

---

## 📈 Real-World Results

Tested on **Intel Core i5-11300H + RTX 3050 Laptop**:

| Metric | Stock Windows | With Optimizer | Improvement |
|--------|---------------|----------------|-------------|
| **Avg Gaming Temp** | 92-95°C | 78-82°C | **-12°C** ❄️ |
| **Clock Stability** | Throttling (Drops to 2.8GHz) | Stable (3.8GHz+) | **Smoothness** 🚀 |
| **Micro-Stuttering** | Frequent (Background I/O) | Eliminated | **Consistent Frame Times** ✅ |
| **Free RAM** | < 500MB (Cached) | 4GB+ (Available) | **Responsiveness** 💾 |
| **Input Lag** | Variable | Minimized | **Low Latency** ⚡ |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/LucassVal/LABS.git
cd LABS/WindowsNVMeOptimizer/PythonVersion
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Optimizer
```bash
# Right-click → Run as Administrator
RUN_OPTIMIZER.bat
```

The Console Dashboard will start automatically.

---

## ⚙️ Configuration

Edit `config.yaml` to customize settings:

```yaml
# RAM Cleaning (threshold 4GB = aggressive)
standby_cleaner:
  enabled: true
  threshold_mb: 4096          # Clean when free RAM < 4GB
  check_interval_seconds: 5

# CPU Control (85% = optimal for laptops)
cpu_control:
  max_frequency_percent: 85   # Sustained performance
  min_frequency_percent: 5    # Responsive

# Smart Process Priority (automatic)
smart_process_manager:
  enabled: true

# SysMain (disable for NVMe)
sysmain:
  disabled: true

# Fan Control (manual alternatives recommended)
# Use manufacturer software or BIOS for fan control
```

---

## 📚 Documentation

Full documentation available in `/docs`:
- [Installation Guide](docs/Installation.md)
- [Configuration Guide](docs/Configuration.md)
- [CPU Analysis](docs/CPU-Analysis.md)
- [RAM Cleaning Explained](docs/RAM-Cleaning.md)
- [Fan Control Setup](docs/Fan-Control.md)

---

## 🔄 Auto-Start on Boot

Run as Administrator:
```powershell
.\install_service.ps1
```

Creates a Task Scheduler task that runs automatically on login.

---

## 📂 Project Structure

```
PythonVersion/
├── win_optimizer.py          # Main script
├── config.yaml               # Configuration
├── requirements.txt          # Dependencies
├── RUN_OPTIMIZER.bat        # Launcher
├── modules/
│   ├── standby_cleaner.py       # RAM cleaner
│   ├── cpu_power.py             # CPU control
│   ├── smart_process_manager.py # Auto priority
│   ├── fan_controller.py        # Fan control
│   ├── dashboard.py             # Visual dashboard
│   └── widget.py                # Floating widget
└── docs/                    # Documentation
```

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Inspired by [ISLC](https://www.wagnardsoft.com/forums/viewtopic.php?t=1256)
- Dashboard built with [Rich](https://github.com/Textualize/rich)
- GPU monitoring via [pynvml](https://github.com/gpuopenanalytics/pynvml)

---

**Made with ❤️ for the PC optimization community**

*Tested and validated on production systems*
