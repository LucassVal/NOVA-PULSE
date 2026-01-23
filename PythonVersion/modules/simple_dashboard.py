"""
NovaPulse - Simple Console Dashboard
Dashboard minimalista e estável usando apenas print básico
"""
import time
import sys
import os
import psutil

try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
except:
    NVIDIA_AVAILABLE = False


class SimpleConsoleDashboard:
    """Dashboard de console ultra-simples sem dependências externas"""
    
    def __init__(self):
        self.running = False
        self.start_time = time.time()
        self.gpu_handle = None
        
        if NVIDIA_AVAILABLE:
            try:
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except:
                pass
    
    def get_uptime(self) -> str:
        """Retorna uptime formatado"""
        elapsed = int(time.time() - self.start_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def get_cpu_info(self) -> tuple:
        """Retorna (percent, cores)"""
        return psutil.cpu_percent(), psutil.cpu_count()
    
    def get_ram_info(self) -> tuple:
        """Retorna (used_gb, total_gb, percent)"""
        mem = psutil.virtual_memory()
        return mem.used / (1024**3), mem.total / (1024**3), mem.percent
    
    def get_gpu_info(self) -> tuple:
        """Retorna (name, percent, temp) ou None"""
        if not NVIDIA_AVAILABLE or not self.gpu_handle:
            return None
        
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, 0)
            name = pynvml.nvmlDeviceGetName(self.gpu_handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            name = name.replace("NVIDIA ", "").replace(" Laptop GPU", "")[:20]
            return name, util.gpu, temp
        except:
            return None
    
    def clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_dashboard(self, services=None):
        """Imprime o dashboard uma vez"""
        # Coleta dados
        cpu_pct, cpu_cores = self.get_cpu_info()
        ram_used, ram_total, ram_pct = self.get_ram_info()
        gpu_info = self.get_gpu_info()
        uptime = self.get_uptime()
        
        # Modo
        mode = "NORMAL"
        if services and 'auto_profiler' in services:
            try:
                mode = services['auto_profiler'].get_current_mode().value.upper()
            except:
                pass
        
        # Print simples
        print()
        print("=" * 50)
        print("       ⚡ NOVAPULSE 2.0 - RUNNING")
        print("=" * 50)
        print()
        print(f"  CPU:  {cpu_pct:5.1f}%  ({cpu_cores} cores)")
        print(f"  RAM:  {ram_used:.1f}/{ram_total:.1f} GB ({ram_pct:.0f}%)")
        
        if gpu_info:
            name, gpu_pct, gpu_temp = gpu_info
            print(f"  GPU:  {name}")
            print(f"        Load: {gpu_pct}% | Temp: {gpu_temp}°C")
        
        print()
        print(f"  Mode: {mode} | Uptime: {uptime}")
        print()
        print("-" * 50)
        print("  Press Ctrl+C to exit")
        print("-" * 50)
    
    def run(self, services=None):
        """Executa o dashboard em loop"""
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                self.clear_screen()
                self.print_dashboard(services)
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.running = False
            print("\n[INFO] Dashboard parado pelo usuário")


# Singleton
_instance = None

def get_dashboard() -> SimpleConsoleDashboard:
    global _instance
    if _instance is None:
        _instance = SimpleConsoleDashboard()
    return _instance


if __name__ == "__main__":
    dash = SimpleConsoleDashboard()
    dash.run()
