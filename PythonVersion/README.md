# ⚡ NovaPulse 2.2.1

**Intelligent Windows System Optimization + Security Shield**

A comprehensive system optimization tool with built-in security scanner and telemetry blocker. Applies kernel-level tweaks to reduce input lag, improve FPS, and maximize privacy. Designed and tested on Intel Tiger Lake laptops.

## 🎯 Target Hardware

- **CPU**: Intel Core i5-11300H (4C/8T, Tiger Lake, 11th Gen)
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU + Intel Iris Xe (iGPU)
- **OS**: Windows 10/11
- **Note**: Works on other Intel/AMD systems, but optimizations are tuned for Tiger Lake

## 📦 Features

### Optimization Modules (13 total)

| Module                 | Description                                             | Impact                      |
| ---------------------- | ------------------------------------------------------- | --------------------------- |
| **Core Parking**       | Disables CPU core parking, forces High Performance plan | -5ms latency                |
| **Memory Optimizer**   | Disables compression, Superfetch, optimizes paging      | +500MB-2GB free RAM         |
| **NTFS Optimizer**     | Disables 8.3 names, Last Access Time                    | +10-30% disk I/O            |
| **GPU Scheduler**      | HAGS, GPU Priority, TDR, PhysX→NVIDIA, Global GPU Pref  | +3-10 FPS, -1GB iGPU RAM    |
| **CUDA Optimizer**     | Shader Cache unlimited, Pre-rendered frames, ASPM off   | Reduced stuttering          |
| **MMCSS Optimizer**    | Gaming/Audio task priority, SystemResponsiveness=0      | -5ms audio/input            |
| **Network Stack**      | CTCP, disable Nagle, optimize AFD buffers               | -5-20ms ping                |
| **USB Optimizer**      | Disable selective suspend, optimize buffers             | Better mouse/keyboard       |
| **IRQ Affinity**       | MSI mode for GPU/USB/Network                            | Less interrupt latency      |
| **HPET Controller**    | Disables HPET, enables TSC sync                         | -0.5-2ms timer              |
| **Advanced CPU**       | Disable C-States, force Turbo Boost                     | Consistent clock speeds     |
| **Advanced Storage**   | Write caching, NVMe queue depth, Large Pages            | Faster disk access          |
| **Process Controller** | Allowlist-only HIGH priority, bloatware→LOW, stats      | Smarter resource allocation |

### 🛡️ Security Shield (NEW in v2.2)

| Feature                | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| **Process Scanner**    | Scans all processes, flags unsigned/suspicious executables   |
| **Network Monitor**    | Lists outbound connections, flags unknown IPs/ports          |
| **Startup Auditor**    | Checks Run/RunOnce registry + Startup folder for persistence |
| **Port Scanner**       | Shows open listening ports, flags unusual ports              |
| **Telemetry Blocker**  | Blocks 21+ Microsoft telemetry domains via hosts file        |
| **Registry Hardening** | Disables telemetry flags, Advertising ID, Activity History   |
| **Defender Privacy**   | Blocks SpyNet/MAPS data sharing (keeps protection ON)        |
| **Privacy Score**      | 0-100% score based on how many data leaks are blocked        |

### Monitoring & Control

- **Rich Console Dashboard**: 3-panel layout (Hardware + Memory & Status + Security Shield)
- **CPU GHz/Turbo Display**: Shows current vs max frequency in real-time
- **Dynamic Infographic Footer**: Shows what NovaPulse applied at boot + live stats
- **System Tray Icon**: Quick access, minimize to tray, compact tooltip
- **Auto-Profiler (2-Stage)**: ACTIVE (80% CPU) / IDLE (20% CPU after 5 min inactivity)
- **Windows Defender Hardening**: Enables ASR rules, ransomware protection, exploit mitigations
- **Auto-Start**: Runs at system startup via Task Scheduler (before login)

### Temperature Service (5-stage hierarchy)

```text
Priority 1: OpenHardwareMonitor / LibreHardwareMonitor (most accurate)
Priority 2: WMI Win32_TemperatureProbe
Priority 3: ACPI ThermalZone (MSAcpi_ThermalZoneTemperature) ← Intel DPTF
Priority 4: NVIDIA GPU estimation (+12°C offset)
Priority 5: Intel iGPU reference (+5°C offset)
```

**Design Decision**: On Intel DPTF systems (like i5-11300H), the ACPI thermal zone reports actual CPU die temperature, NOT chassis temperature. No offset is applied.

### GPU → NVIDIA Enforcement

- **Global GPU Preference**: Forces all graphical apps to NVIDIA RTX via `DirectXUserGlobalSettings`
- **Per-App Override**: Critical apps (IDE, NovaPulse, Node.js) explicitly set to High Performance
- **PhysX → RTX 3050**: Prevents CPU from calculating physics geometry
- **Effect**: Frees Intel Iris Xe shared RAM back to system (~1GB+)

### Intel Power Control

Controls CPU power limits via Windows Power Options (works on locked CPUs):

| Profile     | Throttle Min/Max | Boost Mode | Use Case        |
| ----------- | ---------------- | ---------- | --------------- |
| ECO         | 5% / 50%         | Disabled   | Silent, battery |
| BALANCED    | 5% / 85%         | Efficient  | Normal use      |
| PERFORMANCE | 50% / 100%       | Aggressive | Gaming          |
| TURBO       | 100% / 100%      | Maximum    | Benchmarks      |

**Thermal-aware**: Automatically switches to ECO when temp > 85°C.

## 🔧 Why These Optimizations?

### Core Parking (Disabled)

Windows "parks" idle CPU cores to save power. When load spikes, it takes 1-5ms to wake them. For gaming, this causes micro-stuttering. Disabled = all cores always ready.

### C-States (Disabled)

Deep sleep states (C3, C6) save power but take ~100μs to wake. On a gaming rig, we want C0 (active) always for instant response.

### ASPM (Disabled)

Active State Power Management puts PCIe devices (GPU, NVMe) to sleep. When you need a frame rendered NOW, you don't want the GPU waking up. Disabled = instant GPU response.

### HPET (Disabled)

High Precision Event Timer is legacy hardware. Modern CPUs have TSC (Time Stamp Counter) which is faster and more accurate. HPET adds 0.5-2ms overhead.

### Nagle Algorithm (Disabled)

TCP optimization that batches small packets. Great for throughput, terrible for latency. For gaming, every packet should be sent immediately.

### Microsoft Telemetry (Blocked)

Windows sends diagnostic data, crash reports, usage statistics, and browsing patterns to Microsoft. Even "Basic" telemetry sends hardware inventory, app compatibility data, and performance metrics. NovaPulse blocks 21+ telemetry endpoints at the DNS level — completely transparent and reversible.

## 📊 Architecture

```text
novapulse.py (main v2.2.1)
├── optimization_engine.py     ← Orchestrates all 13 modules
├── modules/
│   ├── Core: auto_profiler, standby_cleaner, cpu_power
│   ├── Hardware: core_parking, memory_optimizer, hpet_controller
│   ├── GPU: gpu_scheduler (7 opts), cuda_optimizer
│   ├── Network: network_qos, network_stack_optimizer
│   ├── Input: usb_optimizer, irq_optimizer
│   ├── System: ntfs_optimizer, mmcss_optimizer, services_optimizer
│   ├── Process: process_controller, smart_process_manager
│   ├── Monitoring: temperature_service, intel_power_control
│   ├── Security: security_scanner, telemetry_blocker, defender_hardener
│   ├── Startup: startup_manager
│   └── UI: dashboard (with security panel), tray_icon, dashboard_webview
├── config.yaml               ← All module settings
└── diagnostic.py             ← System diagnostics
```

## 🚀 Usage

### Run from Python

```powershell
# Admin terminal required
cd "G:\Meu Drive\NovaPulse\PythonVersion"
pip install -r requirements.txt
python novapulse.py
```

### Build Standalone EXE

```powershell
python -m PyInstaller --onefile --icon=novapulse_logo.ico --add-data "config.yaml;." --name NovaPulse novapulse.py
# Output: dist/NovaPulse.exe
```

### Configuration

Edit `config.yaml` to customize:

```yaml
optimization_level: gaming # safe, balanced, gaming, aggressive

auto_profiler:
  enabled: true
  active_cpu_cap: 80 # ACTIVE mode CPU cap
  idle_cpu_cap: 20 # IDLE mode CPU cap
  idle_timeout: 300 # 5 min to enter IDLE
  wake_threshold: 15 # CPU >15% = wake to ACTIVE
```

## ⚠️ Notes

- **Restart Required**: Some optimizations (HPET, HAGS, IRQ Affinity) require a PC restart
- **Admin Required**: Must run as Administrator for kernel-level tweaks
- **Reversible**: All changes can be undone by Windows Reset or manually via Registry
- **Telemetry**: Hosts file entries can be removed manually or via `blocker.restore_hosts()`

## 📈 Expected Impact

| Metric          | Improvement    |
| --------------- | -------------- |
| Input Lag       | -5 to -15ms    |
| Boot Time       | -10 to -20%    |
| Available RAM   | +500MB to +2GB |
| Disk I/O        | +10 to +30%    |
| Network Latency | -5 to -20ms    |
| Gaming FPS      | +3 to +10%     |
| Privacy Score   | 80-100%        |

## 📄 License

Personal use. Created for optimizing Windows gaming performance and privacy.

---

**Version**: 2.2.1  
**Last Updated**: 2026-02-09  
**Target CPU**: Intel Core i5-11300H @ 3.10GHz (Tiger Lake)
