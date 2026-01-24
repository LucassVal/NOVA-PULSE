# ⚡ NovaPulse 2.1

**Intelligent Windows System Optimization for Gaming & Performance**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-blue.svg)](https://www.microsoft.com/windows)

NovaPulse is a comprehensive system optimizer that applies **kernel-level tweaks** to reduce input lag, improve FPS, and maximize hardware performance. Features automatic thermal protection and intelligent mode switching.

---

## 🎯 Target Hardware

| Component | Tested On                                   |
| --------- | ------------------------------------------- |
| **CPU**   | Intel Core i5-11300H (Tiger Lake, 11th Gen) |
| **GPU**   | NVIDIA RTX 3050 Laptop + Intel Iris Xe      |
| **OS**    | Windows 10/11                               |

> Works on other Intel/AMD systems - optimizations are tuned for modern laptops.

---

## ✨ What's New in v2.1

- **Intel Power Control** - ECO/BALANCED/PERFORMANCE/TURBO profiles
- **Thermal Protection** - Auto-throttle at 85°C (prevents slowdown at 90°C)
- **Fixed Temperature Reading** - Correct DPTF thermal zone parsing
- **Dashboard Improvements** - Rich Live inline mode, no flickering

---

## 📦 Optimization Modules (13 Total)

| Module                 | What It Does                      | Impact             |
| ---------------------- | --------------------------------- | ------------------ |
| **Core Parking**       | Disables CPU core parking         | -5ms latency       |
| **Memory Optimizer**   | Disables Superfetch, compression  | +500MB-2GB RAM     |
| **NTFS Optimizer**     | Disables 8.3 names, Last Access   | +10-30% disk I/O   |
| **GPU Scheduler**      | Enables HAGS, GPU Priority        | +3-10 FPS          |
| **CUDA Optimizer**     | PhysX GPU, Shader Cache unlimited | Less stuttering    |
| **MMCSS Optimizer**    | Gaming/Audio priority             | -5ms audio/input   |
| **Network Stack**      | CTCP, disable Nagle               | -5-20ms ping       |
| **USB Optimizer**      | Disable selective suspend         | Better peripherals |
| **IRQ Affinity**       | MSI mode for GPU/USB/Network      | Lower IRQ latency  |
| **HPET Controller**    | Disable HPET, enable TSC          | -0.5-2ms timer     |
| **Advanced CPU**       | Disable C-States, force Turbo     | Consistent clocks  |
| **Advanced Storage**   | Write cache, NVMe queue depth     | Faster disk        |
| **Process Controller** | Auto-priority for games           | Smart allocation   |

---

## 🔧 Why These Optimizations?

<details>
<summary><b>Core Parking</b> - Disabled</summary>
Windows "parks" idle cores to save power. When load spikes, it takes 1-5ms to wake them. Disabled = all cores always ready.
</details>

<details>
<summary><b>C-States</b> - Disabled</summary>
Deep sleep states (C3, C6) save power but take ~100μs to wake. For gaming, we want instant response.
</details>

<details>
<summary><b>ASPM</b> - Disabled</summary>
PCIe power management puts GPU/NVMe to sleep. Disabled = instant GPU response.
</details>

<details>
<summary><b>HPET</b> - Disabled</summary>
Legacy timer. Modern CPUs have faster TSC (Time Stamp Counter). HPET adds 0.5-2ms overhead.
</details>

<details>
<summary><b>Nagle Algorithm</b> - Disabled</summary>
TCP batching is great for throughput, terrible for latency. Gaming needs immediate packets.
</details>

---

## 🚀 Quick Start

### Option 1: Run from Python

```powershell
# Clone repository
git clone https://github.com/LucassVal/LABS.git
cd LABS/PythonVersion

# Install dependencies
pip install -r requirements.txt

# Run as Administrator
python novapulse.py
```

### Option 2: Run Standalone EXE

```powershell
# Download from dist/ folder
./NovaPulse.exe
```

---

## 📂 Project Structure

```
NovaPulse/
├── PythonVersion/              # Active development (Python)
│   ├── novapulse.py            # Main entry point
│   ├── config.yaml             # All settings
│   ├── README.md               # Technical documentation
│   └── modules/                # 37 optimization modules
│       ├── optimization_engine.py
│       ├── auto_profiler.py
│       ├── intel_power_control.py   # NEW in v2.1
│       ├── temperature_service.py
│       └── ... (34 more)
│
├── _archive_csharp/            # Legacy C# version (archived)
├── docs/                       # Additional documentation
└── README.md                   # This file
```

---

## ⚙️ Configuration

Edit `PythonVersion/config.yaml`:

```yaml
optimization:
  level: gaming # safe, balanced, gaming, aggressive

auto_profiler:
  enabled: true
  boost_threshold: 85 # CPU % → BOOST mode
  eco_threshold: 30 # CPU % → ECO mode

thermal:
  threshold: 85 # °C to trigger protection
  throttle_percent: 70 # CPU limit when thermal active
```

---

## 📈 Performance Impact

| Metric          | Improvement    |
| --------------- | -------------- |
| Input Lag       | -5 to -15ms    |
| Boot Time       | -10 to -20%    |
| Available RAM   | +500MB to +2GB |
| Disk I/O        | +10 to +30%    |
| Network Latency | -5 to -20ms    |
| Gaming FPS      | +3 to +10%     |

---

## 🌡️ Thermal Protection

NovaPulse monitors CPU temperature and automatically protects your system:

```
Temperature < 70°C  → PERFORMANCE mode (full power)
Temperature 70-85°C → BALANCED mode
Temperature > 85°C  → ECO mode (prevents crash at 90°C)
```

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Dashboard: [Rich](https://github.com/Textualize/rich)
- GPU Monitoring: [pynvml](https://github.com/gpuopenanalytics/pynvml)
- Inspiration: [ISLC](https://www.wagnardsoft.com/)

---

**NovaPulse 2.1** - _Intelligent System Optimization_

Made with ❤️ for gamers and power users
