"""
NVMe/SSD Manager
Otimizações específicas para drives de estado sólido (NVMe/SATA SSD)
"""
import subprocess
import threading
import time
import ctypes
import sys

class NVMeManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.trim_interval = self.config.get('trim_interval_hours', 24) * 3600
        self.running = False
        self.thread = None

    def apply_filesystem_optimizations(self):
        """Aplica otimizações de sistema de arquivos (NTFS)"""
        print("[NVMe] Verificando otimizações de NTFS...")
        
        # 1. Desativar Last Access Update (Ganho de IOPS em leitura)
        # fsutil behavior set disablelastaccess 1
        try:
            # Check current status
            check = subprocess.run(['fsutil', 'behavior', 'query', 'DisableLastAccess'], 
                                 capture_output=True, text=True)
            
            if " = 1" not in check.stdout:
                print("[NVMe] Desativando 'Last Access Update' (Otimizando IOPS)...")
                subprocess.run(['fsutil', 'behavior', 'set', 'DisableLastAccess', '1'], 
                             capture_output=True)
                print("[NVMe] ✓ Last Access Update desativado")
            else:
                print("[NVMe] ✓ Last Access Update já estava otimizado")
                
        except Exception as e:
            print(f"[NVMe] Erro ao otimizar NTFS: {e}")

    def apply_power_optimizations(self):
        """Impede que o SSD entre em suspensão (Evita APST Lag)"""
        try:
            print("[NVMe] Configurando Plano de Energia (Disco: Nunca suspender)...")
            # AC (Tomada)
            subprocess.run(['powercfg', '/change', 'disk-timeout-ac', '0'], capture_output=True)
            # DC (Bateria - opcional, mas bom para performance)
            subprocess.run(['powercfg', '/change', 'disk-timeout-dc', '0'], capture_output=True)
            print("[NVMe] ✓ Suspensão de disco desativada")
        except Exception as e:
            print(f"[NVMe] Erro ao configurar energia: {e}")

    def run_retrim(self):
        """Executa comando de ReTrim (Powershell)"""
        print("[NVMe] 🧹 Iniciando TRIM inteligente...")
        try:
            # ReTrim é rápido e seguro. Defrag é bloqueado pelo Windows em SSDs automaticamente.
            # Removed -Verbose to prevent dashboard glitches
            cmd = "Optimize-Volume -DriveLetter C -ReTrim"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            print("[NVMe] ✓ TRIM executado com sucesso")
            return True
        except Exception as e:
            print(f"[NVMe] Erro ao executar TRIM: {e}")
            return False

    def start_periodic_trim(self):
        """Inicia thread de TRIM periódico"""
        if self.running: return
        
        self.running = True
        
        def trim_loop():
            # Executa um TRIM logo na inicialização
            time.sleep(10) # Aguarda sistema estabilizar
            self.run_retrim()
            
            while self.running:
                # Aguarda intervalo (padrão 24h)
                for _ in range(int(self.trim_interval / 10)):
                    if not self.running: break
                    time.sleep(10)
                
                if self.running:
                    self.run_retrim()
        
        self.thread = threading.Thread(target=trim_loop, daemon=True)
        self.thread.start()
        print(f"[NVMe] Agendador de TRIM iniciado (Intervalo: {self.trim_interval/3600:.1f}h)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
