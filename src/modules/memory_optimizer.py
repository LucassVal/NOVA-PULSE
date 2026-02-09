"""
NovaPulse - Memory Optimizer Pro (Endgame Edition)
Advanced RAM memory optimizations

V4: Compression + Deduplication + File Cache Limit + Working Set Trim
"""
import winreg
import ctypes
import subprocess
import os
import psutil
from typing import Dict, Optional


class MemoryOptimizerPro:
    """
    Advanced Windows memory management optimizations
    
    Includes:
    - Memory compression control
    - Superfetch/SysMain
    - Prefetch
    - Working Set optimization
    """
    
    MEMORY_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    PREFETCH_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, value_type=winreg.REG_DWORD) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[MEMORY] Registry error: {e}")
            return False
    
    def _get_registry_value(self, key_path: str, value_name: str) -> Optional[any]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def _run_service_cmd(self, service: str, action: str) -> bool:
        """Stop/start a Windows service"""
        try:
            result = subprocess.run(
                f"sc {action} {service}",
                shell=True, capture_output=True, text=True
            )
            return result.returncode == 0 or "1062" in result.stderr  # 1062 = already stopped
        except:
            return False
    
    def disable_memory_compression(self) -> bool:
        """
        Disable Windows memory compression
        
        Memory compression uses CPU to compress data in RAM,
        reducing memory usage but increasing CPU usage.
        
        Recommended to disable for:
        - PCs with plenty of RAM (16GB+)
        - Gaming (reduces stuttering)
        - Slower CPUs
        """
        if not self.is_admin:
            return False
        
        try:
            # Disable via PowerShell
            result = subprocess.run(
                'powershell -Command "Disable-MMAgent -MemoryCompression"',
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("[MEMORY] ✓ Memory compression disabled")
                self.applied_changes['compression'] = False
                return True
            else:
                print(f"[MEMORY] ℹ Compression may already be disabled")
                return True
        except Exception as e:
            print(f"[MEMORY] ✗ Error disabling compression: {e}")
            return False
    
    def enable_memory_compression(self) -> bool:
        """Re-enable memory compression"""
        if not self.is_admin:
            return False
        
        try:
            subprocess.run(
                'powershell -Command "Enable-MMAgent -MemoryCompression"',
                shell=True, capture_output=True
            )
            print("[MEMORY] ✓ Memory compression re-enabled")
            self.applied_changes['compression'] = True
            return True
        except:
            return False
    
    def configure_superfetch(self, mode: int = 0) -> bool:
        """
        Configure SysMain (formerly Superfetch)
        
        Modes:
        0 = Disabled (best for SSDs)
        1 = Boot only
        2 = Applications only
        3 = Boot + Applications (Windows default)
        """
        if not self.is_admin:
            return False
        
        success = self._set_registry_value(
            self.PREFETCH_KEY,
            "EnableSuperfetch",
            mode
        )
        
        if mode == 0:
            # Also stop the service
            self._run_service_cmd("SysMain", "stop")
            subprocess.run(
                'sc config SysMain start= disabled',
                shell=True, capture_output=True
            )
            print("[MEMORY] ✓ SysMain/Superfetch disabled")
        else:
            print(f"[MEMORY] ✓ Superfetch configured (mode {mode})")
        
        self.applied_changes['superfetch'] = mode
        return success
    
    def configure_prefetch(self, mode: int = 0) -> bool:
        """
        Configure Prefetch
        
        Modes:
        0 = Disabled
        1 = Applications only
        2 = Boot only
        3 = Boot + Applications (default)
        """
        if not self.is_admin:
            return False
        
        success = self._set_registry_value(
            self.PREFETCH_KEY,
            "EnablePrefetcher",
            mode
        )
        
        if success:
            state = "disabled" if mode == 0 else f"mode {mode}"
            print(f"[MEMORY] ✓ Prefetch {state}")
            self.applied_changes['prefetch'] = mode
        
        return success
    
    def optimize_paging(self, disable_executive: bool = True) -> bool:
        """
        Optimize paging settings
        
        disable_executive: Keep kernel/drivers in RAM (don't page to disk)
        Recommended for PCs with sufficient RAM
        """
        if not self.is_admin:
            return False
        
        value = 1 if disable_executive else 0
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "DisablePagingExecutive",
            value
        )
        
        if success:
            state = "kernel kept in RAM" if disable_executive else "normal paging"
            print(f"[MEMORY] ✓ Paging: {state}")
            self.applied_changes['paging_executive'] = disable_executive
        
        return success
    
    def set_large_system_cache(self, enable: bool = False) -> bool:
        """
        Set large system cache usage
        
        enable=True: Prioritize file cache (servers)
        enable=False: Prioritize applications (desktop/gaming)
        """
        if not self.is_admin:
            return False
        
        value = 1 if enable else 0
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "LargeSystemCache",
            value
        )
        
        if success:
            mode = "cache" if enable else "applications"
            print(f"[MEMORY] ✓ Memory priority: {mode}")
            self.applied_changes['large_cache'] = enable
        
        return success
    
    def optimize_io_page_lock_limit(self) -> bool:
        """
        Increase locked page limit for I/O
        Improves disk performance for intensive workloads
        """
        if not self.is_admin:
            return False
        
        # Value in bytes (0 = automatic, high values = more RAM for I/O)
        # 512MB = 536870912
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "IoPageLockLimit",
            536870912
        )
        
        if success:
            print("[MEMORY] ✓ IoPageLockLimit optimized (512MB)")
            self.applied_changes['io_page_lock'] = True
        
        return success
    
    # ──────────────────────────────────────────────────────────
    #  ENDGAME V4.0 — New features
    # ──────────────────────────────────────────────────────────
    
    def enable_mmagent_combo(self) -> bool:
        """
        Enable the "Triple Combo" — ZRAM-style memory optimization:
        1. MemoryCompression  — compresses inactive pages in RAM (avoids SSD swap)
        2. PageCombining      — deduplicates identical pages (huge for Chrome)
        3. ApplicationPreLaunch — keeps frequently used apps warm
        """
        if not self.is_admin:
            return False
        
        features = ['MemoryCompression', 'PageCombining', 'ApplicationPreLaunch']
        success = True
        
        for feat in features:
            try:
                result = subprocess.run(
                    f'powershell -Command "Enable-MMAgent -{feat}"',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"[MEMORY] ✓ {feat} enabled")
                else:
                    print(f"[MEMORY] ℹ {feat} may already be enabled")
            except Exception as e:
                print(f"[MEMORY] ✗ Error enabling {feat}: {e}")
                success = False
        
        self.applied_changes['mmagent_combo'] = success
        return success
    
    def limit_file_cache(self, max_mb: int = 512) -> bool:
        """
        Cap the Windows file system cache to a hard limit.
        
        Windows silently uses 2-4 GB for file caching — invisible in Task Manager.
        Capping to 512MB frees 1-3 GB of 'phantom' RAM usage.
        Requires SeIncreaseQuotaPrivilege (elevated via ctypes).
        """
        if not self.is_admin:
            return False
        
        try:
            # Enable SeIncreaseQuotaPrivilege via ctypes (no pywin32 needed)
            TOKEN_ADJUST_PRIVILEGES = 0x0020
            TOKEN_QUERY = 0x0008
            SE_PRIVILEGE_ENABLED = 0x00000002
            
            class LUID(ctypes.Structure):
                _fields_ = [("LowPart", ctypes.c_ulong), ("HighPart", ctypes.c_long)]
            
            class LUID_AND_ATTRIBUTES(ctypes.Structure):
                _fields_ = [("Luid", LUID), ("Attributes", ctypes.c_ulong)]
            
            class TOKEN_PRIVILEGES(ctypes.Structure):
                _fields_ = [("PrivilegeCount", ctypes.c_ulong), ("Privileges", LUID_AND_ATTRIBUTES * 1)]
            
            # Open our process token
            token = ctypes.c_void_p()
            ctypes.windll.advapi32.OpenProcessToken(
                ctypes.windll.kernel32.GetCurrentProcess(),
                TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                ctypes.byref(token)
            )
            
            # Lookup SeIncreaseQuotaPrivilege LUID
            luid = LUID()
            ctypes.windll.advapi32.LookupPrivilegeValueW(
                None, "SeIncreaseQuotaPrivilege", ctypes.byref(luid)
            )
            
            # Enable the privilege
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
            ctypes.windll.advapi32.AdjustTokenPrivileges(
                token, False, ctypes.byref(tp), 0, None, None
            )
            ctypes.windll.kernel32.CloseHandle(token)
            
            # Now set the cache limit
            max_bytes = max_mb * 1024 * 1024
            min_bytes = max_bytes // 2
            
            # FILE_CACHE_MAX_HARD_ENABLE (1) | FILE_CACHE_MIN_HARD_ENABLE (4) = 5
            ret = ctypes.windll.kernel32.SetSystemFileCacheSize(
                ctypes.c_size_t(min_bytes),
                ctypes.c_size_t(max_bytes),
                ctypes.c_ulong(5)
            )
            
            if ret != 0:
                print(f"[MEMORY] ✓ File cache capped at {max_mb}MB")
                self.applied_changes['file_cache_limit'] = max_mb
                return True
            else:
                err = ctypes.GetLastError()
                print(f"[MEMORY] ℹ File cache limit not applied (Win32 error {err})")
                return False
                
        except Exception as e:
            print(f"[MEMORY] ✗ File cache error: {e}")
            return False
    
    def trim_working_sets(self) -> int:
        """
        Force idle processes to release unused RAM pages.
        
        This is what apps like Razer Cortex and MemReduct do internally.
        Pages go to compressed memory or standby list, not lost.
        Returns number of processes trimmed.
        """
        if not self.is_admin:
            return 0
        
        # Never touch these — they're critical kernel/security processes
        PROTECTED = {
            'system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
            'services.exe', 'lsass.exe', 'svchost.exe', 'dwm.exe',
            'winlogon.exe', 'fontdrvhost.exe', 'audiodg.exe',
            'novapulse.exe'  # Don't trim ourselves
        }
        
        # PROCESS_SET_QUOTA is all we need (0x0100) — much safer than ALL_ACCESS
        PROCESS_SET_QUOTA = 0x0100
        
        trimmed = 0
        mem_before = psutil.virtual_memory().available
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = (proc.info['name'] or '').lower()
                if name in PROTECTED:
                    continue
                
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_SET_QUOTA, False, proc.info['pid']
                )
                if handle:
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                    ctypes.windll.kernel32.CloseHandle(handle)
                    trimmed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        mem_after = psutil.virtual_memory().available
        freed_mb = max(0, int((mem_after - mem_before) / (1024 * 1024)))
        
        if trimmed > 0:
            print(f"[MEMORY] ✓ Trimmed {trimmed} processes, freed ~{freed_mb}MB")
        
        self.applied_changes['working_set_trim'] = trimmed
        return trimmed
    
    # ──────────────────────────────────────────────────────────
    #  Original features (preserved)
    # ──────────────────────────────────────────────────────────
    
    def clear_standby_list(self) -> int:
        """
        Clear Standby List (cached memory)
        Returns amount freed in MB
        """
        try:
            mem_before = psutil.virtual_memory().available
            
            ntdll = ctypes.windll.ntdll
            # SystemMemoryListInformation = 80, MemoryPurgeStandbyList = 4
            command = ctypes.c_int(4)
            result = ntdll.NtSetSystemInformation(80, ctypes.byref(command), ctypes.sizeof(command))
            
            if result == 0:
                mem_after = psutil.virtual_memory().available
                freed_mb = int((mem_after - mem_before) / (1024 * 1024))
                if freed_mb > 0:
                    print(f"[MEMORY] ✓ Standby List cleared: {freed_mb}MB freed")
                return max(0, freed_mb)
            
        except Exception as e:
            print(f"[MEMORY] ✗ Error clearing standby: {e}")
        
        return 0
    
    def apply_all_optimizations(self, gaming_mode: bool = False) -> Dict[str, bool]:
        """
        Apply all memory optimizations.
        
        gaming_mode=False: Workstation mode (compression ON, dedup ON)
        gaming_mode=True:  Gaming mode (compression OFF, less CPU usage)
        """
        print("\n[MEMORY] Applying Endgame memory optimizations...")
        
        results = {}
        
        # === Stage 1: MMAgent features ===
        if gaming_mode:
            results['compression'] = self.disable_memory_compression()
        else:
            # Workstation: enable ZRAM-style combo (compression + dedup)
            results['mmagent_combo'] = self.enable_mmagent_combo()
        
        # === Stage 2: Registry optimizations (same for both modes) ===
        results['superfetch'] = self.configure_superfetch(0)     # OFF (SSD)
        results['prefetch'] = self.configure_prefetch(0)          # OFF (SSD)
        results['paging'] = self.optimize_paging(disable_executive=True)  # Kernel in RAM
        results['cache'] = self.set_large_system_cache(enable=False)       # Apps > file cache
        results['io_lock'] = self.optimize_io_page_lock_limit()            # 512MB I/O lock
        
        # === Stage 3: Endgame (runtime optimizations) ===
        results['file_cache'] = self.limit_file_cache(512)        # Cap invisible cache
        results['trim'] = self.trim_working_sets() > 0            # Force idle procs to release RAM
        
        success_count = sum(1 for v in results.values() if v)
        print(f"[MEMORY] Result: {success_count}/{len(results)} optimizations applied")
        print("[MEMORY] ⚠ Restart PC for registry changes to take full effect")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Returns current memory settings status"""
        status = {}
        
        try:
            # Check compression
            result = subprocess.run(
                'powershell -Command "(Get-MMAgent).MemoryCompression"',
                shell=True, capture_output=True, text=True
            )
            status['compression'] = "Enabled" if "True" in result.stdout else "Disabled"
        except:
            status['compression'] = "Unknown"
        
        status['superfetch'] = self._get_registry_value(self.PREFETCH_KEY, "EnableSuperfetch")
        status['prefetch'] = self._get_registry_value(self.PREFETCH_KEY, "EnablePrefetcher")
        status['paging_executive'] = self._get_registry_value(self.MEMORY_KEY, "DisablePagingExecutive")
        
        return status


# Singleton
_instance = None

def get_optimizer() -> MemoryOptimizerPro:
    global _instance
    if _instance is None:
        _instance = MemoryOptimizerPro()
    return _instance


if __name__ == "__main__":
    optimizer = MemoryOptimizerPro()
    print("Current status:", optimizer.get_status())
    print()
    optimizer.apply_all_optimizations(gaming_mode=False)
