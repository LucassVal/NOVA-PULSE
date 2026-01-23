#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    ⚡ NOVAPULSE 2.0 ⚡                                 ║
║              Intelligent System Optimization                          ║
║                 Advanced Hardware Control                             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Sistema automatizado de otimização com detecção inteligente de carga.
Auto-ajusta CPU, RAM, I/O, GPU e rede baseado no uso real do sistema.

Novidades 2.0:
- Core Parking Control
- Memory Optimization Pro
- HPET/Timer Control
- GPU Scheduler (HAGS)
- IRQ Affinity Optimizer
- Network Stack Optimizer
- Process Controller (Process Lasso Style)
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
from modules.dashboard import Dashboard
from modules.nvme_manager import NVMeManager

# Detection Modules
from modules.game_detector import GameModeDetector
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

# NovaPulse 2.0 - Advanced Optimizations
try:
    from modules.optimization_engine import get_engine, OptimizationLevel
    OPTIMIZATION_ENGINE_AVAILABLE = True
except ImportError:
    OPTIMIZATION_ENGINE_AVAILABLE = False

# Inicializa colorama para cores no terminal
init()

# Versão
VERSION = "2.0"
APP_NAME = "NovaPulse"


def is_admin():
    """Verifica se está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def load_config():
    """Carrega configuração do arquivo YAML"""
    import os
    
    # Determina o caminho base (funciona com PyInstaller)
    if getattr(sys, 'frozen', False):
        # Rodando como EXE empacotado
        base_path = sys._MEIPASS
    else:
        # Rodando como script Python
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_path, 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.YELLOW}[WARN] Config não encontrado, usando padrões{Style.RESET_ALL}")
        return get_default_config()


def get_default_config():
    """Retorna configuração padrão"""
    return {
        'standby_cleaner': {
            'enabled': True,
            'threshold_mb': 4096,
            'check_interval_seconds': 5
        },
        'cpu_control': {
            'max_frequency_percent': 85,
            'min_frequency_percent': 5
        },
        'auto_profiler': {
            'enabled': True,
            'check_interval': 2,
            'boost_threshold': 85,
            'eco_threshold': 30,
            'boost_hold_time': 2,
            'eco_hold_time': 5
        },
        'network_qos': {
            'enabled': True,
            'dns_provider': 'adguard'
        },
        'game_detector': {
            'enabled': True
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
    """Executa diagnóstico e salva log na área de trabalho"""
    import os
    import datetime
    import psutil
    
    results = []
    results.append("=" * 60)
    results.append("⚡ NOVAPULSE SYSTEM DIAGNOSTIC")
    results.append(f"📅 Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("=" * 60)
    results.append("")
    
    def check(name, func):
        try:
            if func():
                return f"[✓] {name}"
            return f"[✗] {name}"
        except Exception as e:
            return f"[✗] {name} - {str(e)[:40]}"
    
    # Dependências
    results.append("📦 DEPENDÊNCIAS")
    results.append("-" * 40)
    results.append(check("psutil", lambda: True))
    results.append(check("wmi", lambda: __import__('wmi') is not None))
    results.append(check("pynvml (NVIDIA)", lambda: __import__('pynvml').nvmlInit() or True))
    results.append(check("pystray", lambda: __import__('pystray') is not None))
    results.append(check("rich", lambda: __import__('rich') is not None))
    results.append("")
    
    # Módulos
    results.append("🔧 MÓDULOS NOVAPULSE")
    results.append("-" * 40)
    modules = ['auto_profiler', 'standby_cleaner', 'cpu_power', 'smart_process_manager',
               'dashboard', 'tray_icon', 'game_detector', 'network_qos', 'timer_resolution']
    for m in modules:
        results.append(check(m, lambda mod=m: __import__(f'modules.{mod}', fromlist=[mod]) is not None))
    results.append("")
    
    # Hardware
    results.append("🖥️ HARDWARE")
    results.append("-" * 40)
    results.append(f"[✓] CPU: {psutil.cpu_count()} cores")
    results.append(f"[✓] RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(h)
        if isinstance(name, bytes): name = name.decode()
        results.append(f"[✓] GPU: {name}")
    except:
        results.append("[⚠] GPU NVIDIA: Não detectada")
    results.append("")
    
    # Funcionalidades
    results.append("⚙️ FUNCIONALIDADES")
    results.append("-" * 40)
    results.append(check("Privilégios Admin", is_admin))
    results.append(check("API ntdll", lambda: hasattr(ctypes.WinDLL('ntdll'), 'NtSetSystemInformation')))
    results.append(check("PowerCfg", lambda: os.system('powercfg /? >nul 2>&1') == 0))
    
    try:
        from modules.temperature_service import get_service
        temp = get_service().get_cpu_temp()
        if temp > 0:
            results.append(f"[✓] Temperatura CPU: {temp:.0f}°C")
        else:
            results.append("[⚠] Temperatura CPU: Usar LibreHardwareMonitor")
    except:
        results.append("[⚠] Temperatura CPU: Não disponível")
    results.append("")
    
    # Resumo
    ok = sum(1 for r in results if "[✓]" in r)
    fail = sum(1 for r in results if "[✗]" in r)
    warn = sum(1 for r in results if "[⚠]" in r)
    results.append("=" * 60)
    results.append(f"📊 RESUMO: {ok} OK | {fail} Falhas | {warn} Avisos")
    results.append("=" * 60)
    
    # Salva
    desktop = os.path.join(os.environ.get('USERPROFILE', '.'), 'Desktop')
    log_path = os.path.join(desktop, 'NovaPulse_Diagnostic.txt')
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(results))
        print(f"{Fore.GREEN}✓ Diagnóstico salvo: {log_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}[WARN] Não foi possível salvar diagnóstico: {e}{Style.RESET_ALL}")
    
    return ok, fail, warn


def main():
    """Função principal"""
    print_header()
    
    # Verifica privilégios de administrador
    if not is_admin():
        print(f"{Fore.RED}[ERRO] {APP_NAME} requer privilégios de Administrador!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Por favor, execute como administrador.{Style.RESET_ALL}\n")
        input("Pressione ENTER para sair...")
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ Rodando como Administrador{Style.RESET_ALL}\n")
    
    # Executa diagnóstico e gera log
    print(f"{Fore.CYAN}[DIAG] Executando diagnóstico do sistema...{Style.RESET_ALL}")
    ok, fail, warn = run_startup_diagnostic()
    print(f"{Fore.CYAN}[DIAG] Resultado: {ok} OK, {fail} Falhas, {warn} Avisos{Style.RESET_ALL}\n")
    
    # Carrega configuração
    print(f"{Fore.CYAN}[INFO] Carregando configuração...{Style.RESET_ALL}")
    config = load_config()
    
    # === NOVAPULSE 2.0: OPTIMIZATION ENGINE ===
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
        print(f"{Fore.MAGENTA}⚡ NovaPulse 2.0 - Advanced Optimizations{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
        
        try:
            engine = get_engine()
            engine.apply_all(opt_level)
        except Exception as e:
            print(f"{Fore.YELLOW}[WARN] Optimization Engine: {e}{Style.RESET_ALL}")
    
    # Inicializa serviços
    services = {}
    
    # === STANDBY MEMORY CLEANER ===
    if config.get('standby_cleaner', {}).get('enabled', True):
        cleaner_config = config['standby_cleaner']
        services['cleaner'] = StandbyMemoryCleaner(
            threshold_mb=cleaner_config.get('threshold_mb', 4096),
            check_interval=cleaner_config.get('check_interval_seconds', 5)
        )
        services['cleaner'].start()
    
    # === SMART PROCESS MANAGER ===
    services['smart_priority'] = SmartProcessManager()
    services['smart_priority'].start()
    print(f"{Fore.GREEN}✓ Priorização inteligente ativada{Style.RESET_ALL}")
    
    # === CPU POWER MANAGER ===
    services['cpu_power'] = CPUPowerManager()
    
    cpu_config = config.get('cpu_control', {})
    max_freq = cpu_config.get('max_frequency_percent', 85)
    min_freq = cpu_config.get('min_frequency_percent', 5)
    
    if max_freq != 100:
        services['cpu_power'].set_max_cpu_frequency(max_freq)
    
    if min_freq != 5:
        services['cpu_power'].set_min_cpu_frequency(min_freq)
    
    # === NVMe/SSD OPTIMIZER ===
    nvme_config = config.get('nvme', {'enabled': True})
    if nvme_config.get('enabled', True):
        nvme_mgr = NVMeManager(nvme_config)
        
        if nvme_config.get('disable_last_access', True):
            nvme_mgr.apply_filesystem_optimizations()
            
        if nvme_config.get('prevent_disk_sleep', True):
            nvme_mgr.apply_power_optimizations()
            
        if nvme_config.get('periodic_trim', True):
            nvme_mgr.start_periodic_trim()
            services['nvme'] = nvme_mgr

    # === NETWORK QoS ===
    qos_config = config.get('network_qos', {'enabled': True})
    if qos_config.get('enabled', True):
        print(f"\n{Fore.CYAN}[NET] Configurando Network QoS...{Style.RESET_ALL}")
        qos_mgr = NetworkQoSManager(qos_config)
        if qos_mgr.apply_qos_rules():
            services['network_qos'] = qos_mgr
    
    # === GAME MODE DETECTOR ===
    game_config = config.get('game_detector', {'enabled': True})
    if game_config.get('enabled', True):
        game_detector = GameModeDetector(optimizer_services=services, config=game_config)
        game_detector.start()
        services['game_detector'] = game_detector
        print(f"{Fore.GREEN}✓ Game Mode Detector ativado{Style.RESET_ALL}")
    
    # === HISTORY LOGGER ===
    history = get_history_logger()
    history.log_event("novapulse_start", f"NovaPulse {VERSION} Initialized")
    services['history'] = history
    
    # === TIMER RESOLUTION ===
    print(f"\n{Fore.CYAN}[OPT] Aplicando otimizações avançadas...{Style.RESET_ALL}")
    timer_opt = TimerResolutionOptimizer()
    if timer_opt.apply_optimization():
        timer_opt.start_persistent()
        services['timer'] = timer_opt
    
    # === GAME BAR DISABLER ===
    gamebar_opt = GameBarOptimizer()
    gamebar_opt.apply_all_optimizations()
    services['gamebar'] = gamebar_opt
    
    # === WINDOWS SERVICES OPTIMIZER ===
    services_opt = WindowsServicesOptimizer()
    services_opt.optimize()
    services['services_opt'] = services_opt

    # === AUTO-PROFILER (NOVAPULSE CORE) ===
    profiler_config = config.get('auto_profiler', {})
    if profiler_config.get('enabled', True):
        profiler = get_profiler()
        profiler.config = profiler_config
        profiler.boost_threshold = profiler_config.get('boost_threshold', 85)
        profiler.eco_threshold = profiler_config.get('eco_threshold', 30)
        profiler.check_interval = profiler_config.get('check_interval', 2)
        profiler.boost_hold_time = profiler_config.get('boost_hold_time', 2)
        profiler.eco_hold_time = profiler_config.get('eco_hold_time', 5)
        profiler.set_services(services)
        profiler.start()
        services['auto_profiler'] = profiler
        print(f"{Fore.GREEN}✓ Auto-Profiler ativado (reação: {profiler.check_interval}s){Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}✓ Todos os serviços NovaPulse iniciados{Style.RESET_ALL}")
    
    time.sleep(1)
    
    # === SYSTEM TRAY ===
    tray = None
    try:
        tray = SystemTrayIcon(optimizer_services=services)
        if tray.start():
            services['tray'] = tray
    except:
        pass
    
    # === DASHBOARD ===
    # Dashboard Rich original (console colorido)
    try:
        print(f"\n{Fore.CYAN}Iniciando Dashboard Console...{Style.RESET_ALL}\n")
        
        dashboard = Dashboard()
        dashboard.run(services)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Dashboard: {e}{Style.RESET_ALL}")
    
    # Cleanup
    print(f"\n{Fore.YELLOW}[INFO] Parando serviços...{Style.RESET_ALL}")
    stop_all_services(services)
    print(f"{Fore.GREEN}✓ NovaPulse finalizado{Style.RESET_ALL}\n")


def stop_all_services(services):
    """Para todos os serviços"""
    if 'cleaner' in services:
        services['cleaner'].stop()
    if 'smart_priority' in services:
        services['smart_priority'].stop()
    if 'auto_profiler' in services:
        services['auto_profiler'].stop()
    if 'game_detector' in services:
        services['game_detector'].stop()
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

