"""
NovaPulse - IRQ Affinity Optimizer
Optimizes hardware interrupt distribution across CPU cores
"""
import winreg
import ctypes
import subprocess
from typing import Dict, List, Optional, Tuple
import os


class IRQAffinityOptimizer:
    """
    Optimizes IRQ (Interrupt Request) affinity
    
    Hardware interrupts are processed by the CPU.
    Distributing across cores can improve performance.
    Concentrating on specific cores can reduce latency for gaming.
    """
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
        self.cpu_count = os.cpu_count() or 4
    
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
            return False
    
    def get_pci_devices(self) -> List[Dict]:
        """List PCI devices that can have MSI configured"""
        devices = []
        try:
            # Enumerate devices via registry
            base_key = r"SYSTEM\CurrentControlSet\Enum\PCI"
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key)
            i = 0
            while True:
                try:
                    device_id = winreg.EnumKey(reg_key, i)
                    device_path = f"{base_key}\\{device_id}"
                    # Get subkeys (device instances)
                    device_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_path)
                    j = 0
                    while True:
                        try:
                            instance_id = winreg.EnumKey(device_key, j)
                            instance_path = f"{device_path}\\{instance_id}"
                            # Try to read device name
                            try:
                                inst_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, instance_path)
                                name, _ = winreg.QueryValueEx(inst_key, "DeviceDesc")
                                # Extract clean name
                                if ";" in name:
                                    name = name.split(";")[-1]
                                devices.append({
                                    'id': device_id,
                                    'instance': instance_id,
                                    'path': instance_path,
                                    'name': name
                                })
                                winreg.CloseKey(inst_key)
                            except:
                                pass
                            j += 1
                        except OSError:
                            break
                    winreg.CloseKey(device_key)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(reg_key)
        except Exception as e:
            print(f"[IRQ] Error enumerating devices: {e}")
        return devices
    
    def enable_msi_for_device(self, device_path: str) -> bool:
        """
        Enable MSI (Message Signaled Interrupts) for a device
        
        MSI is more efficient than traditional IRQ:
        - Lower latency
        - Better distribution across cores
        - Avoids IRQ sharing
        """
        if not self.is_admin:
            return False
        try:
            msi_path = f"{device_path}\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties"
            # Create key if it doesn't exist
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, msi_path, 0, 
                winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY)
            # MSISupported = 1
            winreg.SetValueEx(key, "MSISupported", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False
    
    def set_device_affinity(self, device_path: str, core_mask: int) -> bool:
        """
        Set CPU affinity for a device's interrupts
        
        core_mask: Bitmask of cores (e.g.: 0x0F = cores 0-3)
        """
        if not self.is_admin:
            return False
        try:
            affinity_path = f"{device_path}\\Device Parameters\\Interrupt Management\\Affinity Policy"
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, affinity_path, 0,
                winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY)
            # DevicePolicy = 4 (IrqPolicySpreadMessagesAcrossAllProcessors)
            # For gaming, use 1 (IrqPolicyAllCloseProcessors)
            winreg.SetValueEx(key, "DevicePolicy", 0, winreg.REG_DWORD, 4)
            # AssignmentSetOverride - core bitmask
            winreg.SetValueEx(key, "AssignmentSetOverride", 0, winreg.REG_BINARY, 
                core_mask.to_bytes(8, 'little'))
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False
    
    def optimize_gpu_irq(self) -> bool:
        """Optimize GPU IRQ for lower latency"""
        if not self.is_admin:
            return False
        devices = self.get_pci_devices()
        gpu_optimized = False
        for device in devices:
            name_lower = device['name'].lower()
            if 'nvidia' in name_lower or 'geforce' in name_lower or 'radeon' in name_lower or 'amd' in name_lower:
                # Enable MSI
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI enabled for GPU: {device['name']}")
                    gpu_optimized = True
                # Set affinity to higher cores (less used by system)
                # Uses last 2-4 cores
                high_cores_mask = (1 << self.cpu_count) - (1 << max(0, self.cpu_count - 4))
                if self.set_device_affinity(device['path'], high_cores_mask):
                    print("[IRQ] ✓ GPU affinity set to high cores")
        self.applied_changes['gpu_irq'] = gpu_optimized
        return gpu_optimized
    
    def optimize_network_irq(self) -> bool:
        """Optimize network adapter IRQ"""
        if not self.is_admin:
            return False
        devices = self.get_pci_devices()
        net_optimized = False
        keywords = ['ethernet', 'network', 'wifi', 'wireless', 'realtek', 'intel', 'killer']
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI enabled for network: {device['name'][:40]}")
                    net_optimized = True
                # Network on dedicated cores (doesn't compete with GPU/games)
                # Uses cores 0-1
                net_mask = 0x03  # Cores 0 and 1
                self.set_device_affinity(device['path'], net_mask)
        self.applied_changes['network_irq'] = net_optimized
        return net_optimized
    
    def optimize_storage_irq(self) -> bool:
        """Optimize storage controller IRQ (NVMe, SATA)"""
        if not self.is_admin:
            return False
        devices = self.get_pci_devices()
        storage_optimized = False
        keywords = ['nvme', 'ssd', 'sata', 'ahci', 'storage', 'raid']
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI enabled for storage: {device['name'][:40]}")
                    storage_optimized = True
                # Storage distributed across all cores
                all_cores = (1 << self.cpu_count) - 1
                self.set_device_affinity(device['path'], all_cores)
        self.applied_changes['storage_irq'] = storage_optimized
        return storage_optimized
    
    def optimize_usb_irq(self) -> bool:
        """Optimize USB controller IRQ"""
        if not self.is_admin:
            return False
        devices = self.get_pci_devices()
        usb_optimized = False
        keywords = ['usb', 'xhci', 'ehci', 'ohci']
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI enabled for USB: {device['name'][:40]}")
                    usb_optimized = True
                # USB to low cores (alongside network)
                usb_mask = 0x03
                self.set_device_affinity(device['path'], usb_mask)
        self.applied_changes['usb_irq'] = usb_optimized
        return usb_optimized
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Apply IRQ optimizations for all relevant devices"""
        print("\n[IRQ] Applying IRQ affinity optimizations...")
        results = {}
        results['gpu'] = self.optimize_gpu_irq()
        results['network'] = self.optimize_network_irq()
        results['storage'] = self.optimize_storage_irq()
        results['usb'] = self.optimize_usb_irq()
        success_count = sum(results.values())
        print(f"[IRQ] Result: {success_count}/{len(results)} categories optimized")
        print("[IRQ] ⚠ Restart PC to apply IRQ changes")
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Returns IRQ settings summary"""
        devices = self.get_pci_devices()
        status = {
            'total_pci_devices': len(devices),
            'cpu_cores': self.cpu_count
        }
        # Count devices by category
        gpu_count = sum(1 for d in devices if any(x in d['name'].lower() for x in ['nvidia', 'geforce', 'radeon', 'amd']))
        net_count = sum(1 for d in devices if any(x in d['name'].lower() for x in ['ethernet', 'network', 'wifi']))
        status['gpu_devices'] = gpu_count
        status['network_devices'] = net_count
        return status


# Singleton
_instance = None

def get_optimizer() -> IRQAffinityOptimizer:
    global _instance
    if _instance is None:
        _instance = IRQAffinityOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = IRQAffinityOptimizer()
    print("Status:", optimizer.get_status())
    devices = optimizer.get_pci_devices()
    print(f"\nPCI devices found: {len(devices)}")
    for d in devices[:10]:
        print(f"  - {d['name'][:60]}")
