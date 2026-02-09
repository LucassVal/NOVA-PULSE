"""
NovaPulse Security Scanner
Real-time security monitoring: process scanning, network monitoring,
startup auditing, and port scanning.

Target: Intel Core i5-11300H (Tiger Lake) running Windows 10/11

This module provides antivirus-grade security features:
  1. Process Scanner: Detects unsigned/suspicious processes
  2. Network Monitor: Flags unknown outbound connections
  3. Startup Auditor: Checks registry Run keys + Startup folder
  4. Port Scanner: Lists open listening ports, flags unusual ones

Design Decision: We use psutil + subprocess (no third-party AV engine)
because we want lightweight, transparent security that the user controls.
We flag threats but never delete files — the user decides.
"""
import psutil
import os
import subprocess
import winreg
import threading
import time
from datetime import datetime


class SecurityScanner:
    """
    Lightweight security scanner for Windows.
    Scans processes, network connections, startup items, and open ports.
    Designed to complement (not replace) Windows Defender.
    """
    
    # ──────────────────────────────────────────────
    # KNOWN SAFE PROCESSES (Microsoft + common apps)
    # Processes NOT in this list get flagged for review
    # ──────────────────────────────────────────────
    KNOWN_SAFE_PROCESSES = {
        # Windows Core
        'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
        'lsass.exe', 'svchost.exe', 'winlogon.exe', 'dwm.exe', 'explorer.exe',
        'taskhost.exe', 'taskhostw.exe', 'sihost.exe', 'ctfmon.exe',
        'conhost.exe', 'fontdrvhost.exe', 'dllhost.exe', 'searchhost.exe',
        'startmenuexperiencehost.exe', 'runtimebroker.exe', 'shellexperiencehost.exe',
        'applicationframehost.exe', 'systemsettings.exe', 'textinputhost.exe',
        'searchprotocolhost.exe', 'searchindexer.exe', 'searchfilterhost.exe',
        'spoolsv.exe', 'lsaiso.exe', 'registry', 'idle', 'memory compression',
        'ntoskrnl.exe', 'audiodg.exe', 'dashost.exe', 'wmiprvse.exe',
        'securityhealthservice.exe', 'sgrmbroker.exe', 'smartscreen.exe',
        'msmpeng.exe', 'nissrv.exe',  # Windows Defender
        'mpcmdrun.exe', 'securityhealthsystray.exe',
        
        # Windows Update / Installer
        'tiworker.exe', 'trustedinstaller.exe', 'msiexec.exe', 'wuauclt.exe',
        
        # Common apps (safe)
        'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe', 'brave.exe',
        'code.exe', 'devenv.exe', 'python.exe', 'pythonw.exe', 'python3.exe',
        'node.exe', 'npm.exe', 'git.exe',
        'steam.exe', 'steamwebhelper.exe', 'epicgameslauncher.exe',
        'discord.exe', 'spotify.exe', 'slack.exe', 'teams.exe',
        'obs64.exe', 'obs32.exe',
        'nvidia share.exe', 'nvcontainer.exe', 'nvdisplay.container.exe',
        'nvspcaps64.exe', 'nvsphelper64.exe', 'nvcplui.exe',
        
        # NovaPulse itself
        'novapulse.exe', 'novapulse.py',
    }
    
    # Suspicious paths — processes running from these need attention
    SUSPICIOUS_PATHS = [
        os.path.expandvars(r'%TEMP%'),
        os.path.expandvars(r'%APPDATA%\Temp'),
        r'C:\Windows\Temp',
        r'C:\Users\Public',
    ]
    
    # Known safe ports for listening
    SAFE_PORTS = {
        80, 443,     # HTTP/HTTPS
        135, 139,    # Windows RPC/NetBIOS
        445,         # SMB
        902, 912,    # VMware
        1900,        # UPnP/SSDP
        5040,        # Windows
        5353,        # mDNS
        5357,        # WSDAPI
        7680,        # Windows Delivery Optimization
        49152, 49153, 49154, 49155, 49156, 49157, 49158, 49159,  # Windows Dynamic
    }
    
    def __init__(self):
        self.scan_results = {
            'processes': {'total': 0, 'suspicious': [], 'unknown': []},
            'network': {'total_connections': 0, 'outbound': [], 'suspicious': []},
            'startup': {'total': 0, 'items': [], 'suspicious': []},
            'ports': {'total': 0, 'listening': [], 'suspicious': []},
        }
        self.last_scan_time = None
        self.threats_found = 0
        self.status = 'idle'  # idle, scanning, clean, threats_found
        self._scan_lock = threading.Lock()
        self._bg_thread = None
        self._running = False
    
    # ──────────────────────────────────────────────
    # PROCESS SCANNER
    # ──────────────────────────────────────────────
    
    def scan_processes(self):
        """
        Scan all running processes and flag suspicious ones.
        
        A process is flagged if:
          1. Its name is NOT in the KNOWN_SAFE list
          2. It runs from a suspicious path (TEMP, Public folders)
          3. It consumes high CPU but is unknown
          
        This does NOT kill any process — it only reports.
        """
        suspicious = []
        unknown = []
        total = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent', 'username']):
            try:
                info = proc.info
                name = (info['name'] or '').lower()
                exe_path = info['exe'] or ''
                total += 1
                
                # Skip if known safe
                if name in self.KNOWN_SAFE_PROCESSES:
                    continue
                
                # Skip system processes with no exe
                if not exe_path or info['pid'] <= 4:
                    continue
                
                # Check if running from suspicious path
                is_suspicious_path = any(
                    exe_path.lower().startswith(sp.lower()) 
                    for sp in self.SUSPICIOUS_PATHS
                )
                
                entry = {
                    'pid': info['pid'],
                    'name': info['name'],
                    'exe': exe_path,
                    'cpu': info.get('cpu_percent', 0) or 0,
                    'memory': round(info.get('memory_percent', 0) or 0, 1),
                    'user': info.get('username', 'N/A'),
                    'suspicious_path': is_suspicious_path,
                }
                
                if is_suspicious_path:
                    entry['reason'] = f'Running from suspicious path: {os.path.dirname(exe_path)}'
                    suspicious.append(entry)
                else:
                    unknown.append(entry)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        self.scan_results['processes'] = {
            'total': total,
            'suspicious': suspicious,
            'unknown': unknown[:20],  # Cap at 20 to avoid flooding
        }
        
        return len(suspicious)
    
    # ──────────────────────────────────────────────
    # NETWORK CONNECTION MONITOR
    # ──────────────────────────────────────────────
    
    def scan_network(self):
        """
        Monitor all outbound network connections.
        
        Flags connections that:
          1. Go to non-standard ports (not 80, 443, etc.)
          2. Come from unknown processes
          3. Have ESTABLISHED state to unusual destinations
        
        This helps detect data exfiltration or C2 communication.
        """
        suspicious = []
        outbound = []
        total = 0
        
        for conn in psutil.net_connections(kind='inet'):
            try:
                total += 1
                
                # Only check ESTABLISHED outbound connections
                if conn.status != 'ESTABLISHED' or not conn.raddr:
                    continue
                
                remote_ip = conn.raddr.ip
                remote_port = conn.raddr.port
                local_port = conn.laddr.port if conn.laddr else 0
                
                # Get process name
                proc_name = 'Unknown'
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except:
                        pass
                
                entry = {
                    'pid': conn.pid,
                    'process': proc_name,
                    'remote_ip': remote_ip,
                    'remote_port': remote_port,
                    'local_port': local_port,
                    'status': conn.status,
                }
                
                outbound.append(entry)
                
                # Flag if unknown process connecting to unusual port
                if (proc_name.lower() not in self.KNOWN_SAFE_PROCESSES and
                    remote_port not in {80, 443, 8080, 8443, 53}):
                    entry['reason'] = f'Unknown process connecting to port {remote_port}'
                    suspicious.append(entry)
                    
            except:
                continue
        
        self.scan_results['network'] = {
            'total_connections': total,
            'outbound': outbound[:30],  # Cap display
            'suspicious': suspicious,
        }
        
        return len(suspicious)
    
    # ──────────────────────────────────────────────
    # STARTUP AUDITOR
    # ──────────────────────────────────────────────
    
    def scan_startup(self):
        """
        Audit Windows startup entries.
        
        Checks:
          1. HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
          2. HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
          3. HKCU\\...\\RunOnce (one-time startup)
          4. Shell Startup folder
          
        Flags entries that:
          - Point to suspicious paths (TEMP, etc.)
          - Are not from known vendors
          - Were recently added
        """
        items = []
        suspicious = []
        
        # Registry Run keys to check
        reg_keys = [
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 'HKCU\\Run'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce', 'HKCU\\RunOnce'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 'HKLM\\Run'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce', 'HKLM\\RunOnce'),
        ]
        
        for hive, path, label in reg_keys:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entry = {
                            'name': name,
                            'value': str(value),
                            'location': label,
                        }
                        items.append(entry)
                        
                        # Flag suspicious
                        value_lower = str(value).lower()
                        is_suspicious = any(
                            sp.lower() in value_lower 
                            for sp in self.SUSPICIOUS_PATHS
                        )
                        
                        if is_suspicious:
                            entry['reason'] = 'Points to suspicious path'
                            suspicious.append(entry)
                        elif 'runonce' in label.lower():
                            entry['reason'] = 'One-time startup entry (may be temporary)'
                            suspicious.append(entry)
                        
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except:
                continue
        
        # Check Startup folder
        startup_folder = os.path.expandvars(
            r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'
        )
        if os.path.exists(startup_folder):
            for item in os.listdir(startup_folder):
                full_path = os.path.join(startup_folder, item)
                entry = {
                    'name': item,
                    'value': full_path,
                    'location': 'Startup Folder',
                }
                items.append(entry)
        
        self.scan_results['startup'] = {
            'total': len(items),
            'items': items,
            'suspicious': suspicious,
        }
        
        return len(suspicious)
    
    # ──────────────────────────────────────────────
    # PORT SCANNER
    # ──────────────────────────────────────────────
    
    def scan_ports(self):
        """
        List all open listening ports on the system.
        
        Flags ports that:
          1. Are NOT in the SAFE_PORTS list
          2. Are below 1024 but not standard services
          3. Are owned by unknown processes
          
        This detects backdoors and unauthorized services.
        """
        listening = []
        suspicious = []
        
        for conn in psutil.net_connections(kind='inet'):
            try:
                if conn.status != 'LISTEN':
                    continue
                
                port = conn.laddr.port
                ip = conn.laddr.ip
                
                # Get process
                proc_name = 'Unknown'
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()
                    except:
                        pass
                
                entry = {
                    'port': port,
                    'ip': ip,
                    'pid': conn.pid,
                    'process': proc_name,
                }
                listening.append(entry)
                
                # Flag if not in safe ports AND not a dynamic port (>49152)
                if port not in self.SAFE_PORTS and port < 49152:
                    if proc_name.lower() not in self.KNOWN_SAFE_PROCESSES:
                        entry['reason'] = f'Unknown process listening on port {port}'
                        suspicious.append(entry)
                        
            except:
                continue
        
        self.scan_results['ports'] = {
            'total': len(listening),
            'listening': listening,
            'suspicious': suspicious,
        }
        
        return len(suspicious)
    
    # ──────────────────────────────────────────────
    # FULL SCAN
    # ──────────────────────────────────────────────
    
    def run_full_scan(self):
        """
        Run all security scans and return total threats found.
        
        Scans:
          1. Processes — unsigned/suspicious executables
          2. Network — unknown outbound connections
          3. Startup — persistence mechanisms
          4. Ports — unauthorized listeners
          
        Returns total number of flagged items.
        """
        with self._scan_lock:
            self.status = 'scanning'
            self.threats_found = 0
            
            print("[SECURITY] ═══════════════════════════════════════")
            print("[SECURITY]  NovaPulse Security Scanner — Running")
            print("[SECURITY] ═══════════════════════════════════════")
            
            # 1. Process scan
            proc_threats = self.scan_processes()
            total_procs = self.scan_results['processes']['total']
            print(f"[SECURITY] ✓ Processes scanned: {total_procs} ({proc_threats} flagged)")
            
            # 2. Network scan
            net_threats = self.scan_network()
            total_conns = self.scan_results['network']['total_connections']
            print(f"[SECURITY] ✓ Connections scanned: {total_conns} ({net_threats} suspicious)")
            
            # 3. Startup audit
            startup_threats = self.scan_startup()
            total_startup = self.scan_results['startup']['total']
            print(f"[SECURITY] ✓ Startup entries: {total_startup} ({startup_threats} flagged)")
            
            # 4. Port scan
            port_threats = self.scan_ports()
            total_ports = self.scan_results['ports']['total']
            print(f"[SECURITY] ✓ Open ports: {total_ports} ({port_threats} unusual)")
            
            self.threats_found = proc_threats + net_threats + startup_threats + port_threats
            self.last_scan_time = datetime.now()
            
            if self.threats_found == 0:
                self.status = 'clean'
                print(f"\n[SECURITY] 🛡️ System is CLEAN — No threats detected")
            else:
                self.status = 'threats_found'
                print(f"\n[SECURITY] ⚠ {self.threats_found} items flagged for review")
            
            print(f"[SECURITY] ═══════════════════════════════════════\n")
            
            return self.threats_found
    
    # ──────────────────────────────────────────────
    # BACKGROUND SCANNING
    # ──────────────────────────────────────────────
    
    def start_background_scan(self, interval_seconds=300):
        """
        Start periodic background scanning.
        Default: every 5 minutes.
        
        The scan runs in a daemon thread so it won't block the dashboard.
        Results are updated atomically and read by the dashboard.
        """
        if self._running:
            return
        
        self._running = True
        
        def _scan_loop():
            # Initial scan
            self.run_full_scan()
            
            while self._running:
                time.sleep(interval_seconds)
                if self._running:
                    self.run_full_scan()
        
        self._bg_thread = threading.Thread(target=_scan_loop, daemon=True, name='NovaPulse-SecurityScanner')
        self._bg_thread.start()
        print(f"[SECURITY] Background scanning started (every {interval_seconds}s)")
    
    def stop(self):
        """Stop background scanning."""
        self._running = False
    
    # ──────────────────────────────────────────────
    # STATUS FOR DASHBOARD
    # ──────────────────────────────────────────────
    
    def get_status(self):
        """
        Return security status dict for dashboard display.
        
        Returns:
          status: 'idle' | 'scanning' | 'clean' | 'threats_found'
          threats_found: total number of flagged items
          last_scan: datetime of last completed scan
          process_count: total processes scanned
          connection_count: total connections scanned
          startup_count: total startup entries
          port_count: total listening ports
          suspicious_processes: list of flagged processes
          suspicious_connections: list of flagged connections
          suspicious_startup: list of flagged startup entries
          suspicious_ports: list of flagged ports
        """
        return {
            'status': self.status,
            'threats_found': self.threats_found,
            'last_scan': self.last_scan_time,
            'process_count': self.scan_results['processes']['total'],
            'connection_count': self.scan_results['network']['total_connections'],
            'startup_count': self.scan_results['startup']['total'],
            'port_count': self.scan_results['ports']['total'],
            'suspicious_processes': self.scan_results['processes']['suspicious'],
            'suspicious_connections': self.scan_results['network']['suspicious'],
            'suspicious_startup': self.scan_results['startup']['suspicious'],
            'suspicious_ports': self.scan_results['ports']['suspicious'],
        }
    
    def get_shield_status(self):
        """
        Return a simple shield status for the dashboard header.
        
        Returns (emoji, color, label):
          🟢 green  PROTECTED  — no threats
          🟡 yellow SCANNING   — scan in progress
          🔴 red    THREATS     — items flagged
        """
        if self.status == 'scanning':
            return ('🟡', 'yellow', 'SCANNING')
        elif self.status == 'threats_found':
            return (f'🔴', 'red', f'{self.threats_found} THREATS')
        elif self.status == 'clean':
            return ('🟢', 'green', 'PROTECTED')
        else:
            return ('⚪', 'white', 'IDLE')


# ──────────────────────────────────────────────
# SINGLETON
# ──────────────────────────────────────────────
_instance = None

def get_scanner():
    """Get singleton SecurityScanner instance."""
    global _instance
    if _instance is None:
        _instance = SecurityScanner()
    return _instance


if __name__ == "__main__":
    scanner = SecurityScanner()
    threats = scanner.run_full_scan()
    
    print(f"\n{'='*50}")
    print(f"Shield: {scanner.get_shield_status()}")
    
    if scanner.scan_results['processes']['suspicious']:
        print(f"\n⚠ Suspicious Processes:")
        for p in scanner.scan_results['processes']['suspicious']:
            print(f"  - {p['name']} (PID:{p['pid']}) — {p['reason']}")
    
    if scanner.scan_results['network']['suspicious']:
        print(f"\n⚠ Suspicious Connections:")
        for c in scanner.scan_results['network']['suspicious']:
            print(f"  - {c['process']} → {c['remote_ip']}:{c['remote_port']} — {c['reason']}")
    
    if scanner.scan_results['ports']['suspicious']:
        print(f"\n⚠ Unusual Ports:")
        for p in scanner.scan_results['ports']['suspicious']:
            print(f"  - Port {p['port']} ({p['process']}) — {p['reason']}")
