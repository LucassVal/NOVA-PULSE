"""
NovaPulse - Memory Optimizer Pro
Advanced RAM memory optimizations
"""
import winreg
import ctypes
import subprocess
import os
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
    
    def clear_standby_list(self) -> int:
        """
        Clear Standby List (cached memory)
        Returns amount freed in MB
        """
        try:
            import psutil
            mem_before = psutil.virtual_memory().available
            
            # Use RAMMap or system command
            # Through the NtSetSystemInformation API
            ntdll = ctypes.windll.ntdll
            
            # SystemMemoryListInformation = 80
            # MemoryPurgeStandbyList = 4
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
    
    def apply_all_optimizations(self, gaming_mode: bool = True) -> Dict[str, bool]:
        """
        Apply all memory optimizations
        
        gaming_mode: Optimize for gaming (disable caches, prioritize apps)
        """
        print("\n[MEMORY] Applying memory optimizations...")
        
        results = {}
        
        if gaming_mode:
            # For gaming: disable everything that competes for RAM
            results['compression'] = self.disable_memory_compression()
            results['superfetch'] = self.configure_superfetch(0)  # Disabled
            results['prefetch'] = self.configure_prefetch(0)  # Disabled
            results['paging'] = self.optimize_paging(disable_executive=True)
            results['cache'] = self.set_large_system_cache(enable=False)
            results['io_lock'] = self.optimize_io_page_lock_limit()
        else:
            # For general use: balanced
            results['compression'] = self.disable_memory_compression()  # Still disable for CPUs
            results['superfetch'] = self.configure_superfetch(3)  # Keep for HDDs
            results['prefetch'] = self.configure_prefetch(3)
            results['paging'] = self.optimize_paging(disable_executive=True)
            results['cache'] = self.set_large_system_cache(enable=False)
            results['io_lock'] = self.optimize_io_page_lock_limit()
        
        success_count = sum(results.values())
        print(f"[MEMORY] Result: {success_count}/{len(results)} optimizations applied")
        print("[MEMORY] ⚠ Restart PC to apply all changes")
        
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
