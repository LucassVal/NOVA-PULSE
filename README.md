# ⚡ NovaPulse 2.2.1 — Intelligent System Optimizer

![Version](https://img.shields.io/badge/version-2.2.1_GOLD-brightgreen?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-blue?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-Private-red?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-success?style=for-the-badge)
![Admin](https://img.shields.io/badge/requires-Administrator-orange?style=for-the-badge&logo=windows-terminal)
![CPU](https://img.shields.io/badge/target-Intel_Tiger_Lake-0071C5?style=for-the-badge&logo=intel)
![GPU](https://img.shields.io/badge/GPU-NVIDIA_CUDA-76B900?style=for-the-badge&logo=nvidia)

> **Kernel-level Windows 10/11 optimizer** targeting Intel Core i5-11300H (Tiger Lake) + NVIDIA GPU systems.
> Requires Administrator privileges. Designed for gaming & productivity workloads.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Core Files](#core-files)
4. [Module Registry](#module-registry)
   - [CPU & Power](#cpu--power)
   - [GPU & CUDA](#gpu--cuda)
   - [Memory](#memory)
   - [Storage](#storage)
   - [Network](#network)
   - [Process Management](#process-management)
   - [Security & Privacy](#security--privacy)
   - [Dashboard & Monitoring](#dashboard--monitoring)
   - [System Services](#system-services)
   - [Utilities](#utilities)
5. [Configuration Reference](#configuration-reference)
6. [Dependencies](#dependencies)
7. [Build & Distribution](#build--distribution)
8. [Hardware Rationale](#hardware-rationale)
9. [Safety & Risks](#safety--risks)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   novapulse.py                      │
│              (Main Entry Point / CLI)               │
│       Loads config.yaml → Initializes all services  │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│             optimization_engine.py                  │
│          (Central Orchestrator / Engine)             │
│   4 Levels: SAFE → BALANCED → GAMING → AGGRESSIVE   │
│   Manages conflict resolution & execution order     │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┼────────┬──────────┬──────────┬─────────┐
    ▼        ▼        ▼          ▼          ▼         ▼
┌───────┐┌───────┐┌────────┐┌────────┐┌────────┐┌────────┐
│  CPU  ││  GPU  ││ Memory ││Storage ││Network ││Process │
│ Layer ││ Layer ││ Layer  ││ Layer  ││ Layer  ││ Layer  │
└───┬───┘└───┬───┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
    │        │        │         │         │         │
    ▼        ▼        ▼         ▼         ▼         ▼
 Registry  pynvml   WinAPI    fsutil    netsh    psutil
 powercfg  CUDA     ctypes    powershell registry  ctypes
 ctypes    HAGS     kernel32             DNS
           DXGI
```

**Design Patterns:**

- **Singleton** — Every module uses `_instance` + `get_*()` factory for global access
- **Service Dict** — `novapulse.py` passes `services={}` dict to all modules at runtime
- **Background Threads** — Monitoring loops run as daemon threads (auto-profiler, TRIM, security scanner, temperature service)
- **Config-Driven** — All toggles in `config.yaml`, modules respect `enabled: false`

---

## Quick Start

```powershell
# 1. Clone the repo
git clone https://github.com/LucassVal/NOVA-PULSE.git
cd NOVA-PULSE/src

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run (Administrator PowerShell required)
python novapulse.py

# Optional: Run diagnostics first
python diagnostic.py

# Optional: Build standalone .exe
pyinstaller novapulse.spec
```

> **Note:** Python 3.10+ must be installed. Run PowerShell as Administrator.
> `pip install -r requirements.txt` installs: `psutil`, `pynvml`, `rich`, `pyyaml`, `wmi`

---

## Core Files

### `novapulse.py` — Main Entry Point

| Detail | Value                                                              |
| ------ | ------------------------------------------------------------------ |
| Lines  | ~400                                                               |
| Role   | CLI entry, config loader, service bootstrapper, dashboard launcher |

**Key Responsibilities:**

- Parses `config.yaml` using PyYAML
- Instantiates all optimization modules into `services={}` dict
- Calls `optimization_engine.apply_optimizations(level)` with configured level
- Applies CPU control via `CPUPowerManager.set_max_cpu_frequency(80)` and `set_min_cpu_frequency(5)`
- Starts background services: auto-profiler, game detector, security scanner, NVMe TRIM
- Launches `Dashboard.run(services)` as the main UI loop
- Sets process priority to HIGH for itself

**Configuration Loaded:**

- `optimization_level` → passed to engine
- `cpu_control.max_frequency_percent` → CPU cap (default 80)
- `nvme.enabled` → NVMe optimizations
- `auto_profiler.enabled` → 2-stage profiler
- `network_qos` → DNS & QoS settings
- `game_detector` → game boost

---

### `optimization_engine.py` — Central Orchestrator

| Detail  | Value                        |
| ------- | ---------------------------- |
| Lines   | 383                          |
| Class   | `OptimizationEngine`         |
| Pattern | Singleton via `get_engine()` |

**Optimization Levels:**

| Level        | Modules Applied                                      |
| ------------ | ---------------------------------------------------- |
| `SAFE`       | Core parking, timer resolution, gamebar              |
| `BALANCED`   | + MMCSS, NTFS, memory optimizer                      |
| `GAMING`     | + CUDA, IRQ, network stack, process controller       |
| `AGGRESSIVE` | + services optimizer, advanced CPU, advanced storage |

**Key Methods:**

- `apply_optimizations(level)` — Executes modules in dependency order
- `get_optimization_summary()` — Returns dict of all applied optimizations
- `get_conflicts()` — Lists conflicting module settings

---

### `diagnostic.py` — System Health Check

| Detail | Value                                             |
| ------ | ------------------------------------------------- |
| Lines  | 251                                               |
| Role   | Standalone diagnostic tool, generates text report |

**Checks Performed:**

- Python version, OS version, admin privileges
- Import verification for all modules (psutil, pynvml, wmi, yaml, rich)
- NVIDIA GPU detection and driver info
- CPU info (model, cores, frequency)
- RAM amount and usage
- Temperature service connectivity
- Module instantiation health (each module tested individually)
- Saves report to `~/Desktop/NovaPulse_Diagnostic.txt`

---

## Module Registry

### CPU & Power

#### `modules/cpu_power.py` — CPU Frequency Controller

| Detail  | Value                                  |
| ------- | -------------------------------------- |
| Lines   | ~159                                   |
| Class   | `CPUPowerManager`                      |
| Pattern | Singleton via `get_manager()`          |
| Backend | `powercfg.exe` (Windows Power Options) |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `set_max_cpu_frequency(percent)` | Sets max CPU state (0-100%) via powercfg |
| `set_min_cpu_frequency(percent)` | Sets min CPU state (0-100%) |
| `start_adaptive_governor(base_cap=80)` | Thermal-aware throttle loop; respects profiler cap as ceiling |
| `restore_defaults()` | Resets to 100%/5% |

**Design Notes:**

- `start_adaptive_governor` accepts `base_cap` parameter and NEVER exceeds this ceiling
- This prevents thermal governor from overriding auto_profiler's 80% cap
- The `start_adaptive_governor` function was identified as unused dead code in current flow

---

#### `modules/auto_profiler.py` — 2-Stage CPU Power Manager

| Detail  | Value                                   |
| ------- | --------------------------------------- |
| Lines   | ~267                                    |
| Class   | `AutoProfiler`                          |
| Pattern | Background thread with `start()/stop()` |

**Profiles:**

| Mode   | CPU Cap | Trigger                      | Behavior                              |
| ------ | ------- | ---------------------------- | ------------------------------------- |
| ACTIVE | 80%     | CPU > 15% or recent activity | Normal operation, Turbo Boost allowed |
| IDLE   | 20%     | 5 min inactivity (cpu < 15%) | Maximum power saving                  |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `start(services)` | Begins monitoring loop (2s interval) |
| `get_current_mode()` | Returns `ACTIVE` or `IDLE` |
| `get_avg_cpu()` | Returns smoothed CPU usage average |
| `active_cpu_cap` | Property returning current cap (80 or 20) |

**Design Notes:**

- Uses `cpu_power` service to apply limits
- Uses `intel_power_control` for Intel-specific profiles
- Adjusts memory cleaner threshold based on mode (3GB active, 1.5GB idle)

---

#### `modules/advanced_cpu_optimizer.py` — Advanced CPU Tweaks

| Detail  | Value                           |
| ------- | ------------------------------- |
| Lines   | 244                             |
| Class   | `AdvancedCPUOptimizer`          |
| Pattern | Singleton via `get_optimizer()` |

**Optimizations Applied:**

| Tweak                    | Registry/Command                      | Impact                                       |
| ------------------------ | ------------------------------------- | -------------------------------------------- |
| Disable C-States         | Registry `Attributes`                 | Prevents CPU sleep states, less latency      |
| Force Turbo Boost        | `powercfg /setacvalueindex`           | Always-on burst frequency                    |
| Large System Cache       | Registry `LargeSystemCache`           | Prioritize apps over file cache              |
| Optimize Scheduling      | Registry `SystemResponsiveness=0`     | Max priority for foreground                  |
| Disable Power Throttling | Registry `PowerThrottlingOff=1`       | No background throttle                       |
| CPU Priority Separation  | Registry `Win32PrioritySeparation=38` | Foreground boost                             |
| Interrupt Affinity       | Registry MSI mode                     | Better IRQ distribution across cores         |
| SvcHost Splitting        | Registry `SvcHostSplitThresholdInKB`  | Separates services into individual processes |

---

#### `modules/intel_power_control.py` — Intel-Specific Power Profiles

| Detail  | Value                                              |
| ------- | -------------------------------------------------- |
| Lines   | 343                                                |
| Class   | `IntelPowerControl`                                |
| Enum    | `PowerProfile` (ECO, BALANCED, PERFORMANCE, TURBO) |
| Pattern | Singleton via `get_controller()`                   |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `set_throttle_min(percent)` | Min processor state via powercfg |
| `set_throttle_max(percent)` | Max processor state (PL1-like cap) |
| `set_boost_mode(mode)` | Turbo Boost behavior (0=off, 2=aggressive, 4=efficient-aggressive) |
| `set_cooling_policy(active)` | Active=fan first, Passive=throttle first |
| `apply_profile(profile)` | Applies complete power profile preset |
| `thermal_aware_update(cpu_temp)` | Auto-throttles if temp > 85°C |

**Profile Presets:**

| Profile     | Min% | Max% | Boost          | Cooling |
| ----------- | ---- | ---- | -------------- | ------- |
| ECO         | 5    | 50   | 0 (off)        | Passive |
| BALANCED    | 5    | 85   | 3 (efficient)  | Active  |
| PERFORMANCE | 50   | 100  | 2 (aggressive) | Active  |
| TURBO       | 100  | 100  | 2 (aggressive) | Active  |

---

#### `modules/core_parking.py` — Core Parking Manager

| Detail  | Value                         |
| ------- | ----------------------------- |
| Lines   | 258                           |
| Class   | `CoreParkingManager`          |
| Pattern | Singleton via `get_manager()` |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `disable_core_parking()` | All CPU cores always active (0% parking) |
| `enable_core_parking(min_percent)` | Re-enable with custom minimum |
| `optimize_parking_timers()` | Faster unparking, slower parking |
| `set_high_performance_scheme()` | Activates High Performance power plan |
| `create_ultimate_performance_scheme()` | Creates/activates Ultimate Performance |
| `apply_all_optimizations(use_ultimate)` | Full suite |

---

#### `modules/timer_resolution.py` — Timer Resolution Optimizer

| Detail  | Value                                                                        |
| ------- | ---------------------------------------------------------------------------- |
| Lines   | 105                                                                          |
| Class   | `TimerResolutionOptimizer`                                                   |
| Backend | `ntdll.NtSetTimerResolution` / `NtQueryTimerResolution` (direct kernel call) |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `get_current_resolution()` | Returns current timer resolution in ms |
| `set_resolution(resolution_100ns)` | Sets timer (target: 5000 = 0.5ms) |
| `apply_optimization()` | Changes from default 15.625ms → 0.5ms |
| `start_persistent()` | Re-applies every 60s (some apps reset it) |
| `restore()` | Returns to 15.625ms default |

---

### GPU & CUDA

#### `modules/cuda_optimizer.py` — CUDA & GPU Advanced Optimizer

| Detail  | Value                                   |
| ------- | --------------------------------------- |
| Lines   | 536                                     |
| Class   | `CUDAOptimizer`                         |
| Pattern | Singleton via `get_optimizer()`         |
| Backend | Registry, pynvml, environment variables |

**Optimizations (20+):**
| Category | Tweaks |
|----------|--------|
| CUDA Environment | `CUDA_CACHE_MAXSIZE`, `CUDA_FORCE_PTX_JIT`, `CUDA_AUTO_BOOST` |
| PhysX | Force dedicated GPU |
| GPU Preference | Global NVIDIA preference for graphical apps |
| Hardware Accel | Enable HW video encode/decode |
| Power Mgmt | Maximum Performance / Thermal throttle |
| Pre-Render Frames | Set to 1 (reduces input lag from default 3) |
| Shader Cache | Unlimited (reduces stuttering) |
| CUDA P2 State | Disable downclocking during compute |
| DPC Handling | Per-core DPC distribution |
| ASPM | Disable PCIe power saving (lower latency) |
| Texture Filtering | High Performance mode |
| Triple Buffering | Disabled (less latency) |
| GPU Preemption | Disabled (less context switching) |
| Threaded Optimization | Multi-thread rendering |

**Thermal Protection:**

- `check_thermal_throttle()` — Monitors GPU temp, auto-throttles at 90°C
- `get_gpu_temp()`, `get_gpu_power_limit()`, `set_gpu_power_limit(watts)`

---

#### `modules/gpu_scheduler.py` — GPU Scheduler Controller

| Detail  | Value                            |
| ------- | -------------------------------- |
| Lines   | 362                              |
| Class   | `GPUSchedulerController`         |
| Pattern | Singleton via `get_controller()` |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `enable_hardware_accelerated_scheduling()` | Enable/disable HAGS (Windows 10 2004+, NVIDIA 1000+) |
| `set_gpu_priority(priority=8)` | Max GPU priority in system (0-8) |
| `optimize_dxgi()` | Reduce DXGI frame presentation latency |
| `disable_fullscreen_optimizations_globally()` | Disable FSO system-wide |
| `enable_game_mode()` | Enable Windows Game Mode |
| `set_preferred_gpu_high_performance()` | Force NVIDIA as default for key apps (GpuPreference=2) |
| `set_physx_gpu()` | Force dedicated GPU for PhysX (frees CPU) |
| `check_gpu_support()` | Verify HAGS compatibility |

---

#### `modules/gamebar_optimizer.py` — Game Bar / Xbox DVR Disabler

| Detail | Value              |
| ------ | ------------------ |
| Lines  | 153                |
| Class  | `GameBarOptimizer` |

**Disables:**

- Xbox Game Bar (`AppCaptureEnabled`, `GameDVR_Enabled`)
- Fullscreen Optimizations (`HwSchMode=2`)
- Auto Game Mode (`AutoGameModeEnabled=0`)
- Expected result: +5-10 FPS, less stuttering

---

### Memory

> **Focus: Memory Pressure Management** — On systems with 16GB RAM hitting 85%+ usage,
> NovaPulse squeezes every last byte via ZRAM-style compression, page deduplication,
> working set trimming, and file cache limiting — techniques used by Linux (zswap/KSM)
> and commercial tools (MemReduct, Razer Cortex).

#### `modules/memory_optimizer.py` — Memory Optimizer Pro (Endgame Edition)

| Detail  | Value                           |
| ------- | ------------------------------- |
| Lines   | ~470                            |
| Class   | `MemoryOptimizerPro`            |
| Pattern | Singleton via `get_optimizer()` |
| Version | V4.0 Endgame                    |

**Optimization Pipeline (3 Stages):**

| Stage        | Tweak                  | API                                    | Impact                                                  |
| ------------ | ---------------------- | -------------------------------------- | ------------------------------------------------------- |
| 1 — ZRAM     | Memory Compression     | `Enable-MMAgent -MemoryCompression`    | Compresses inactive pages in RAM (~25% effective gain)  |
| 1 — ZRAM     | Page Combining         | `Enable-MMAgent -PageCombining`        | Deduplicates identical pages (huge for Chrome/Electron) |
| 1 — ZRAM     | Application PreLaunch  | `Enable-MMAgent -ApplicationPreLaunch` | Keeps frequent apps warm                                |
| 2 — Registry | SysMain OFF            | Registry + `sc stop SysMain`           | Removes predictive prefetching (redundant on SSDs)      |
| 2 — Registry | Prefetch OFF           | Registry `EnablePrefetcher=0`          | Disables boot/app prefetching                           |
| 2 — Registry | DisablePagingExecutive | Registry = 1                           | Keeps kernel/drivers in RAM (never paged to SSD)        |
| 2 — Registry | LargeSystemCache OFF   | Registry = 0                           | Prioritizes app memory over file cache                  |
| 2 — Registry | IoPageLockLimit 512MB  | Registry                               | More RAM reserved for I/O operations                    |
| 3 — Endgame  | File Cache Limit       | `kernel32.SetSystemFileCacheSize`      | Caps invisible file cache to 512MB (frees 1-3 GB)       |
| 3 — Endgame  | Working Set Trim       | `psapi.EmptyWorkingSet`                | Forces idle processes to release unused RAM pages       |
| 3 — Endgame  | Standby List Purge     | `ntdll.NtSetSystemInformation`         | Clears cached memory on demand                          |

**Privilege Elevation:**

- `SeIncreaseQuotaPrivilege` enabled via `ctypes`/`advapi32` (no pywin32 dependency)
- `SeProfileSingleProcessPrivilege` for standby list purge
- Process handles opened with `PROCESS_SET_QUOTA` (0x0100) — minimal permission

---

#### `modules/smart_process_manager.py` — Smart Process Priority Manager

| Detail | Value                                                           |
| ------ | --------------------------------------------------------------- |
| Lines  | ~195                                                            |
| Role   | Background thread that auto-deprioritizes heavy background apps |

**Known Apps Auto-Lowered:**
`chrome.exe`, `msedge.exe`, `firefox.exe`, `discord.exe`, `spotify.exe`, `steam.exe`, `epicgameslauncher.exe`, `onedrive.exe`, `dropbox.exe`

---

#### `modules/standby_cleaner.py` — Standby Memory Cleaner (ISLC-style)

| Detail  | Value                                               |
| ------- | --------------------------------------------------- |
| Lines   | 231                                                 |
| Class   | `StandbyMemoryCleaner`                              |
| Backend | `ntdll.NtSetSystemInformation` (direct kernel call) |
| Pattern | Background thread with cooldown                     |

**How it works:**

- Monitors free RAM every 10s
- When free RAM < `threshold_mb` (default 3072MB), purges Windows Standby List
- Minimum 30s between cleans (prevents thrashing)
- Requires `SeProfileSingleProcessPrivilege` (auto-enabled)

**Key Methods:**
| Method | Description |
|--------|-------------|
| `start()` | Begin automatic monitoring loop |
| `stop()` | Stop monitoring |
| `clean_standby_memory()` | Manual purge, returns MB freed |
| `get_memory_info()` | Returns dict with current RAM state for dashboard |

---

### Storage

#### `modules/advanced_storage_optimizer.py` — Advanced Storage Optimizer

| Detail | Value                      |
| ------ | -------------------------- |
| Lines  | 248                        |
| Class  | `AdvancedStorageOptimizer` |

**Optimizations:**
| Tweak | Description |
|-------|-------------|
| Write Caching | Enable for all disks |
| NVMe Queue Depth | Optimize for performance |
| Large Pages | Enable system-wide |
| Pagefile Compression | Disable (save CPU) |
| Disk Timeout | Optimize I/O timeout values |
| Disk Performance | Configure for max throughput |

---

#### `modules/ntfs_optimizer.py` — NTFS Filesystem Optimizer

| Detail  | Value                 |
| ------- | --------------------- |
| Lines   | 186                   |
| Class   | `NTFSOptimizer`       |
| Backend | `fsutil behavior set` |

**Tweaks:**
| Command | Impact |
|---------|--------|
| `disable8dot3 1` | Removes legacy DOS filename creation |
| `disablelastaccess 1` | Reduces unnecessary SSD writes |
| `memoryusage 0` | Prioritize app memory over file cache |
| `encryptpagingfile 0` | Small I/O improvement |
| `mftzone 2` | 25% MFT reservation (less fragmentation) |

---

#### `modules/nvme_manager.py` — NVMe/SSD Manager

| Detail | Value         |
| ------ | ------------- |
| Lines  | 94            |
| Class  | `NVMeManager` |

**Key Methods:**
| Method | Description |
|--------|-------------|
| `apply_filesystem_optimizations()` | Disables Last Access Update |
| `apply_power_optimizations()` | Prevents disk sleep (APST lag fix) |
| `run_retrim()` | Executes `Optimize-Volume -DriveLetter C -ReTrim` |
| `start_periodic_trim()` | Background TRIM every 24h (configurable) |

---

### Network

#### `modules/network_qos.py` — Network QoS Manager

| Detail | Value               |
| ------ | ------------------- |
| Lines  | 184                 |
| Class  | `NetworkQoSManager` |

**DNS Providers:**
| Key | Name | Primary | Description |
|-----|------|---------|-------------|
| `google` | Google DNS | 8.8.8.8 | Fast & reliable |
| `adguard` | AdGuard DNS | 94.140.14.14 | Blocks ads, trackers & malware |
| `adguard_family` | AdGuard Family | 94.140.14.15 | + adult content blocking |
| `cloudflare` | Cloudflare | 1.1.1.1 | Fastest DNS |
| `cloudflare_malware` | Cloudflare Malware | 1.1.1.2 | Blocks malware |

**Optimizations:**

- Nagle algorithm disabled (`TcpAckFrequency=1`, `TCPNoDelay=1`)
- Network buffers optimized (`autotuninglevel=normal`, `rss=enabled`)
- Secure DNS auto-configured on active adapter

---

#### `modules/network_stack_optimizer.py` — Extended Network Stack

| Detail | Value                                                  |
| ------ | ------------------------------------------------------ |
| Lines  | 325                                                    |
| Class  | `NetworkStackOptimizer`                                |
| Role   | Complements `network_qos.py` with deeper TCP/IP tweaks |

**Tweaks:**
| Category | Settings |
|----------|----------|
| Congestion Control | CTCP (Compound TCP, best for Windows gaming) |
| ECN | Explicit Congestion Notification enabled |
| RSS | Receive Side Scaling across cores |
| Auto-Tuning | TCP window auto-tuning level |
| Timestamps | Disabled (reduce overhead) |
| Initial RTO | 2000ms (faster retransmit than default 3000ms) |
| SYN Retransmissions | Max 2 (fail fast on bad connections) |
| Default TTL | Optimized for better routing |
| AFD Buffers | Socket-layer buffer optimization |
| Network Throttling | Disabled during media playback |

---

### Process Management

#### `modules/process_controller.py` — Process Lasso-Style Controller

| Detail       | Value                                        |
| ------------ | -------------------------------------------- |
| Lines        | 353                                          |
| Class        | `ProcessController`                          |
| Data Classes | `ProcessRule`, `PriorityClass`, `IOPriority` |

**Features:**

- Persistent per-app CPU affinity rules (saved to JSON)
- Persistent per-app priority classes
- I/O priority control via `NtSetInformationProcess`
- Background monitoring loop (10s interval)
- Gaming preset: boost game process + throttle background

**Key Methods:**
| Method | Description |
|--------|-------------|
| `add_rule(ProcessRule)` | Register persistent optimization rule |
| `boost_process(name)` | HIGH priority + all cores + HIGH I/O |
| `throttle_background()` | BELOW_NORMAL for all non-essential processes |
| `apply_gaming_preset()` | Combined boost + throttle preset |

---

### Security & Privacy

#### `modules/security_scanner.py` — Security Scanner

| Detail  | Value                                      |
| ------- | ------------------------------------------ |
| Lines   | 568                                        |
| Class   | `SecurityScanner`                          |
| Pattern | Background thread (5-minute scan interval) |

**Scan Types:**
| Scan | What It Checks |
|------|---------------|
| Processes | Unknown executables, suspicious paths (TEMP, Public), high-CPU unknowns |
| Network | Non-standard outbound connections, unknown process connections |
| Startup | Registry Run keys, suspicious paths, recently added entries |
| Ports | Unauthorized listeners, unknown process listeners |

**Design:** Never deletes files — flags only, user decides.

---

#### `modules/telemetry_blocker.py` — Telemetry Blocker

| Detail | Value              |
| ------ | ------------------ |
| Lines  | 484                |
| Class  | `TelemetryBlocker` |

**Methods:**
| Method | Description |
|--------|-------------|
| `block_telemetry_hosts()` | Adds 40+ Microsoft domains to `hosts` file (null-routed to 0.0.0.0) |
| `apply_registry_tweaks()` | Disables `AllowTelemetry`, AdvertisingInfo, ActivityFeed, InputPersonalization |
| `harden_defender()` | Stops Defender data sharing (keeps protection active) |
| `disable_telemetry_tasks()` | Disables scheduled tasks (Appraiser, CEIP, DiskDiagnostic) |
| `apply_full_protection()` | All of the above in one call |
| `restore_hosts()` | Removes NovaPulse entries from hosts file |

---

#### `modules/defender_hardener.py` — Windows Defender Hardening

| Detail | Value              |
| ------ | ------------------ |
| Lines  | 417                |
| Class  | `DefenderHardener` |

**10-Step Hardening Process:**

1. Real-Time Protection
2. Cloud-Delivered Protection (block at first sight)
3. PUA Protection (Potentially Unwanted Apps)
4. Controlled Folder Access (Ransomware Protection)
5. Network Protection (blocks malicious URLs/IPs)
6. Attack Surface Reduction (enterprise ASR rules)
7. Exploit Protection (DEP, ASLR, CFG)
8. Windows Firewall (all profiles enabled)
9. Scan Schedules (daily quick + weekly full)
10. Tamper Protection reminder

---

### Dashboard & Monitoring

#### `modules/dashboard.py` — Rich Console Dashboard

| Detail  | Value                                                       |
| ------- | ----------------------------------------------------------- |
| Lines   | ~730                                                        |
| Class   | `Dashboard`                                                 |
| Backend | `rich.live.Live`, `rich.table`, `rich.panel`, `rich.layout` |

**Display Panels:**
| Panel | Content |
|-------|---------|
| Header | NovaPulse logo, uptime, shield status |
| CPU/GPU | CPU usage/temp/governor/frequency, GPU load/temp/clock/VRAM, thermal status |
| RAM/Storage | RAM usage/cleaned, NVMe TRIM status |
| Network | Ping, DNS provider, QoS status |
| Processes | Top processes, game detector status, auto-profiler mode |
| Security | Scanner status, threats found |
| Footer | Controls, version info |

**Anti-Flicker Implementation:**

- `screen=True` — Uses alternate screen buffer (isolates from stray prints)
- `refresh_per_second=2` — Reduced rendering frequency
- `stdout` redirected to `io.StringIO` during Live execution
- Restored in `finally` block

**Key Methods:**
| Method | Description |
|--------|-------------|
| `run(services)` | Main display loop with Live rendering |
| `update_stats(services)` | Collects all system stats from services dict |
| `make_cpu_gpu_panel()` | Builds CPU/GPU statistics table |
| `make_ram_panel()` | RAM usage and cleanup stats |

---

#### `modules/temperature_service.py` — Centralized Temperature Service

| Detail  | Value                                     |
| ------- | ----------------------------------------- |
| Lines   | 221                                       |
| Class   | `TemperatureService`                      |
| Pattern | Thread-safe singleton with TTL cache (2s) |

**Temperature Reading Methods (by priority):**

1. **OpenHardwareMonitor / LibreHardwareMonitor** (WMI, most accurate)
2. **Win32_TemperatureProbe** (WMI, some systems)
3. **ACPI MSAcpi_ThermalZoneTemperature** (WMI, DPTF/ESIF zones)
4. **NVIDIA GPU** estimate (GPU temp + 12°C for shared laptop cooling)
5. **Intel iGPU** estimate (iGPU + 5°C, same die)

---

#### `modules/history_logger.py` — History Logger

| Detail  | Value                                  |
| ------- | -------------------------------------- |
| Lines   | 113                                    |
| Class   | `HistoryLogger`                        |
| Storage | CSV files in `~/.nvme_optimizer/logs/` |

**Log Files:**
| File | Columns |
|------|---------|
| `cleanup_history.csv` | timestamp, freed_mb, trigger, ram_before_mb, ram_after_mb |
| `events.csv` | timestamp, event_type, details |

---

### System Services

#### `modules/services_optimizer.py` — Windows Services Optimizer

| Detail | Value                      |
| ------ | -------------------------- |
| Lines  | 166                        |
| Class  | `WindowsServicesOptimizer` |

**Safe-to-Disable Services:**
| Service | Description |
|---------|-------------|
| `DiagTrack` | Telemetry |
| `dmwappushservice` | WAP Push |
| `XblAuthManager` / `XblGameSave` / `XboxGipSvc` / `XboxNetApiSvc` | Xbox services |
| `WSearch` | Windows Search indexing |
| `SysMain` | Superfetch |
| `MapsBroker` | Downloaded Maps |
| `lfsvc` | Geolocation |
| `RetailDemo` | Retail Demo |
| `WMPNetworkSvc` | WMP Network |

**Estimated RAM saved:** ~15MB per disabled service

---

#### `modules/startup_manager.py` — Windows Startup Manager

| Detail | Value            |
| ------ | ---------------- |
| Lines  | 244              |
| Class  | `StartupManager` |

**Registration Method:** Windows Task Scheduler (preferred over Registry Run key)

- Runs with HIGHEST privileges (admin) automatically
- Starts at boot BEFORE user login
- Fallback: PowerShell `Register-ScheduledTask`

---

### Utilities

#### `modules/irq_optimizer.py` — IRQ Affinity Optimizer

| Detail | Value                  |
| ------ | ---------------------- |
| Lines  | 317                    |
| Class  | `IRQAffinityOptimizer` |

**Optimizations:**
| Category | Method |
|----------|--------|
| MSI Mode | Enable Message Signaled Interrupts for PCI devices |
| GPU IRQ | Dedicate GPU interrupts to high-performance cores |
| Network IRQ | Distribute network interrupts for throughput |
| Storage IRQ | Optimize NVMe/SATA controller interrupts |
| USB IRQ | Reduce USB interrupt latency |

---

#### `modules/mmcss_optimizer.py` — MMCSS Optimizer

| Detail | Value            |
| ------ | ---------------- |
| Lines  | 221              |
| Class  | `MMCSSOptimizer` |

**Tweaks:**
| Setting | Value | Impact |
|---------|-------|--------|
| SystemResponsiveness | 0 | Max priority for media threads |
| Network Throttling | Disabled | No bandwidth limiting during media |
| Games task | Priority=8, Background=false, Clock=10000 | Gaming-optimized scheduling |
| Audio task | Priority=6, Background=false | Low-latency audio |
| Pro Audio task | Priority=1, Background=false | DAW/music production |

---

#### `modules/hpet_controller.py` — HPET Timer Controller

| Detail  | Value                               |
| ------- | ----------------------------------- |
| Lines   | 316                                 |
| Class   | `HPETController`                    |
| Backend | `bcdedit` (Boot Configuration Data) |

**Timer Optimizations:**
| Method | Impact |
|--------|--------|
| `disable_hpet()` | Reduces input lag (HPET adds latency on some systems) |
| `disable_dynamic_tick()` | Forces constant tick — lower latency, more power |
| `set_tscsyncpolicy("enhanced")` | Better TSC precision for gaming |
| `disable_synthetic_timers()` | Removes Hyper-V timer overhead |
| `optimize_boot_options()` | Boot-level timing tweaks |
| `benchmark_latency()` | Measures timer latency in microseconds |
| `restore_defaults()` | Reverts all BCD timer changes |

---

#### `modules/usb_optimizer.py` — USB Polling Optimizer

| Detail  | Value                 |
| ------- | --------------------- |
| Lines   | 266                   |
| Class   | `USBPollingOptimizer` |
| Backend | Registry, `powercfg`  |

**Optimizations:**
| Method | Impact |
|--------|--------|
| `set_mouse_polling_rate(1000)` | 1ms polling (from default 8ms/125Hz) |
| `set_keyboard_polling_rate()` | Optimized keyboard repeat/delay |
| `disable_usb_selective_suspend()` | Prevents USB port sleep |
| `disable_usb_power_management()` | Disables power saving for all USB hubs |
| `optimize_usb_latency()` | General USB latency tweaks |
| `enable_msi_mode_for_usb()` | MSI interrupts for USB controllers |

---

#### `modules/tray_icon.py` — System Tray Integration

| Detail  | Value                                     |
| ------- | ----------------------------------------- |
| Lines   | 305                                       |
| Class   | `SystemTrayIcon`                          |
| Backend | `pystray`, `pillow`, Windows API (ctypes) |

**Features:**

- Minimize-to-tray (auto-hides console when minimized)
- Context menu: Show/Hide, Force Clean RAM, Force Mode, Quit
- Mini-dashboard in tooltip (CPU%, RAM%, GPU%, mode)
- Color-coded icon by mode (green=normal, orange=gaming)
- Auto-updates tooltip every 2s

---

## Configuration Reference

**File:** `config.yaml` (v2.2.1)

```yaml
# Top-level
optimization_level: gaming # safe | balanced | gaming | aggressive

# Standby Cleaner
standby_cleaner:
  threshold_mb: 3072 # Clean when < 3GB free
  check_interval_seconds: 5

# CPU Control
cpu_control:
  max_frequency_percent: 80 # Auto-Profiler adjusts dynamically
  min_frequency_percent: 5

# Auto-Profiler (2 Stages)
auto_profiler:
  active_cpu_cap: 80 # ACTIVE mode cap
  idle_cpu_cap: 20 # IDLE mode cap
  idle_timeout: 300 # 5 min to IDLE
  wake_threshold: 15 # CPU >15% = ACTIVE

# Network
network_qos:
  dns_provider: adguard # google | adguard | cloudflare | etc.


# All modules follow `enabled: true/false` pattern
```

---

## Dependencies

| Package      | Version | Purpose                                           |
| ------------ | ------- | ------------------------------------------------- |
| `psutil`     | ≥5.9    | Process/CPU/RAM monitoring                        |
| `pynvml`     | ≥11.5   | NVIDIA GPU control (via NVML)                     |
| `rich`       | ≥13.0   | Console dashboard (Live, Table, Panel, Layout)    |
| `pyyaml`     | ≥6.0    | Config file parsing                               |
| `wmi`        | ≥1.5    | Windows Management Instrumentation (temperatures) |
| `ctypes`     | stdlib  | Windows API (kernel32, ntdll, shell32)            |
| `winreg`     | stdlib  | Windows Registry access                           |
| `subprocess` | stdlib  | powercfg, sc, fsutil, netsh, PowerShell           |
| `threading`  | stdlib  | Background daemon threads                         |

---

## Build & Distribution

### PyInstaller Build

**Spec file:** `novapulse.spec`

```bash
pyinstaller novapulse.spec
# Output: dist/NovaPulse.exe (standalone, no Python required)
```

**Key spec settings:**

- `--uac-admin` — Requests admin elevation on launch
- Hidden imports: `pynvml`, `wmi`, `psutil`, `yaml`, `rich`
- Data files: `config.yaml` bundled
- Console mode: `console=True` (required for rich dashboard)

### File Structure

```
NOVA-PULSE/               ← repo root (clean)
├── README.md              # This file
├── LICENSE                # MIT License
├── .gitignore
└── src/                   ← all source code
    ├── novapulse.py        # Main entry point
    ├── diagnostic.py       # Health check tool
    ├── config.yaml         # All configuration
    ├── requirements.txt    # pip dependencies
    ├── novapulse.ico       # App icon
    └── modules/            # 32 optimization modules
        ├── dashboard.py           # Rich console UI
        ├── optimization_engine.py # Central orchestrator
        ├── auto_profiler.py       # 2-stage CPU profiler
        ├── cpu_power.py           # CPU frequency control
        ├── intel_power_control.py # Intel-specific power
        ├── advanced_cpu_optimizer.py # Registry-level CPU tweaks
        ├── core_parking.py        # CPU core parking
        ├── timer_resolution.py    # Sub-ms timer resolution
        ├── cuda_optimizer.py      # NVIDIA CUDA/GPU tweaks
        ├── gpu_scheduler.py       # HAGS + GPU scheduling + DXGI
        ├── gamebar_optimizer.py   # Xbox/Game Bar disabler
        ├── memory_optimizer.py    # RAM optimization
        ├── smart_process_manager.py # Auto priority manager
        ├── standby_cleaner.py     # Standby RAM cleaner
        ├── advanced_storage_optimizer.py # Storage tweaks
        ├── ntfs_optimizer.py      # NTFS filesystem tweaks
        ├── nvme_manager.py        # NVMe/SSD + TRIM
        ├── network_qos.py         # DNS + QoS + Nagle
        ├── network_stack_optimizer.py # TCP/IP stack tweaks
        ├── process_controller.py  # Process Lasso-style controller

        ├── security_scanner.py    # Lightweight security scanner
        ├── telemetry_blocker.py   # Microsoft telemetry blocker
        ├── defender_hardener.py   # Windows Defender hardening
        ├── services_optimizer.py  # Disable unnecessary services
        ├── startup_manager.py     # Task Scheduler auto-start
        ├── history_logger.py      # CSV operation logs
        ├── temperature_service.py # Multi-method temp reading
        ├── hpet_controller.py     # HPET timer control
        ├── usb_optimizer.py       # USB latency optimizer
        ├── tray_icon.py           # System tray integration
        ├── irq_optimizer.py       # IRQ/MSI optimization
        └── mmcss_optimizer.py     # Multimedia scheduler tweaks
```

---

## Hardware Rationale

**Target System:** Intel Core i5-11300H (Tiger Lake, 4C/8T, locked) + NVIDIA MX450/GTX 1650

| Optimization     | Why (for this hardware)                                                                                                                  |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 80% CPU cap      | i5-11300H thermal throttles at 95°C in sustained loads; 80% (~2.9GHz) keeps temps ~75°C while Turbo Boost handles short bursts to 4.4GHz |
| Core Parking OFF | Only 4 cores — sleeping any causes stuttering in multi-threaded games                                                                    |
| Timer 0.5ms      | Tiger Lake supports sub-1ms; reduces input lag from default 15.625ms                                                                     |
| CTCP congestion  | Best for Windows-to-Windows game server connections                                                                                      |
| AdGuard DNS      | Blocks ads at DNS level, reducing background network load                                                                                |
| SysMain OFF      | System has NVMe SSD — Superfetch adds no benefit, wastes RAM                                                                             |
| NTFS tweaks      | NVMe benefits from disabling last-access writes (reduces write amplification)                                                            |

---

## Safety & Risks

> **NovaPulse modifies kernel-level settings, registry keys, and boot configuration.**
> This section explains the risks, safeguards, and recommended usage.

### 🚨 Emergency Recovery (If System Becomes Unstable)

| Step | Action                                                                                     | When to Use                |
| ---- | ------------------------------------------------------------------------------------------ | -------------------------- |
| 1    | **Boot normally** — NovaPulse session-only changes (timer, priority) reset automatically   | Minor issues after reboot  |
| 2    | **Safe Mode** — Press `F8` / `Shift+Restart` → run `bcdedit /deletevalue useplatformclock` | Boot failure or time drift |
| 3    | **System Restore** — Use the restore point created before first run                        | Multiple issues at once    |

**Contact for help:** Open an [Issue](https://github.com/LucassVal/NOVA-PULSE/issues) — include `~/Desktop/NovaPulse_Diagnostic.txt` and exact error message.

---

### ⚠️ What NovaPulse Touches

| Layer                    | Examples                                         | Risk Level                                                    | Potential Symptom If Incompatible    |
| ------------------------ | ------------------------------------------------ | ------------------------------------------------------------- | ------------------------------------ |
| Boot Configuration (BCD) | HPET, Dynamic Tick, TSC sync                     | 🟠 High — requires reboot to revert                           | Boot failure, time drift, BSOD       |
| Windows Registry         | Power plans, GPU settings, NTFS behavior         | 🟡 Medium — reversible via `restore_defaults()`               | Reduced performance, driver warnings |
| System Services          | DiagTrack, SysMain, Xbox services                | 🟡 Medium — re-enabled via `services_optimizer.restore_all()` | Longer boot time, missing telemetry  |
| Hosts File               | Telemetry domains blocked                        | 🟢 Low — `telemetry_blocker.restore_hosts()`                  | Some Microsoft services unreachable  |
| Kernel APIs              | Timer resolution, memory purge, process priority | 🟢 Low — session-only, resets on reboot                       | None — auto-resets on reboot         |

---

### 🛡️ Every Optimization is Reversible

All modules implement restore/undo methods:

| Module                  | Restore Method                                           |
| ----------------------- | -------------------------------------------------------- |
| `cpu_power.py`          | `restore_defaults()` → resets to 100%/5%                 |
| `core_parking.py`       | `enable_core_parking()` → re-enables parking             |
| `hpet_controller.py`    | `restore_defaults()` → reverts all BCD timer changes     |
| `services_optimizer.py` | `restore_all()` → re-enables all disabled services       |
| `telemetry_blocker.py`  | `restore_hosts()` → removes NovaPulse entries from hosts |
| `timer_resolution.py`   | `restore()` → returns to 15.625ms default                |

---

### 🎯 Recommended Usage Flow

```
1. Run diagnostic.py         ← Verify system compatibility
2. Start with SAFE level     ← Network + memory tweaks only
3. Monitor for 24-48h        ← Check stability, temps, performance
4. Upgrade to BALANCED       ← Adds CPU + GPU optimizations
5. Upgrade to GAMING         ← Full suite (timer, core parking, HPET)
6. AGGRESSIVE (optional)     ← Services, advanced storage, deep tweaks
```

**Never jump straight to AGGRESSIVE.** Each level builds on the previous, and the `optimization_engine.py` enforces dependency order.

---

### 🖥️ Hardware Compatibility

NovaPulse is **optimized for Intel Tiger Lake + NVIDIA**, but most modules work across all Windows 10/11 systems:

| Compatibility                   | Modules                                                                                      | Notes                            |
| ------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------- |
| ✅ **Universal** (any Win10/11) | NTFS, network stack, services, telemetry, memory, security, standby cleaner, USB, IRQ, MMCSS | ~75% of all modules              |
| ✅ **Any NVIDIA GPU**           | CUDA optimizer, GPU scheduler, gamebar                                                       | Requires NVIDIA driver           |
| ⚡ **Intel-optimized**          | `intel_power_control`, `auto_profiler`                                                       | Works on Intel; no effect on AMD |
| ⚙️ **Tiger Lake tuned**         | `cpu_power` (80% cap rationale)                                                              | Cap values are hardware-specific |

> **AMD users:** NovaPulse will not break your system. Intel-specific modules simply skip when Intel hardware is not detected. All universal modules provide full benefit.

---

### 🔄 Windows Updates & NovaPulse

Windows updates may reset some optimizations. After major updates (Feature Updates):

1. Re-run `diagnostic.py` to check for changes
2. Re-apply your optimization level if needed
3. Check the [Releases](https://github.com/LucassVal/NOVA-PULSE/releases) page for NovaPulse updates addressing new Windows versions

> **Note:** Registry-based tweaks persist through updates. BCD and service changes may be reset by major Feature Updates (e.g., 23H2 → 24H2).

---

### ❓ Common Questions

**Q: Will NovaPulse work on my AMD Ryzen + NVIDIA system?**
A: Yes — all universal modules (~75%) work fully. Intel-specific modules skip themselves. NVIDIA modules work normally.

**Q: Can I use NovaPulse on a laptop?**
A: Yes, but monitor temperatures closely. The 80% CPU cap is specifically designed for laptop thermal constraints.

**Q: What if I want to uninstall NovaPulse?**
A: Run each module's restore method before removing. All changes are reversible — nothing is permanent.

**Q: Does this work with Windows 11 24H2?**
A: Yes, tested on Windows 10 22H2 and Windows 11 23H2/24H2. The `diagnostic.py` tool verifies compatibility.

**Q: Will this void my warranty?**
A: No. NovaPulse only changes software settings (registry, services, power plans). No firmware or hardware modifications are made.

---

### 🧪 Before You Start

1. **Create a System Restore Point** — `PowerShell: Checkpoint-Computer -Description "Before NovaPulse"`
2. **Run diagnostics** — `python diagnostic.py` generates a full compatibility report
3. **Read the README** — Every module documents exactly what it changes and why
4. **Start with SAFE** — Graduate to higher levels only after confirmed stability
5. **Keep NovaPulse running** — Background services (auto-profiler, standby cleaner) need to stay active to maintain optimizations

---

> **NovaPulse v2.2.1 GOLD** — Built for Intel Tiger Lake + NVIDIA mobile systems.
> All optimizations are reversible. Run `diagnostic.py` before reporting issues.
