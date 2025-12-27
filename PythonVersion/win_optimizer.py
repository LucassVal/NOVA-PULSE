#!/usr/bin/env python3
"""
Windows NVMe RAM Optimizer - V3.0
Sistema automatizado de otimização RAM/SSD/Gaming
"""
import sys
import time
import yaml
import ctypes
from colorama import init, Fore, Style

# Core Modules
from modules.standby_cleaner import StandbyMemoryCleaner
from modules.cpu_power import CPUPowerManager
from modules.stress_test import CPUStressTest
from modules.smart_process_manager import SmartProcessManager
from modules.fan_controller import FanController
from modules.dashboard import Dashboard
from modules.gpu_controller import GPUController
from modules.nvme_manager import NVMeManager

# V3.0 New Modules
from modules.network_qos import NetworkQoSManager
from modules.game_detector import GameModeDetector
from modules.history_logger import get_logger as get_history_logger
from modules.profiles import get_manager as get_profile_manager, OptimizationProfile
from modules.tray_icon import SystemTrayIcon

# Inicializa colorama para cores no terminal
init()

def is_admin():
    """Verifica se está rodando como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def load_config():
    """Carrega configuração do arquivo YAML"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.YELLOW}[WARN] Erro ao carregar config: {e}{Style.RESET_ALL}")
        return get_default_config()

def get_default_config():
    """Retorna configuração padrão"""
    return {
        'standby_cleaner': {
            'enabled': True,
            'threshold_mb': 1024,
            'check_interval_seconds': 5
        },
        'cpu_control': {
            'max_frequency_percent': 100,
            'min_frequency_percent': 5
        },
        'stress_test': {
            'enabled': False,
            'target_load_percent': 70,
            'thread_count': 0
        },
        'network_qos': {
            'enabled': True
        },
        'game_detector': {
            'enabled': True
        }
    }

def print_header():
    """Imprime cabeçalho do programa"""
    print(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     {Fore.YELLOW}⚡ Windows NVMe RAM Optimizer v3.0 ⚡{Fore.CYAN}             ║
║                                                           ║
║     {Fore.GREEN}Gaming • Produtividade • Performance{Fore.CYAN}               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

def main():
    """Função principal"""
    print_header()
    
    # Verifica privilégios de administrador
    if not is_admin():
        print(f"{Fore.RED}[ERRO] Este programa requer privilégios de Administrador!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Por favor, execute como administrador.{Style.RESET_ALL}\n")
        input("Pressione ENTER para sair...")
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ Rodando como Administrador{Style.RESET_ALL}\n")
    
    # Carrega configuração
    print(f"{Fore.CYAN}[INFO] Carregando configuração...{Style.RESET_ALL}")
    config = load_config()
    
    # Inicializa serviços
    services = {}
    
    # === STANDBY MEMORY CLEANER ===
    if config.get('standby_cleaner', {}).get('enabled', True):
        cleaner_config = config['standby_cleaner']
        services['cleaner'] = StandbyMemoryCleaner(
            threshold_mb=cleaner_config.get('threshold_mb', 1024),
            check_interval=cleaner_config.get('check_interval_seconds', 5)
        )
        services['cleaner'].start()
    
    # === SMART PROCESS MANAGER (PRIORIZAÇÃO AUTOMÁTICA) ===
    services['smart_priority'] = SmartProcessManager()
    services['smart_priority'].start()
    print(f"{Fore.GREEN}✓ Priorização inteligente ativada{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  → Apps do usuário: Prioridade ALTA automaticamente{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  → Navegadores/Background: Prioridade baixa{Style.RESET_ALL}")
    
    # === CPU POWER MANAGER ===
    services['cpu_power'] = CPUPowerManager()
    
    cpu_config = config.get('cpu_control', {})
    max_freq = cpu_config.get('max_frequency_percent', 100)
    min_freq = cpu_config.get('min_frequency_percent', 5)
    
    if max_freq != 100:
        services['cpu_power'].set_max_cpu_frequency(max_freq)
    
    # [V2.0] Adaptive Thermal Governor
    # Auto-enabled unless user specifically forced a low fixed manual limit (< 80)
    if max_freq >= 80:
        services['cpu_power'].start_adaptive_governor()
    
    if min_freq != 5:
        services['cpu_power'].set_min_cpu_frequency(min_freq)
    
    # === STRESS TEST ===
    stress_config = config.get('stress_test', {})
    if stress_config.get('enabled', False):
        services['stress'] = CPUStressTest()
        services['stress'].start(
            target_load_percent=stress_config.get('target_load_percent', 70),
            thread_count=stress_config.get('thread_count', 0)
        )
    
    # === FAN CONTROL ===
    fan_config = config.get('fan_control', {})
    if fan_config.get('try_auto_detect', True):
        fan_ctrl = FanController()
        print(f"\n{Fore.CYAN}[FAN] Tentando configurar ventoinhas...{Style.RESET_ALL}")
        if fan_ctrl.detect_fan_control_method():
            fan_ctrl.set_max_speed()
        elif fan_config.get('show_instructions', True):
            print(f"{Fore.YELLOW}{fan_ctrl.get_recommendation()}{Style.RESET_ALL}")
    
    # === GPU CONTROL (POWER LIMIT) ===
    gpu_config = config.get('gpu_control', {})
    if gpu_config.get('enabled', False):
        gpu_ctrl = GPUController()
        if gpu_ctrl.initialized:
            power_limit = gpu_config.get('power_limit_percent', 90)
            print(f"\n{Fore.CYAN}[GPU] Aplicando power limit: {power_limit}%{Style.RESET_ALL}")
            if gpu_ctrl.set_power_limit_percent(power_limit):
                print(f"{Fore.GREEN}✓ GPU power limit ajustado{Style.RESET_ALL}")
                services['gpu_ctrl'] = gpu_ctrl  # Salva no dict para dashboard
            else:
                print(f"{Fore.YELLOW}⚠ Não foi possível ajustar power limit (pode precisar drivers atualizados){Style.RESET_ALL}")
    
    # === NVMe/SSD OPTIMIZER ===
    nvme_config = config.get('nvme', {'enabled': True})
    if nvme_config.get('enabled', True):
        nvme_mgr = NVMeManager(nvme_config)
        
        # 1. FileSystem Opt
        if nvme_config.get('disable_last_access', True):
            nvme_mgr.apply_filesystem_optimizations()
            
        # 2. Power Plan
        if nvme_config.get('prevent_disk_sleep', True):
            nvme_mgr.apply_power_optimizations()
            
        # 3. Periodic Trim
        if nvme_config.get('periodic_trim', True):
            nvme_mgr.start_periodic_trim()
            services['nvme'] = nvme_mgr

    # === V3.0: NETWORK QoS (PING BOOSTER) ===
    qos_config = config.get('network_qos', {'enabled': True})
    if qos_config.get('enabled', True):
        print(f"\n{Fore.CYAN}[NET] Configurando Network QoS...{Style.RESET_ALL}")
        qos_mgr = NetworkQoSManager(qos_config)
        if qos_mgr.apply_qos_rules():
            services['network_qos'] = qos_mgr
    
    # === V3.0: GAME MODE DETECTOR ===
    game_config = config.get('game_detector', {'enabled': True})
    if game_config.get('enabled', True):
        game_detector = GameModeDetector(optimizer_services=services, config=game_config)
        game_detector.start()
        services['game_detector'] = game_detector
        print(f"{Fore.GREEN}✓ Game Mode Detector ativado (Auto-Boost){Style.RESET_ALL}")
    
    # === V3.0: HISTORY LOGGER ===
    history = get_history_logger()
    history.log_event("optimizer_start", "V3.0 Initialized")
    services['history'] = history
    print(f"{Fore.GREEN}✓ History Logger ativado (CSV){Style.RESET_ALL}")
    
    # === V3.0: PROFILE MANAGER ===
    profile_mgr = get_profile_manager()
    profile_mgr.set_services(services)
    services['profiles'] = profile_mgr
    # Aplica perfil padrão (Balanced)
    profile_mgr.apply_profile(OptimizationProfile.BALANCED)

    print(f"\n{Fore.GREEN}✓ Todos os serviços V3.0 iniciados{Style.RESET_ALL}")
    
    time.sleep(1)
    
    # === V3.0: SYSTEM TRAY (Background) ===
    tray = None
    try:
        tray = SystemTrayIcon(optimizer_services=services)
        if tray.start():
            services['tray'] = tray
    except:
        pass  # Tray is optional - may fail without pystray

    # Loop principal - Modo Dashboard
    try:
        print(f"\n{Fore.CYAN}Iniciando Dashboard Console...{Style.RESET_ALL}\n")
        dashboard = Dashboard()
        dashboard.run(services)
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[INFO] Parando serviços...{Style.RESET_ALL}")
        
        # Para todos os serviços
        if 'cleaner' in services:
            services['cleaner'].stop()
        if 'smart_priority' in services:
            services['smart_priority'].stop()
        if 'stress' in services:
            services['stress'].stop()
        
        print(f"{Fore.GREEN}✓ Finalizado{Style.RESET_ALL}\n")

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
