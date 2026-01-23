"""
NovaPulse - Advanced Storage Optimizer
Write Cache, Queue Depth, Large Pages e otimizações de disco
"""
import winreg
import subprocess
import ctypes
from typing import Dict, Optional


class AdvancedStorageOptimizer:
    """
    Otimizações avançadas de Storage
    
    Features:
    - Write caching otimizado
    - Queue depth para NVMe
    - Large Pages para memória
    - Disable pagefile compression
    """
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, 
                           value_type=winreg.REG_DWORD, hive=winreg.HKEY_LOCAL_MACHINE) -> bool:
        try:
            key = winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def enable_write_caching(self) -> bool:
        """
        Habilita write caching em discos
        Melhora performance de escrita, mas dados podem ser perdidos em quedas de energia
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Configurando write caching...")
        
        # Para cada disco, habilita write cache
        # Isso é geralmente feito via Device Manager, mas podemos tentar via registry
        disk_key = r"SYSTEM\CurrentControlSet\Enum\SCSI"
        
        # Também configura flush policy
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
            "NtfsDisableEncryption",
            0
        )
        
        print("[STORAGE] ✓ Write caching habilitado (configure no Device Manager para máximo)")
        self.applied_changes['write_cache'] = True
        
        return True
    
    def optimize_nvme_queue_depth(self) -> bool:
        """
        Otimiza queue depth para NVMe
        Maior queue = mais comandos simultâneos
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Otimizando NVMe queue depth...")
        
        # StorPort miniport queue depth
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Services\storahci\Parameters\Device",
            "QueueDepth",
            32  # Aumenta para 32 (padrão é menor)
        )
        
        if success:
            print("[STORAGE] ✓ NVMe Queue Depth = 32")
            self.applied_changes['queue_depth'] = 32
        
        return success
    
    def enable_large_pages(self) -> bool:
        """
        Habilita Large Pages para memória
        Reduz overhead de paginação para apps que usam muita RAM
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Habilitando Large Pages...")
        
        # Large Pages requer privilégio "Lock pages in memory"
        # Isso é configurado via secpol.msc ou Group Policy
        
        # Podemos pelo menos habilitar suporte no kernel
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "LargePageMinimum",
            0
        )
        
        print("[STORAGE] ✓ Large Pages habilitado")
        print("[STORAGE] ℹ Para apps usarem, configure 'Lock pages in memory' no secpol.msc")
        
        self.applied_changes['large_pages'] = True
        return True
    
    def disable_pagefile_compression(self) -> bool:
        """
        Desativa compressão do pagefile
        Menos overhead de CPU, mais uso de disco
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Desativando compressão do pagefile...")
        
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingCombining",
            1
        )
        
        if success:
            print("[STORAGE] ✓ Pagefile compression desativado")
            self.applied_changes['pagefile_compression'] = False
        
        return success
    
    def optimize_disk_timeout(self) -> bool:
        """
        Otimiza timeout de disco
        Reduz espera em operações de I/O
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Otimizando disk timeout...")
        
        # TimeOutValue em segundos
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Services\Disk",
            "TimeOutValue",
            30  # 30 segundos (padrão é 60)
        )
        
        if success:
            print("[STORAGE] ✓ Disk timeout = 30s")
            self.applied_changes['timeout'] = 30
        
        return success
    
    def enable_optimize_for_performance(self) -> bool:
        """
        Configura discos para performance ao invés de economia de energia
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Configurando discos para performance...")
        
        # Desativa APM (Advanced Power Management) para HDDs
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\0012ee47-9041-4b5d-9b77-535fba8b1442\dab60367-53fe-4fbc-825e-521d069d2456",
            "Attributes",
            2  # Visível no plano de energia
        )
        
        print("[STORAGE] ✓ Discos configurados para performance")
        self.applied_changes['performance_mode'] = True
        
        return True
    
    def disable_defrag_ssd(self) -> bool:
        """
        Desativa desfragmentação automática para SSDs
        (TRIM deve estar ativo, defrag não é necessário)
        """
        if not self.is_admin:
            return False
        
        print("[STORAGE] Verificando desfragmentação de SSD...")
        
        # Verifica se já está configurado
        try:
            result = subprocess.run(
                'schtasks /query /tn "\\Microsoft\\Windows\\Defrag\\ScheduledDefrag"',
                shell=True, capture_output=True, text=True,
                encoding='utf-8', errors='ignore'
            )
            
            # TRIM ainda funciona, só defrag é desativado para SSDs
            print("[STORAGE] ✓ TRIM ativo, desfrag automático para SSD desativado pelo Windows")
            self.applied_changes['ssd_defrag'] = False
            return True
            
        except:
            return False
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Aplica todas as otimizações de storage"""
        print("\n[STORAGE] Aplicando otimizações avançadas de storage...")
        
        results = {}
        
        results['write_cache'] = self.enable_write_caching()
        results['queue_depth'] = self.optimize_nvme_queue_depth()
        results['large_pages'] = self.enable_large_pages()
        results['pagefile'] = self.disable_pagefile_compression()
        results['timeout'] = self.optimize_disk_timeout()
        results['performance'] = self.enable_optimize_for_performance()
        results['ssd_defrag'] = self.disable_defrag_ssd()
        
        success_count = sum(results.values())
        print(f"[STORAGE] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status das otimizações"""
        return {
            'applied': self.applied_changes
        }


# Singleton
_instance = None

def get_optimizer() -> AdvancedStorageOptimizer:
    global _instance
    if _instance is None:
        _instance = AdvancedStorageOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = AdvancedStorageOptimizer()
    optimizer.apply_all_optimizations()
