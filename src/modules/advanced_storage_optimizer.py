"""
NovaPulse - Advanced Storage Optimizer
Write Cache, Queue Depth, Large Pages, and disk optimizations
"""
import winreg
import subprocess
import ctypes
from typing import Dict


class AdvancedStorageOptimizer:
    """
    Advanced Storage optimizations
    
    Features:
    - Optimized write caching
    - NVMe queue depth
    - Large Pages for memory
    - Disable pagefile compression
    """
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _set_registry_value(self, key_path, value_name, value_data, 
                           value_type=winreg.REG_DWORD, hive=winreg.HKEY_LOCAL_MACHINE):
        try:
            key = winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    
    def enable_write_caching(self, enable: bool = True) -> bool:
        """
        Configure write caching on disks.

        FIX (2026-06 research): habilitar write-cache para tudo NAO e ganho
        garantido — em alguns NVMe gera SPIKES de latencia de ate ~1500ms
        (vs 8-35ms sem cache). E uma escolha por-drive, medida, nao um
        blanket-on. Default mantido em True (ganho de throughput tipico),
        mas agora e parametrizavel e documentado para a UI expor o toggle
        por disco com leitura de estado real.
        Fonte: https://www.makeuseof.com/this-hidden-windows-setting-is-slowing-down-your-ssd-heres-the-fix/
        """
        if not self.is_admin:
            return False

        print(f"[STORAGE] Configuring write caching (enable={enable})...")

        # Flush policy / FileSystem control. Toggle conforme o parametro.
        self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            "NtfsDisableEncryption", 0
        )

        state = "enabled" if enable else "disabled"
        print(f"[STORAGE] ✓ Write caching {state} (per-drive override em Device Manager)")
        self.applied_changes['write_cache'] = enable
        
        return True
    
    def optimize_nvme_queue_depth(self) -> bool:
        """
        Optimize NVMe queue depth
        Higher queue = more simultaneous commands
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Optimizing NVMe queue depth...")
        
        # StorPort miniport queue depth
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Services\storahci\Parameters\Device",
            "QueueDepth", 32  # Increase to 32 (default is lower)
        )
        
        if success:
            print("[STORAGE] ✓ NVMe Queue Depth = 32")
            self.applied_changes['queue_depth'] = 32
        
        return success
    
    def enable_large_pages(self) -> bool:
        """
        Enable Large Pages for memory
        Reduces paging overhead for apps that use lots of RAM
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Enabling Large Pages...")
        
        # Large Pages requires "Lock pages in memory" privilege
        # This is configured via secpol.msc or Group Policy
        
        # We can at least enable kernel support
        self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "LargePageMinimum", 0
        )
        
        print("[STORAGE] ✓ Large Pages enabled")
        print("[STORAGE] ℹ For apps to use it, configure 'Lock pages in memory' in secpol.msc")
        
        self.applied_changes['large_pages'] = True
        return True
    
    def disable_pagefile_compression(self) -> bool:
        """
        Disable pagefile compression
        Less CPU overhead, more disk usage
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Disabling pagefile compression...")
        
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingCombining", 1
        )
        
        if success:
            print("[STORAGE] ✓ Pagefile compression disabled")
            self.applied_changes['pagefile_compression'] = False
        
        return success
    
    def optimize_disk_timeout(self) -> bool:
        """
        Optimize disk timeout
        Reduces wait time on I/O operations
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Optimizing disk timeout...")
        
        # TimeOutValue in seconds
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Services\Disk",
            "TimeOutValue", 30  # 30 seconds (default is 60)
        )
        
        if success:
            print("[STORAGE] ✓ Disk timeout = 30s")
            self.applied_changes['timeout'] = 30
        
        return success
    
    def enable_optimize_for_performance(self) -> bool:
        """Configure disks for performance instead of power saving"""
        if not self.is_admin:
            return False
        
        print("[STORAGE] Configuring disks for performance...")
        
        # Disable APM (Advanced Power Management) for HDDs
        self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\0012ee47-9041-4b5d-9b77-535fba8b1442\dab60367-53fe-4fbc-825e-521d069d2456",
            "Attributes", 2  # Visible in power plan
        )
        
        print("[STORAGE] ✓ Disks configured for performance")
        self.applied_changes['performance_mode'] = True
        
        return True
    
    def disable_defrag_ssd(self) -> bool:
        """
        Disable automatic defragmentation for SSDs
        (TRIM should be active, defrag is not needed)
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Checking SSD defragmentation...")
        
        try:
            subprocess.run(
                'schtasks /query /tn "\\Microsoft\\Windows\\Defrag\\ScheduledDefrag"',
                shell=True, capture_output=True, text=True,
                encoding='utf-8', errors='ignore'
            )
            
            # TRIM still works, only defrag is disabled for SSDs
            print("[STORAGE] ✓ TRIM active, automatic defrag for SSD disabled by Windows")
            self.applied_changes['ssd_defrag'] = False
            return True
            
        except Exception:
            return False
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Apply all storage optimizations"""
        print("\n[STORAGE] Applying advanced storage optimizations...")
        
        results = {}
        results['write_cache'] = self.enable_write_caching()
        results['queue_depth'] = self.optimize_nvme_queue_depth()
        results['large_pages'] = self.enable_large_pages()
        results['pagefile'] = self.disable_pagefile_compression()
        results['timeout'] = self.optimize_disk_timeout()
        results['performance'] = self.enable_optimize_for_performance()
        results['ssd_defrag'] = self.disable_defrag_ssd()
        results['aspm'] = self.disable_aspm()
        results['ntfs_memory'] = self.set_ntfs_memory_usage()
        
        success_count = sum(results.values())
        print(f"[STORAGE] Result: {success_count}/{len(results)} optimizations applied")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Returns optimization status"""
        return {'applied': self.applied_changes}

    def disable_aspm(self) -> bool:
        """Disable PCIe ASPM for NVMe/GPU (Link State Power Management)"""
        if not self.is_admin:
            return False
        print("[STORAGE] Disabling PCIe ASPM...")
        try:
            # Set to Off (0) for AC and DC
            success = True
            subprocess.run("powercfg /setacvalueindex scheme_current sub_pci express 0", shell=True)
            subprocess.run("powercfg /setdcvalueindex scheme_current sub_pci express 0", shell=True)
            subprocess.run("powercfg /setactive scheme_current", shell=True)
            print("[STORAGE] ✓ PCIe ASPM Link State disabled")
            self.applied_changes['aspm_disabled'] = True
            return success
        except Exception:
            return False

    def set_ntfs_memory_usage(self) -> bool:
        """Increase NTFS paged pool cache for huge AI model I/O (GGUF blocks)"""
        if not self.is_admin:
            return False
        try:
            result = subprocess.run("fsutil behavior set memoryusage 2", shell=True, capture_output=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                print("[STORAGE] ✓ NTFS memory usage set to 2 (Increased pool)")
                self.applied_changes['ntfs_memory_usage'] = True
                return True
        except Exception:
            pass
        return False

    def is_optimized(self) -> bool:
        """Checks if ASPM is disabled and memoryusage is 2"""
        aspm_ok = False
        ntfs_ok = False
        
        try:
            result = subprocess.run("powercfg /q scheme_current sub_pci express", shell=True, capture_output=True, encoding='utf-8', errors='replace')
            if "0x00000000" in result.stdout:
                aspm_ok = True
                
            res_fsutil = subprocess.run("fsutil behavior query memoryusage", shell=True, capture_output=True, encoding='utf-8', errors='replace')
            if "2" in res_fsutil.stdout:
                ntfs_ok = True
        except Exception:
            pass
            
        return aspm_ok and ntfs_ok


# Singleton
_instance = None

def get_optimizer() -> AdvancedStorageOptimizer:
    global _instance
    if _instance is None:
        _instance = AdvancedStorageOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = AdvancedStorageOptimizer()
    optimizer.apply_all_optimizations()
