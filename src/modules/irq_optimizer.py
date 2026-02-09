"""
NovaPulse - IRQ Affinity Optimizer
Otimiza distribuição de interrupções de hardware entre cores da CPU
"""
import winreg
import ctypes
import subprocess
from typing import Dict, List, Optional, Tuple
import os


class IRQAffinityOptimizer:
    """
    Otimiza afinidade de IRQ (Interrupt Request)
    
    Interrupções de hardware são processadas pela CPU.
    Distribuir entre cores pode melhorar performance.
    Concentrar em cores específicos pode reduzir latência para gaming.
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
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, value_type=winreg.REG_DWORD) -> bool:
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False
    
    def get_pci_devices(self) -> List[Dict]:
        """
        Lista dispositivos PCI que podem ter MSI configurado
        """
        devices = []
        
        try:
            # Enumera dispositivos via registro
            base_key = r"SYSTEM\CurrentControlSet\Enum\PCI"
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key)
            
            i = 0
            while True:
                try:
                    device_id = winreg.EnumKey(reg_key, i)
                    device_path = f"{base_key}\\{device_id}"
                    
                    # Pega subchaves (instâncias do dispositivo)
                    device_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, device_path)
                    j = 0
                    while True:
                        try:
                            instance_id = winreg.EnumKey(device_key, j)
                            instance_path = f"{device_path}\\{instance_id}"
                            
                            # Tenta ler nome do dispositivo
                            try:
                                inst_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, instance_path)
                                name, _ = winreg.QueryValueEx(inst_key, "DeviceDesc")
                                
                                # Extrai nome limpo
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
            print(f"[IRQ] Erro ao enumerar dispositivos: {e}")
        
        return devices
    
    def enable_msi_for_device(self, device_path: str) -> bool:
        """
        Habilita MSI (Message Signaled Interrupts) para um dispositivo
        
        MSI é mais eficiente que IRQ tradicional:
        - Menor latência
        - Melhor distribuição entre cores
        - Evita compartilhamento de IRQ
        """
        if not self.is_admin:
            return False
        
        try:
            msi_path = f"{device_path}\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties"
            
            # Cria chave se não existir
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
        Define afinidade de CPU para interrupções de um dispositivo
        
        core_mask: Bitmask dos cores (ex: 0x0F = cores 0-3)
        """
        if not self.is_admin:
            return False
        
        try:
            affinity_path = f"{device_path}\\Device Parameters\\Interrupt Management\\Affinity Policy"
            
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, affinity_path, 0,
                winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY)
            
            # DevicePolicy = 4 (IrqPolicySpreadMessagesAcrossAllProcessors)
            # Para gaming, use 1 (IrqPolicyAllCloseProcessors)
            winreg.SetValueEx(key, "DevicePolicy", 0, winreg.REG_DWORD, 4)
            
            # AssignmentSetOverride - bitmask dos cores
            winreg.SetValueEx(key, "AssignmentSetOverride", 0, winreg.REG_BINARY, 
                core_mask.to_bytes(8, 'little'))
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False
    
    def optimize_gpu_irq(self) -> bool:
        """
        Otimiza IRQ da GPU para menor latência
        """
        if not self.is_admin:
            return False
        
        devices = self.get_pci_devices()
        gpu_optimized = False
        
        for device in devices:
            name_lower = device['name'].lower()
            if 'nvidia' in name_lower or 'geforce' in name_lower or 'radeon' in name_lower or 'amd' in name_lower:
                # Habilita MSI
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI habilitado para GPU: {device['name']}")
                    gpu_optimized = True
                
                # Define afinidade para cores mais altos (menos usado pelo sistema)
                # Usa últimos 2-4 cores
                high_cores_mask = (1 << self.cpu_count) - (1 << max(0, self.cpu_count - 4))
                if self.set_device_affinity(device['path'], high_cores_mask):
                    print(f"[IRQ] ✓ GPU afinidade definida para cores altos")
        
        self.applied_changes['gpu_irq'] = gpu_optimized
        return gpu_optimized
    
    def optimize_network_irq(self) -> bool:
        """
        Otimiza IRQ de adaptadores de rede
        """
        if not self.is_admin:
            return False
        
        devices = self.get_pci_devices()
        net_optimized = False
        
        keywords = ['ethernet', 'network', 'wifi', 'wireless', 'realtek', 'intel', 'killer']
        
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI habilitado para rede: {device['name'][:40]}")
                    net_optimized = True
                
                # Rede em cores dedicados (não compete com GPU/jogos)
                # Usa cores 0-1
                net_mask = 0x03  # Cores 0 e 1
                self.set_device_affinity(device['path'], net_mask)
        
        self.applied_changes['network_irq'] = net_optimized
        return net_optimized
    
    def optimize_storage_irq(self) -> bool:
        """
        Otimiza IRQ de controladoras de armazenamento (NVMe, SATA)
        """
        if not self.is_admin:
            return False
        
        devices = self.get_pci_devices()
        storage_optimized = False
        
        keywords = ['nvme', 'ssd', 'sata', 'ahci', 'storage', 'raid']
        
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI habilitado para storage: {device['name'][:40]}")
                    storage_optimized = True
                
                # Storage distribuído entre todos os cores
                all_cores = (1 << self.cpu_count) - 1
                self.set_device_affinity(device['path'], all_cores)
        
        self.applied_changes['storage_irq'] = storage_optimized
        return storage_optimized
    
    def optimize_usb_irq(self) -> bool:
        """
        Otimiza IRQ de controladores USB
        """
        if not self.is_admin:
            return False
        
        devices = self.get_pci_devices()
        usb_optimized = False
        
        keywords = ['usb', 'xhci', 'ehci', 'ohci']
        
        for device in devices:
            name_lower = device['name'].lower()
            if any(kw in name_lower for kw in keywords):
                if self.enable_msi_for_device(device['path']):
                    print(f"[IRQ] ✓ MSI habilitado para USB: {device['name'][:40]}")
                    usb_optimized = True
                
                # USB para cores baixos (junto com rede)
                usb_mask = 0x03
                self.set_device_affinity(device['path'], usb_mask)
        
        self.applied_changes['usb_irq'] = usb_optimized
        return usb_optimized
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """
        Aplica otimizações de IRQ para todos os dispositivos relevantes
        """
        print("\n[IRQ] Aplicando otimizações de afinidade de IRQ...")
        
        results = {}
        
        results['gpu'] = self.optimize_gpu_irq()
        results['network'] = self.optimize_network_irq()
        results['storage'] = self.optimize_storage_irq()
        results['usb'] = self.optimize_usb_irq()
        
        success_count = sum(results.values())
        print(f"[IRQ] Resultado: {success_count}/{len(results)} categorias otimizadas")
        print("[IRQ] ⚠ Reinicie o PC para aplicar mudanças de IRQ")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna resumo das configurações de IRQ"""
        devices = self.get_pci_devices()
        
        status = {
            'total_pci_devices': len(devices),
            'cpu_cores': self.cpu_count
        }
        
        # Conta dispositivos por categoria
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
    print(f"\nDispositivos PCI encontrados: {len(devices)}")
    for d in devices[:10]:
        print(f"  - {d['name'][:60]}")
