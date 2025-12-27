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

### 🧹 Automatic RAM Cleaning
- Monitors RAM usage every 5 seconds
- Cleans Windows Standby Cache when free RAM < 4GB
- Liberates 2-6GB instantly
- Similar to ISLC but automated

### 🔥 CPU Thermal Control
- Limits CPU to 85% frequency (configurable)
- **Result**: Sustained 85% performance vs 100% that throttles to 50%
- Equivalent to -60mV to -75mV undervolt
- Temperature reduction: **-20°C**

### 🎯 Intelligent Process Priority
- Automatically detects user-initiated apps (games, work tools)
- Assigns HIGH priority to your important processes
- Assigns LOW priority to browsers and background tasks
- **Zero manual configuration**

### 📊 Real-Time Dashboard
- Beautiful console dashboard with live stats
- Alternative: Floating widget (always-on-top window)
- Monitors: CPU, GPU, RAM, Temperatures
- Update interval: 5 seconds (no flickering!)

### 🎮 Dual GPU Support
- NVIDIA GPU: Full stats (usage, temp, VRAM)
- Intel iGPU: Detection and status
- Automatic temperature monitoring

> **Note**: Fan control via software is limited on Windows. NBFC project was discontinued.  
> **Alternatives**: Use manufacturer software (ASUS Armoury Crate, MSI Dragon Center) or BIOS settings.

---

## 📈 Performance Gains

Real-world results from Intel i5-11300H + RTX 3050 Laptop:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **CPU Temperature** | 95°C | 75°C | **-20°C** 🔥 |
| **Sustained CPU** | ~50% (throttled) | 85% | **+70%** 🚀 |
| **GPU Temperature** | 83°C | 60-65°C | **-20°C** ❄️ |
| **Free RAM** | 0.5GB | 4-8GB | **+6GB** 💾 |
| **Stuttering** | Frequent | Zero | **100%** ✅ |

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

### 4. Choose Dashboard Mode
```
[1] Console Dashboard (full-featured, recommended)
[2] Floating Widget (compact, always-on-top)
```

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
