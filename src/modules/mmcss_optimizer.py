"""
NovaPulse - MMCSS Optimizer
Optimizes Multimedia Class Scheduler Service for better audio/video
"""
import winreg
import ctypes
from typing import Dict, Optional


class MMCSSOptimizer:
    """
    Optimizes the Multimedia Class Scheduler Service (MMCSS)
    MMCSS manages media thread priority (audio, video, games)
    """
    
    MMCSS_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    TASKS_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path, value_name, value_data, value_type=winreg.REG_DWORD):
        """Set registry value"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[MMCSS] Registry error: {e}")
            return False
    
    def _get_registry_value(self, key_path, value_name):
        """Get registry value"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def set_system_responsiveness(self, value=0):
        """
        Set system responsiveness (0-100)
        0 = Maximum media priority (may affect other tasks)
        10 = Recommended for gaming (good balance)
        20 = Windows default
        """
        if not self.is_admin: return False
        value = max(0, min(100, value))
        success = self._set_registry_value(self.MMCSS_KEY, "SystemResponsiveness", value)
        if success:
            print(f"[MMCSS] ✓ SystemResponsiveness = {value}")
            self.applied_changes['responsiveness'] = value
        return success
    
    def disable_network_throttling(self):
        """Disable network throttling during media playback"""
        if not self.is_admin: return False
        # NetworkThrottlingIndex = FFFFFFFF (disabled)
        success = self._set_registry_value(self.MMCSS_KEY, "NetworkThrottlingIndex", 0xFFFFFFFF)
        if success:
            print("[MMCSS] ✓ Network Throttling disabled")
            self.applied_changes['network_throttling'] = False
        return success
    
    def optimize_gaming_task(self):
        """Optimize 'Games' task settings"""
        if not self.is_admin: return False
        games_key = f"{self.TASKS_KEY}\\Games"
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, games_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Games' optimized")
            self.applied_changes['games_task'] = True
            return True
        except Exception as e:
            print(f"[MMCSS] ✗ Error optimizing Games task: {e}")
            return False
    
    def optimize_audio_task(self):
        """Optimize 'Audio' task settings"""
        if not self.is_admin: return False
        audio_key = f"{self.TASKS_KEY}\\Audio"
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, audio_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "True")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Audio' optimized")
            self.applied_changes['audio_task'] = True
            return True
        except Exception as e:
            print(f"[MMCSS] ✗ Error optimizing Audio task: {e}")
            return False
    
    def optimize_pro_audio_task(self):
        """Optimize 'Pro Audio' task settings (DAWs, music production)"""
        if not self.is_admin: return False
        proaudio_key = f"{self.TASKS_KEY}\\Pro Audio"
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, proaudio_key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Pro Audio' optimized")
            self.applied_changes['proaudio_task'] = True
            return True
        except Exception as e:
            print(f"[MMCSS] ✗ Error optimizing Pro Audio task: {e}")
            return False
    
    def apply_all_optimizations(self, gaming_focused=True):
        """Apply all MMCSS optimizations"""
        print("\n[MMCSS] Applying Multimedia Scheduler optimizations...")
        results = {}
        responsiveness = 0 if gaming_focused else 10
        results['responsiveness'] = self.set_system_responsiveness(responsiveness)
        results['network_throttling'] = self.disable_network_throttling()
        results['games_task'] = self.optimize_gaming_task()
        results['audio_task'] = self.optimize_audio_task()
        results['proaudio_task'] = self.optimize_pro_audio_task()
        success_count = sum(results.values())
        print(f"[MMCSS] Result: {success_count}/{len(results)} optimizations applied")
        return results
    
    def get_status(self):
        """Returns current MMCSS settings status"""
        status = {}
        status['responsiveness'] = self._get_registry_value(self.MMCSS_KEY, "SystemResponsiveness")
        status['network_throttling'] = self._get_registry_value(self.MMCSS_KEY, "NetworkThrottlingIndex")
        return status


_instance = None
def get_optimizer():
    global _instance
    if _instance is None:
        _instance = MMCSSOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = MMCSSOptimizer()
    print("Current status:", optimizer.get_status())
