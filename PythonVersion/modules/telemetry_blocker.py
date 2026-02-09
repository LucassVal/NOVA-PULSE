"""
NovaPulse Telemetry Blocker
Blocks Microsoft telemetry, antivirus data sharing, and tracking endpoints.
Keeps Windows Defender real-time protection active — only blocks data exfiltration.

Target: Intel Core i5-11300H (Tiger Lake) running Windows 10/11

Methods:
  1. Hosts file: Blocks DNS resolution for telemetry domains
  2. Registry: Disables telemetry flags (AllowTelemetry, Advertising ID, etc.)
  3. Scheduled Tasks: Disables CEIP, Compatibility Appraiser, DiskDiagnostic
  4. Defender: Disables SpyNet/MAPS reporting (keeps protection ON)

Design Decision: We use the hosts file approach because it's:
  - Transparent (user can see exactly what's blocked)
  - Reversible (just remove the lines)
  - No driver/firewall dependency
  - Works even if Windows resets registry keys after updates
"""
import subprocess
import ctypes
import os
import winreg
from datetime import datetime


class TelemetryBlocker:
    """Blocks Microsoft telemetry, tracking, and antivirus data sharing."""
    
    # ──────────────────────────────────────────────
    # TELEMETRY DOMAINS TO BLOCK VIA HOSTS FILE
    # Each domain is documented with what it sends
    # ──────────────────────────────────────────────
    TELEMETRY_DOMAINS = {
        # Core Windows Telemetry
        'vortex.data.microsoft.com': 'Windows telemetry data upload',
        'vortex-win.data.microsoft.com': 'Windows telemetry (alternate)',
        'settings-win.data.microsoft.com': 'Settings sync / telemetry config',
        'telemetry.microsoft.com': 'General telemetry endpoint',
        'df.telemetry.microsoft.com': 'Diagnostics Framework telemetry',
        'watson.telemetry.microsoft.com': 'Crash report / Watson data',
        'oca.telemetry.microsoft.com': 'Office Client Analytics',
        'sqm.telemetry.microsoft.com': 'Software Quality Metrics',
        
        # Diagnostic & Feedback
        'telecommand.telemetry.microsoft.com': 'Telemetry remote commands',
        'reports.wes.df.telemetry.microsoft.com': 'WES diagnostic reports',
        'wes.df.telemetry.microsoft.com': 'Windows Error Services',
        'services.wes.df.telemetry.microsoft.com': 'WES services telemetry',
        'feedback.microsoft-hohm.com': 'Feedback / Home Energy reports',
        'choice.microsoft.com': 'Customer Experience Improvement Program',
        
        # Advertising & Tracking
        'corpext.msitadfs.glbdns2.microsoft.com': 'Corporate telemetry',
        'compatexchange.cloudapp.net': 'Compatibility telemetry exchange',
        'cs1.wpc.v0cdn.net': 'Telemetry CDN',
        'a-0001.a-msedge.net': 'Edge telemetry',
        'statsfe2.update.microsoft.com.akadns.net': 'Update statistics',
        
        # Cortana / Search
        'pre.footprintpredict.com': 'Cortana prediction data',
        'i1.services.social.microsoft.com': 'Social integration telemetry',
    }
    
    # ──────────────────────────────────────────────
    # REGISTRY KEYS TO DISABLE TELEMETRY
    # ──────────────────────────────────────────────
    REGISTRY_TWEAKS = [
        # Disable telemetry level (0 = Security/Off)
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\DataCollection',
            'name': 'AllowTelemetry',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Windows telemetry collection'
        },
        # Disable feedback notifications
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\DataCollection',
            'name': 'DoNotShowFeedbackNotifications',
            'value': 1,
            'type': winreg.REG_DWORD,
            'desc': 'Disable feedback popups'
        },
        # Disable Advertising ID
        {
            'path': r'SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo',
            'name': 'Enabled',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Advertising ID tracking'
        },
        # Disable Activity History
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\System',
            'name': 'EnableActivityFeed',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Activity History'
        },
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\System',
            'name': 'PublishUserActivities',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable publishing user activities'
        },
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\System',
            'name': 'UploadUserActivities',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable uploading user activities'
        },
        # Disable App Telemetry
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows\AppCompat',
            'name': 'AITEnable',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Application Impact Telemetry'
        },
        # Disable Input Personalization (keylogger-like)
        {
            'path': r'SOFTWARE\Policies\Microsoft\InputPersonalization',
            'name': 'RestrictImplicitTextCollection',
            'value': 1,
            'type': winreg.REG_DWORD,
            'desc': 'Disable text/ink data collection'
        },
        {
            'path': r'SOFTWARE\Policies\Microsoft\InputPersonalization',
            'name': 'RestrictImplicitInkCollection',
            'value': 1,
            'type': winreg.REG_DWORD,
            'desc': 'Disable handwriting data sharing'
        },
        # Disable Error Reporting
        {
            'path': r'SOFTWARE\Microsoft\Windows\Windows Error Reporting',
            'name': 'Disabled',
            'value': 1,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Windows Error Reporting'
        },
    ]
    
    # ──────────────────────────────────────────────
    # DEFENDER DATA SHARING (keep protection, block reporting)
    # ──────────────────────────────────────────────
    DEFENDER_TWEAKS = [
        # Disable SpyNet (MAPS) reporting
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows Defender\Spynet',
            'name': 'SpynetReporting',
            'value': 0,
            'type': winreg.REG_DWORD,
            'desc': 'Disable Defender cloud reporting (SpyNet/MAPS)'
        },
        # Disable automatic sample submission
        {
            'path': r'SOFTWARE\Policies\Microsoft\Windows Defender\Spynet',
            'name': 'SubmitSamplesConsent',
            'value': 2,  # 2 = Never send
            'type': winreg.REG_DWORD,
            'desc': 'Disable automatic sample submission'
        },
        # Disable MRT (Malicious Software Removal Tool) reporting
        {
            'path': r'SOFTWARE\Policies\Microsoft\MRT',
            'name': 'DontReportInfectionInformation',
            'value': 1,
            'type': winreg.REG_DWORD,
            'desc': 'Disable MRT infection reporting'
        },
    ]
    
    # ──────────────────────────────────────────────
    # SCHEDULED TASKS TO DISABLE
    # ──────────────────────────────────────────────
    TASKS_TO_DISABLE = [
        r'Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser',
        r'Microsoft\Windows\Application Experience\ProgramDataUpdater',
        r'Microsoft\Windows\Autochk\Proxy',
        r'Microsoft\Windows\Customer Experience Improvement Program\Consolidator',
        r'Microsoft\Windows\Customer Experience Improvement Program\UsbCeip',
        r'Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector',
        r'Microsoft\Windows\Feedback\Siuf\DmClient',
        r'Microsoft\Windows\Feedback\Siuf\DmClientOnScenarioDownload',
    ]
    
    NOVAPULSE_MARKER = '# === NovaPulse Telemetry Blocker ==='
    
    def __init__(self):
        self.blocked_domains = 0
        self.registry_applied = 0
        self.tasks_disabled = 0
        self.defender_hardened = False
        self.status = 'idle'  # idle, scanning, protected, error
    
    def is_admin(self):
        """Check for administrator privileges (required for hosts file and registry)."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    # ──────────────────────────────────────────────
    # HOSTS FILE BLOCKING
    # ──────────────────────────────────────────────
    
    def block_telemetry_hosts(self):
        """
        Block telemetry domains by adding 0.0.0.0 entries to the Windows hosts file.
        
        How it works:
          - Maps telemetry domains to 0.0.0.0 (null route)
          - Windows DNS resolver checks hosts file BEFORE querying DNS
          - Result: telemetry requests fail silently
          
        Why 0.0.0.0 instead of 127.0.0.1:
          - 0.0.0.0 fails instantly (no connection attempt)
          - 127.0.0.1 might try to connect to local services
        """
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
        
        try:
            # Read current hosts file
            with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_content = f.read()
            
            # Check if we already applied our blocks
            if self.NOVAPULSE_MARKER in current_content:
                # Count existing blocks
                self.blocked_domains = current_content.count('0.0.0.0')
                print(f"[TELEMETRY] ✓ Hosts file already protected ({self.blocked_domains} domains blocked)")
                return True
            
            # Build new entries
            new_entries = [
                '',
                self.NOVAPULSE_MARKER,
                f'# Applied: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                '# These domains send your data to Microsoft without consent.',
                '# Remove this block by deleting everything below this marker.',
                ''
            ]
            
            count = 0
            for domain, description in self.TELEMETRY_DOMAINS.items():
                # Skip if already in hosts (from another tool)
                if domain not in current_content:
                    new_entries.append(f'0.0.0.0 {domain}  # {description}')
                    count += 1
            
            new_entries.append(f'# === End NovaPulse ({count} domains blocked) ===')
            new_entries.append('')
            
            # Write to hosts file
            with open(hosts_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(new_entries))
            
            self.blocked_domains = count
            print(f"[TELEMETRY] ✓ Blocked {count} telemetry domains via hosts file")
            return True
            
        except PermissionError:
            print("[TELEMETRY] ✗ Cannot write to hosts file — run as Administrator")
            return False
        except Exception as e:
            print(f"[TELEMETRY] ✗ Hosts file error: {e}")
            return False
    
    # ──────────────────────────────────────────────
    # REGISTRY TWEAKS
    # ──────────────────────────────────────────────
    
    def apply_registry_tweaks(self):
        """
        Disable telemetry via Windows Registry.
        
        These keys control:
          - AllowTelemetry: Master switch for diagnostic data (0=off)
          - AdvertisingInfo: Unique ID for ad targeting
          - ActivityFeed: Tracks app usage, sends to Microsoft
          - InputPersonalization: Collects typing/handwriting data
          - AITEnable: Application telemetry for compatibility
        """
        applied = 0
        
        for tweak in self.REGISTRY_TWEAKS:
            if self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                tweak['path'],
                tweak['name'],
                tweak['value'],
                tweak['type']
            ):
                applied += 1
                print(f"[TELEMETRY] ✓ {tweak['desc']}")
            else:
                print(f"[TELEMETRY] ✗ Failed: {tweak['desc']}")
        
        self.registry_applied = applied
        return applied > 0
    
    def harden_defender(self):
        """
        Disable Windows Defender DATA SHARING while keeping protection active.
        
        IMPORTANT: This does NOT disable Windows Defender.
        It only stops Defender from:
          - Sending file samples to Microsoft (SpyNet/MAPS)
          - Reporting infection data to Microsoft
          - Uploading suspicious files automatically
          
        Real-time protection, virus definitions, and scanning remain ACTIVE.
        """
        applied = 0
        
        for tweak in self.DEFENDER_TWEAKS:
            if self._set_registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                tweak['path'],
                tweak['name'],
                tweak['value'],
                tweak['type']
            ):
                applied += 1
                print(f"[DEFENDER] ✓ {tweak['desc']}")
        
        self.defender_hardened = applied > 0
        return self.defender_hardened
    
    def _set_registry_value(self, hive, path, name, value, reg_type):
        """Set a registry value, creating the key if it doesn't exist."""
        try:
            key = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            winreg.SetValueEx(key, name, 0, reg_type, value)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    
    # ──────────────────────────────────────────────
    # SCHEDULED TASKS
    # ──────────────────────────────────────────────
    
    def disable_telemetry_tasks(self):
        """
        Disable Windows scheduled tasks that collect and send telemetry.
        
        Key tasks disabled:
          - Compatibility Appraiser: Scans all installed software, sends inventory
          - CEIP Consolidator: Aggregates usage data for "improvement program"
          - DiskDiagnostic: Sends disk health data to Microsoft
          - Feedback/Siuf: Collects user feedback data
        """
        disabled = 0
        
        for task in self.TASKS_TO_DISABLE:
            try:
                result = subprocess.run(
                    ['schtasks', '/Change', '/TN', task, '/DISABLE'],
                    capture_output=True, text=True, timeout=5,
                    encoding='utf-8', errors='ignore'
                )
                if result.returncode == 0:
                    disabled += 1
                    task_name = task.split('\\')[-1]
                    print(f"[TELEMETRY] ✓ Disabled task: {task_name}")
            except Exception:
                pass
        
        self.tasks_disabled = disabled
        return disabled > 0
    
    # ──────────────────────────────────────────────
    # FULL PROTECTION
    # ──────────────────────────────────────────────
    
    def apply_full_protection(self):
        """
        Apply all telemetry blocking measures.
        Call this once on startup for complete protection.
        
        Returns a summary dict with counts of blocked items.
        """
        if not self.is_admin():
            print("[TELEMETRY] ⚠ Requires administrator privileges")
            self.status = 'error'
            return self.get_status()
        
        self.status = 'scanning'
        print("[TELEMETRY] ═══════════════════════════════════════")
        print("[TELEMETRY]  NovaPulse Privacy Shield — Activating")
        print("[TELEMETRY] ═══════════════════════════════════════")
        
        self.block_telemetry_hosts()
        self.apply_registry_tweaks()
        self.disable_telemetry_tasks()
        self.harden_defender()
        
        self.status = 'protected'
        
        total = self.blocked_domains + self.registry_applied + self.tasks_disabled
        print(f"\n[TELEMETRY] ═══════════════════════════════════════")
        print(f"[TELEMETRY]  Privacy Shield ACTIVE — {total} items blocked")
        print(f"[TELEMETRY]  Domains: {self.blocked_domains} | Registry: {self.registry_applied} | Tasks: {self.tasks_disabled}")
        print(f"[TELEMETRY]  Defender data sharing: {'BLOCKED' if self.defender_hardened else 'UNCHANGED'}")
        print(f"[TELEMETRY] ═══════════════════════════════════════\n")
        
        return self.get_status()
    
    def get_status(self):
        """Return current protection status for dashboard display."""
        total = self.blocked_domains + self.registry_applied + self.tasks_disabled
        max_possible = len(self.TELEMETRY_DOMAINS) + len(self.REGISTRY_TWEAKS) + len(self.TASKS_TO_DISABLE)
        privacy_score = int((total / max_possible) * 100) if max_possible > 0 else 0
        
        return {
            'status': self.status,
            'blocked_domains': self.blocked_domains,
            'registry_applied': self.registry_applied,
            'tasks_disabled': self.tasks_disabled,
            'defender_hardened': self.defender_hardened,
            'total_blocked': total,
            'privacy_score': privacy_score,
        }
    
    # ──────────────────────────────────────────────
    # RESTORE (undo all changes)
    # ──────────────────────────────────────────────
    
    def restore_hosts(self):
        """Remove NovaPulse entries from hosts file."""
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
        try:
            with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Remove everything between our markers
            new_lines = []
            skip = False
            for line in lines:
                if self.NOVAPULSE_MARKER in line:
                    skip = True
                    continue
                if skip and '=== End NovaPulse' in line:
                    skip = False
                    continue
                if not skip:
                    new_lines.append(line)
            
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            print("[TELEMETRY] ✓ Hosts file restored")
            return True
        except Exception as e:
            print(f"[TELEMETRY] ✗ Restore failed: {e}")
            return False


# ──────────────────────────────────────────────
# SINGLETON
# ──────────────────────────────────────────────
_instance = None

def get_blocker():
    """Get singleton TelemetryBlocker instance."""
    global _instance
    if _instance is None:
        _instance = TelemetryBlocker()
    return _instance


if __name__ == "__main__":
    blocker = TelemetryBlocker()
    print("NovaPulse Telemetry Blocker")
    print("=" * 40)
    status = blocker.apply_full_protection()
    print(f"\nPrivacy Score: {status['privacy_score']}%")
