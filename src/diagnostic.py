"""
NovaPulse System Diagnostic & Runtime Logger v2.0
Comprehensive system audit + persistent runtime event logging.
All output is in English. Generates Desktop TXT with full session history.

Usage:
  Pre-flight:  python diagnostic.py          (runs full system check)
  Runtime:     from diagnostic import RuntimeLogger
               logger = RuntimeLogger.get()
               logger.log("MODULE_INIT", "cpu_power", "CPUPowerManager started, cap=80%")
"""
import sys
import os
import datetime
import platform
import ctypes
import subprocess
import threading
from pathlib import Path

# NovaPulse module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Desktop log path
DESKTOP = Path(os.environ.get('USERPROFILE', Path.home())) / 'Desktop'
LOG_FILE = DESKTOP / 'NovaPulse_Diagnostic.txt'


# ============================================================
# PART 1: RUNTIME LOGGER (used by all modules during execution)
# ============================================================

class RuntimeLogger:
    """Singleton logger that appends timestamped events to Desktop TXT.
    
    Categories:
      BOOT       — NovaPulse startup sequence
      MODULE     — Module initialization / configuration
      OPTIMIZE   — Optimization applied (registry, BCD, service, etc.)
      MONITOR    — Runtime monitoring event (temp, RAM, profiler switch)
      SECURITY   — Security scanner / telemetry blocker / defender
      CLEANUP    — RAM cleanup / standby list purge
      NETWORK    — DNS, QoS, ping changes
      WARNING    — Non-critical issue
      ERROR      — Critical failure
      SHUTDOWN   — Service stop / cleanup
    """
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._log_path = LOG_FILE
        self._entries = []
        self._file_lock = threading.Lock()
        
        # Write session header
        self._write_header()
    
    @classmethod
    def get(cls):
        """Return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = RuntimeLogger()
        return cls._instance
    
    def _write_header(self):
        """Write session start header to log file."""
        now = datetime.datetime.now()
        header = [
            "",
            "=" * 70,
            f"  NOVAPULSE SESSION — {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
        ]
        with self._file_lock:
            with open(self._log_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(header) + '\n')
    
    def log(self, category: str, source: str, message: str):
        """Log a timestamped event.
        
        Args:
            category: Event category (BOOT, MODULE, OPTIMIZE, etc.)
            source:   Module or component name
            message:  Human-readable description of what happened
        """
        now = datetime.datetime.now().strftime('%H:%M:%S')
        entry = f"[{now}] [{category:8s}] {source}: {message}"
        self._entries.append(entry)
        
        with self._file_lock:
            try:
                with open(self._log_path, 'a', encoding='utf-8') as f:
                    f.write(entry + '\n')
            except Exception:
                pass  # Never crash the optimizer for a log failure
    
    def log_optimization(self, module: str, action: str, detail: str = ""):
        """Shorthand for logging an optimization action."""
        msg = action
        if detail:
            msg += f" — {detail}"
        self.log("OPTIMIZE", module, msg)
    
    def log_error(self, source: str, error: str):
        """Shorthand for logging an error."""
        self.log("ERROR", source, error)
    
    def log_warning(self, source: str, message: str):
        """Shorthand for logging a warning."""
        self.log("WARNING", source, message)
    
    def get_entries(self):
        """Return all logged entries for this session."""
        return list(self._entries)
    
    def write_summary(self, stats: dict = None):
        """Write session summary footer."""
        now = datetime.datetime.now().strftime('%H:%M:%S')
        lines = [
            "",
            "-" * 70,
            f"  SESSION SUMMARY at {now}",
            "-" * 70,
            f"  Total events logged: {len(self._entries)}",
        ]
        if stats:
            for key, value in stats.items():
                lines.append(f"  {key}: {value}")
        lines.append("-" * 70)
        lines.append("")
        
        with self._file_lock:
            with open(self._log_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')


# ============================================================
# PART 2: PRE-FLIGHT DIAGNOSTIC (system compatibility check)
# ============================================================

def check_feature(name, check_func):
    """Execute a check and return formatted result."""
    try:
        result = check_func()
        if result:
            return f"[OK]   {name}"
        else:
            return f"[FAIL] {name} — Not available"
    except Exception as e:
        return f"[FAIL] {name} — Error: {str(e)[:60]}"


def run_diagnostics():
    """Run full system diagnostic and return report string."""
    results = []
    results.append("=" * 70)
    results.append("  NOVAPULSE SYSTEM DIAGNOSTIC v2.0")
    results.append(f"  Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append(f"  OS:   {platform.system()} {platform.version()}")
    results.append(f"  Arch: {platform.machine()}")
    results.append("=" * 70)
    results.append("")
    
    # === PYTHON DEPENDENCIES ===
    results.append("PYTHON DEPENDENCIES")
    results.append("-" * 40)
    
    deps = [
        ("psutil", "System Monitoring"),
        ("wmi", "Windows Management"),
        ("yaml", "Configuration (PyYAML)"),
        ("colorama", "Terminal Colors"),
        ("rich", "Visual Dashboard"),
        ("pystray", "System Tray"),
        ("PIL", "Image Support (Pillow)"),
    ]
    
    for module, desc in deps:
        results.append(check_feature(f"{desc} ({module})",
            lambda m=module: __import__(m) is not None))
    
    # NVIDIA special check
    def check_nvidia():
        import pynvml
        pynvml.nvmlInit()
        return pynvml.nvmlDeviceGetCount() > 0
    results.append(check_feature("NVIDIA GPU (pynvml)", check_nvidia))
    
    results.append("")
    
    # === NOVAPULSE MODULES ===
    results.append("NOVAPULSE MODULES")
    results.append("-" * 40)
    
    modules = [
        # Core Engine
        ("optimization_engine", "Optimization Engine"),
        ("auto_profiler", "Auto-Profiler (2-Stage Load Detection)"),
        ("dashboard", "Rich Console Dashboard"),
        ("tray_icon", "System Tray Icon"),
        ("history_logger", "History Logger"),
        # CPU
        ("cpu_power", "CPU Power Manager"),
        ("core_parking", "Core Parking Controller"),
        ("advanced_cpu_optimizer", "Advanced CPU Optimizer (C-States, Turbo)"),
        # Memory
        ("memory_optimizer", "Memory Optimizer"),
        ("standby_cleaner", "Standby Memory Cleaner"),
        # GPU
        ("gpu_scheduler", "GPU Scheduler"),
        ("cuda_optimizer", "CUDA & GPU Advanced Optimizer"),
        # Storage
        ("nvme_manager", "NVMe/SSD Manager"),
        ("ntfs_optimizer", "NTFS Optimizer"),
        ("advanced_storage_optimizer", "Advanced Storage Optimizer"),
        # Network
        ("network_qos", "Network QoS Manager"),
        ("network_stack_optimizer", "Network Stack Optimizer (Extended)"),
        # Timers & IRQ
        ("timer_resolution", "Timer Resolution Optimizer"),
        ("hpet_controller", "HPET/Timer Controller"),
        ("irq_optimizer", "IRQ Affinity Optimizer"),
        ("mmcss_optimizer", "MMCSS Gaming Optimizer"),
        # Process Management
        ("smart_process_manager", "Smart Process Manager"),
        ("process_controller", "Process Controller (Lasso Style)"),
        ("services_optimizer", "Windows Services Optimizer"),
        ("startup_manager", "Startup Manager"),
        # Hardware
        ("temperature_service", "Temperature Service"),
        ("intel_power_control", "Intel Power Control"),
        ("usb_optimizer", "USB Power Optimizer"),
        ("gamebar_optimizer", "Game Bar Optimizer"),
        # Security
        ("telemetry_blocker", "Telemetry Blocker"),
        ("security_scanner", "Security Scanner"),
        ("defender_hardener", "Defender Hardener"),
    ]
    
    for module_name, display_name in modules:
        results.append(check_feature(display_name,
            lambda m=module_name: __import__(f'modules.{m}', fromlist=[m]) is not None))
    
    results.append("")
    
    # === HARDWARE ===
    results.append("HARDWARE DETECTED")
    results.append("-" * 40)
    
    # CPU
    try:
        import psutil
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        freq_str = f"{cpu_freq.max:.0f}MHz" if cpu_freq else "N/A"
        results.append(f"[OK]   CPU: {cpu_count} cores @ {freq_str}")
    except Exception as e:
        results.append(f"[FAIL] CPU: {e}")
    
    # RAM
    try:
        mem = psutil.virtual_memory()
        ram_gb = mem.total / (1024**3)
        results.append(f"[OK]   RAM: {ram_gb:.1f} GB")
    except:
        results.append("[FAIL] RAM: Could not detect")
    
    # GPU NVIDIA
    try:
        import pynvml
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        if count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            results.append(f"[OK]   GPU NVIDIA: {name}")
        else:
            results.append("[FAIL] GPU NVIDIA: Not detected")
    except:
        results.append("[FAIL] GPU NVIDIA: Not available")
    
    # GPU Intel
    try:
        import wmi
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            if 'intel' in gpu.Name.lower():
                results.append(f"[OK]   GPU Intel: {gpu.Name}")
                break
    except:
        pass
    
    # Disk
    try:
        import psutil
        for part in psutil.disk_partitions():
            if 'fixed' in part.opts.lower() or part.fstype:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = usage.total / (1024**3)
                free_gb = usage.free / (1024**3)
                results.append(f"[OK]   Disk {part.mountpoint} {part.fstype}: {total_gb:.0f}GB total, {free_gb:.0f}GB free")
    except:
        pass
    
    results.append("")
    
    # === SYSTEM CAPABILITIES ===
    results.append("SYSTEM CAPABILITIES")
    results.append("-" * 40)
    
    # Admin
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    results.append(f"[{'OK' if is_admin else 'FAIL'}]   Administrator Privileges")
    
    # CPU Temperature
    try:
        from modules.temperature_service import get_service
        temp_svc = get_service()
        temp = temp_svc.get_cpu_temp()
        if temp > 0:
            results.append(f"[OK]   CPU Temperature Reading: {temp:.1f}C")
        else:
            results.append("[WARN] CPU Temperature: Not available (use LibreHardwareMonitor)")
    except Exception as e:
        results.append(f"[FAIL] CPU Temperature: {e}")
    
    # NtSetSystemInformation (RAM Cleaner kernel API)
    try:
        ntdll = ctypes.WinDLL('ntdll')
        if hasattr(ntdll, 'NtSetSystemInformation'):
            results.append("[OK]   RAM Cleanup API (ntdll.NtSetSystemInformation)")
        else:
            results.append("[FAIL] RAM Cleanup API")
    except:
        results.append("[FAIL] RAM Cleanup API")
    
    # Timer Resolution
    try:
        ntdll = ctypes.WinDLL('ntdll')
        if hasattr(ntdll, 'NtSetTimerResolution'):
            results.append("[OK]   Timer Resolution API (ntdll.NtSetTimerResolution)")
        else:
            results.append("[FAIL] Timer Resolution API")
    except:
        results.append("[FAIL] Timer Resolution API")
    
    # PowerCfg
    try:
        result = subprocess.run(['powercfg', '/l'], capture_output=True, timeout=5)
        if result.returncode == 0:
            results.append("[OK]   PowerCfg (CPU Power Control)")
        else:
            results.append("[FAIL] PowerCfg")
    except:
        results.append("[FAIL] PowerCfg")
    
    # BCDEdit (boot config)
    try:
        result = subprocess.run(['bcdedit', '/enum'], capture_output=True, timeout=5)
        if result.returncode == 0:
            results.append("[OK]   BCDEdit (Boot Configuration)")
        else:
            results.append("[FAIL] BCDEdit (requires admin)")
    except:
        results.append("[FAIL] BCDEdit")
    
    # Network Adapter
    try:
        cmd = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1 -ExpandProperty Name'
        result = subprocess.run(['powershell', '-Command', cmd],
                               capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            results.append(f"[OK]   Network Adapter: {result.stdout.strip()}")
        else:
            results.append("[FAIL] Network Adapter: Not found")
    except:
        results.append("[WARN] Network Adapter: Not checked")
    
    # Hosts file writable
    hosts = Path(r"C:\Windows\System32\drivers\etc\hosts")
    try:
        if hosts.exists() and os.access(str(hosts), os.W_OK):
            results.append("[OK]   Hosts File: Writable (telemetry blocking ready)")
        else:
            results.append("[WARN] Hosts File: Read-only (run as admin for telemetry blocking)")
    except:
        results.append("[WARN] Hosts File: Cannot check")
    
    results.append("")
    
    # === SUMMARY ===
    results.append("=" * 70)
    ok_count = sum(1 for r in results if "[OK]" in r)
    fail_count = sum(1 for r in results if "[FAIL]" in r)
    warn_count = sum(1 for r in results if "[WARN]" in r)
    
    results.append(f"  SUMMARY: {ok_count} OK | {fail_count} Failures | {warn_count} Warnings")
    results.append("=" * 70)
    
    if fail_count == 0:
        results.append("  System fully compatible with NovaPulse!")
    elif fail_count <= 3:
        results.append("  Some features may be limited. Check failures above.")
    else:
        results.append("  Multiple features unavailable. Run as Administrator.")
    
    results.append("")
    results.append("  Generated by NovaPulse Diagnostic v2.0")
    results.append(f"  Log file: {LOG_FILE}")
    results.append("")
    
    return "\n".join(results)


if __name__ == "__main__":
    print("Running NovaPulse System Diagnostic...\n")
    
    report = run_diagnostics()
    
    # Save to Desktop
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\nReport saved to: {LOG_FILE}")
    
    input("\nPress ENTER to close...")
