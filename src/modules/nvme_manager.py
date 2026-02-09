"""
NVMe/SSD Manager
Specific optimizations for solid state drives (NVMe/SATA SSD)
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
        """Apply file system optimizations (NTFS)"""
        print("[NVMe] Checking NTFS optimizations...")
        
        # 1. Disable Last Access Update (Read IOPS improvement)
        # fsutil behavior set disablelastaccess 1
        try:
            # Check current status
            check = subprocess.run(['fsutil', 'behavior', 'query', 'DisableLastAccess'], 
                                 capture_output=True, text=True)
            
            if " = 1" not in check.stdout:
                print("[NVMe] Disabling 'Last Access Update' (Optimizing IOPS)...")
                subprocess.run(['fsutil', 'behavior', 'set', 'DisableLastAccess', '1'], 
                             capture_output=True)
                print("[NVMe] ✓ Last Access Update disabled")
            else:
                print("[NVMe] ✓ Last Access Update already optimized")
                
        except Exception as e:
            print(f"[NVMe] Error optimizing NTFS: {e}")

    def apply_power_optimizations(self):
        """Prevent SSD from entering sleep (Avoids APST Lag)"""
        try:
            print("[NVMe] Configuring Power Plan (Disk: Never sleep)...")
            # AC (Wall power)
            subprocess.run(['powercfg', '/change', 'disk-timeout-ac', '0'], capture_output=True)
            # DC (Battery - optional, but good for performance)
            subprocess.run(['powercfg', '/change', 'disk-timeout-dc', '0'], capture_output=True)
            print("[NVMe] ✓ Disk sleep disabled")
        except Exception as e:
            print(f"[NVMe] Error configuring power: {e}")

    def run_retrim(self):
        """Execute ReTrim command (Powershell)"""
        print("[NVMe] Starting smart TRIM...")
        try:
            # ReTrim is fast and safe. Defrag is blocked by Windows on SSDs automatically.
            # Removed -Verbose to prevent dashboard glitches
            cmd = "Optimize-Volume -DriveLetter C -ReTrim"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            print("[NVMe] ✓ TRIM completed successfully")
            return True
        except Exception as e:
            print(f"[NVMe] Error running TRIM: {e}")
            return False

    def start_periodic_trim(self):
        """Start periodic TRIM thread"""
        if self.running: return
        
        self.running = True
        
        def trim_loop():
            # Run a TRIM at startup
            time.sleep(10) # Wait for system to stabilize
            self.run_retrim()
            
            while self.running:
                # Wait for interval (default 24h)
                for _ in range(int(self.trim_interval / 10)):
                    if not self.running: break
                    time.sleep(10)
                
                if self.running:
                    self.run_retrim()
        
        self.thread = threading.Thread(target=trim_loop, daemon=True)
        self.thread.start()
        print(f"[NVMe] TRIM scheduler started (Interval: {self.trim_interval/3600:.1f}h)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
