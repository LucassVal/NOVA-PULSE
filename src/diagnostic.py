"""
NovaPulse System Diagnostic
Verifica todos os componentes e gera relatório
"""
import sys
import os
import datetime

# Adiciona path do NovaPulse
sys.path.insert(0, r"G:\Meu Drive\NovaPulse\PythonVersion")

def check_feature(name, check_func):
    """Executa verificação e retorna resultado"""
    try:
        result = check_func()
        if result:
            return f"[✓] {name}"
        else:
            return f"[✗] {name} - Não disponível"
    except Exception as e:
        return f"[✗] {name} - Erro: {str(e)[:50]}"

def run_diagnostics():
    """Executa todos os diagnósticos"""
    results = []
    results.append("=" * 60)
    results.append("⚡ NOVAPULSE SYSTEM DIAGNOSTIC")
    results.append(f"📅 Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("=" * 60)
    results.append("")
    
    # === DEPENDÊNCIAS PYTHON ===
    results.append("📦 DEPENDÊNCIAS PYTHON")
    results.append("-" * 40)
    
    # psutil
    results.append(check_feature("psutil (Monitoramento de Sistema)", 
        lambda: __import__('psutil') is not None))
    
    # wmi
    results.append(check_feature("wmi (Windows Management)", 
        lambda: __import__('wmi') is not None))
    
    # yaml
    results.append(check_feature("pyyaml (Configuração)", 
        lambda: __import__('yaml') is not None))
    
    # colorama
    results.append(check_feature("colorama (Cores no Terminal)", 
        lambda: __import__('colorama') is not None))
    
    # rich
    results.append(check_feature("rich (Dashboard Visual)", 
        lambda: __import__('rich') is not None))
    
    # pynvml
    def check_nvidia():
        import pynvml
        pynvml.nvmlInit()
        return pynvml.nvmlDeviceGetCount() > 0
    results.append(check_feature("pynvml (GPU NVIDIA)", check_nvidia))
    
    # pystray
    results.append(check_feature("pystray (System Tray)", 
        lambda: __import__('pystray') is not None))
    
    # pillow
    results.append(check_feature("pillow (Imagens)", 
        lambda: __import__('PIL') is not None))
    
    results.append("")
    
    # === MÓDULOS NOVAPULSE ===
    results.append("🔧 MÓDULOS NOVAPULSE")
    results.append("-" * 40)
    
    modules = [
        ("auto_profiler", "Auto-Profiler (Detecção de Carga)"),
        ("standby_cleaner", "Standby Memory Cleaner"),
        ("cpu_power", "CPU Power Manager"),
        ("smart_process_manager", "Smart Process Manager"),
        ("dashboard", "Dashboard Visual"),
        ("tray_icon", "System Tray Icon"),

        ("network_qos", "Network QoS Manager"),
        ("timer_resolution", "Timer Resolution"),
        ("services_optimizer", "Windows Services Optimizer"),
        ("gamebar_optimizer", "Game Bar Optimizer"),
        ("nvme_manager", "NVMe/SSD Manager"),
        ("temperature_service", "Temperature Service"),
        ("gpu_controller", "GPU Controller"),
        ("history_logger", "History Logger"),
        ("profiles", "Profile Manager (Legacy)"),
    ]
    
    for module_name, display_name in modules:
        results.append(check_feature(display_name, 
            lambda m=module_name: __import__(f'modules.{m}', fromlist=[m]) is not None))
    
    results.append("")
    
    # === HARDWARE ===
    results.append("🖥️ HARDWARE DETECTADO")
    results.append("-" * 40)
    
    # CPU
    import psutil
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.max:.0f}MHz" if cpu_freq else "N/A"
    results.append(f"[✓] CPU: {cpu_count} cores @ {freq_str}")
    
    # RAM
    mem = psutil.virtual_memory()
    ram_gb = mem.total / (1024**3)
    results.append(f"[✓] RAM: {ram_gb:.1f} GB")
    
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
            results.append(f"[✓] GPU NVIDIA: {name}")
        else:
            results.append("[✗] GPU NVIDIA: Não detectada")
    except:
        results.append("[✗] GPU NVIDIA: Não disponível")
    
    # GPU Intel
    try:
        import wmi
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            if 'intel' in gpu.Name.lower():
                results.append(f"[✓] GPU Intel: {gpu.Name}")
                break
    except:
        pass
    
    results.append("")
    
    # === FUNCIONALIDADES ===
    results.append("⚙️ FUNCIONALIDADES DO SISTEMA")
    results.append("-" * 40)
    
    # Admin
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    results.append(f"[{'✓' if is_admin else '✗'}] Privilégios de Administrador")
    
    # Temperatura CPU
    try:
        from modules.temperature_service import get_service
        temp_svc = get_service()
        temp = temp_svc.get_cpu_temp()
        if temp > 0:
            results.append(f"[✓] Leitura de Temperatura CPU: {temp:.1f}°C")
        else:
            results.append("[⚠] Leitura de Temperatura CPU: Não disponível (use LibreHardwareMonitor)")
    except Exception as e:
        results.append(f"[✗] Leitura de Temperatura CPU: {e}")
    
    # NtSetSystemInformation (RAM Cleaner)
    try:
        ntdll = ctypes.WinDLL('ntdll')
        if hasattr(ntdll, 'NtSetSystemInformation'):
            results.append("[✓] API de Limpeza de RAM (ntdll)")
        else:
            results.append("[✗] API de Limpeza de RAM")
    except:
        results.append("[✗] API de Limpeza de RAM")
    
    # Timer Resolution
    try:
        ntdll = ctypes.WinDLL('ntdll')
        if hasattr(ntdll, 'NtSetTimerResolution'):
            results.append("[✓] API de Timer Resolution")
        else:
            results.append("[✗] API de Timer Resolution")
    except:
        results.append("[✗] API de Timer Resolution")
    
    # PowerCfg (CPU Control)
    import subprocess
    try:
        result = subprocess.run(['powercfg', '/l'], capture_output=True, timeout=5)
        if result.returncode == 0:
            results.append("[✓] PowerCfg (Controle de CPU)")
        else:
            results.append("[✗] PowerCfg")
    except:
        results.append("[✗] PowerCfg")
    
    # Network Adapter
    try:
        cmd = 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1 -ExpandProperty Name'
        result = subprocess.run(['powershell', '-Command', cmd], 
                               capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            results.append(f"[✓] Adaptador de Rede: {result.stdout.strip()}")
        else:
            results.append("[✗] Adaptador de Rede: Não encontrado")
    except:
        results.append("[⚠] Adaptador de Rede: Não verificado")
    
    results.append("")
    
    # === RESUMO ===
    results.append("=" * 60)
    ok_count = sum(1 for r in results if "[✓]" in r)
    fail_count = sum(1 for r in results if "[✗]" in r)
    warn_count = sum(1 for r in results if "[⚠]" in r)
    
    results.append(f"📊 RESUMO: {ok_count} OK | {fail_count} Falhas | {warn_count} Avisos")
    results.append("=" * 60)
    
    if fail_count == 0:
        results.append("🎉 Sistema totalmente compatível com NovaPulse!")
    elif fail_count <= 3:
        results.append("⚠️ Algumas funcionalidades podem estar limitadas.")
    else:
        results.append("❌ Várias funcionalidades não disponíveis.")
    
    results.append("")
    results.append("Gerado por NovaPulse Diagnostic Tool v1.0")
    
    return "\n".join(results)


if __name__ == "__main__":
    print("Executando diagnóstico NovaPulse...")
    
    report = run_diagnostics()
    
    # Salva na área de trabalho
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    log_path = os.path.join(desktop, 'NovaPulse_Diagnostic.txt')
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n✓ Relatório salvo em: {log_path}")
    
    input("\nPressione ENTER para fechar...")
