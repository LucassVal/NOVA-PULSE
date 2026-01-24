"""
Intel Power Control Module
Controls CPU power limits via Windows Power Options
Works on locked CPUs (non-K series) like i5-11300H

Available Controls:
1. Processor Performance Boost Mode (Turbo)
2. Processor Min/Max State (Throttle %)
3. System Cooling Policy
4. Processor Performance Core Parking
"""
import subprocess
import winreg
from enum import Enum
from typing import Optional, Tuple
import ctypes

class PowerProfile(Enum):
    """Power profiles with different PL1/PL2 style behavior"""
    ECO = "eco"           # Low power, quiet - PL1-style limit
    BALANCED = "balanced" # Normal operation
    PERFORMANCE = "perf"  # Max power, max noise
    TURBO = "turbo"       # Aggressive - disable all limits

class IntelPowerControl:
    """
    Intel CPU Power Control via Windows Power Options
    Works on locked CPUs (non-K series)
    """
    
    # Power GUIDs
    GUID_SUB_PROCESSOR = "54533251-82be-4824-96c1-47b60b740d00"
    GUID_THROTTLE_MIN = "893dee8e-2bef-41e0-89c6-b55d0929964c"
    GUID_THROTTLE_MAX = "bc5038f7-23e0-4960-96da-33abaf5935ec"
    GUID_BOOST_MODE = "be337238-0d82-4146-a960-4f3749d470c7"
    GUID_COOLING_POLICY = "94d3a615-a899-4ac5-ae2b-e4d8f634367f"
    GUID_CORE_PARKING_MIN = "0cc5b647-c1df-4637-891a-dec35c318583"
    
    # Boost Mode Values
    BOOST_DISABLED = 0
    BOOST_ENABLED = 1
    BOOST_AGGRESSIVE = 2
    BOOST_EFFICIENT_ENABLED = 3
    BOOST_EFFICIENT_AGGRESSIVE = 4
    BOOST_AGGRESSIVE_AT_GUARANTEED = 5
    
    def __init__(self):
        self.is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        self._current_scheme = self._get_active_scheme()
        
        # Profile presets
        self.profiles = {
            PowerProfile.ECO: {
                'throttle_min': 5,
                'throttle_max': 50,
                'boost_mode': self.BOOST_DISABLED,
                'cooling_policy': 0,  # Passive
            },
            PowerProfile.BALANCED: {
                'throttle_min': 5,
                'throttle_max': 85,
                'boost_mode': self.BOOST_EFFICIENT_ENABLED,
                'cooling_policy': 1,  # Active
            },
            PowerProfile.PERFORMANCE: {
                'throttle_min': 50,
                'throttle_max': 100,
                'boost_mode': self.BOOST_AGGRESSIVE,
                'cooling_policy': 1,  # Active
            },
            PowerProfile.TURBO: {
                'throttle_min': 100,
                'throttle_max': 100,
                'boost_mode': self.BOOST_AGGRESSIVE,
                'cooling_policy': 1,  # Active
            },
        }
    
    def _get_active_scheme(self) -> Optional[str]:
        """Get the active power scheme GUID"""
        try:
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True, text=True, timeout=5
            )
            # Parse: "GUID do Esquema de Energia: xxx-xxx-xxx  (Name)"
            for line in result.stdout.split('\n'):
                if 'GUID' in line or 'Power Scheme' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        guid = parts[1].strip().split()[0]
                        return guid
        except:
            pass
        return None
    
    def _run_powercfg(self, args: list) -> bool:
        """Run powercfg command"""
        try:
            result = subprocess.run(
                ['powercfg'] + args,
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def set_throttle_min(self, percent: int, ac: bool = True) -> bool:
        """
        Set minimum processor state (throttle floor)
        percent: 0-100
        ac: True for AC power, False for battery
        """
        if not self._current_scheme:
            return False
        
        flag = '/setacvalueindex' if ac else '/setdcvalueindex'
        return self._run_powercfg([
            flag, self._current_scheme,
            self.GUID_SUB_PROCESSOR,
            self.GUID_THROTTLE_MIN,
            str(percent)
        ])
    
    def set_throttle_max(self, percent: int, ac: bool = True) -> bool:
        """
        Set maximum processor state (throttle ceiling)
        percent: 0-100
        ac: True for AC power, False for battery
        
        This effectively limits power consumption similar to PL1
        """
        if not self._current_scheme:
            return False
        
        flag = '/setacvalueindex' if ac else '/setdcvalueindex'
        return self._run_powercfg([
            flag, self._current_scheme,
            self.GUID_SUB_PROCESSOR,
            self.GUID_THROTTLE_MAX,
            str(percent)
        ])
    
    def set_boost_mode(self, mode: int, ac: bool = True) -> bool:
        """
        Set processor performance boost mode (Turbo Boost behavior)
        
        0 = Disabled
        1 = Enabled
        2 = Aggressive
        3 = Efficient Enabled
        4 = Efficient Aggressive
        5 = Aggressive At Guaranteed
        """
        if not self._current_scheme:
            return False
        
        flag = '/setacvalueindex' if ac else '/setdcvalueindex'
        return self._run_powercfg([
            flag, self._current_scheme,
            self.GUID_SUB_PROCESSOR,
            self.GUID_BOOST_MODE,
            str(mode)
        ])
    
    def set_cooling_policy(self, active: bool, ac: bool = True) -> bool:
        """
        Set system cooling policy
        active=True: Fan spins up first (better cooling)
        active=False: Throttle first (quieter)
        """
        if not self._current_scheme:
            return False
        
        flag = '/setacvalueindex' if ac else '/setdcvalueindex'
        return self._run_powercfg([
            flag, self._current_scheme,
            self.GUID_SUB_PROCESSOR,
            self.GUID_COOLING_POLICY,
            '1' if active else '0'
        ])
    
    def apply_profile(self, profile: PowerProfile, ac: bool = True) -> dict:
        """
        Apply a complete power profile
        Returns dict with success status for each setting
        """
        settings = self.profiles[profile]
        results = {}
        
        results['throttle_min'] = self.set_throttle_min(settings['throttle_min'], ac)
        results['throttle_max'] = self.set_throttle_max(settings['throttle_max'], ac)
        results['boost_mode'] = self.set_boost_mode(settings['boost_mode'], ac)
        results['cooling_policy'] = self.set_cooling_policy(settings['cooling_policy'] == 1, ac)
        
        # Apply changes
        self._run_powercfg(['/setactive', self._current_scheme])
        
        return results
    
    def get_current_settings(self) -> dict:
        """Get current processor power settings"""
        settings = {}
        
        try:
            result = subprocess.run(
                ['powercfg', '/query', self._current_scheme, self.GUID_SUB_PROCESSOR],
                capture_output=True, text=True, timeout=10
            )
            
            lines = result.stdout.split('\n')
            current_setting = None
            
            for line in lines:
                line_lower = line.lower()
                
                # Detect which setting we're looking at
                if 'desempenho mínimo' in line_lower or 'minimum' in line_lower:
                    current_setting = 'throttle_min'
                elif 'desempenho máximo' in line_lower or 'maximum' in line_lower:
                    current_setting = 'throttle_max'
                elif 'boost' in line_lower:
                    current_setting = 'boost_mode'
                elif 'resfriamento' in line_lower or 'cooling' in line_lower:
                    current_setting = 'cooling_policy'
                
                # Extract AC value
                if current_setting and ('alternadas' in line_lower or 'ac power' in line_lower):
                    try:
                        value = line.split(':')[1].strip()
                        if value.startswith('0x'):
                            settings[f'{current_setting}_ac'] = int(value, 16)
                        else:
                            settings[f'{current_setting}_ac'] = int(value)
                    except:
                        pass
                    current_setting = None
                    
        except:
            pass
        
        return settings
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary"""
        settings = self.get_current_settings()
        
        lines = ["Intel Power Control Status:"]
        lines.append(f"  Active Scheme: {self._current_scheme[:8]}...")
        
        if 'throttle_min_ac' in settings:
            lines.append(f"  Throttle Min: {settings['throttle_min_ac']}%")
        if 'throttle_max_ac' in settings:
            lines.append(f"  Throttle Max: {settings['throttle_max_ac']}%")
        if 'boost_mode_ac' in settings:
            boost_names = {0: 'Disabled', 1: 'Enabled', 2: 'Aggressive', 
                          3: 'Efficient', 4: 'EfficientAggressive', 5: 'AggressiveGuaranteed'}
            boost = boost_names.get(settings['boost_mode_ac'], str(settings['boost_mode_ac']))
            lines.append(f"  Boost Mode: {boost}")
        
        return '\n'.join(lines)


# Module-level functions for easy access
_instance = None

def get_controller() -> IntelPowerControl:
    """Get singleton instance"""
    global _instance
    if _instance is None:
        _instance = IntelPowerControl()
    return _instance

def apply_eco_mode():
    """Quick: Apply ECO mode (low power, quiet)"""
    ctrl = get_controller()
    return ctrl.apply_profile(PowerProfile.ECO)

def apply_performance_mode():
    """Quick: Apply Performance mode (max power)"""
    ctrl = get_controller()
    return ctrl.apply_profile(PowerProfile.PERFORMANCE)

def apply_turbo_mode():
    """Quick: Apply Turbo mode (no limits)"""
    ctrl = get_controller()
    return ctrl.apply_profile(PowerProfile.TURBO)

def apply_balanced_mode():
    """Quick: Apply Balanced mode (default)"""
    ctrl = get_controller()
    return ctrl.apply_profile(PowerProfile.BALANCED)


def thermal_aware_update(cpu_temp: float, threshold_high: float = 85.0, threshold_low: float = 70.0) -> Optional[str]:
    """
    Thermal-aware power control.
    Automatically adjusts power profile based on CPU temperature.
    
    Args:
        cpu_temp: Current CPU temperature in Celsius
        threshold_high: Temp above which to apply ECO mode (default 85°C)
        threshold_low: Temp below which to allow PERFORMANCE mode (default 70°C)
    
    Returns:
        Name of applied profile, or None if no change needed
    
    Prevents severe thermal throttling at 90°C by proactively limiting power at 85°C.
    """
    ctrl = get_controller()
    
    if cpu_temp >= threshold_high:
        # HOT! Apply ECO to prevent throttle at 90°C
        ctrl.apply_profile(PowerProfile.ECO)
        return "ECO (thermal protection)"
    elif cpu_temp <= threshold_low:
        # Cool enough for performance
        ctrl.apply_profile(PowerProfile.PERFORMANCE)
        return "PERFORMANCE"
    else:
        # Middle zone - balanced
        ctrl.apply_profile(PowerProfile.BALANCED)
        return "BALANCED"


if __name__ == "__main__":
    # Test
    ctrl = IntelPowerControl()
    print(ctrl.get_status_summary())
    
    print("\nApplying Performance profile...")
    results = ctrl.apply_profile(PowerProfile.PERFORMANCE)
    print(f"Results: {results}")
    
    print("\n" + ctrl.get_status_summary())
    
    # Test thermal protection
    print("\n=== Thermal Protection Test ===")
    print(f"Temp 60°C -> {thermal_aware_update(60)}")
    print(f"Temp 80°C -> {thermal_aware_update(80)}")
    print(f"Temp 90°C -> {thermal_aware_update(90)}")

