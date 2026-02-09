"""
NovaPulse - HPET Controller
Controls High Precision Event Timer and system timers
"""
import subprocess
import ctypes
from typing import Dict, Tuple, Optional


class HPETController:
    """
    Controls HPET (High Precision Event Timer) and related timers
    
    HPET can add latency on some systems.
    Disabling it may improve input lag in games.
    
    WARNING: Not all systems benefit from this optimization.
    In some cases, it may cause instability.
    """
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
        self.original_values = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_bcdedit(self, args: str) -> Tuple[bool, str]:
        """Execute bcdedit command"""
        try:
            result = subprocess.run(
                f"bcdedit {args}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def disable_hpet(self) -> bool:
        """
        Disable HPET via BCD
        
        Impact:
        - May reduce input lag in games
        - Improves latency on some systems
        
        Risks:
        - May cause instability on some systems
        - Some software may have timing issues
        """
        if not self.is_admin:
            print("[HPET] ✗ Requires administrator privileges")
            return False
        
        # Save original value
        success, output = self._run_bcdedit("/enum")
        if "useplatformclock" in output.lower():
            self.original_values['useplatformclock'] = True
        
        # Disable HPET
        success, output = self._run_bcdedit("/set useplatformclock false")
        
        if success:
            print("[HPET] ✓ HPET disabled (useplatformclock = false)")
            self.applied_changes['hpet'] = False
        else:
            # Try to delete the entry (restores default)
            self._run_bcdedit("/deletevalue useplatformclock")
            print("[HPET] ✓ HPET configuration removed (system default)")
            self.applied_changes['hpet'] = None
        
        return True
    
    def enable_hpet(self) -> bool:
        """Re-enable HPET"""
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/set useplatformclock true")
        
        if success:
            print("[HPET] ✓ HPET re-enabled")
            self.applied_changes['hpet'] = True
        
        return success
    
    def disable_dynamic_tick(self) -> bool:
        """
        Disable Dynamic Tick (tickless timer)
        
        Windows uses dynamic tick for power saving.
        Disabling forces constant tick, may improve latency.
        
        Impact:
        - Lower latencies
        - Higher power consumption
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_bcdedit("/set disabledynamictick yes")
        
        if success:
            print("[HPET] ✓ Dynamic Tick disabled")
            self.applied_changes['dynamic_tick'] = False
        else:
            print(f"[HPET] ✗ Error disabling Dynamic Tick: {output}")
        
        return success
    
    def enable_dynamic_tick(self) -> bool:
        """Re-enable Dynamic Tick"""
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/deletevalue disabledynamictick")
        
        if success:
            print("[HPET] ✓ Dynamic Tick re-enabled")
            self.applied_changes['dynamic_tick'] = True
        
        return success
    
    def set_tscsyncpolicy(self, policy: str = "enhanced") -> bool:
        """
        Set TSC (Time Stamp Counter) synchronization policy
        
        Policies:
        - "default": Windows default
        - "legacy": Compatibility with older systems
        - "enhanced": Best precision (recommended for gaming)
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_bcdedit(f"/set tscsyncpolicy {policy}")
        
        if success:
            print(f"[HPET] ✓ TSC Sync Policy = {policy}")
            self.applied_changes['tscsync'] = policy
        else:
            print("[HPET] ℹ TSC Sync Policy not applicable on this system")
        
        return success
    
    def disable_synthetic_timers(self) -> bool:
        """
        Disable Hyper-V synthetic timers
        (Only useful if Hyper-V is installed)
        """
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/set hypervisorlaunchtype off")
        
        if success:
            print("[HPET] ✓ Hyper-V hypervisor disabled")
            print("[HPET] ⚠ This may affect WSL2, Docker, etc.")
            self.applied_changes['hypervisor'] = False
        else:
            print("[HPET] ℹ Hyper-V is not installed or already disabled")
        
        return True
    
    def optimize_boot_options(self) -> bool:
        """
        Apply other boot optimizations related to timing
        """
        if not self.is_admin:
            return False
        
        optimizations = []
        
        # Disable debugging (reduces overhead)
        success, _ = self._run_bcdedit("/debug off")
        if success:
            optimizations.append("debug off")
        
        # Disable boot log (less I/O)
        success, _ = self._run_bcdedit("/bootlog no")
        if success:
            optimizations.append("bootlog no")
        
        if optimizations:
            print(f"[HPET] ✓ Boot optimized: {', '.join(optimizations)}")
            self.applied_changes['boot_optimized'] = True
        
        return len(optimizations) > 0
    
    def apply_all_optimizations(self, aggressive: bool = False) -> Dict[str, bool]:
        """
        Apply all timer optimizations
        
        aggressive: If True, applies riskier optimizations
        """
        print("\n[HPET] Applying timer optimizations...")
        
        results = {}
        
        # Safe optimizations
        results['hpet'] = self.disable_hpet()
        results['dynamic_tick'] = self.disable_dynamic_tick()
        results['tscsync'] = self.set_tscsyncpolicy("enhanced")
        results['boot'] = self.optimize_boot_options()
        
        if aggressive:
            print("[HPET] ⚠ Aggressive mode: disabling Hyper-V")
            results['hypervisor'] = self.disable_synthetic_timers()
        
        success_count = sum(results.values())
        print(f"[HPET] Result: {success_count}/{len(results)} optimizations applied")
        print("[HPET] ⚠ RESTART REQUIRED to apply BCD changes")
        
        return results
    
    def restore_defaults(self) -> bool:
        """
        Restore default timer settings
        """
        if not self.is_admin:
            return False
        
        print("[HPET] Restoring default settings...")
        
        self._run_bcdedit("/deletevalue useplatformclock")
        self._run_bcdedit("/deletevalue disabledynamictick")
        self._run_bcdedit("/deletevalue tscsyncpolicy")
        
        print("[HPET] ✓ Timer settings restored")
        print("[HPET] ⚠ Restart to apply")
        
        return True
    
    def get_status(self) -> Dict[str, str]:
        """Returns current timer settings status"""
        status = {}
        
        try:
            success, output = self._run_bcdedit("/enum")
            
            if "useplatformclock" in output.lower():
                if "yes" in output.lower() or "true" in output.lower():
                    status['hpet'] = "Enabled"
                else:
                    status['hpet'] = "Disabled"
            else:
                status['hpet'] = "System default"
            
            if "disabledynamictick" in output.lower():
                status['dynamic_tick'] = "Disabled"
            else:
                status['dynamic_tick'] = "Active (default)"
            
            if "tscsyncpolicy" in output.lower():
                if "enhanced" in output.lower():
                    status['tscsync'] = "Enhanced"
                elif "legacy" in output.lower():
                    status['tscsync'] = "Legacy"
                else:
                    status['tscsync'] = "Custom"
            else:
                status['tscsync'] = "Default"
                
        except:
            status['error'] = "Could not read settings"
        
        return status
    
    def benchmark_latency(self) -> Optional[float]:
        """
        Run a simple timer latency benchmark
        Returns average latency in microseconds
        """
        try:
            import time
            
            samples = []
            for _ in range(1000):
                start = time.perf_counter_ns()
                # Minimal operation
                _ = 1 + 1
                end = time.perf_counter_ns()
                samples.append(end - start)
            
            avg_ns = sum(samples) / len(samples)
            avg_us = avg_ns / 1000
            
            print(f"[HPET] Average timer latency: {avg_us:.2f} µs")
            return avg_us
            
        except Exception as e:
            print(f"[HPET] Benchmark error: {e}")
            return None


# Singleton
_instance = None

def get_controller() -> HPETController:
    global _instance
    if _instance is None:
        _instance = HPETController()
    return _instance


if __name__ == "__main__":
    controller = HPETController()
    print("Current status:", controller.get_status())
    controller.benchmark_latency()
