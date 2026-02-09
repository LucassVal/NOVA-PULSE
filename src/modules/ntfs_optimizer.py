"""
NovaPulse - NTFS Optimizer
NTFS file system optimizations for better I/O
"""
import subprocess
import ctypes
import winreg
from typing import Dict, Tuple


class NTFSOptimizer:
    """Optimizes NTFS file system settings"""
    
    def __init__(self):
        self.applied_changes = {}
        self.is_admin = self._check_admin()
    
    def _check_admin(self) -> bool:
        """Check admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_fsutil(self, args: str) -> Tuple[bool, str]:
        """Execute fsutil command"""
        try:
            result = subprocess.run(
                f"fsutil behavior set {args}",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def disable_8dot3_names(self) -> bool:
        """
        Disable 8.3 short name creation (legacy DOS)
        Impact: Improves file creation performance
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("disable8dot3 1")
        self.applied_changes['8dot3'] = success
        
        if success:
            print("[NTFS] ✓ 8.3 filenames disabled")
        else:
            print(f"[NTFS] ✗ Error disabling 8.3: {output}")
        
        return success
    
    def disable_last_access_time(self) -> bool:
        """
        Disable Last Access Time updates
        Impact: Reduces unnecessary writes (especially on SSDs)
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("disablelastaccess 1")
        self.applied_changes['lastaccess'] = success
        
        if success:
            print("[NTFS] ✓ Last Access Time disabled")
        else:
            print(f"[NTFS] ✗ Error disabling Last Access: {output}")
        
        return success
    
    def optimize_memory_usage(self, large_cache: bool = False) -> bool:
        """
        Optimize memory usage for file cache
        large_cache=True: Prioritize cache (good for servers)
        large_cache=False: Prioritize applications (good for desktop/gaming)
        """
        if not self.is_admin:
            return False
        
        value = 1 if large_cache else 0
        success, output = self._run_fsutil(f"memoryusage {value}")
        self.applied_changes['memoryusage'] = success
        
        if success:
            mode = "cache" if large_cache else "apps"
            print(f"[NTFS] ✓ Memory optimized for {mode}")
        
        return success
    
    def disable_encryption(self) -> bool:
        """
        Disable EFS (Encrypting File System) on the system
        Impact: Slight I/O improvement
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("encryptpagingfile 0")
        self.applied_changes['encryption'] = success
        
        if success:
            print("[NTFS] ✓ Encryption pagefile disabled")
        
        return success
    
    def set_mft_zone(self, size: int = 2) -> bool:
        """
        Set MFT Zone size (1-4)
        1 = 12.5%, 2 = 25%, 3 = 37.5%, 4 = 50%
        Larger = less fragmentation for many small files
        """
        if not self.is_admin:
            return False
        
        size = max(1, min(4, size))
        success, output = self._run_fsutil(f"mftzone {size}")
        self.applied_changes['mftzone'] = success
        
        if success:
            print(f"[NTFS] ✓ MFT Zone set to {size}")
        
        return success
    
    def apply_all_optimizations(self, gaming_mode: bool = True) -> Dict[str, bool]:
        """
        Apply all NTFS optimizations
        gaming_mode=True: Prioritize applications over cache
        """
        print("\n[NTFS] Applying file system optimizations...")
        
        results = {}
        results['8dot3'] = self.disable_8dot3_names()
        results['lastaccess'] = self.disable_last_access_time()
        results['memoryusage'] = self.optimize_memory_usage(large_cache=not gaming_mode)
        results['encryption'] = self.disable_encryption()
        results['mftzone'] = self.set_mft_zone(2)
        
        success_count = sum(results.values())
        print(f"[NTFS] Result: {success_count}/{len(results)} optimizations applied")
        
        return results
    
    def get_status(self) -> Dict[str, str]:
        """Returns current NTFS settings status"""
        status = {}
        
        try:
            # Query current settings
            result = subprocess.run(
                "fsutil behavior query disable8dot3",
                shell=True, capture_output=True, text=True
            )
            status['8dot3'] = "Disabled" if "1" in result.stdout else "Enabled"
            
            result = subprocess.run(
                "fsutil behavior query disablelastaccess",
                shell=True, capture_output=True, text=True
            )
            status['lastaccess'] = "Disabled" if "1" in result.stdout or "2" in result.stdout else "Enabled"
            
        except:
            pass
        
        return status


# Singleton
_instance = None

def get_optimizer() -> NTFSOptimizer:
    global _instance
    if _instance is None:
        _instance = NTFSOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = NTFSOptimizer()
    print("Current status:", optimizer.get_status())
    # optimizer.apply_all_optimizations()
