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
        
        # === ALLOWLIST: Only these get HIGH priority ===
        self.high_priority_apps = {
            # NovaPulse & Antigravity
            'antigravity.exe', 'novapulse.exe',
            # Development tools
            'node.exe', 'rust-analyzer.exe', 'rust-analyzer-proc-macro-srv.exe',
            'codex.exe', 'language_server_windows_x64.exe', 'pyrefly.exe',
            'cloudcode_cli.exe', 'pwsh.exe',
            # Games (generic patterns handled separately)
            # Game launchers
            'epicgameslauncher.exe', 'galaxyclient.exe',
        }
        
        # === BLOCKLIST: These get LOW priority ===
        self.low_priority_apps = {
            # Browsers
            'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe', 'brave.exe',
            # Social / Media
            'discord.exe', 'spotify.exe', 'whatsapp.root.exe', 'ms-teams.exe',
            'teams.exe', 'slack.exe',
            # Cloud sync
            'onedrive.exe', 'dropbox.exe', 'googledrivesync.exe', 'googledriveFS.exe',
            # Steam (launcher, not games)
            'steam.exe', 'steamwebhelper.exe',
            # ASUS bloatware
            'asusoptimization.exe', 'asusoptimizationstartuptask.exe',
            'asussoftwaremanager.exe', 'asussoftwaremanageragent.exe',
            'asussystemdiagnosis.exe', 'asussystemanalysis.exe',
            'asusswitch.exe', 'asusappservice.exe', 'asusosd.exe',
            'asuswiifismartconnect.exe',
            'dsaservice.exe', 'dsaupdateservice.exe', 'dsatray.exe',
            # Windows telemetry / indexing
            'searchindexer.exe', 'compattelrunner.exe',
            'softwareupdatenotificationservice.exe',
            # Widgets
            'widgets.exe', 'widgetservice.exe',
            # Background services
            'mspcmanagerservice.exe',
        }
        
        # System processes — never touch these
        self.system_processes = {
            'svchost.exe', 'csrss.exe', 'dwm.exe', 'winlogon.exe',
            'services.exe', 'lsass.exe', 'smss.exe', 'wininit.exe',
            'System', 'Registry', 'Idle', 'RuntimeBroker.exe',
            'explorer.exe', 'ctfmon.exe', 'searchhost.exe',
            'sihost.exe', 'taskhostw.exe', 'shellhost.exe',
            'audiodg.exe', 'fontdrvhost.exe', 'dllhost.exe',
            'conhost.exe', 'cmd.exe', 'wslservice.exe',
            'lsaiso.exe', 'ngciso.exe', 'smartscreen.exe',
            'spoolsv.exe', 'wmiprvse.exe', 'wmiapsrv.exe',
            'backgroundtaskhost.exe', 'applicationframehost.exe',
            'shellexperiencehost.exe', 'startmenuexperiencehost.exe',
            'lockapp.exe', 'textinputhost.exe', 'crossdeviceresume.exe',
            'useroobbroker.exe', 'dashost.exe', 'unsecapp.exe',
            'prevhost.exe', 'securityhealthsystray.exe',
            'presentationfontcache.exe', 'presentmonservice.exe',
            'gamingservices.exe', 'gamingservicesnet.exe',
        }
        
        self.adjusted_pids = set()
        self._high_count = 0
        self._low_count = 0
        
    def start(self):
        """Start intelligent monitoring"""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        high_rules = len(self.high_priority_apps)
        low_rules = len(self.low_priority_apps)
        print(f"[INFO] SmartProcessManager V2.1 started (allowlist: {high_rules} HIGH, {low_rules} LOW)")
    
    def stop(self):
        self.running = False
        if self.thread: self.thread.join(timeout=5)
    
    def _monitoring_loop(self):
        while self.running:
            try:
                self._scan_and_prioritize()
                time.sleep(3)  # Scan every 3 seconds
            except Exception as e:
                print(f"[ERROR] Monitoring error: {e}")
                time.sleep(10)
    
    def _scan_and_prioritize(self):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    if proc.pid in self.adjusted_pids: continue
                    name = proc.info['name']
                    name_lower = name.lower() if name else ''
                    if name_lower in self.system_processes: continue
                    if not proc.info['username']: continue
                    if 'SYSTEM' in proc.info['username'].upper(): continue
                    if name_lower in self.high_priority_apps:
                        self._set_high_priority(proc)
                        self._high_count += 1
                    elif name_lower in self.low_priority_apps:
                        self._set_low_priority(proc)
                        self._low_count += 1
                    self.adjusted_pids.add(proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self._cleanup_dead_pids()
        except Exception as e:
            print(f"[ERROR] Scan error: {e}")
    
    def _set_io_priority(self, pid, priority):
        """Set I/O priority via native API"""
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
            proc.nice(psutil.HIGH_PRIORITY_CLASS)
            self._set_io_priority(proc.pid, IO_PRIORITY.High)
            print(f"[PRIORITY] ⭐ HIGH → {proc.info['name']}")
        except: pass
    
    def _set_low_priority(self, proc):
        try:
            proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            self._set_io_priority(proc.pid, IO_PRIORITY.VeryLow)
            print(f"[PRIORITY] 🔽 LOW → {proc.info['name']}")
        except: pass
    
    def _cleanup_dead_pids(self):
        try:
            alive = {p.pid for p in psutil.process_iter()}
            self.adjusted_pids = self.adjusted_pids.intersection(alive)
        except: pass
    
    def get_stats(self):
        """Return priority adjustment stats"""
        return {'high': self._high_count, 'low': self._low_count}


if __name__ == "__main__":
    manager = SmartProcessManager()
    manager.start()
    
    print("\nMonitoring processes...")
    print("HIGH priority only for essential apps (Antigravity, node, etc)")
    print("LOW priority for browsers, bloatware, cloud sync")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stats = manager.get_stats()
        manager.stop()
        print(f"\n[INFO] Finished — {stats['high']} HIGH processes, {stats['low']} LOW processes")
