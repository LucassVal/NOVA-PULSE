"""
NovaPulse Windows Defender Hardening v2.2
Configures Windows Defender to maximum protection after removing third-party AV.

This module enables ALL Defender security features that are typically disabled
when a third-party AV (like Kaspersky) is installed. It ensures the user has
enterprise-grade protection using only built-in Windows tools.

What it does:
  1. Enables Real-Time Protection (if disabled by Kaspersky uninstall)
  2. Enables Cloud-Delivered Protection (block-at-first-sight)
  3. Enables PUA Protection (Potentially Unwanted Apps)
  4. Enables Controlled Folder Access (Ransomware Protection)
  5. Enables Network Protection (blocks malicious URLs/IPs)
  6. Enables Attack Surface Reduction (ASR) rules
  7. Enables Exploit Protection (DEP, ASLR, CFG)
  8. Configures Windows Firewall (all profiles enabled)
  9. Schedules daily quick scans + weekly full scans
  10. Enables Tamper Protection reminder

IMPORTANT: Must run as Administrator.

Target: Windows 10/11
"""
import subprocess
import ctypes
import os
import sys
from datetime import datetime


def is_admin():
    """Check if running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_ps(command, description=""):
    """Run a PowerShell command and return success status."""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', command],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  ✓ {description}")
            return True
        else:
            # Some commands fail silently on Home edition
            error = result.stderr.strip()
            if 'not recognized' in error or 'not found' in error:
                print(f"  ⚠ {description} (not available on this Windows edition)")
            else:
                print(f"  ⚠ {description} (may require manual action)")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠ {description} (timeout)")
        return False
    except Exception as e:
        print(f"  ✗ {description}: {e}")
        return False


def run_cmd(command, description=""):
    """Run a CMD command."""
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  ✓ {description}")
            return True
        else:
            print(f"  ⚠ {description}")
            return False
    except Exception as e:
        print(f"  ✗ {description}: {e}")
        return False


class DefenderHardener:
    """
    Configures Windows Defender to maximum protection.

    After uninstalling Kaspersky (or any third-party AV), Windows Defender
    should activate automatically, but many advanced features remain OFF
    by default. This class enables them all.
    """

    def __init__(self):
        self.results = {}
        self.total_applied = 0
        self.total_failed = 0

    def harden_all(self):
        """Apply all hardening steps."""
        if not is_admin():
            print("\n⚠️  MUST RUN AS ADMINISTRATOR!")
            print("   Right-click → Run as administrator\n")
            return self.get_status()

        print("\n" + "=" * 60)
        print("🛡️  NovaPulse Defender Hardening v2.2")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Windows: {self._get_windows_version()}")
        print("=" * 60 + "\n")

        self._step1_realtime_protection()
        self._step2_cloud_protection()
        self._step3_pua_protection()
        self._step4_controlled_folder_access()
        self._step5_network_protection()
        self._step6_asr_rules()
        self._step7_exploit_protection()
        self._step8_firewall()
        self._step9_scan_schedule()
        self._step10_tamper_protection()

        # Summary
        print("\n" + "=" * 60)
        print(f"✅ Applied: {self.total_applied} | ⚠️ Skipped: {self.total_failed}")
        print("=" * 60)

        return self.get_status()

    def _get_windows_version(self):
        """Get Windows version string."""
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 '(Get-CimInstance Win32_OperatingSystem).Caption'],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() or "Windows"
        except:
            return "Windows"

    def _step1_realtime_protection(self):
        """Step 1: Enable Real-Time Protection."""
        print("─── Step 1: Real-Time Protection ───")

        cmds = [
            ('Set-MpPreference -DisableRealtimeMonitoring $false',
             'Real-time monitoring ON'),
            ('Set-MpPreference -DisableBehaviorMonitoring $false',
             'Behavior monitoring ON'),
            ('Set-MpPreference -DisableIOAVProtection $false',
             'Downloaded files scan ON'),
            ('Set-MpPreference -DisableScriptScanning $false',
             'Script scanning ON'),
        ]

        for cmd, desc in cmds:
            if run_ps(cmd, desc):
                self.total_applied += 1
            else:
                self.total_failed += 1
        print()

    def _step2_cloud_protection(self):
        """Step 2: Enable Cloud-Delivered Protection (block-at-first-sight)."""
        print("─── Step 2: Cloud Protection ───")

        cmds = [
            ('Set-MpPreference -MAPSReporting Advanced',
             'Cloud protection: Advanced (block-at-first-sight)'),
            ('Set-MpPreference -SubmitSamplesConsent SendAllSamples',
             'Auto sample submission ON'),
            ('Set-MpPreference -CloudBlockLevel High',
             'Cloud block level: High'),
            ('Set-MpPreference -CloudExtendedTimeout 50',
             'Cloud timeout: 50 seconds (default: 10)'),
        ]

        for cmd, desc in cmds:
            if run_ps(cmd, desc):
                self.total_applied += 1
            else:
                self.total_failed += 1
        print()

    def _step3_pua_protection(self):
        """Step 3: Enable PUA (Potentially Unwanted Application) Protection."""
        print("─── Step 3: PUA Protection ───")

        if run_ps('Set-MpPreference -PUAProtection Enabled',
                   'Block Potentially Unwanted Apps (adware, toolbars)'):
            self.total_applied += 1
        else:
            self.total_failed += 1
        print()

    def _step4_controlled_folder_access(self):
        """Step 4: Enable Controlled Folder Access (Ransomware Protection)."""
        print("─── Step 4: Ransomware Protection ───")

        cmds = [
            ('Set-MpPreference -EnableControlledFolderAccess Enabled',
             'Controlled Folder Access ON (blocks unauthorized writes)'),
        ]

        for cmd, desc in cmds:
            if run_ps(cmd, desc):
                self.total_applied += 1
            else:
                self.total_failed += 1

        # Add common protected folders
        protected = [
            os.path.expanduser('~\\Documents'),
            os.path.expanduser('~\\Desktop'),
            os.path.expanduser('~\\Pictures'),
            os.path.expanduser('~\\Downloads'),
        ]
        for folder in protected:
            if os.path.exists(folder):
                run_ps(f'Add-MpPreference -ControlledFolderAccessProtectedFolders "{folder}"',
                       f'  Protected: {os.path.basename(folder)}')

        print("  ℹ️  If apps are blocked, add them to the allowed list in Windows Security")
        print()

    def _step5_network_protection(self):
        """Step 5: Enable Network Protection (blocks malicious URLs/IPs)."""
        print("─── Step 5: Network Protection ───")

        if run_ps('Set-MpPreference -EnableNetworkProtection Enabled',
                   'Network Protection ON (blocks phishing/exploit sites)'):
            self.total_applied += 1
        else:
            self.total_failed += 1
        print()

    def _step6_asr_rules(self):
        """
        Step 6: Enable Attack Surface Reduction (ASR) rules.

        These are enterprise-grade rules that block common attack vectors.
        Each rule has a GUID and can be set to Block (1), Audit (2), or Off (0).
        We set critical ones to Block, less common to Audit.
        """
        print("─── Step 6: Attack Surface Reduction ───")

        # Critical rules → Block mode (1)
        block_rules = {
            # Block Office macros from creating child processes
            'D4F940AB-401B-4EFC-AADC-AD5F3C50688A': 'Block Office macros → child processes',
            # Block Office apps from creating executable content
            '3B576869-A4EC-4529-8536-B80A7769E899': 'Block Office → executable content',
            # Block execution of obfuscated scripts
            '5BEB7EFE-FD9A-4556-801D-275E5FFC04CC': 'Block obfuscated scripts',
            # Block executable content from email/webmail
            'BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550': 'Block executable email attachments',
            # Block untrusted/unsigned processes from USB
            'B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4': 'Block untrusted USB processes',
            # Block credential stealing from LSASS
            '9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2': 'Block credential stealing (LSASS)',
            # Block process creation from WMI/PSExec
            'D1E49AAC-8F56-4280-B9BA-993A6D77406C': 'Block WMI process creation',
        }

        # Less common rules → Audit mode (2) to avoid false positives
        audit_rules = {
            # Block Win32 API calls from Office macros
            '92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B': 'Audit: Office macro Win32 calls',
            # Block JavaScript/VBScript from launching executables
            'D3E037E1-3EB8-44C8-A917-57927947596D': 'Audit: JS/VBS launching executables',
        }

        for guid, desc in block_rules.items():
            if run_ps(f'Add-MpPreference -AttackSurfaceReductionRules_Ids {guid} '
                      f'-AttackSurfaceReductionRules_Actions Enabled', desc):
                self.total_applied += 1
            else:
                self.total_failed += 1

        for guid, desc in audit_rules.items():
            run_ps(f'Add-MpPreference -AttackSurfaceReductionRules_Ids {guid} '
                   f'-AttackSurfaceReductionRules_Actions AuditMode', desc)

        print()

    def _step7_exploit_protection(self):
        """Step 7: Enable Exploit Protection (DEP, ASLR, CFG)."""
        print("─── Step 7: Exploit Protection ───")

        # System-level exploit mitigations
        mitigations = [
            ('Set-ProcessMitigation -System -Enable DEP',
             'DEP (Data Execution Prevention) ON'),
            ('Set-ProcessMitigation -System -Enable ASLR:BottomUp,ASLR:HighEntropy',
             'ASLR (Address Space Layout Randomization) ON'),
            ('Set-ProcessMitigation -System -Enable CFG',
             'CFG (Control Flow Guard) ON'),
        ]

        for cmd, desc in mitigations:
            if run_ps(cmd, desc):
                self.total_applied += 1
            else:
                self.total_failed += 1
        print()

    def _step8_firewall(self):
        """Step 8: Ensure Windows Firewall is enabled on all profiles."""
        print("─── Step 8: Windows Firewall ───")

        profiles = ['domain', 'private', 'public']
        for profile in profiles:
            if run_cmd(f'netsh advfirewall set {profile}profile state on',
                       f'Firewall {profile.title()} profile: ON'):
                self.total_applied += 1
            else:
                self.total_failed += 1

        # Block inbound by default, allow outbound
        run_cmd('netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound',
                'Default: Block inbound, Allow outbound')
        print()

    def _step9_scan_schedule(self):
        """Step 9: Configure scan schedules."""
        print("─── Step 9: Scan Schedule ───")

        cmds = [
            # Quick scan daily at 12:00
            ('Set-MpPreference -ScanScheduleQuickScanTime 12:00:00',
             'Daily quick scan at 12:00'),
            # Full scan weekly on Sunday
            ('Set-MpPreference -ScanScheduleDay 1',
             'Weekly full scan: Sunday'),
            ('Set-MpPreference -ScanScheduleTime 03:00:00',
             'Full scan at 03:00 AM'),
            # Scan all downloaded files
            ('Set-MpPreference -DisableArchiveScanning $false',
             'Archive scanning: ON (ZIP, RAR, etc.)'),
            # Email scanning
            ('Set-MpPreference -DisableEmailScanning $false',
             'Email scanning: ON'),
        ]

        for cmd, desc in cmds:
            if run_ps(cmd, desc):
                self.total_applied += 1
            else:
                self.total_failed += 1
        print()

    def _step10_tamper_protection(self):
        """Step 10: Reminder about Tamper Protection."""
        print("─── Step 10: Tamper Protection ───")
        print("  ℹ️  Tamper Protection cannot be enabled via script.")
        print("  ℹ️  To enable manually:")
        print("      1. Open Windows Security")
        print("      2. Virus & threat protection → Manage settings")
        print("      3. Turn ON 'Tamper Protection'")
        print("  ℹ️  This prevents malware from disabling Defender.\n")

    def get_status(self):
        """Return hardening status for dashboard integration."""
        return {
            'total_applied': self.total_applied,
            'total_failed': self.total_failed,
            'status': 'hardened' if self.total_applied > 15 else 'partial',
            'score': min(100, int((self.total_applied / 25) * 100)),
        }

    def quick_check(self):
        """Quick check if Defender is active (for dashboard)."""
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 '(Get-MpComputerStatus).RealTimeProtectionEnabled'],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip().lower() == 'true'
        except:
            return False


# Singleton
_instance = None

def get_hardener() -> DefenderHardener:
    """Return singleton DefenderHardener instance."""
    global _instance
    if _instance is None:
        _instance = DefenderHardener()
    return _instance


if __name__ == "__main__":
    print("\n🛡️  NovaPulse Defender Hardening")
    print("   Run this AFTER uninstalling Kaspersky.\n")

    if not is_admin():
        print("❌ Must run as Administrator!")
        print("   Right-click → Run as administrator")
        sys.exit(1)

    hardener = DefenderHardener()
    status = hardener.harden_all()

    print(f"\n🔒 Protection Score: {status['score']}%")
    print(f"   Status: {status['status'].upper()}")

    # Trigger a quick scan
    print("\n🔍 Starting a quick scan...")
    run_ps('Start-MpScan -ScanType QuickScan', 'Quick scan initiated')

    print("\n✅ Done! Your system is now protected by Windows Defender.")
    print("   Recommended: Restart your PC to ensure all changes take effect.")
