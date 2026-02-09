"""
NovaPulse - Advanced CPU Optimizer
C-States, Turbo Boost, Large Pages, and advanced optimizations
"""
import winreg
import subprocess
import ctypes
from typing import Dict, Optional


class AdvancedCPUOptimizer:
    """
    Advanced CPU optimizations
    
    Features:
    - C-States control (disables power-saving states)
    - Turbo Boost lock (forces turbo always active)
    - Large System Cache
    - Optimized processor scheduling
    """
    
    POWER_KEY = r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings"
    PROCESSOR_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path, value_name, value_data, 
                           value_type=winreg.REG_DWORD, hive=winreg.HKEY_LOCAL_MACHINE):
        try:
            key = winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def _run_powercfg(self, args: str) -> bool:
        try:
            result = subprocess.run(
                f"powercfg {args}",
                shell=True, capture_output=True, text=True,
                encoding='utf-8', errors='ignore'
            )
            return result.returncode == 0
        except:
            return False
    
    def disable_c_states(self) -> bool:
        """
        Disable deep processor C-States
        C-States save power but increase wake-up latency
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Disabling deep C-States...")
        
        success = self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 5d76a2ca-e8c0-402f-a133-2158492d58ad 1")
        self._run_powercfg("-setactive scheme_current")
        
        if success:
            print("[CPU ADV] ✓ Deep C-States disabled (lower latency)")
            self.applied_changes['c_states'] = False
        
        return success
    
    def force_turbo_boost(self) -> bool:
        """
        Force Turbo Boost always active
        Processor maintains maximum frequency as long as thermals allow
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Forcing Turbo Boost...")
        
        # Processor Performance Boost Mode
        # 0 = Disabled, 1 = Enabled, 2 = Aggressive, 3 = Efficient Aggressive
        success = self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2")
        self._run_powercfg("-setactive scheme_current")
        
        # Minimum processor state = 100% (forces high frequency)
        self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c 100")
        self._run_powercfg("-setactive scheme_current")
        
        if success:
            print("[CPU ADV] ✓ Turbo Boost forced (aggressive mode)")
            self.applied_changes['turbo_boost'] = True
        
        return success
    
    def enable_large_system_cache(self) -> bool:
        """
        Enable Large System Cache
        Uses more RAM for disk cache (better I/O)
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Enabling Large System Cache...")
        
        success = self._set_registry_value(self.PROCESSOR_KEY, "LargeSystemCache", 1)
        
        if success:
            print("[CPU ADV] ✓ Large System Cache enabled")
            self.applied_changes['large_cache'] = True
        
        return success
    
    def optimize_processor_scheduling(self) -> bool:
        """
        Optimize processor scheduling for foreground apps
        0 = Shorter quantum for foreground, 38 = Longer quantum for background
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Optimizing processor scheduling...")
        
        # Win32PrioritySeparation
        # 38 = Short-quantum, foreground boost (best for gaming)
        # 2 = Long-quantum, no boost (best for servers)
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation", 38
        )
        
        if success:
            print("[CPU ADV] ✓ Foreground apps prioritized")
            self.applied_changes['scheduling'] = True
        
        return success
    
    def disable_power_throttling(self) -> bool:
        """
        Disable Windows Power Throttling
        Windows 10+ throttles background apps - disable for performance
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Disabling Power Throttling...")
        
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff", 1
        )
        
        if success:
            print("[CPU ADV] ✓ Power Throttling disabled")
            self.applied_changes['power_throttling'] = False
        
        return success
    
    def optimize_interrupt_affinity(self) -> bool:
        """
        Optimize interrupt affinity
        Better distributes IRQs across cores
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Optimizing interrupt affinity...")
        
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel",
            "DistributeTimers", 1
        )
        
        if success:
            print("[CPU ADV] ✓ Timer distribution optimized")
            self.applied_changes['interrupt_affinity'] = True
        
        return success
    
    def set_svchost_splitting(self) -> bool:
        """
        Configure svchost splitting for systems with more RAM
        Separates services into individual processes (better for debugging and isolation)
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Configuring svchost splitting...")
        
        # SvcHostSplitThresholdInKB - defines threshold for split
        # 0 = Force split, high value = group
        # For 16GB+ RAM, we can force split
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control",
            "SvcHostSplitThresholdInKB", 0x00380000  # ~3.5GB threshold
        )
        
        if success:
            print("[CPU ADV] ✓ Svchost splitting configured")
            self.applied_changes['svchost_split'] = True
        
        return success
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Apply all advanced CPU optimizations"""
        print("\n[CPU ADV] Applying advanced CPU optimizations...")
        
        results = {}
        results['c_states'] = self.disable_c_states()
        results['turbo_boost'] = self.force_turbo_boost()
        results['large_cache'] = self.enable_large_system_cache()
        results['scheduling'] = self.optimize_processor_scheduling()
        results['power_throttling'] = self.disable_power_throttling()
        results['interrupt'] = self.optimize_interrupt_affinity()
        results['svchost'] = self.set_svchost_splitting()
        
        success_count = sum(results.values())
        print(f"[CPU ADV] Result: {success_count}/{len(results)} optimizations applied")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Returns optimization status"""
        return {'applied': self.applied_changes}


# Singleton
_instance = None

def get_optimizer() -> AdvancedCPUOptimizer:
    global _instance
    if _instance is None:
        _instance = AdvancedCPUOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = AdvancedCPUOptimizer()
    optimizer.apply_all_optimizations()
