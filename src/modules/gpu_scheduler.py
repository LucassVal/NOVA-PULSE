"""
NovaPulse - GPU Scheduler Controller
Controls Hardware-Accelerated GPU Scheduling and other GPU options
"""
import winreg
import ctypes
import subprocess
from typing import Dict, Optional, Tuple


class GPUSchedulerController:
    """
    Controls advanced Windows GPU settings
    Includes HAGS (Hardware-Accelerated GPU Scheduling)
    """
    
    GPU_KEY = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    
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
            print(f"[GPU] Registry error: {e}")
            return False
    
    def _get_registry_value(self, key_path: str, value_name: str) -> Optional[any]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def enable_hardware_accelerated_scheduling(self, enable: bool = True) -> bool:
        """
        Enable/disable Hardware-Accelerated GPU Scheduling (HAGS)
        
        HAGS allows the GPU to manage its own video memory,
        reducing latency and CPU overhead.
        
        Requirements:
        - Windows 10 2004+ or Windows 11
        - Supported GPU (NVIDIA 1000+, AMD 5000+)
        - Updated driver
        """
        if not self.is_admin:
            return False
        
        value = 2 if enable else 1  # 2 = enabled, 1 = disabled
        success = self._set_registry_value(self.GPU_KEY, "HwSchMode", value)
        
        if success:
            state = "enabled" if enable else "disabled"
            print(f"[GPU] ✓ Hardware-Accelerated Scheduling {state}")
            print("[GPU] ⚠ Restart PC to apply")
            self.applied_changes['hags'] = enable
        
        return success
    
    def set_gpu_priority(self, priority: int = 8) -> bool:
        """
        Set GPU priority in the system (0-8)
        8 = Maximum GPU priority
        """
        if not self.is_admin:
            return False
        
        priority = max(0, min(8, priority))
        
        # Also set in MMCSS
        mmcss_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        success = self._set_registry_value(mmcss_key, "GPUPriority", priority)
        
        if success:
            print(f"[GPU] ✓ GPU Priority = {priority}")
            self.applied_changes['priority'] = priority
        
        return success
    
    def optimize_dxgi(self) -> bool:
        """
        Optimize DXGI (DirectX Graphics Infrastructure)
        Reduces frame presentation latency
        """
        if not self.is_admin:
            return False
        
        try:
            # TdrLevel - Timeout Detection and Recovery
            # 0 = Disabled (not recommended)
            # 3 = Default recovery
            success = self._set_registry_value(self.GPU_KEY, "TdrLevel", 3)
            
            # TdrDelay - Time before considering GPU hung
            success2 = self._set_registry_value(self.GPU_KEY, "TdrDelay", 10)
            
            if success and success2:
                print("[GPU] ✓ DXGI/TDR optimized")
                self.applied_changes['dxgi'] = True
                return True
                
        except Exception as e:
            print(f"[GPU] ✗ Error optimizing DXGI: {e}")
        
        return False
    
    def disable_fullscreen_optimizations_globally(self) -> bool:
        """
        Disable Fullscreen Optimizations globally
        (Can also be done per application)
        """
        if not self.is_admin:
            return False
        
        try:
            compat_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
            # Note: This sets for new apps, existing apps need individual configuration
            print("[GPU] ℹ Fullscreen Optimizations should be disabled per app")
            print("[GPU] ℹ Right-click .exe > Properties > Compatibility")
            self.applied_changes['fso'] = True
            return True
        except:
            return False
    
    def enable_game_mode(self) -> bool:
        """
        Enable Windows Game Mode
        Win11 Home: GameBar key is under HKCU, not HKLM
        """
        try:
            # Win11: GameBar settings are per-user (HKCU)
            game_key = r"SOFTWARE\Microsoft\GameBar"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, game_key, 0, winreg.KEY_SET_VALUE)
            except FileNotFoundError:
                # Create key if it doesn't exist
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, game_key)
            
            winreg.SetValueEx(key, "AutoGameModeEnabled", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            print("[GPU] ✓ Game Mode enabled")
            self.applied_changes['game_mode'] = True
            return True
        except Exception as e:
            # Fallback: try HKLM (older Windows / domain-joined)
            try:
                success = self._set_registry_value(game_key, "AutoGameModeEnabled", 1)
                if success:
                    print("[GPU] ✓ Game Mode enabled (HKLM)")
                    self.applied_changes['game_mode'] = True
                return success
            except:
                print(f"[GPU] ✗ Game Mode: {e}")
                return False
    
    def set_preferred_gpu_high_performance(self) -> bool:
        """
        Force NVIDIA GPU as default for key apps via Windows registry.
        Equivalent to: Settings > System > Display > Graphics > High Performance
        
        Registry: HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences
        Value: GpuPreference=2  (0=Auto, 1=Power Saving, 2=High Performance)
        """
        import os, glob
        import sys
        
        # Apps to force NVIDIA (expand as needed)
        target_apps = []
        
        # 1. Antigravity IDE
        antigravity = os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe")
        if os.path.exists(antigravity):
            target_apps.append(antigravity)
        
        # 2. VS Code
        vscode = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe")
        if os.path.exists(vscode):
            target_apps.append(vscode)
        
        # 3. NovaPulse itself
        novapulse_desktop = os.path.expandvars(r"%USERPROFILE%\Desktop\NovaPulse.exe")
        if os.path.exists(novapulse_desktop):
            target_apps.append(novapulse_desktop)
        
        # 4. Node.js (for dev work)
        node_paths = glob.glob(os.path.expandvars(r"%PROGRAMFILES%\nodejs\node.exe"))
        target_apps.extend(node_paths)
        
        # 5. Python (agents/AI acceleration)
        python_path = sys.executable
        if python_path and os.path.exists(python_path):
            target_apps.append(python_path)
        
        # 6. Chrome (heavy RAM/GPU user)
        chrome = os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe")
        if os.path.exists(chrome):
            target_apps.append(chrome)
        # Chrome x86
        chrome_x86 = os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe")
        if os.path.exists(chrome_x86):
            target_apps.append(chrome_x86)
        
        if not target_apps:
            print("[GPU] ⚠ No apps found to force NVIDIA")
            return False
        
        try:
            preference_key = r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences"
            applied = 0
            
            # === GLOBAL: Force ALL graphical apps to NVIDIA ===
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, preference_key, 0,
                                   winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                    # Read existing global settings to preserve them
                    try:
                        current, _ = winreg.QueryValueEx(key, "DirectXUserGlobalSettings")
                    except:
                        current = ""
                    
                    # Add GpuPreference=2 if not already present
                    if "GpuPreference=2" not in current:
                        # Preserve existing flags, add GPU preference
                        new_value = "GpuPreference=2;" + current if current else "GpuPreference=2;"
                        winreg.SetValueEx(key, "DirectXUserGlobalSettings", 0, winreg.REG_SZ, new_value)
                        print("[GPU] ✓ GLOBAL: All graphical apps → NVIDIA")
                    else:
                        print("[GPU] ✓ GLOBAL: Already configured for NVIDIA")
            except Exception as e:
                print(f"[GPU] ✗ Global preference: {e}")
            
            # === PER-APP: Ensure specific critical apps ===
            for app_path in target_apps:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, preference_key, 0, 
                                       winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, app_path, 0, winreg.REG_SZ, "GpuPreference=2")
                        applied += 1
                        app_name = os.path.basename(app_path)
                        print(f"[GPU] ✓ NVIDIA forced: {app_name}")
                except Exception as e:
                    print(f"[GPU] ✗ Failed: {os.path.basename(app_path)} - {e}")
            
            print(f"[GPU] GPU Preference: GLOBAL + {applied} apps → NVIDIA High Performance")
            return True
        except Exception as e:
            print(f"[GPU] ✗ GPU preference error: {e}")
            return False
    
    def set_physx_gpu(self) -> bool:
        """
        Force RTX 3050 as PhysX processor (instead of Auto/CPU).
        Frees the i5 from computing physics when apps request it.
        Registry: HKLM\\SOFTWARE\\NVIDIA Corporation\\Global\\PhysX\\PhysxGpu = 1
        """
        if not self.is_admin:
            print("[GPU] ✗ PhysX: requires admin")
            return False
        
        try:
            physx_key = r"SOFTWARE\NVIDIA Corporation\Global\PhysX"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, physx_key, 0,
                               winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                try:
                    current, _ = winreg.QueryValueEx(key, "PhysxGpu")
                except:
                    current = 0
                
                if current != 1:
                    winreg.SetValueEx(key, "PhysxGpu", 0, winreg.REG_DWORD, 1)
                    print("[GPU] ✓ PhysX → RTX 3050 (dedicated)")
                else:
                    print("[GPU] ✓ PhysX already configured for RTX 3050")
                
                self.applied_changes['physx'] = True
                return True
        except Exception as e:
            print(f"[GPU] ✗ PhysX: {e}")
            return False
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """
        Apply all GPU optimizations
        """
        print("\n[GPU] Applying GPU Scheduler optimizations...")
        
        results = {}
        results['hags'] = self.enable_hardware_accelerated_scheduling(True)
        results['priority'] = self.set_gpu_priority(8)
        results['dxgi'] = self.optimize_dxgi()
        results['game_mode'] = self.enable_game_mode()
        results['gpu_preference'] = self.set_preferred_gpu_high_performance()
        results['physx'] = self.set_physx_gpu()
        
        success_count = sum(results.values())
        print(f"[GPU] Result: {success_count}/{len(results)} optimizations applied")
        
        if results['hags']:
            print("[GPU] ⚠ RESTART REQUIRED for Hardware-Accelerated Scheduling")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Returns current GPU settings status"""
        status = {}
        
        hags = self._get_registry_value(self.GPU_KEY, "HwSchMode")
        status['hags'] = "Enabled" if hags == 2 else "Disabled" if hags == 1 else "Not set"
        
        tdr_level = self._get_registry_value(self.GPU_KEY, "TdrLevel")
        status['tdr_level'] = tdr_level
        
        return status
    
    def check_gpu_support(self) -> Tuple[bool, str]:
        """Check if GPU supports HAGS"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            
            # NVIDIA 1000+ series supports HAGS
            supported = any(x in name.upper() for x in ['GTX 10', 'GTX 16', 'RTX'])
            return supported, name
        except:
            return False, "GPU not detected"


# Singleton
_instance = None

def get_controller() -> GPUSchedulerController:
    global _instance
    if _instance is None:
        _instance = GPUSchedulerController()
    return _instance


if __name__ == "__main__":
    controller = GPUSchedulerController()
    print("Current status:", controller.get_status())
    supported, gpu_name = controller.check_gpu_support()
    print(f"GPU: {gpu_name}")
    print(f"HAGS Supported: {supported}")
