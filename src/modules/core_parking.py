"""
NovaPulse - Core Parking Manager
Controls CPU core parking (Core Parking)
"""
import winreg
import ctypes
import subprocess
from typing import Dict, Optional


class CoreParkingManager:
    """
    Manages Windows Core Parking
    
    Core Parking is a feature that "sleeps" inactive cores to save energy.
    Disabling it improves responsiveness at the cost of higher power consumption.
    """
    
    # Power settings GUIDs
    PROCESSOR_SUBGROUP = "54533251-82be-4824-96c1-47b60b740d00"
    
    # Core Parking settings
    CORE_PARKING_MIN = "0cc5b647-c1df-4637-891a-dec35c318583"  # Min cores
    CORE_PARKING_MAX = "ea062031-0e34-4ff1-9b6d-eb1059334028"  # Max cores
    CORE_PARKING_INCREASE_TIME = "2ddd5a84-5a71-437e-912a-db0b8c788732"
    CORE_PARKING_DECREASE_TIME = "dfd10d17-d5eb-45dd-877a-9a34ddd15c82"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_powercfg(self, args: str) -> bool:
        """Execute powercfg command"""
        try:
            result = subprocess.run(
                f"powercfg {args}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _set_power_setting(self, setting_guid: str, value: int, ac: bool = True) -> bool:
        """Set a power setting via powercfg"""
        power_type = "/setacvalueindex" if ac else "/setdcvalueindex"
        
        cmd = f"{power_type} scheme_current sub_processor {setting_guid} {value}"
        return self._run_powercfg(cmd)
    
    def disable_core_parking(self) -> bool:
        """
        Disable Core Parking completely
        All cores remain active at all times
        
        Impact:
        - ⚡ Faster response
        - ⚡ Less stuttering in games
        - 🔋 Higher power consumption
        """
        if not self.is_admin:
            print("[PARKING] ✗ Requires administrator privileges")
            return False
        
        print("[PARKING] Disabling Core Parking...")
        
        success = True
        
        # Min cores unparked = 100% (all active)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, 100, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, 100, ac=False)
        
        # Max cores unparked = 100%
        success &= self._set_power_setting(self.CORE_PARKING_MAX, 100, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MAX, 100, ac=False)
        
        # Apply changes
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print("[PARKING] ✓ Core Parking disabled (100% cores active)")
            self.applied_changes['parking_disabled'] = True
        else:
            print("[PARKING] ✗ Error disabling Core Parking")
        
        return success
    
    def enable_core_parking(self, min_percent: int = 50) -> bool:
        """
        Re-enable Core Parking with custom configuration
        min_percent: Minimum cores that stay active (0-100)
        """
        if not self.is_admin:
            return False
        
        min_percent = max(0, min(100, min_percent))
        
        success = True
        success &= self._set_power_setting(self.CORE_PARKING_MIN, min_percent, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, min_percent, ac=False)
        
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print(f"[PARKING] ✓ Core Parking re-enabled (min {min_percent}% cores)")
            self.applied_changes['parking_disabled'] = False
        
        return success
    
    def optimize_parking_timers(self) -> bool:
        """
        Optimize parking timers for faster response
        - Time to increase cores: Reduced
        - Time to decrease cores: Increased
        """
        if not self.is_admin:
            return False
        
        success = True
        
        # Increase time: 1ms (react quickly to load)
        success &= self._set_power_setting(self.CORE_PARKING_INCREASE_TIME, 1, ac=True)
        
        # Decrease time: 100ms (takes longer to sleep)
        success &= self._set_power_setting(self.CORE_PARKING_DECREASE_TIME, 100, ac=True)
        
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print("[PARKING] ✓ Parking timers optimized")
            self.applied_changes['timers_optimized'] = True
        
        return success
    
    def set_high_performance_scheme(self) -> bool:
        """
        Activate High Performance power plan
        (Disables many power-saving optimizations automatically)
        """
        if not self.is_admin:
            return False
        
        # High Performance scheme GUID
        # 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
        success = self._run_powercfg("/setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
        
        if success:
            print("[PARKING] ✓ High Performance plan activated")
            self.applied_changes['high_performance'] = True
        else:
            # Try to create if it doesn't exist
            self._run_powercfg("/duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
            success = self._run_powercfg("/setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
            if success:
                print("[PARKING] ✓ High Performance plan created and activated")
                self.applied_changes['high_performance'] = True
        
        return success
    
    def create_ultimate_performance_scheme(self) -> bool:
        """
        Create and activate Ultimate Performance plan (Windows 10 Pro+)
        """
        if not self.is_admin:
            return False
        
        # Try to activate Ultimate Performance
        # e9a42b02-d5df-448d-aa00-03f14749eb61
        success = self._run_powercfg("/setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
        
        if not success:
            # Try to create the scheme
            result = subprocess.run(
                "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
                shell=True, capture_output=True, text=True
            )
            if "e9a42b02" in result.stdout or result.returncode == 0:
                success = self._run_powercfg("/setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
        
        if success:
            print("[PARKING] ✓ Ultimate Performance activated")
            self.applied_changes['ultimate_performance'] = True
        else:
            print("[PARKING] ℹ Ultimate Performance not available, using High Performance")
            return self.set_high_performance_scheme()
        
        return success
    
    def apply_all_optimizations(self, use_ultimate: bool = True) -> Dict[str, bool]:
        """
        Apply all Core Parking optimizations
        """
        print("\n[PARKING] Applying Core Parking optimizations...")
        
        results = {}
        
        # First set the power scheme
        if use_ultimate:
            results['power_scheme'] = self.create_ultimate_performance_scheme()
        else:
            results['power_scheme'] = self.set_high_performance_scheme()
        
        # Disable parking
        results['disable_parking'] = self.disable_core_parking()
        
        # Optimize timers
        results['timers'] = self.optimize_parking_timers()
        
        success_count = sum(results.values())
        print(f"[PARKING] Result: {success_count}/{len(results)} optimizations applied")
        
        return results
    
    def get_status(self) -> Dict[str, str]:
        """Returns current Core Parking status"""
        status = {}
        
        try:
            # Check active plan
            result = subprocess.run(
                "powercfg /getactivescheme",
                shell=True, capture_output=True, text=True
            )
            if "Ultimate" in result.stdout:
                status['power_scheme'] = "Ultimate Performance"
            elif "High" in result.stdout:
                status['power_scheme'] = "High Performance"
            elif "Balanced" in result.stdout:
                status['power_scheme'] = "Balanced"
            else:
                status['power_scheme'] = result.stdout.strip()
        except:
            status['power_scheme'] = "Unknown"
        
        return status


# Singleton
_instance = None

def get_manager() -> CoreParkingManager:
    global _instance
    if _instance is None:
        _instance = CoreParkingManager()
    return _instance


if __name__ == "__main__":
    manager = CoreParkingManager()
    print("Current status:", manager.get_status())
