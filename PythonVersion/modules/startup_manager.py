"""
NovaPulse Windows Startup Manager v2.2
Registers NovaPulse to start with Windows using Task Scheduler.

Why Task Scheduler instead of Registry Run key:
  - Task Scheduler can run with HIGHEST privileges (admin) automatically
  - Runs at SYSTEM STARTUP (before user login) — earliest possible
  - More reliable than HKCU\Run (survives registry cleaners)
  - Can set conditions (only on AC power, network available, etc.)

The BIOS/UEFI level is NOT accessible from user-mode applications.
The earliest we can run is after the Windows kernel loads, which is
exactly what "At startup" trigger does in Task Scheduler.

Boot sequence:
  BIOS/UEFI → Bootloader → Windows Kernel → Services → Task Scheduler
  → NovaPulse (runs here, before user login screen)

Requires: Administrator privileges
Target: Windows 10/11
"""
import subprocess
import ctypes
import os
import sys


def is_admin():
    """Check admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class StartupManager:
    """Manages NovaPulse auto-start via Windows Task Scheduler."""

    TASK_NAME = "NovaPulse"

    def __init__(self, script_path=None):
        """
        Args:
            script_path: Full path to novapulse.py or NovaPulse.exe.
                         Auto-detects if not provided.
        """
        if script_path:
            self.script_path = script_path
        else:
            self.script_path = self._detect_path()

    def _detect_path(self):
        """Auto-detect NovaPulse location."""
        # Check if running as .exe (PyInstaller)
        if getattr(sys, 'frozen', False):
            return sys.executable

        # Running as .py — find novapulse.py relative to this module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(module_dir)
        script = os.path.join(project_dir, 'novapulse.py')
        if os.path.exists(script):
            return script

        return None

    def register(self):
        """
        Register NovaPulse to start at Windows boot.

        Creates a scheduled task that runs with HIGHEST privileges
        at system startup (before user login).

        Returns: True if successful
        """
        if not is_admin():
            print("⚠️  Must run as Administrator to register startup")
            return False

        if not self.script_path:
            print("✗ Could not detect NovaPulse path")
            return False

        # Remove old task if exists
        self.unregister(quiet=True)

        # Build the command to run
        if self.script_path.endswith('.exe'):
            # Running as compiled executable
            action = f'"{self.script_path}"'
            program = self.script_path
        else:
            # Running as Python script — find python.exe
            python_exe = sys.executable
            program = python_exe
            action = f'"{python_exe}" "{self.script_path}"'

        # Working directory
        working_dir = os.path.dirname(self.script_path)

        # Create scheduled task via schtasks
        # /SC ONSTART = Run at system startup (before login)
        # /RL HIGHEST = Run with admin privileges
        # /DELAY 0000:30 = 30 second delay (let Windows finish loading)
        cmd = (
            f'schtasks /Create /TN "{self.TASK_NAME}" '
            f'/TR "{action}" '
            f'/SC ONSTART '
            f'/RL HIGHEST '
            f'/DELAY 0000:30 '
            f'/F '
            f'/RU "{os.environ.get("USERNAME", "SYSTEM")}"'
        )

        try:
            result = subprocess.run(
                cmd, shell=True,
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                print(f"✓ NovaPulse registered for Windows startup")
                print(f"  Path: {self.script_path}")
                print(f"  Trigger: At system startup (30s delay)")
                print(f"  Privileges: HIGHEST (Administrator)")
                return True
            else:
                # Fallback: try with PowerShell (more reliable on some systems)
                return self._register_powershell(program, working_dir)

        except Exception as e:
            print(f"✗ Failed to register: {e}")
            return False

    def _register_powershell(self, program, working_dir):
        """Fallback registration using PowerShell."""
        try:
            if self.script_path.endswith('.exe'):
                arg = ""
                exe = self.script_path
            else:
                exe = sys.executable
                arg = f'"{self.script_path}"'

            ps_cmd = f'''
$action = New-ScheduledTaskAction -Execute '"{exe}"' -Argument '{arg}' -WorkingDirectory '"{working_dir}"'
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = 'PT30S'
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "{os.environ.get("USERNAME", "SYSTEM")}" -RunLevel Highest
Register-ScheduledTask -TaskName "{self.TASK_NAME}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
'''
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_cmd],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                print(f"✓ NovaPulse registered for startup (PowerShell)")
                return True
            else:
                print(f"✗ PowerShell registration failed: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"✗ PowerShell fallback failed: {e}")
            return False

    def unregister(self, quiet=False):
        """Remove NovaPulse from Windows startup."""
        try:
            result = subprocess.run(
                f'schtasks /Delete /TN "{self.TASK_NAME}" /F',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and not quiet:
                print(f"✓ NovaPulse removed from Windows startup")
            return result.returncode == 0
        except:
            return False

    def is_registered(self):
        """Check if NovaPulse is registered for startup."""
        try:
            result = subprocess.run(
                f'schtasks /Query /TN "{self.TASK_NAME}" /FO CSV /NH',
                shell=True, capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and self.TASK_NAME in result.stdout
        except:
            return False

    def get_status(self):
        """Return startup status for dashboard."""
        registered = self.is_registered()
        return {
            'registered': registered,
            'path': self.script_path,
            'method': 'Task Scheduler (ONSTART)',
            'status': 'ENABLED' if registered else 'DISABLED',
        }


# Singleton
_instance = None

def get_startup_manager() -> StartupManager:
    """Return singleton StartupManager instance."""
    global _instance
    if _instance is None:
        _instance = StartupManager()
    return _instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='NovaPulse Startup Manager')
    parser.add_argument('action', choices=['register', 'unregister', 'status'],
                        help='Action to perform')
    args = parser.parse_args()

    manager = StartupManager()

    if args.action == 'register':
        if not is_admin():
            print("❌ Must run as Administrator!")
            sys.exit(1)
        manager.register()

    elif args.action == 'unregister':
        if not is_admin():
            print("❌ Must run as Administrator!")
            sys.exit(1)
        manager.unregister()

    elif args.action == 'status':
        status = manager.get_status()
        print(f"Startup: {status['status']}")
        print(f"Method: {status['method']}")
        print(f"Path: {status['path']}")
