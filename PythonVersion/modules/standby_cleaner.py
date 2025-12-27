"""
Módulo de limpeza de memória Standby usando ctypes
Similar ao ISLC
"""
import ctypes
from ctypes import wintypes
import time
import threading
import psutil
from datetime import datetime

# Constantes da API do Windows
SystemMemoryListInformation = 80
MemoryPurgeStandbyList = 4
MemoryEmptyWorkingSets = 2

# Carregar ntdll.dll
ntdll = ctypes.WinDLL('ntdll')
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

class StandbyMemoryCleaner:
    def __init__(self, threshold_mb=1024, check_interval=5):
        self.threshold_mb = threshold_mb
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.last_cleaned_mb = 0
        self.clean_count = 0
        self.total_cleaned_mb = 0  # Total acumulado na sessão
        
    def start(self):
        """Inicia monitoramento automático"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        print(f"[INFO] StandbyMemoryCleaner iniciado (threshold: {self.threshold_mb}MB)")
        
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[INFO] StandbyMemoryCleaner parado")
        
    def _monitoring_loop(self):
        """Loop de monitoramento contínuo"""
        while self.running:
            try:
                mem = psutil.virtual_memory()
                available_mb = mem.available // (1024 * 1024)
                
                if available_mb < self.threshold_mb:
                    freed_mb = self.clean_standby_memory()
                    self.last_cleaned_mb = freed_mb
                    self.clean_count += 1
                    self.total_cleaned_mb += freed_mb
                    print(f"[CLEAN] Memória limpa: {freed_mb}MB liberados | "
                          f"Disponível: {available_mb}MB → {(mem.available + freed_mb * 1024 * 1024) // (1024 * 1024)}MB")
                
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"[ERROR] Erro no monitoramento: {e}")
                time.sleep(10)
    
    def clean_standby_memory(self):
        """Limpa a lista de memória Standby"""
        try:
            # Eleva privilégios
            self._enable_privilege()
            
            # Obtém memória antes
            mem_before = psutil.virtual_memory().available // (1024 * 1024)
            
            # Purge Standby List
            command = ctypes.c_int(MemoryPurgeStandbyList)
            ntdll.NtSetSystemInformation(
                SystemMemoryListInformation,
                ctypes.byref(command),
                ctypes.sizeof(command)
            )
            
            # Empty Working Sets (fallback)
            command = ctypes.c_int(MemoryEmptyWorkingSets)
            ntdll.NtSetSystemInformation(
                SystemMemoryListInformation,
                ctypes.byref(command),
                ctypes.sizeof(command)
            )
            
            time.sleep(0.1)  # Aguarda processamento
            
            # Obtém memória depois
            mem_after = psutil.virtual_memory().available // (1024 * 1024)
            
            return max(0, mem_after - mem_before)
        except Exception as e:
            print(f"[ERROR] Erro ao limpar memória: {e}")
            return 0
    
    def _enable_privilege(self):
        """Habilita privilégio SE_PROF_SINGLE_PROCESS_NAME"""
        try:
            SE_PRIVILEGE_ENABLED = 0x00000002
            TOKEN_ADJUST_PRIVILEGES = 0x0020
            TOKEN_QUERY = 0x0008
            
            # Abre token do processo
            token = wintypes.HANDLE()
            kernel32.OpenProcessToken(
                kernel32.GetCurrentProcess(),
                TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                ctypes.byref(token)
            )
            
            # Lookup privilege value
            luid = wintypes.LUID()
            ctypes.windll.advapi32.LookupPrivilegeValueW(
                None,
                "SeProfileSingleProcessPrivilege",
                ctypes.byref(luid)
            )
            
            # Adjust privileges
            class TOKEN_PRIVILEGES(ctypes.Structure):
                _fields_ = [
                    ("PrivilegeCount", wintypes.DWORD),
                    ("Luid", wintypes.LUID),
                    ("Attributes", wintypes.DWORD),
                ]
            
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Luid = luid
            tp.Attributes = SE_PRIVILEGE_ENABLED
            
            ctypes.windll.advapi32.AdjustTokenPrivileges(
                token,
                False,
                ctypes.byref(tp),
                ctypes.sizeof(tp),
                None,
                None
            )
            
            kernel32.CloseHandle(token)
        except:
            pass  # Privilégio pode já estar habilitado
    
    def get_memory_info(self):
        """Retorna informações da memória"""
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total // (1024 * 1024),
            'available_mb': mem.available // (1024 * 1024),
            'used_percent': mem.percent
        }


if __name__ == "__main__":
    # Teste básico
    cleaner = StandbyMemoryCleaner(threshold_mb=1024, check_interval=5)
    cleaner.start()
    
    try:
        while True:
            mem_info = cleaner.get_memory_info()
            print(f"\rRAM: {mem_info['available_mb']}MB livre / {mem_info['total_mb']}MB total "
                  f"({100 - mem_info['used_percent']:.1f}% livre) | Limpezas: {cleaner.clean_count}", end='')
            time.sleep(2)
    except KeyboardInterrupt:
        cleaner.stop()
        print("\n[INFO] Finalizado")
