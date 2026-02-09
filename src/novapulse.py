#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                   ⚡ NOVAPULSE 2.2.1 ⚡                                ║
║              Intelligent System Optimization                          ║
║                 Advanced Hardware Control                             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Automated optimization system with intelligent load detection.
Auto-adjusts CPU, RAM, I/O, GPU and network based on real system usage.

v2.2.1: Codebase audit, 2-stage profiler, security shield
v2.2:   Security Scanner + Telemetry Blocker + Defender Hardener
v2.0:   Optimization Engine with 13 kernel-level modules
"""
import sys
import time
import yaml
import ctypes
from colorama import init, Fore, Style

# Core Modules
from modules.standby_cleaner import StandbyMemoryCleaner
from modules.cpu_power import CPUPowerManager
from modules.smart_process_manager import SmartProcessManager
from modules.dashboard import Dashboard  # Rich console fallback
try:
    from modules.html_dashboard import HtmlDashboard
    HTML_DASHBOARD_AVAILABLE = True
except ImportError:
    HTML_DASHBOARD_AVAILABLE = False
from modules.nvme_manager import NVMeManager

# Detection Modules
from modules.temperature_service import get_service as get_temp_service

# Optimizer Modules
from modules.network_qos import NetworkQoSManager
from modules.timer_resolution import TimerResolutionOptimizer
from modules.services_optimizer import WindowsServicesOptimizer
from modules.gamebar_optimizer import GameBarOptimizer

# NovaPulse Core
from modules.auto_profiler import AutoProfiler, get_profiler, SystemMode
from modules.history_logger import get_logger as get_history_logger
from modules.tray_icon import SystemTrayIcon

# NovaPulse 2.2.1 - Optimization Engine
try:
    from modules.optimization_engine import get_engine, OptimizationLevel
    OPTIMIZATION_ENGINE_AVAILABLE = True
except ImportError:
    OPTIMIZATION_ENGINE_AVAILABLE = False

# NovaPulse 2.2.1 - Security & Privacy
try:
    from modules.telemetry_blocker import get_blocker
    from modules.security_scanner import get_scanner
    from modules.defender_hardener import get_hardener
    from modules.startup_manager import get_startup_manager
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# Initialize colorama for terminal colors
init()

# Version
VERSION = "2.2.1"
APP_NAME = "NovaPulse"


def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def load_config():
    """Load configuration from YAML file"""
    import os
    
    # Determine base path (works with PyInstaller)
    if getattr(sys, 'frozen', False):
        # Running as packaged EXE
        base_path = sys._MEIPASS
    else:
        # Running as Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_path, 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.YELLOW}[WARN] Config not found, using defaults{Style.RESET_ALL}")
        return get_default_config()


def get_default_config():
    """Returns default configuration"""
    return {
        'standby_cleaner': {
            'enabled': True,
            'threshold_mb': 3072,
            'check_interval_seconds': 5
        },
        'cpu_control': {
            'max_frequency_percent': 80,
            'min_frequency_percent': 5
        },
        'auto_profiler': {
            'enabled': True,
            'check_interval': 2,
            'active_cpu_cap': 80,
            'idle_cpu_cap': 20,
            'idle_timeout': 300,
            'wake_threshold': 15
        },
        'network_qos': {
            'enabled': True,
            'dns_provider': 'adguard'
        },

        'nvme': {
            'enabled': True
        }
    }


def print_header():
    """Imprime cabeçalho do programa"""
    print(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     {Fore.YELLOW}⚡ NOVAPULSE ⚡{Fore.CYAN}                                                 ║
║     {Fore.WHITE}Intelligent System Optimization{Fore.CYAN}                                 ║
║     {Fore.GREEN}Version {VERSION}{Fore.CYAN}                                                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")


def run_startup_diagnostic():
    """Run pre-flight diagnostic and write to Desktop log."""
    from diagnostic import run_diagnostics, LOG_FILE
    
    report = run_diagnostics()
    
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"{Fore.GREEN}[OK] Diagnostic saved: {LOG_FILE}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}[WARN] Could not save diagnostic: {e}{Style.RESET_ALL}")
    
    ok = report.count("[OK]")
    fail = report.count("[FAIL]")
    warn = report.count("[WARN]")
    return ok, fail, warn


def main():
    """Main entry point."""
    print_header()
    
    # Check administrator privileges
    if not is_admin():
        print(f"{Fore.RED}[ERROR] {APP_NAME} requires Administrator privileges!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please run as Administrator.{Style.RESET_ALL}\n")
        input("Press ENTER to exit...")
        sys.exit(1)
    
    print(f"{Fore.GREEN}[OK] Running as Administrator{Style.RESET_ALL}\n")
    
    # Run pre-flight diagnostic
    print(f"{Fore.CYAN}[DIAG] Running system diagnostic...{Style.RESET_ALL}")
    ok, fail, warn = run_startup_diagnostic()
    print(f"{Fore.CYAN}[DIAG] Result: {ok} OK, {fail} Failures, {warn} Warnings{Style.RESET_ALL}\n")
    
    # Initialize Runtime Logger (appends all events to Desktop TXT)
    from diagnostic import RuntimeLogger
    rlog = RuntimeLogger.get()
    rlog.log("BOOT", "novapulse", f"NovaPulse {VERSION} starting (diag: {ok} OK, {fail} fail, {warn} warn)")
    
    # Load configuration
    print(f"{Fore.CYAN}[INFO] Loading configuration...{Style.RESET_ALL}")
    config = load_config()
    rlog.log("BOOT", "config", f"Configuration loaded from config.yaml")
    
    # === NOVAPULSE 2.2.1: OPTIMIZATION ENGINE ===
    if OPTIMIZATION_ENGINE_AVAILABLE:
        opt_level_str = config.get('optimization_level', 'gaming')
        level_map = {
            'safe': OptimizationLevel.SAFE,
            'balanced': OptimizationLevel.BALANCED,
            'gaming': OptimizationLevel.GAMING,
            'aggressive': OptimizationLevel.AGGRESSIVE
        }
        opt_level = level_map.get(opt_level_str, OptimizationLevel.GAMING)
        
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}NovaPulse 2.2.1 - Advanced Optimizations{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
        
        try:
            engine = get_engine()
            engine.apply_all(opt_level)
            rlog.log_optimization("optimization_engine", f"Applied level: {opt_level_str.upper()}")
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Optimization Engine: {e}{Style.RESET_ALL}")
            rlog.log_error("optimization_engine", str(e))
    
    # Initialize services
    services = {}
    
    # === STANDBY MEMORY CLEANER ===
    if config.get('standby_cleaner', {}).get('enabled', True):
        cleaner_config = config['standby_cleaner']
        threshold = cleaner_config.get('threshold_mb', 4096)
        interval = cleaner_config.get('check_interval_seconds', 5)
        services['cleaner'] = StandbyMemoryCleaner(
            threshold_mb=threshold,
            check_interval=interval
        )
        services['cleaner'].start()
        rlog.log("MODULE", "standby_cleaner", f"Started (threshold={threshold}MB, interval={interval}s)")
    
    # === SMART PROCESS MANAGER ===
    services['smart_priority'] = SmartProcessManager()
    services['smart_priority'].start()
    print(f"{Fore.GREEN}[OK] Smart Process Priority active{Style.RESET_ALL}")
    rlog.log("MODULE", "smart_process_manager", "Started — auto priority management active")
    
    # === CPU POWER MANAGER ===
    services['cpu_power'] = CPUPowerManager()
    
    cpu_config = config.get('cpu_control', {})
    max_freq = cpu_config.get('max_frequency_percent', 80)
    min_freq = cpu_config.get('min_frequency_percent', 5)
    
    if max_freq != 100:
        services['cpu_power'].set_max_cpu_frequency(max_freq)
    
    if min_freq != 5:
        services['cpu_power'].set_min_cpu_frequency(min_freq)
    
    rlog.log_optimization("cpu_power", f"Governor set: max={max_freq}%, min={min_freq}%")
    
    # === NVMe/SSD OPTIMIZER ===
    nvme_config = config.get('nvme', {'enabled': True})
    if nvme_config.get('enabled', True):
        nvme_mgr = NVMeManager(nvme_config)
        
        if nvme_config.get('disable_last_access', True):
            nvme_mgr.apply_filesystem_optimizations()
            rlog.log_optimization("nvme_manager", "NTFS last-access disabled")
            
        if nvme_config.get('prevent_disk_sleep', True):
            nvme_mgr.apply_power_optimizations()
            
        if nvme_config.get('periodic_trim', True):
            nvme_mgr.start_periodic_trim()
            services['nvme'] = nvme_mgr

    # === NETWORK QoS ===
    qos_config = config.get('network_qos', {'enabled': True})
    if qos_config.get('enabled', True):
        print(f"\n{Fore.CYAN}[NET] Configuring Network QoS...{Style.RESET_ALL}")
        qos_mgr = NetworkQoSManager(qos_config)
        if qos_mgr.apply_qos_rules():
            services['network_qos'] = qos_mgr
            rlog.log_optimization("network_qos", "QoS rules applied (Nagle OFF, AdGuard DNS)")
    
    
    # === HISTORY LOGGER ===
    history = get_history_logger()
    history.log_event("novapulse_start", f"NovaPulse {VERSION} Initialized")
    services['history'] = history
    
    # === TIMER RESOLUTION ===
    print(f"\n{Fore.CYAN}[OPT] Applying advanced optimizations...{Style.RESET_ALL}")
    timer_opt = TimerResolutionOptimizer()
    if timer_opt.apply_optimization():
        timer_opt.start_persistent()
        services['timer'] = timer_opt
        rlog.log_optimization("timer_resolution", "Set to 0.5ms (persistent)")
    
    # === GAME BAR DISABLER ===
    gamebar_opt = GameBarOptimizer()
    gamebar_opt.apply_all_optimizations()
    services['gamebar'] = gamebar_opt
    rlog.log_optimization("gamebar_optimizer", "Game Bar, Game DVR, Game Mode disabled")
    
    # === WINDOWS SERVICES OPTIMIZER ===
    services_opt = WindowsServicesOptimizer()
    services_opt.optimize()
    services['services_opt'] = services_opt
    rlog.log_optimization("services_optimizer", "Disabled DiagTrack, SysMain, Xbox services")

    # === NOVAPULSE 2.2.1: SECURITY & PRIVACY ===
    if SECURITY_AVAILABLE:
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}NovaPulse 2.2.1 - Security & Privacy Shield{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
        
        # Telemetry Blocker (blocks Microsoft data collection)
        try:
            blocker = get_blocker()
            blocker.apply_full_protection()
            services['telemetry_blocker'] = blocker
            rlog.log("SECURITY", "telemetry_blocker", "Full telemetry protection applied")
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Telemetry Blocker: {e}{Style.RESET_ALL}")
            rlog.log_error("telemetry_blocker", str(e))
        
        # Security Scanner (process/network/startup/port monitoring)
        try:
            scanner = get_scanner()
            scanner.start_background_scan(interval_seconds=300)  # Scan every 5 min
            services['security_scanner'] = scanner
            print(f"{Fore.GREEN}[OK] Security Scanner active (5 min interval){Style.RESET_ALL}")
            rlog.log("SECURITY", "security_scanner", "Background scan started (5 min interval)")
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Security Scanner: {e}{Style.RESET_ALL}")
            rlog.log_error("security_scanner", str(e))

        # Defender Hardening (enables all advanced Defender features)
        try:
            hardener = get_hardener()
            hardener.harden_all()
            services['defender_hardener'] = hardener
            rlog.log("SECURITY", "defender_hardener", "All advanced Defender features enabled")
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Defender Hardener: {e}{Style.RESET_ALL}")
            rlog.log_error("defender_hardener", str(e))

        # Startup Registration (Task Scheduler at boot)
        try:
            startup = get_startup_manager()
            if not startup.is_registered():
                startup.register()
                rlog.log("MODULE", "startup_manager", "Auto-start registered via Task Scheduler")
            else:
                print(f"{Fore.GREEN}[OK] Auto-start already registered{Style.RESET_ALL}")
                rlog.log("MODULE", "startup_manager", "Auto-start already registered")
            services['startup_manager'] = startup
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Startup Manager: {e}{Style.RESET_ALL}")
            rlog.log_error("startup_manager", str(e))

    # === AUTO-PROFILER (NOVAPULSE CORE) ===
    profiler_config = config.get('auto_profiler', {})
    if profiler_config.get('enabled', True):
        profiler = get_profiler()
        profiler.config = profiler_config
        profiler.active_cpu_cap = profiler_config.get('active_cpu_cap', 80)
        profiler.idle_cpu_cap = profiler_config.get('idle_cpu_cap', 20)
        profiler.idle_timeout = profiler_config.get('idle_timeout', 300)
        profiler.check_interval = profiler_config.get('check_interval', 2)
        profiler.set_services(services)
        profiler.start()
        services['auto_profiler'] = profiler
        print(f"{Fore.GREEN}[OK] Auto-Profiler v2.2 (ACTIVE {profiler.active_cpu_cap}% / IDLE {profiler.idle_cpu_cap}% after {profiler.idle_timeout}s){Style.RESET_ALL}")
        rlog.log("MODULE", "auto_profiler", f"Started (active={profiler.active_cpu_cap}%, idle={profiler.idle_cpu_cap}%, timeout={profiler.idle_timeout}s)")

    print(f"\n{Fore.GREEN}[OK] All NovaPulse services started{Style.RESET_ALL}")
    rlog.log("BOOT", "novapulse", f"All services started ({len(services)} active)")
    
    time.sleep(1)
    
    # === SYSTEM TRAY ===
    tray = None
    try:
        tray = SystemTrayIcon(optimizer_services=services)
        if tray.start():
            services['tray'] = tray
            rlog.log("MODULE", "tray_icon", "System tray icon active")
    except:
        pass
    
    # === DASHBOARD ===
    try:
        if HTML_DASHBOARD_AVAILABLE:
            print(f"\n{Fore.CYAN}Starting HTML Dashboard (pywebview)...{Style.RESET_ALL}\n")
            rlog.log("MODULE", "dashboard", "HTML glassmorphism dashboard starting")
            html_dash = HtmlDashboard(services)
            if not html_dash.start():
                # Fallback to Rich console if HTML dashboard fails
                print(f"{Fore.YELLOW}[WARN] HTML dashboard failed, falling back to console...{Style.RESET_ALL}")
                rlog.log("WARN", "dashboard", "HTML dashboard failed, using Rich fallback")
                dashboard = Dashboard()
                dashboard.run(services)
        else:
            print(f"\n{Fore.CYAN}Starting Console Dashboard...{Style.RESET_ALL}\n")
            rlog.log("MODULE", "dashboard", "Rich console dashboard starting (pywebview not available)")
            dashboard = Dashboard()
            dashboard.run(services)
            
    except KeyboardInterrupt:
        rlog.log("SHUTDOWN", "dashboard", "User pressed Ctrl+C")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Dashboard: {e}{Style.RESET_ALL}")
        rlog.log_error("dashboard", str(e))
    
    # Cleanup
    print(f"\n{Fore.YELLOW}[INFO] Stopping services...{Style.RESET_ALL}")
    rlog.log("SHUTDOWN", "novapulse", "Stopping all services...")
    stop_all_services(services)
    
    # Write session summary to Desktop log
    rlog.write_summary({
        'Services active': len(services),
        'Version': VERSION,
    })
    
    print(f"{Fore.GREEN}[OK] NovaPulse stopped{Style.RESET_ALL}\n")


def stop_all_services(services):
    """Stop all running services cleanly."""
    if 'cleaner' in services:
        services['cleaner'].stop()
    if 'smart_priority' in services:
        services['smart_priority'].stop()
    if 'auto_profiler' in services:
        services['auto_profiler'].stop()

    if 'security_scanner' in services:
        services['security_scanner'].stop()
    if 'tray' in services:
        try:
            services['tray'].stop()
        except:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n{Fore.RED}═══ FATAL ERROR ═══{Style.RESET_ALL}")
        print(f"{Fore.RED}An unhandled exception occurred:{Style.RESET_ALL}")
        traceback.print_exc()
        print(f"\n{Fore.YELLOW}Please report this error.{Style.RESET_ALL}")
        input(f"\n{Fore.WHITE}Press ENTER to exit...{Style.RESET_ALL}")

