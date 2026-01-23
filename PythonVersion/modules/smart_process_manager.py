# === I/O Priority API (ctypes) ===
from ctypes import wintypes
import ctypes
import threading
import psutil
import time

class IO_PRIORITY:
    VeryLow = 0    # Background (Chrome, Updates)
    Low = 1
    Normal = 2
    High = 3       # Games, Active Apps
    Critical = 4

class SmartProcessManager:
    def __init__(self):
        self.running = False
        self.thread = None
        
        # Load Windows API
        try:
            self.ntdll = ctypes.WinDLL('ntdll.dll')
            self.kernel32 = ctypes.WinDLL('kernel32.dll')
            self.ProcessIoPriority = 33
            self.api_available = True
        except:
            self.api_available = False
            print("[WARN] I/O Priority API not available")
        
        # Lista de processos do sistema que NUNCA devem ter prioridade alta
        self.system_processes = {
            'svchost.exe', 'csrss.exe', 'dwm.exe', 'winlogon.exe',
            'services.exe', 'lsass.exe', 'smss.exe', 'wininit.exe',
            'System', 'Registry', 'Idle', 'RuntimeBroker.exe'
        }
        
        # Processos que devem ter prioridade BAIXA (mesmo se iniciados pelo usuário)
        self.low_priority_apps = {
            'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe',
            'discord.exe', 'spotify.exe', 'steam.exe',
            'onedrive.exe', 'dropbox.exe', 'googledrivesync.exe',
            'SearchIndexer.exe', 'CompatTelRunner.exe'
        }
        
        self.adjusted_pids = set()
        
    def start(self):
        """Inicia monitoramento inteligente"""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        print("[INFO] SmartProcessManager V2.0 iniciado (CPU + I/O Priority)")
    
    def stop(self):
        self.running = False
        if self.thread: self.thread.join(timeout=5)
    
    def _monitoring_loop(self):
        while self.running:
            try:
                self._scan_and_prioritize()
                time.sleep(2)  # Scan every 2 seconds for fast reaction
            except Exception as e:
                print(f"[ERROR] Erro no monitoramento: {e}")
                time.sleep(10)
    
    def _scan_and_prioritize(self):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'nice']):
                try:
                    if proc.pid in self.adjusted_pids: continue
                    if proc.info['name'] in self.system_processes: continue
                    if not proc.info['username']: continue
                    
                    is_user_process = 'SYSTEM' not in proc.info['username'].upper()
                    
                    if is_user_process:
                        if proc.info['name'].lower() in self.low_priority_apps:
                            self._set_low_priority(proc)
                        else:
                            self._set_high_priority(proc)
                        self.adjusted_pids.add(proc.pid)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self._cleanup_dead_pids()
        except Exception as e:
            print(f"[ERROR] Erro scan: {e}")
    
    def _set_io_priority(self, pid, priority):
        """Define prioridade de I/O via native API"""
        if not self.api_available: return False
        try:
            PROCESS_SET_INFORMATION = 0x0200
            handle = self.kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
            if not handle: return False
            
            prio = ctypes.c_int(priority)
            self.ntdll.NtSetInformationProcess(
                handle, self.ProcessIoPriority, ctypes.byref(prio), ctypes.sizeof(prio)
            )
            self.kernel32.CloseHandle(handle)
            return True
        except:
            return False

    def _set_high_priority(self, proc):
        try:
            # CPU: High
            proc.nice(psutil.HIGH_PRIORITY_CLASS)
            # I/O: High (3)
            io_ok = self._set_io_priority(proc.pid, IO_PRIORITY.High)
            
            msg = f"[PRIORITY] ⭐ ALTA (CPU+I/O) → {proc.info['name']}"
            if io_ok: msg += " [IO: High]"
            print(msg)
        except: pass
    
    def _set_low_priority(self, proc):
        try:
            # CPU: Below Normal
            proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            # I/O: Very Low (0) - Background mode!
            io_ok = self._set_io_priority(proc.pid, IO_PRIORITY.VeryLow)
            
            msg = f"[PRIORITY] 🔽 BAIXA (CPU+I/O) → {proc.info['name']}"
            if io_ok: msg += " [IO: Background]"
            print(msg)
        except: pass
    
    def _cleanup_dead_pids(self):
        try:
            alive = {p.pid for p in psutil.process_iter()}
            self.adjusted_pids = self.adjusted_pids.intersection(alive)
        except: pass


if __name__ == "__main__":
    # Teste
    manager = SmartProcessManager()
    manager.start()
    
    print("\nMonitorando processos...")
    print("Qualquer app iniciado pelo usuário receberá prioridade ALTA automaticamente!")
    print("\nPressione Ctrl+C para parar\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
        print("\n[INFO] Finalizado")
