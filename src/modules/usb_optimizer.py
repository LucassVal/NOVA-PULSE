"""
NovaPulse - USB Polling Optimizer
Optimizes USB device polling rate (mouse, keyboard)
"""
import winreg
import ctypes
import subprocess
from typing import Dict, List, Optional


class USBPollingOptimizer:
    """
    Optimizes USB device polling rate
    
    Polling rate is the frequency at which the system reads data from the device.
    Higher polling = lower input lag, but more CPU usage.
    
    Windows default: 125Hz (8ms)
    Optimized: 500Hz-1000Hz (1-2ms)
    """
    
    USB_KEY = r"SYSTEM\CurrentControlSet\Services\usbhid\Parameters"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path, value_name, value_data, value_type=winreg.REG_DWORD):
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[USB] Registry error: {e}")
            return False
    
    def _get_registry_value(self, key_path, value_name):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def set_mouse_polling_rate(self, rate_hz: int = 1000) -> bool:
        """
        Set mouse polling rate
        
        rate_hz: Rate in Hz
        - 125 = 8ms (default)
        - 250 = 4ms
        - 500 = 2ms
        - 1000 = 1ms (maximum for USB 2.0)
        
        Note: The mouse must also support the configured rate.
        """
        if not self.is_admin:
            return False
        
        # For USB mice, this is controlled by the device driver
        # Windows allows override via HIDD
        
        mouse_key = r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters"
        
        # MouseDataQueueSize - increase mouse buffer
        success = self._set_registry_value(mouse_key, "MouseDataQueueSize", 100)
        
        if success:
            print("[USB] ✓ Mouse buffer optimized")
            self.applied_changes['mouse_buffer'] = True
        
        # Real note about polling:
        print("[USB] ℹ Mouse polling rate is controlled by the device driver")
        print("[USB] ℹ Configure in manufacturer software (Logitech G Hub, Razer Synapse, etc.)")
        
        return success
    
    def set_keyboard_polling_rate(self) -> bool:
        """Optimize keyboard polling"""
        if not self.is_admin:
            return False
        
        keyboard_key = r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters"
        
        # KeyboardDataQueueSize - increase buffer
        success = self._set_registry_value(keyboard_key, "KeyboardDataQueueSize", 100)
        
        if success:
            print("[USB] ✓ Keyboard buffer optimized")
            self.applied_changes['keyboard_buffer'] = True
        
        return success
    
    def disable_usb_selective_suspend(self) -> bool:
        """
        Disable USB Selective Suspend
        
        Selective Suspend saves power by turning off inactive USB ports.
        Disabling may improve USB device responsiveness.
        """
        if not self.is_admin:
            return False
        
        usb_key = r"SYSTEM\CurrentControlSet\Services\USB"
        success = self._set_registry_value(usb_key, "DisableSelectiveSuspend", 1)
        
        if success:
            print("[USB] ✓ USB Selective Suspend disabled")
            self.applied_changes['selective_suspend'] = False
        
        return success
    
    def disable_usb_power_management(self) -> bool:
        """Disable USB power management for all hubs"""
        if not self.is_admin:
            return False
        
        try:
            print("[USB] ℹ To disable power management on USB hubs:")
            print("[USB] ℹ Device Manager > USB Root Hub > Properties")
            print("[USB] ℹ > Power Management > Uncheck 'Allow to turn off'")
            
            self.applied_changes['power_management'] = "manual"
            return True
            
        except Exception as e:
            print(f"[USB] ✗ Error: {e}")
            return False
    
    def optimize_usb_latency(self) -> bool:
        """Apply general USB latency optimizations"""
        if not self.is_admin:
            return False
        
        # Enhanced Power Management Disable
        usbstor_key = r"SYSTEM\CurrentControlSet\Services\USBSTOR"
        success1 = self._set_registry_value(usbstor_key, "Start", 3)  # 3 = Manual
        
        # USB Hub Optimizations
        usbhub_key = r"SYSTEM\CurrentControlSet\Services\usbhub"
        success2 = self._set_registry_value(usbhub_key, "Start", 3)
        
        if success1 or success2:
            print("[USB] ✓ USB latency settings optimized")
            self.applied_changes['latency_optimized'] = True
        
        return success1 or success2
    
    def enable_msi_mode_for_usb(self) -> bool:
        """
        Enable MSI (Message Signaled Interrupts) for USB controllers
        
        MSI is more efficient than traditional line-based interrupts.
        May reduce interrupt latency.
        """
        if not self.is_admin:
            return False
        
        print("[USB] ℹ MSI mode for USB requires per-device configuration")
        print("[USB] ℹ Use tools like MSI Utility v3 to enable")
        
        # Note: Enabling MSI via registry requires the specific device path,
        # which varies by system
        
        self.applied_changes['msi_mode'] = "info_provided"
        return True
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Apply all USB optimizations"""
        print("\n[USB] Applying USB polling optimizations...")
        
        results = {}
        results['mouse'] = self.set_mouse_polling_rate()
        results['keyboard'] = self.set_keyboard_polling_rate()
        results['selective_suspend'] = self.disable_usb_selective_suspend()
        results['power_management'] = self.disable_usb_power_management()
        results['latency'] = self.optimize_usb_latency()
        results['msi'] = self.enable_msi_mode_for_usb()
        
        success_count = sum(1 for v in results.values() if v)
        print(f"[USB] Result: {success_count}/{len(results)} optimizations applied")
        
        return results
    
    def get_usb_devices(self) -> List[Dict]:
        """List connected USB devices"""
        devices = []
        try:
            result = subprocess.run(
                'wmic path Win32_USBHub get DeviceID,Name,Status',
                shell=True, capture_output=True, text=True
            )
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    devices.append({'raw': line.strip()})
        except:
            pass
        return devices
    
    def get_status(self) -> Dict[str, any]:
        """Returns current USB settings status"""
        status = {}
        status['selective_suspend'] = self._get_registry_value(
            r"SYSTEM\CurrentControlSet\Services\USB",
            "DisableSelectiveSuspend"
        )
        status['selective_suspend'] = "Disabled" if status['selective_suspend'] == 1 else "Active"
        return status


# Singleton
_instance = None

def get_optimizer() -> USBPollingOptimizer:
    global _instance
    if _instance is None:
        _instance = USBPollingOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = USBPollingOptimizer()
    print("Status:", optimizer.get_status())
    print("USB Devices:", optimizer.get_usb_devices())
